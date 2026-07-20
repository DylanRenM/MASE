"""Single-source MASE change state and derived status reports."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Union

from mase_cli.config import load_yaml


TASK_PATTERN = re.compile(r"^- \[(?P<done>[ xX])\] ", re.MULTILINE)
FINISHED_PHASES = {"verify", "retro", "release", "complete", "archived"}


@dataclass(frozen=True)
class ChangeState:
    path: Path
    schema: str
    profile: str
    stack: str
    phase: str
    risk: dict[str, Any]
    gates: dict[str, str]
    evidence: list[dict[str, Any]]

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ChangeState":
        source = Path(path)
        payload = load_yaml(source)
        required = ("schema", "profile", "stack", "phase", "risk", "gates", "evidence")
        missing = [key for key in required if key not in payload]
        if missing:
            raise ValueError(f"Missing state fields: {', '.join(missing)}")
        return cls(
            path=source,
            schema=str(payload["schema"]),
            profile=str(payload["profile"]),
            stack=str(payload["stack"]),
            phase=str(payload["phase"]),
            risk=dict(payload["risk"]),
            gates=dict(payload["gates"]),
            evidence=list(payload["evidence"]),
        )


@dataclass(frozen=True)
class StatusReport:
    change: str
    profile: str
    stack: str
    phase: str
    complete: int
    total: int
    consistent: bool
    issues: tuple[str, ...]
    evidence: tuple[dict[str, Any], ...]

    @property
    def all_tasks_done(self) -> bool:
        return self.total > 0 and self.complete == self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "profile": self.profile,
            "stack": self.stack,
            "phase": self.phase,
            "tasks": {"complete": self.complete, "total": self.total},
            "consistent": self.consistent,
            "issues": list(self.issues),
            "evidence": list(self.evidence),
        }


def inspect_change_status(change_dir: Union[str, Path]) -> StatusReport:
    change = Path(change_dir)
    state = ChangeState.load(change / "mase-state.yaml")
    tasks_path = change / "tasks.md"
    matches = TASK_PATTERN.findall(tasks_path.read_text(encoding="utf-8")) if tasks_path.exists() else []
    total = len(matches)
    complete = sum(marker.lower() == "x" for marker in matches)
    issues: list[str] = []
    if total and complete == total and state.phase not in FINISHED_PHASES:
        issues.append(f"all tasks are complete but phase is {state.phase}")
    if complete < total and state.phase in {"complete", "archived"}:
        issues.append(f"phase is {state.phase} but {total - complete} tasks remain")
    return StatusReport(
        change=change.name,
        profile=state.profile,
        stack=state.stack,
        phase=state.phase,
        complete=complete,
        total=total,
        consistent=not issues,
        issues=tuple(issues),
        evidence=tuple(state.evidence),
    )


def create_archive_snapshot(
    change_dir: Union[str, Path], destination: Union[str, Path], commit: Optional[str] = None
) -> Path:
    source = Path(change_dir)
    target = Path(destination)
    if target.exists():
        raise FileExistsError(target)
    shutil.copytree(source, target)
    metadata = {"source_change": source.name, "commit": commit}
    (target / "snapshot-metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return target
