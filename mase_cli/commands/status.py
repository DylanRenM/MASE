"""mase status — derived status from the canonical change state and tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union

from mase_cli.state import StatusReport, inspect_change_status


def _select_change(root: Path, name: Optional[str]) -> Path:
    changes = root / "openspec" / "changes"
    if name:
        if Path(name).name != name or name in {".", ".."}:
            raise ValueError("change name must be a single safe path component")
        return changes / name
    candidates = sorted(path for path in changes.iterdir() if path.is_dir() and (path / "mase-state.yaml").exists())
    if len(candidates) != 1:
        raise ValueError("Specify --change when the project has zero or multiple active changes")
    return candidates[0]


def get_status(project_dir: Union[str, Path] = ".", change: Optional[str] = None) -> StatusReport:
    root = Path(project_dir).expanduser().resolve()
    return inspect_change_status(_select_change(root, change))


def run(project_dir: Union[str, Path] = ".", change: Optional[str] = None, json_output: bool = False):
    report = get_status(project_dir, change)
    if json_output:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        marker = "✓" if report.consistent else "✗"
        print(
            f"{marker} {report.change}: phase={report.phase} profile={report.profile} "
            f"stack={report.stack} tasks={report.complete}/{report.total}"
        )
        for issue in report.issues:
            print(f"  ! {issue}")
    return report
