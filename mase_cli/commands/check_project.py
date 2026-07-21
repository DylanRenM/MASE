"""mase check — profile- and stack-aware project compliance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Union

from mase_cli.schema import GovernanceError, ProjectMetadata
from mase_cli.state import ChangeState


@dataclass(frozen=True)
class CheckItem:
    path: str
    ok: bool
    required: bool = True
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "ok": self.ok, "required": self.required, "message": self.message}


@dataclass(frozen=True)
class ProjectReport:
    root: Path
    stack: str
    profile: str
    items: tuple[CheckItem, ...]

    @property
    def ok(self) -> bool:
        return all(item.ok or not item.required for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "root": str(self.root),
            "stack": self.stack,
            "profile": self.profile,
            "items": [item.to_dict() for item in self.items],
        }


def _exists(root: Path, relative: str, required: bool = True) -> CheckItem:
    present = (root / relative).exists()
    return CheckItem(relative, present, required, "present" if present else "missing")


def inspect_project(project_dir: Union[str, Path] = ".") -> ProjectReport:
    root = Path(project_dir).expanduser().resolve()
    marker = root / ".mase.yaml"
    if not marker.exists():
        return ProjectReport(root, "unknown", "unknown", (CheckItem(".mase.yaml", False),))
    try:
        metadata = ProjectMetadata.load(marker, allow_legacy=True)
    except GovernanceError as exc:
        return ProjectReport(
            root,
            "unknown",
            "unknown",
            (CheckItem(".mase.yaml", False, True, str(exc)),),
        )
    stack = metadata.stack
    profile = metadata.profile
    layout = metadata.layout
    common = [
        _exists(root, ".mase.yaml"),
        _exists(root, "README.md"),
        _exists(root, ".gitignore"),
        _exists(root, "project-rules.md"),
        _exists(root, "openspec/changes"),
    ]
    stack_items: List[CheckItem] = []
    if stack == "python":
        stack_items.extend((_exists(root, "pyproject.toml"), _exists(root, "src"), _exists(root, "tests")))
    elif stack == "swift":
        product_root = str(layout.get("product", "Sources"))
        test_root = str(layout.get("tests", "Tests"))
        stack_items.extend(
            (_exists(root, "Package.swift"), _exists(root, product_root), _exists(root, test_root))
        )
    elif stack == "generic":
        # Generic projects may be frameworks, documentation repositories, or
        # orchestration workspaces with no conventional product source tree.
        # Their required structure is intentionally limited to common MASE files.
        pass
    else:
        stack_items.append(CheckItem("stack", False, True, f"unsupported stack: {stack}"))
    state_items: List[CheckItem] = []
    changes_root = root / "openspec" / "changes"
    if changes_root.is_dir():
        for change in sorted(item for item in changes_root.iterdir() if item.is_dir()):
            state_path = change / "mase-state.yaml"
            if not state_path.exists():
                if (change / "proposal.md").exists() or (change / "tasks.md").exists():
                    relative = state_path.relative_to(root).as_posix()
                    state_items.append(CheckItem(relative, False, True, "missing change state"))
                continue
            relative = state_path.relative_to(root).as_posix()
            try:
                ChangeState.load(state_path)
            except (GovernanceError, ValueError) as exc:
                state_items.append(CheckItem(relative, False, True, str(exc)))
            else:
                state_items.append(CheckItem(relative, True, True, "valid"))
    return ProjectReport(root, stack, profile, tuple(common + stack_items + state_items))


def run(project_dir: Union[str, Path] = ".", json_output: bool = False) -> ProjectReport:
    report = inspect_project(project_dir)
    if json_output:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        status = "✓ PASS" if report.ok else "✗ FAIL"
        print(f"MASE check — {status} · profile={report.profile} · stack={report.stack}")
        for item in report.items:
            symbol = "✓" if item.ok else ("!" if not item.required else "✗")
            print(f"  {symbol} {item.path}: {item.message}")
    return report
