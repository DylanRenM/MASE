"""mase check — profile- and stack-aware project compliance."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Union

from mase_cli.config import load_yaml


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
    metadata = load_yaml(marker).get("mase", {})
    stack = str(metadata.get("stack", "python" if (root / "pyproject.toml").exists() else "generic"))
    profile = str(metadata.get("profile", "standard"))
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
        stack_items.extend((_exists(root, "Package.swift"), _exists(root, "Sources"), _exists(root, "Tests")))
    elif stack == "generic":
        stack_items.extend((_exists(root, "src"), _exists(root, "tests")))
    else:
        stack_items.append(CheckItem("stack", False, True, f"unsupported stack: {stack}"))
    return ProjectReport(root, stack, profile, tuple(common + stack_items))


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
