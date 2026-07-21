"""mase doctor — non-mutating environment preflight."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class DoctorItem:
    name: str
    available: bool
    required: bool
    path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "available": self.available, "required": self.required, "path": self.path}


@dataclass(frozen=True)
class DoctorReport:
    stack: str
    build_mode: str
    items: tuple[DoctorItem, ...]

    @property
    def ok(self) -> bool:
        return all(item.available or not item.required for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "stack": self.stack, "build_mode": self.build_mode, "items": [i.to_dict() for i in self.items]}


def _tool(name: str, required: bool) -> DoctorItem:
    path = shutil.which(name)
    return DoctorItem(name, path is not None, required, path)


def inspect_environment(stack: str = "generic") -> DoctorReport:
    items = [_tool("git", True)]
    mode = "generic"
    if stack == "python":
        items.append(_tool("python3", True))
        mode = "python"
    elif stack == "swift":
        swift = _tool("swift", True)
        xcode = _tool("xcodebuild", False)
        items.extend((swift, xcode))
        mode = "xcode" if xcode.available else "swiftpm-command-line-tools"
    return DoctorReport(stack, mode, tuple(items))


def run(stack: str = "generic", json_output: bool = False) -> DoctorReport:
    report = inspect_environment(stack)
    if json_output:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"MASE doctor — {'✓ PASS' if report.ok else '✗ FAIL'} · mode={report.build_mode}")
        for item in report.items:
            note = "required" if item.required else "optional"
            print(f"  {'✓' if item.available else '!'} {item.name} ({note})")
    return report
