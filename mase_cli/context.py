"""Auditable, manifest-backed context planning without concatenating contents."""

from __future__ import annotations

import fnmatch
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


def _expand_candidate(root: Path, relative: str) -> list[Path]:
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
        return sorted(item for item in path.rglob("*") if item.is_file())
    return []


def build_context_plan(
    project_root: PathInput,
    change_name: str,
    *,
    explicit_reads: Iterable[str] = (),
    allow_excluded: bool = False,
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
    profile = str(state.get("profile", "standard"))
    manifest_data = dict(manifest or load_manifest())
    exclusions = tuple(str(item) for item in manifest_data.get("default_context_excludes", []))
    budgets = {**DEFAULT_BUDGETS, **dict(manifest_data.get("context_budgets", {}))}
    budget = dict(budgets.get(profile, DEFAULT_BUDGETS["standard"]))

    candidates: list[tuple[str, str, bool]] = []
    rules = root / "project-rules.md"
    if rules.is_file():
        candidates.append(("project-rules.md", "project rules", False))
    for spec in sorted((change / "specs").glob("**/spec.md")) if (change / "specs").is_dir() else ():
        candidates.append((spec.relative_to(root).as_posix(), "current spec", False))
    if (change / "tasks.md").is_file():
        candidates.append(((change / "tasks.md").relative_to(root).as_posix(), "current tasks", False))
    for impact in state.get("impact", {}).get("paths", []):
        candidates.append((str(impact), "change impact", False))
    for explicit in explicit_reads:
        candidates.append((str(explicit), "explicit read", True))

    included: dict[str, ContextItem] = {}
    excluded: dict[str, ContextItem] = {}
    for candidate, reason, explicit in candidates:
        safe_candidate = _safe_relative(root, candidate)
        matched_candidate = _matches_exclusion(safe_candidate, exclusions)
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
    )
