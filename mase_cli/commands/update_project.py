"""mase update — manifest-driven, previewable and non-destructive migration."""

from __future__ import annotations

import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

import yaml

from mase_cli.config import load_manifest
from mase_cli.rules import RuleSynchronizer


LEGACY_VERSION = "1.3"
REQUIRED_GITIGNORE_ENTRIES = ["e2e/sandbox/", ".mase-backup/", ".mase/cache/"]
SANDBOX_SUBDIRS = ["uploads", "exports", "logs", "snapshots", "backups"]
PathInput = Union[str, Path]


def _version(framework: Path) -> str:
    manifest = framework / "framework-manifest.yaml"
    return str(load_manifest(framework)["version"]) if manifest.exists() else LEGACY_VERSION


def _change(component: str, action: str, reason: str, **extra) -> dict:
    return {"component": component, "action": action, "reason": reason, **extra}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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
    framework = Path(framework_home).expanduser().resolve() if framework_home else Path.home() / ".measures-framework"
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
    missing_metadata = [key for key in ("profile", "stack") if key not in mase_metadata]
    if current_version != target_version or missing_metadata:
        changes.append(
            _change(
                ".mase.yaml",
                "update",
                f"metadata migration: {current_version} -> {target_version}",
                target_version=target_version,
            )
        )

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
    if not path.exists() or path.is_dir():
        return
    relative = path.relative_to(project)
    target = backup_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
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
) -> None:
    project = Path(project_dir).expanduser().resolve()
    if dry_run:
        for change in changes:
            print(f"[dry-run] {change['action']}: {change['component']} — {change['reason']}")
        return
    if not changes:
        return
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
        if component == ".mase.yaml":
            _backup(target, project, backup_root)
            _apply_version(target, str(change["target_version"]), project)
        elif component == ".gitignore":
            _backup(target, project, backup_root)
            existing = _read(target) if target.exists() else ""
            addition = "\n".join(change["entries"])
            target.write_text(existing.rstrip() + "\n" + addition + "\n", encoding="utf-8")
        elif component == "tests/e2e/sandbox/":
            for child in SANDBOX_SUBDIRS:
                (target / child).mkdir(parents=True, exist_ok=True)
        else:
            _backup(target, project, backup_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            if change.get("source"):
                shutil.copy2(change["source"], target)
            elif change.get("content") is not None:
                target.write_text(change["content"], encoding="utf-8")


def run(args):
    changes = check_updates(args.dir)
    if getattr(args, "check_only", False):
        for change in changes:
            print(f"{change['action']}: {change['component']} — {change['reason']}")
        return changes
    apply_updates(changes, args.dir, getattr(args, "dry_run", False))
    return changes
