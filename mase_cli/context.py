"""Auditable, manifest-backed context planning without concatenating contents."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Union

from mase_cli.config import load_manifest
from mase_cli.schema import GovernanceError, load_yaml_document


PathInput = Union[str, Path]
DEFAULT_BUDGETS = {
    "lite": {"input_tokens": 8000, "max_files": 12, "max_characters": 32000},
    "standard": {"input_tokens": 16000, "max_files": 24, "max_characters": 64000},
    "strict": {"input_tokens": 24000, "max_files": 36, "max_characters": 96000},
}


@dataclass(frozen=True)
class ContextItem:
    path: str
    reason: str
    characters: int = 0
    override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "reason": self.reason,
            "characters": self.characters,
            "override": self.override,
        }


@dataclass(frozen=True)
class ContextPlan:
    change: str
    profile: str
    included: tuple[ContextItem, ...]
    excluded: tuple[ContextItem, ...]
    characters: int
    measurement_kind: str
    token_budget: int
    max_files: int
    max_characters: int
    over_budget: bool
    budget_reasons: tuple[str, ...]
    state_summary: dict[str, Any]
    scope_kind: str = "change"
    scope_name: str = ""
    diagnostics: tuple[str, ...] = ()
    budget_override_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "profile": self.profile,
            "measurement_kind": self.measurement_kind,
            "token_budget": self.token_budget,
            "max_files": self.max_files,
            "max_characters": self.max_characters,
            "files": len(self.included),
            "characters": self.characters,
            "over_budget": self.over_budget,
            "budget_reasons": list(self.budget_reasons),
            "state_summary": dict(self.state_summary),
            "scope": {"kind": self.scope_kind, "name": self.scope_name},
            "diagnostics": list(self.diagnostics),
            "budget_override_reason": self.budget_override_reason,
            "included": [item.to_dict() for item in self.included],
            "excluded": [item.to_dict() for item in self.excluded],
            "note": "Characters and file counts are context proxies, not Token counts.",
        }


def _safe_relative(root: Path, value: str) -> str:
    raw = str(value or "").replace("\\", "/").strip()
    if not raw or Path(raw).is_absolute() or ".." in raw.split("/"):
        raise GovernanceError(f"context path must be project-relative: {value}", code="path")
    candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise GovernanceError(f"context path escapes project root: {value}", code="path") from exc
    return raw.rstrip("/")


def _matches_exclusion(relative: str, patterns: Iterable[str]) -> Optional[str]:
    normalized = relative.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    for raw in patterns:
        pattern = str(raw).replace("\\", "/").strip("/")
        if not pattern:
            continue
        if normalized == pattern or normalized.startswith(pattern + "/"):
            return pattern
        if fnmatch.fnmatchcase(normalized, pattern) or fnmatch.fnmatchcase(normalized, pattern + "/**"):
            return pattern
        if "/" not in pattern and pattern in parts:
            return pattern
    return None


def _expand_candidate(root: Path, relative: str, *, expand_directory: bool = True) -> list[Path]:
    safe = _safe_relative(root, relative)
    if any(char in safe for char in "*[?"):
        matches = []
        for path in root.glob(safe):
            if path.is_file():
                matches.append(path)
            elif path.is_dir():
                matches.extend(item for item in path.rglob("*") if item.is_file())
        return sorted(set(matches))
    path = root / safe
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(item for item in path.rglob("*") if item.is_file()) if expand_directory else []
    return []


_TASK_LINE = re.compile(r"^- \[[ xX]\] (?P<id>[A-Za-z0-9_.-]+)\s")
_TASK_READS = re.compile(r"^\s*(?:-\s*)?reads\s*:\s*(?P<paths>.+)$", re.IGNORECASE)
_TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".css", ".csv", ".go", ".h", ".html", ".java",
    ".js", ".json", ".jsx", ".kt", ".md", ".mjs", ".properties", ".py",
    ".rb", ".rs", ".sh", ".sql", ".swift", ".toml", ".ts", ".tsx", ".txt",
    ".xml", ".yaml", ".yml",
}
_CANONICAL_HIDDEN_CONTEXT = {".mase/gates.yaml", ".mase/tests.yaml"}


def _task_reads(tasks_path: Path, task_id: str) -> tuple[str, ...]:
    if not tasks_path.is_file():
        raise GovernanceError("tasks.md is missing", path=tasks_path, code="not_found")
    active = False
    reads: list[str] = []
    found = False
    for line in tasks_path.read_text(encoding="utf-8").splitlines():
        task = _TASK_LINE.match(line)
        if task:
            active = task.group("id") == task_id
            found = found or active
            continue
        if active:
            match = _TASK_READS.match(line)
            if match:
                reads.extend(item.strip() for item in match.group("paths").split(",") if item.strip())
    if not found:
        raise GovernanceError(f"task is not declared: {task_id}", path=tasks_path, code="not_found")
    if not reads:
        raise GovernanceError(
            f"task {task_id} does not declare reads", path=tasks_path, code="incomplete"
        )
    return tuple(dict.fromkeys(reads))


def _is_text_candidate(path: Path, relative: str) -> bool:
    hidden = any(part.startswith(".") for part in Path(relative).parts)
    if path.name == ".DS_Store" or (hidden and relative not in _CANONICAL_HIDDEN_CONTEXT):
        return False
    if path.suffix.lower() in _TEXT_SUFFIXES or not path.suffix:
        try:
            return b"\x00" not in path.read_bytes()[:4096]
        except OSError:
            return False
    return False


def build_context_plan(
    project_root: PathInput,
    change_name: str,
    *,
    explicit_reads: Iterable[str] = (),
    allow_excluded: bool = False,
    task: str = "",
    capability: str = "",
    allow_over_budget: bool = False,
    budget_reason: str = "",
    manifest: Optional[Mapping[str, Any]] = None,
) -> ContextPlan:
    root = Path(project_root).expanduser().resolve()
    if Path(change_name).name != change_name or change_name in {"", ".", ".."}:
        raise GovernanceError("change name must be a single safe path component", code="invalid_name")
    change = root / "openspec" / "changes" / change_name
    state_path = change / "mase-state.yaml"
    if not state_path.is_file():
        raise GovernanceError(f"change state not found: {change_name}", path=state_path, code="not_found")

    state = load_yaml_document(state_path)
    if task and capability:
        raise GovernanceError("context plan accepts either task or capability, not both", code="conflict")
    profile = str(state.get("profile", "standard"))
    manifest_data = dict(manifest or load_manifest())
    exclusions = tuple(str(item) for item in manifest_data.get("default_context_excludes", []))
    budgets = {**DEFAULT_BUDGETS, **dict(manifest_data.get("context_budgets", {}))}
    budget = dict(budgets.get(profile, DEFAULT_BUDGETS["standard"]))

    candidates: list[tuple[str, str, bool]] = []
    diagnostics: list[str] = []
    scope_kind = "task" if task else ("capability" if capability else "change")
    scope_name = task or capability
    rules = root / "project-rules.md"
    if rules.is_file():
        candidates.append(("project-rules.md", "project rules", False))
    specs = sorted((change / "specs").glob("**/spec.md")) if (change / "specs").is_dir() else ()
    for spec in specs:
        if capability and spec.parent.name != capability:
            continue
        candidates.append((spec.relative_to(root).as_posix(), "current spec", False))
    if (change / "tasks.md").is_file():
        candidates.append(((change / "tasks.md").relative_to(root).as_posix(), "current tasks", False))
    if task:
        for read in _task_reads(change / "tasks.md", task):
            candidates.append((read, f"task {task} reads", False))
    elif capability:
        risk_capabilities = dict(state.get("risk", {})).get("capabilities", {})
        impact_capabilities = dict(state.get("impact_analysis", {})).get("capabilities", {})
        definition = dict(risk_capabilities.get(capability, {}))
        impact_definition = dict(impact_capabilities.get(capability, {}))
        paths = definition.get("paths") or impact_definition.get("paths") or ()
        if not paths:
            raise GovernanceError(
                f"capability has no precise paths: {capability}", path=state_path, code="incomplete"
            )
        for impact in paths:
            candidates.append((str(impact), f"capability {capability}", False))
    else:
        for impact in state.get("impact", {}).get("paths", []):
            candidates.append((str(impact), "change impact", False))
    for explicit in explicit_reads:
        candidates.append((str(explicit), "explicit read", True))

    included: dict[str, ContextItem] = {}
    excluded: dict[str, ContextItem] = {}
    for candidate, reason, explicit in candidates:
        safe_candidate = _safe_relative(root, candidate)
        matched_candidate = _matches_exclusion(safe_candidate, exclusions)
        direct_path = root / safe_candidate
        broad_change_directory = (
            not explicit
            and not any(char in safe_candidate for char in "*[?")
            and direct_path.is_dir()
        )
        if broad_change_directory:
            diagnostics.append(
                f"broad_scope:{safe_candidate}:use --task, --capability or explicit --read"
            )
            excluded.setdefault(
                safe_candidate,
                ContextItem(safe_candidate, "broad directory not expanded"),
            )
            continue
        expanded = _expand_candidate(root, safe_candidate)
        if not expanded and matched_candidate:
            excluded.setdefault(
                safe_candidate,
                ContextItem(safe_candidate, f"excluded by {matched_candidate}"),
            )
        for path in expanded:
            relative = path.relative_to(root).as_posix()
            matched = _matches_exclusion(relative, exclusions)
            if matched and not (explicit and allow_excluded):
                excluded.setdefault(relative, ContextItem(relative, f"excluded by {matched}"))
                continue
            if not (matched and explicit and allow_excluded) and not _is_text_candidate(path, relative):
                excluded.setdefault(relative, ContextItem(relative, "non-text or hidden file"))
                continue
            characters = len(path.read_text(encoding="utf-8", errors="replace"))
            item = ContextItem(
                relative,
                f"{reason}; exclusion override" if matched else reason,
                characters,
                override=bool(matched),
            )
            if relative not in included or explicit:
                included[relative] = item

    ordered = tuple(included[key] for key in sorted(included))
    excluded_items = tuple(excluded[key] for key in sorted(excluded))
    characters = sum(item.characters for item in ordered)
    max_files = int(budget.get("max_files", 0) or 0)
    max_characters = int(budget.get("max_characters", 0) or 0)
    reasons = []
    if max_files and len(ordered) > max_files:
        reasons.append("files")
    if max_characters and characters > max_characters:
        reasons.append("characters")
    if allow_over_budget and reasons and not str(budget_reason).strip():
        raise GovernanceError("over-budget context requires --budget-reason", code="incomplete")

    return ContextPlan(
        change=change_name,
        profile=profile,
        included=ordered,
        excluded=excluded_items,
        characters=characters,
        measurement_kind="context_proxy",
        token_budget=int(budget.get("input_tokens", 0) or 0),
        max_files=max_files,
        max_characters=max_characters,
        over_budget=bool(reasons),
        budget_reasons=tuple(reasons),
        state_summary={
            "phase": state.get("phase", ""),
            "risk_triggers": list(state.get("risk", {}).get("triggers", [])),
            "impact_paths": list(state.get("impact", {}).get("paths", [])),
        },
        scope_kind=scope_kind,
        scope_name=scope_name,
        diagnostics=tuple(dict.fromkeys(diagnostics)),
        budget_override_reason=str(budget_reason).strip() if allow_over_budget else "",
    )
