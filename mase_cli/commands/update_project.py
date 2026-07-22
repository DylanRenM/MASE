"""mase update — manifest-driven, previewable and non-destructive migration."""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

import yaml

from mase_cli.config import framework_home as resolve_framework_home, load_manifest
from mase_cli.rules import RuleSynchronizer
from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


LEGACY_VERSION = "1.3"
REQUIRED_GITIGNORE_ENTRIES = ["e2e/sandbox/", ".mase-backup/", ".mase/cache/"]
SANDBOX_SUBDIRS = ["uploads", "exports", "logs", "snapshots", "backups"]
PathInput = Union[str, Path]
ALLOWED_STACKS = {"generic", "python", "swift"}


def _version(framework: Path) -> str:
    manifest = framework / "framework-manifest.yaml"
    return str(load_manifest(framework)["version"]) if manifest.exists() else LEGACY_VERSION


def _change(component: str, action: str, reason: str, **extra) -> dict:
    return {"component": component, "action": action, "reason": reason, **extra}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _render_yaml(payload: dict) -> str:
    return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)


def _normalize_stack(value: object, project: Path) -> tuple[str, list[str]]:
    raw = str(value or "").strip().lower()
    tokens = [item for item in re.split(r"[^a-z0-9.#+]+", raw) if item]
    if raw in ALLOWED_STACKS:
        primary = raw
    elif (project / "Package.swift").exists() or "swift" in tokens:
        primary = "swift"
    elif (project / "pyproject.toml").exists() or "python" in tokens:
        primary = "python"
    else:
        primary = "generic"
    toolchains = sorted({item for item in tokens if item not in ALLOWED_STACKS and item != primary})
    return primary, toolchains


def _metadata_migration(marker: Path, project: Path, target_version: str) -> dict:
    payload = load_yaml_document(marker)
    metadata = payload.get("mase")
    if not isinstance(metadata, dict):
        raise GovernanceError("mase must be a mapping", path=marker, code="schema")
    migrated = {**payload, "mase": dict(metadata)}
    target = migrated["mase"]
    primary, inferred_tools = _normalize_stack(target.get("stack"), project)
    existing_tools = target.get("toolchains", [])
    if not isinstance(existing_tools, list):
        raise GovernanceError("mase.toolchains must be an array", path=marker, code="schema")
    target["version"] = target_version
    target.setdefault("project", project.name)
    target.setdefault("profile", "standard")
    target["stack"] = primary
    target["toolchains"] = sorted(
        {str(item).strip().lower() for item in [*existing_tools, *inferred_tools] if str(item).strip()}
    )
    validate_payload(migrated, "mase-project.schema.json", path=marker)
    return migrated


def _state_migration(state_path: Path, project: Path, project_metadata: dict) -> tuple[dict, list[str]]:
    payload = load_yaml_document(state_path)
    schema = payload.get("schema")
    if schema not in (None, "mase-project/v2"):
        raise GovernanceError(f"unsupported state schema: {schema}", path=state_path, code="schema")
    migrated = dict(payload)
    changes: list[str] = []
    migrated["schema"] = "mase-project/v2"
    migrated.setdefault("profile", project_metadata.get("profile", "standard"))

    primary, inferred_tools = _normalize_stack(
        migrated.get("stack", project_metadata.get("stack", "generic")), project
    )
    existing_tools = migrated.get("toolchains", [])
    if not isinstance(existing_tools, list):
        raise GovernanceError("toolchains must be an array", path=state_path, code="schema")
    project_tools = project_metadata.get("toolchains", [])
    migrated["stack"] = primary
    migrated["toolchains"] = sorted(
        {
            str(item).strip().lower()
            for item in [*project_tools, *existing_tools, *inferred_tools]
            if str(item).strip()
        }
    )
    if migrated.get("stack") != payload.get("stack") or migrated["toolchains"] != payload.get("toolchains", []):
        changes.append("stack/toolchains")

    if "product" not in migrated:
        old_product = migrated.pop("project_type", {})
        migrated["product"] = dict(old_product) if isinstance(old_product, dict) else {}
        changes.append("product")
    migrated["product"].setdefault("has_ui", False)
    migrated.setdefault("impact", {"ui_changed": False, "paths": []})
    migrated["impact"].setdefault("ui_changed", False)
    migrated["impact"].setdefault("paths", [])
    migrated.setdefault("phase", "build")
    migrated.setdefault("risk", {"triggers": [], "capabilities": {}})
    migrated["risk"].setdefault("triggers", [])
    migrated["risk"].setdefault("capabilities", {})
    migrated.setdefault("gates", {})
    migrated.setdefault("evidence", [])
    migrated.setdefault("dependencies", [])
    migrated.setdefault("conflicts_with", [])
    migrated.setdefault("blockers", [])

    structured_passes: set[str] = set()
    migrated_evidence = []
    for raw in migrated["evidence"]:
        if not isinstance(raw, dict):
            raise GovernanceError("evidence entries must be mappings", path=state_path, code="schema")
        item = dict(raw)
        kind = item.get("kind")
        if kind not in {"automatic", "manual"}:
            item["kind"] = "legacy"
            if item.get("result") == "passed":
                item["result"] = "stale"
            changes.append("evidence")
        elif item.get("result") == "passed":
            structured_passes.add(str(item.get("gate", "")))
        migrated_evidence.append(item)
    migrated["evidence"] = migrated_evidence
    for gate, result in list(migrated["gates"].items()):
        if result == "passed" and gate not in structured_passes:
            migrated["gates"][gate] = "stale"
            if "evidence" not in changes:
                changes.append("evidence")

    validate_payload(migrated, "mase-state.schema.json", path=state_path)
    if migrated != payload and not changes:
        changes.append("schema defaults")
    return migrated, changes


def _template_change(project: Path, framework: Path, relative: str) -> Optional[dict]:
    source = framework / "templates" / relative
    if not source.exists():
        return None
    target = project / relative
    if not target.exists():
        return _change(relative, "create", "framework template is missing", source=str(source))
    if _read(target) != _read(source):
        return _change(relative, "conflict", "project file differs from framework template", source=str(source))
    return None


def check_updates(project_dir: PathInput = ".", framework_home: Optional[PathInput] = None) -> list[dict]:
    project = Path(project_dir).expanduser().resolve()
    framework = (
        Path(framework_home).expanduser().resolve()
        if framework_home
        else resolve_framework_home()
    )
    marker = project / ".mase.yaml"
    if not marker.exists():
        print("错误: 当前目录不是 MASE 项目（未找到 .mase.yaml）")
        raise SystemExit(1)

    changes: list[dict] = []
    target_version = _version(framework)
    marker_text = _read(marker)
    marker_payload = yaml.safe_load(marker_text) or {}
    mase_metadata = marker_payload.get("mase", {}) if isinstance(marker_payload, dict) else {}
    match = re.search(r'version:\s*["\']?([^"\'\s]+)', marker_text)
    current_version = match.group(1) if match else "0.0"
    try:
        migrated_marker = _metadata_migration(marker, project, target_version)
    except (GovernanceError, ValueError) as exc:
        changes.append(
            _change(
                ".mase.yaml",
                "conflict",
                f"metadata migration could not be validated: {exc}",
            )
        )
        migrated_metadata = mase_metadata if isinstance(mase_metadata, dict) else {}
    else:
        migrated_metadata = migrated_marker["mase"]
        if migrated_marker != marker_payload:
            changes.append(
                _change(
                    ".mase.yaml",
                    "update",
                    f"metadata/stack/toolchains migration: {current_version} -> {target_version}",
                    target_version=target_version,
                    content=_render_yaml(migrated_marker),
                )
            )

    changes_root = project / "openspec" / "changes"
    if changes_root.is_dir():
        for change_dir in sorted(item for item in changes_root.iterdir() if item.is_dir()):
            state_path = change_dir / "mase-state.yaml"
            if not state_path.exists():
                continue
            relative = state_path.relative_to(project).as_posix()
            try:
                migrated_state, state_categories = _state_migration(
                    state_path, project, migrated_metadata
                )
            except (GovernanceError, ValueError) as exc:
                changes.append(
                    _change(relative, "conflict", f"state migration could not be validated: {exc}")
                )
                continue
            original_state = load_yaml_document(state_path)
            if migrated_state != original_state:
                categories = ", ".join(dict.fromkeys(state_categories))
                changes.append(
                    _change(
                        relative,
                        "update",
                        f"state migration: {categories}",
                        content=_render_yaml(migrated_state),
                    )
                )

    baseline = project / ".mase" / "baseline.yaml"
    if baseline.exists():
        try:
            baseline_payload = load_yaml_document(baseline)
            validate_payload(baseline_payload, "mase-baseline.schema.json", path=baseline)
        except (GovernanceError, ValueError) as exc:
            changes.append(
                _change(
                    ".mase/baseline.yaml",
                    "conflict",
                    f"baseline migration could not be validated: {exc}",
                )
            )

    gate_template = framework / "templates" / "gates.yaml"
    project_gates = project / ".mase" / "gates.yaml"
    if gate_template.is_file() and not project_gates.exists():
        changes.append(_change(
            ".mase/gates.yaml",
            "create",
            "canonical gate definitions are missing; legacy mode keeps candidate freeze, exact reuse, covers and "
            "overlap diagnostics remain unavailable until the generated template is configured",
            source=str(gate_template),
        ))

    canonical = framework / "project-rules.md"
    if canonical.exists():
        project_rules = project / "project-rules.md"
        if not project_rules.exists():
            changes.append(_change("project-rules.md", "create", "canonical rules missing", source=str(canonical)))
        elif _read(project_rules) != _read(canonical):
            changes.append(_change("project-rules.md", "update", "canonical rules changed", source=str(canonical)))
        sync = RuleSynchronizer(canonical)
        for item in sync.plan(project):
            relative = str(item.path.relative_to(project))
            if item.action != "none":
                changes.append(
                    _change(
                        relative,
                        item.action,
                        item.reason,
                        content=item.content,
                    )
                )

    for relative in (
        "sandbox.config.json",
        "tests/e2e/helpers/sandbox.js",
        "tests/e2e/conftest.py",
    ):
        candidate = _template_change(project, framework, relative)
        if candidate:
            changes.append(candidate)

    sandbox = project / "tests" / "e2e" / "sandbox"
    if any(not (sandbox / child).is_dir() for child in SANDBOX_SUBDIRS):
        changes.append(_change("tests/e2e/sandbox/", "create", "sandbox directories are incomplete"))

    gitignore = project / ".gitignore"
    content = _read(gitignore) if gitignore.exists() else ""
    missing = [entry for entry in REQUIRED_GITIGNORE_ENTRIES if entry not in content.splitlines()]
    if missing:
        changes.append(_change(".gitignore", "update", "required entries missing", entries=missing))
    return changes


def _backup(path: Path, project: Path, backup_root: Path) -> None:
    if not path.exists():
        return
    relative = path.relative_to(project)
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.is_dir():
        shutil.copytree(path, target, dirs_exist_ok=True)
    else:
        shutil.copy2(path, target)


def _apply_version(path: Path, target_version: str, project: Path) -> None:
    payload = yaml.safe_load(_read(path)) or {}
    if not isinstance(payload, dict):
        raise ValueError(".mase.yaml must contain a mapping")
    metadata = payload.setdefault("mase", {})
    metadata["version"] = target_version
    metadata.setdefault("profile", "standard")
    if "stack" not in metadata:
        if (project / "Package.swift").exists():
            metadata["stack"] = "swift"
        elif (project / "pyproject.toml").exists():
            metadata["stack"] = "python"
        else:
            metadata["stack"] = "generic"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def apply_updates(
    changes: list[dict],
    project_dir: PathInput = ".",
    dry_run: bool = False,
    framework_home: Optional[PathInput] = None,
) -> Optional[Path]:
    project = Path(project_dir).expanduser().resolve()
    if dry_run:
        for change in changes:
            print(f"[dry-run] {change['action']}: {change['component']} — {change['reason']}")
        return None
    if not changes:
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = project / ".mase-backup" / stamp
    backup_root.mkdir(parents=True, exist_ok=True)

    for change in changes:
        component = change["component"]
        action = change["action"]
        target = project / component.rstrip("/")
        if action == "conflict":
            _backup(target, project, backup_root)
            print(f"! conflict preserved: {component}")
            continue
        if component == ".mase.yaml" and change.get("content") is None:
            _backup(target, project, backup_root)
            _apply_version(target, str(change["target_version"]), project)
        elif component == ".gitignore":
            _backup(target, project, backup_root)
            existing = _read(target) if target.exists() else ""
            addition = "\n".join(change["entries"])
            target.write_text(existing.rstrip() + "\n" + addition + "\n", encoding="utf-8")
        elif component == "tests/e2e/sandbox/":
            _backup(target, project, backup_root)
            for child in SANDBOX_SUBDIRS:
                (target / child).mkdir(parents=True, exist_ok=True)
        else:
            _backup(target, project, backup_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            if change.get("source"):
                shutil.copy2(change["source"], target)
            elif change.get("content") is not None:
                target.write_text(change["content"], encoding="utf-8")
    return backup_root


def rollback_updates(
    changes: list[dict],
    project_dir: PathInput,
    backup_root: PathInput,
    *,
    dry_run: bool = False,
) -> None:
    """Restore one update plan from its backup, including partially created directories."""

    project = Path(project_dir).expanduser().resolve()
    backup = Path(backup_root).expanduser().resolve()
    if not backup.is_dir():
        raise FileNotFoundError(f"migration backup does not exist: {backup}")
    for change in reversed(changes):
        if change.get("action") == "conflict":
            continue
        relative = str(change["component"]).rstrip("/")
        target = (project / relative).resolve()
        try:
            target.relative_to(project)
        except ValueError as exc:
            raise ValueError(f"Unsafe rollback component: {relative}") from exc
        saved = backup / relative
        if dry_run:
            print(f"[dry-run] rollback: {relative}")
            continue
        if saved.exists():
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            target.parent.mkdir(parents=True, exist_ok=True)
            if saved.is_dir():
                shutil.copytree(saved, target)
            else:
                shutil.copy2(saved, target)
        elif change.get("action") == "create":
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()


def run(args):
    changes = check_updates(args.dir)
    if getattr(args, "check_only", False):
        for change in changes:
            print(f"{change['action']}: {change['component']} — {change['reason']}")
        return changes
    apply_updates(changes, args.dir, getattr(args, "dry_run", False))
    return changes
