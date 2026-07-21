"""Validated single-source MASE change state and derived lifecycle reports."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Union

from mase_cli.profiles import ProfileRegistry
from mase_cli.risk import GatePlan, derive_gate_plan
from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


TASK_PATTERN = re.compile(r"^- \[(?P<done>[ xX])\] ", re.MULTILINE)
TERMINAL_PHASES = {"complete", "archived"}
PASSING_GATE_STATES = {"passed", "passed_with_baseline", "skipped"}


@dataclass(frozen=True)
class EvidenceRecord(Mapping[str, Any]):
    gate: str
    kind: str
    result: str
    at: str = ""
    duration_seconds: float = 0.0
    exit_code: Optional[int] = None
    command: tuple[str, ...] = ()
    platform: str = ""
    commit: Optional[str] = None
    worktree: str = ""
    input_digest: str = ""
    inputs: tuple[str, ...] = ()
    log_path: str = ""
    artifacts: dict[str, str] = field(default_factory=dict)
    actor: str = ""
    subject: str = ""
    reference: str = ""
    path: str = ""
    legacy: bool = False
    freshness: str = "fresh"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "EvidenceRecord":
        kind = str(payload.get("kind") or "legacy")
        legacy = kind == "legacy" or "kind" not in payload
        result = str(payload.get("result", "pending"))
        freshness = "stale" if legacy and result == "passed" else (
            "invalid" if legacy else ("fresh" if result in PASSING_GATE_STATES else result)
        )
        return cls(
            gate=str(payload.get("gate", "")),
            kind=kind,
            result=result,
            at=str(payload.get("at", "")),
            duration_seconds=float(payload.get("duration_seconds", 0) or 0),
            exit_code=payload.get("exit_code"),
            command=tuple(str(item) for item in payload.get("command", [])),
            platform=str(payload.get("platform", "")),
            commit=payload.get("commit"),
            worktree=str(payload.get("worktree", "")),
            input_digest=str(payload.get("input_digest", "")),
            inputs=tuple(str(item) for item in payload.get("inputs", [])),
            log_path=str(payload.get("log_path", "")),
            artifacts={str(key): str(value) for key, value in payload.get("artifacts", {}).items()},
            actor=str(payload.get("actor", "")),
            subject=str(payload.get("subject", "")),
            reference=str(payload.get("reference", "")),
            path=str(payload.get("path", "")),
            legacy=legacy,
            freshness=freshness,
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "gate": self.gate,
            "kind": self.kind,
            "result": self.result,
            "at": self.at,
        }
        optional = {
            "duration_seconds": self.duration_seconds,
            "exit_code": self.exit_code,
            "command": list(self.command),
            "platform": self.platform,
            "commit": self.commit,
            "worktree": self.worktree,
            "input_digest": self.input_digest,
            "inputs": list(self.inputs),
            "log_path": self.log_path,
            "artifacts": dict(self.artifacts),
            "actor": self.actor,
            "subject": self.subject,
            "reference": self.reference,
            "path": self.path,
        }
        data.update({key: value for key, value in optional.items() if value not in (None, "", (), [], {})})
        return data

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())


@dataclass(frozen=True)
class ChangeState:
    path: Path
    schema: str
    profile: str
    stack: str
    toolchains: tuple[str, ...]
    phase: str
    product: dict[str, Any]
    impact: dict[str, Any]
    risk: dict[str, Any]
    gates: dict[str, str]
    evidence: tuple[EvidenceRecord, ...]
    dependencies: tuple[dict[str, str], ...]
    conflicts_with: tuple[str, ...]
    blockers: tuple[dict[str, Any], ...]
    gate_plan: GatePlan
    legacy: bool = False

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ChangeState":
        source = Path(path)
        payload = load_yaml_document(source)
        validate_payload(payload, "mase-state.schema.json", path=source)
        product = payload.get("product")
        legacy = False
        if not isinstance(product, dict):
            legacy_project_type = payload.get("project_type", {})
            product = dict(legacy_project_type) if isinstance(legacy_project_type, dict) else {}
            legacy = bool(legacy_project_type)
        impact = payload.get("impact", {})
        impact = dict(impact) if isinstance(impact, dict) else {}
        evidence = tuple(EvidenceRecord.from_dict(item) for item in payload.get("evidence", []))
        legacy = legacy or any(item.legacy for item in evidence)
        gates = {str(key): str(value) for key, value in payload.get("gates", {}).items()}
        risk = dict(payload.get("risk", {}))
        registry = ProfileRegistry()
        gate_plan = derive_gate_plan(
            registry,
            str(payload["profile"]),
            risk.get("triggers", []),
            product,
            impact,
            gates,
        )
        return cls(
            path=source,
            schema=str(payload["schema"]),
            profile=str(payload["profile"]),
            stack=str(payload["stack"]),
            toolchains=tuple(str(item) for item in payload.get("toolchains", [])),
            phase=str(payload["phase"]),
            product=product,
            impact=impact,
            risk=risk,
            gates=gates,
            evidence=evidence,
            dependencies=tuple(dict(item) for item in payload.get("dependencies", [])),
            conflicts_with=tuple(str(item) for item in payload.get("conflicts_with", [])),
            blockers=tuple(dict(item) for item in payload.get("blockers", [])),
            gate_plan=gate_plan,
            legacy=legacy,
        )


@dataclass(frozen=True)
class StatusReport:
    change: str
    profile: str
    stack: str
    phase: str
    complete: int
    total: int
    lifecycle: str
    consistent: bool
    issues: tuple[str, ...]
    evidence: tuple[EvidenceRecord, ...]
    required_gates: tuple[str, ...] = ()
    dependencies: tuple[dict[str, str], ...] = ()
    impact_paths: tuple[str, ...] = ()
    blockers: tuple[dict[str, Any], ...] = ()
    conflicts_with: tuple[str, ...] = ()

    @property
    def all_tasks_done(self) -> bool:
        return self.total > 0 and self.complete == self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "profile": self.profile,
            "stack": self.stack,
            "phase": self.phase,
            "lifecycle": self.lifecycle,
            "tasks": {"complete": self.complete, "total": self.total},
            "consistent": self.consistent,
            "issues": list(self.issues),
            "required_gates": list(self.required_gates),
            "dependencies": list(self.dependencies),
            "impact_paths": list(self.impact_paths),
            "blockers": list(self.blockers),
            "conflicts_with": list(self.conflicts_with),
            "evidence": [item.to_dict() for item in self.evidence],
        }


def _lifecycle(state: ChangeState, complete: int, total: int) -> str:
    all_done = total > 0 and complete == total
    required = state.gate_plan.required_gates
    gates_done = all(state.gates.get(gate) in PASSING_GATE_STATES for gate in required)
    if state.phase in TERMINAL_PHASES and all_done and gates_done:
        return state.phase
    if all_done and not gates_done:
        return "ready_for_gate"
    if all_done and gates_done and state.phase in {"verify", "retro", "release"}:
        return "ready_to_complete"
    return "active"


def inspect_change_status(change_dir: Union[str, Path]) -> StatusReport:
    change = Path(change_dir)
    state = ChangeState.load(change / "mase-state.yaml")
    tasks_path = change / "tasks.md"
    matches = TASK_PATTERN.findall(tasks_path.read_text(encoding="utf-8")) if tasks_path.exists() else []
    total = len(matches)
    complete = sum(marker.lower() == "x" for marker in matches)
    issues: list[str] = []
    if total and complete == total and state.phase in {"draft", "proposal", "design", "build"}:
        issues.append(f"all tasks are complete but phase is {state.phase}")
    if complete < total and state.phase in TERMINAL_PHASES:
        issues.append(f"phase is {state.phase} but {total - complete} tasks remain")
    if state.gate_plan.missing_gates:
        issues.append("missing required gates: " + ", ".join(state.gate_plan.missing_gates))
    if state.gate_plan.unknown_triggers:
        issues.append("unknown risk triggers: " + ", ".join(state.gate_plan.unknown_triggers))
    if state.blockers:
        issues.append(f"{len(state.blockers)} blocker(s) remain")
    return StatusReport(
        change=change.name,
        profile=state.gate_plan.profile,
        stack=state.stack,
        phase=state.phase,
        complete=complete,
        total=total,
        lifecycle=_lifecycle(state, complete, total),
        consistent=not issues,
        issues=tuple(issues),
        evidence=state.evidence,
        required_gates=state.gate_plan.required_gates,
        dependencies=state.dependencies,
        impact_paths=tuple(str(item) for item in state.impact.get("paths", [])),
        blockers=state.blockers,
        conflicts_with=state.conflicts_with,
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
