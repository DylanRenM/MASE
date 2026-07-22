"""Canonical gate definitions, stage planning, candidate freeze and safe reuse."""

from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union

from mase_cli.evidence import (
    _append_evidence,
    _atomic_write_yaml,
    _inside,
    assess_evidence,
    path_digest,
    run_gate,
)
from mase_cli.profiles import ProfileRegistry
from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload
from mase_cli.state import ChangeState, EvidenceRecord, PASSING_GATE_STATES, inspect_change_status


PathInput = Union[str, Path]


@dataclass(frozen=True)
class GateDefinition:
    name: str
    stage: str
    command: tuple[str, ...]
    inputs: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    covers: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    candidate_bound: bool = False


@dataclass(frozen=True)
class GateDefinitions:
    path: Path
    gates: dict[str, GateDefinition]
    retention: int = 3
    overlap_warning_threshold: float = 0.8
    legacy: bool = False


@dataclass(frozen=True)
class GateDiagnostic:
    code: str
    message: str
    gates: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "gates": list(self.gates)}


@dataclass(frozen=True)
class PlannedGate:
    name: str
    stage: str
    status: str
    reason: str
    scope: str = "change"
    next_action: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "gate": self.name,
            "scope": self.scope,
            "stage": self.stage,
            "status": self.status,
            "reason": self.reason,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class GatePlanReport:
    change: str
    profile: str
    test_schedule: dict[str, tuple[str, ...]]
    instances: dict[str, PlannedGate]
    diagnostics: tuple[GateDiagnostic, ...] = ()
    legacy: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "profile": self.profile,
            "test_schedule": {
                stage: list(checks) for stage, checks in self.test_schedule.items()
            },
            "legacy": self.legacy,
            "instances": {name: item.to_dict() for name, item in self.instances.items()},
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


@dataclass(frozen=True)
class Candidate:
    id: str
    created_at: str
    input_digest: str
    inputs: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Candidate":
        return cls(
            str(payload["id"]),
            str(payload["created_at"]),
            str(payload["input_digest"]),
            tuple(str(item) for item in payload.get("inputs", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "input_digest": self.input_digest,
            "inputs": list(self.inputs),
        }


@dataclass(frozen=True)
class GateExecution:
    record: EvidenceRecord
    reused: bool = False


def _safe_change(root: Path, name: str) -> Path:
    if Path(name).name != name or name in {"", ".", ".."}:
        raise GovernanceError("change name must be a single safe path component", code="invalid_name")
    change = root / "openspec" / "changes" / name
    if not change.is_dir():
        raise GovernanceError(f"change does not exist: {name}", path=change, code="not_found")
    return change


def _validate_relative(root: Path, value: str) -> None:
    # Resolve the non-wildcard prefix so glob patterns remain supported while
    # traversal and absolute paths are rejected.
    first_wildcard = min((value.find(char) for char in "*[?" if char in value), default=len(value))
    prefix = value[:first_wildcard].rstrip("/") or "."
    _inside(root, prefix)


def load_gate_definitions(project_root: PathInput, required: bool = True) -> GateDefinitions:
    root = Path(project_root).expanduser().resolve()
    path = root / ".mase" / "gates.yaml"
    if not path.is_file():
        if required:
            raise GovernanceError(
                "canonical gate definitions are missing; create .mase/gates.yaml",
                path=path,
                code="not_found",
            )
        return GateDefinitions(path, {}, legacy=True)
    payload = load_yaml_document(path)
    validate_payload(payload, "mase-gates.schema.json", path=path)
    gates = {}
    for name, raw in payload.get("gates", {}).items():
        definition = GateDefinition(
            name=str(name),
            stage=str(raw["stage"]),
            command=tuple(str(item) for item in raw["command"]),
            inputs=tuple(str(item) for item in raw.get("inputs", [])),
            artifacts=tuple(str(item) for item in raw.get("artifacts", [])),
            tests=tuple(str(item) for item in raw.get("tests", [])),
            covers=tuple(str(item) for item in raw.get("covers", [])),
            capabilities=tuple(str(item) for item in raw.get("capabilities", [])),
            candidate_bound=bool(raw.get("candidate_bound", False)),
        )
        for relative in definition.inputs + definition.artifacts:
            _validate_relative(root, relative)
        gates[definition.name] = definition
    for definition in gates.values():
        if definition.name in definition.covers:
            raise GovernanceError(
                f"gate {definition.name} cannot cover itself",
                path=path,
                code="schema",
            )
        unknown = [name for name in definition.covers if name not in gates]
        if unknown:
            raise GovernanceError(
                f"gate {definition.name} covers undefined gates: {', '.join(unknown)}",
                path=path,
                code="schema",
            )
    return GateDefinitions(
        path,
        gates,
        retention=int(payload.get("retention", 3)),
        overlap_warning_threshold=float(payload.get("overlap_warning_threshold", 0.8)),
        legacy=not gates,
    )


def _overlap_diagnostics(definitions: GateDefinitions) -> tuple[GateDiagnostic, ...]:
    diagnostics = []
    names = sorted(definitions.gates)
    for index, left_name in enumerate(names):
        left = definitions.gates[left_name]
        for right_name in names[index + 1 :]:
            right = definitions.gates[right_name]
            left_tests, right_tests = set(left.tests), set(right.tests)
            if not left_tests or not right_tests:
                continue
            union = left_tests | right_tests
            overlap = len(left_tests & right_tests) / len(union)
            explicit = right_name in left.covers or left_name in right.covers
            if overlap == 1.0 and left.command == right.command and not explicit:
                diagnostics.append(GateDiagnostic(
                    "duplicate_test_set",
                    f"{left_name} and {right_name} execute the same declared test set",
                    (left_name, right_name),
                ))
            elif overlap >= definitions.overlap_warning_threshold and not explicit:
                diagnostics.append(GateDiagnostic(
                    "high_test_overlap",
                    f"{left_name} and {right_name} test selectors overlap {overlap:.0%}",
                    (left_name, right_name),
                ))
    return tuple(diagnostics)


def candidate_freshness(project_root: PathInput, change_name: str) -> str:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, change_name)
    state = ChangeState.load(change / "mase-state.yaml")
    if not state.candidate:
        return "missing"
    candidate = Candidate.from_dict(state.candidate)
    return "fresh" if path_digest(root, candidate.inputs) == candidate.input_digest else "stale"


def plan_change(project_root: PathInput, change_name: str) -> GatePlanReport:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, change_name)
    definitions = load_gate_definitions(root, required=False)
    report = inspect_change_status(change)
    state = ChangeState.load(change / "mase-state.yaml")
    profile = ProfileRegistry().get(report.profile)
    test_schedule = {
        str(stage): tuple(str(item) for item in checks)
        for stage, checks in profile.test_schedule.items()
    }
    missing_required_definitions = tuple(
        gate for gate in report.required_gates if gate not in definitions.gates
    )
    incomplete_non_final = tuple(
        gate
        for gate in report.required_gates
        if gate in definitions.gates
        and definitions.gates[gate].stage != "final"
        and report.effective_gates.get(gate) not in PASSING_GATE_STATES
    )
    instances = {}
    scope_diagnostics = []
    for name, definition in definitions.gates.items():
        if definition.capabilities:
            applicable_scopes = []
            for scope in definition.capabilities:
                capability = state.gate_plan.capability_plans.get(scope)
                if capability is None:
                    scope_diagnostics.append(GateDiagnostic(
                        "unknown_capability_scope",
                        f"gate {name} references undefined capability {scope}",
                        (name,),
                    ))
                elif name in capability.required_gates:
                    applicable_scopes.append(scope)
            scopes = tuple(applicable_scopes)
        else:
            scopes = ("change",)
        for scope in scopes:
            instance_key = name if scope == "change" else f"{name}@{scope}"
            effective = report.effective_gates.get(instance_key, "pending")
            if definition.stage == "final" and not report.all_tasks_done:
                status, reason = "deferred", "tasks are not complete"
                next_action = "complete remaining tasks"
            elif definition.stage == "final" and missing_required_definitions:
                status = "blocked"
                reason = (
                    "required gate definitions are missing: "
                    + ", ".join(missing_required_definitions)
                )
                next_action = "define missing gates in .mase/gates.yaml"
            elif definition.stage == "final" and incomplete_non_final:
                first = incomplete_non_final[0]
                status = "deferred"
                reason = "required non-final gates are not fresh: " + ", ".join(
                    incomplete_non_final
                )
                next_action = f"mase gate run {first} --change {change_name}"
                first_definition = definitions.gates[first]
                if first_definition.capabilities:
                    next_action += f" --scope {first_definition.capabilities[0]}"
            elif definition.stage == "final" and definition.candidate_bound:
                freshness = candidate_freshness(root, change_name)
                if freshness != "fresh":
                    status, reason = "deferred", f"candidate freeze is {freshness}"
                    next_action = f"mase gate freeze --change {change_name}"
                elif effective in PASSING_GATE_STATES:
                    status, reason = "reusable", "fresh evidence already satisfies this candidate"
                    next_action = "none"
                else:
                    status, reason = "runnable", "frozen candidate is ready for final verification"
                    next_action = f"mase gate run {name} --change {change_name}"
            elif effective in PASSING_GATE_STATES:
                status, reason = "reusable", "fresh evidence is available"
                next_action = "none"
            elif effective in {"stale", "missing", "invalid", "failed"}:
                status, reason = effective, f"effective gate state is {effective}"
                next_action = f"mase gate run {name} --change {change_name}"
            else:
                status, reason = "runnable", "gate inputs require verification"
                next_action = f"mase gate run {name} --change {change_name}"
            if scope != "change" and next_action.startswith("mase gate run"):
                next_action += f" --scope {scope}"
            instances[instance_key] = PlannedGate(
                name, definition.stage, status, reason, scope=scope,
                next_action=next_action,
            )
    diagnostics = [*_overlap_diagnostics(definitions), *scope_diagnostics]
    for required_gate in report.required_gates:
        if required_gate not in definitions.gates:
            diagnostics.append(GateDiagnostic(
                "missing_gate_definition",
                f"required gate {required_gate} has no canonical definition",
                (required_gate,),
            ))
    return GatePlanReport(
        change_name,
        report.profile,
        test_schedule,
        instances,
        tuple(diagnostics),
        definitions.legacy,
    )


def _candidate_inputs(root: Path, change: Path, definitions: GateDefinitions) -> tuple[str, ...]:
    inputs = set()
    for definition in definitions.gates.values():
        if definition.stage == "final":
            inputs.update(definition.inputs)
    for name in ("proposal.md", "design.md", "tasks.md", "specs"):
        target = change / name
        if target.exists():
            inputs.add(target.relative_to(root).as_posix())
    inputs.add(definitions.path.relative_to(root).as_posix())
    return tuple(sorted(inputs))


def freeze_candidate(project_root: PathInput, change_name: str) -> Candidate:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, change_name)
    definitions = load_gate_definitions(root, required=True)
    report = inspect_change_status(change)
    state = ChangeState.load(change / "mase-state.yaml")
    if not report.all_tasks_done:
        raise GovernanceError("cannot freeze candidate while tasks remain", code="blocked")
    if state.blockers:
        raise GovernanceError("cannot freeze candidate while blockers remain", code="blocked")
    missing_definitions = [
        gate for gate in report.required_gates if gate not in definitions.gates
    ]
    if missing_definitions:
        raise GovernanceError(
            "cannot freeze candidate; required gate definitions are missing: "
            + ", ".join(sorted(missing_definitions)),
            code="blocked",
        )
    non_final = {
        gate
        for gate in report.required_gates
        if gate in definitions.gates and definitions.gates[gate].stage != "final"
    }
    incomplete = [
        gate for gate in sorted(non_final)
        if report.effective_gates.get(gate) not in PASSING_GATE_STATES
    ]
    if incomplete:
        raise GovernanceError(
            "cannot freeze candidate; non-final gates are not fresh: " + ", ".join(incomplete),
            code="blocked",
        )
    inputs = _candidate_inputs(root, change, definitions)
    digest = path_digest(root, inputs)
    identifier = hashlib.sha256(digest.encode("ascii")).hexdigest()[:16]
    if state.candidate and state.candidate.get("input_digest") == digest:
        return Candidate.from_dict(state.candidate)
    candidate = Candidate(
        identifier,
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        digest,
        inputs,
    )
    payload = load_yaml_document(change / "mase-state.yaml")
    payload["candidate"] = candidate.to_dict()
    validate_payload(payload, "mase-state.schema.json", path=change / "mase-state.yaml")
    _atomic_write_yaml(change / "mase-state.yaml", payload)
    return candidate


def _test_digest(tests: Sequence[str]) -> str:
    encoded = json.dumps(sorted(set(str(item) for item in tests)), separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _execution_signature(
    command: Sequence[str], input_digest: str, test_digest: str,
    candidate_id: str, scope: str,
) -> str:
    payload = {
        "command": list(command),
        "input_digest": input_digest,
        "test_digest": test_digest,
        "candidate_id": candidate_id,
        "scope": scope,
        "platform": f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _scoped_inputs(
    definition: GateDefinition, state: ChangeState, scope: str
) -> tuple[str, ...]:
    allowed_scopes = definition.capabilities or ("change",)
    if scope not in allowed_scopes:
        raise GovernanceError(
            f"gate {definition.name} is not defined for scope {scope}", code="conflict"
        )
    capability = state.gate_plan.capability_plans.get(scope)
    if scope != "change" and capability is None:
        raise GovernanceError(f"unknown capability scope: {scope}", code="not_found")
    if scope != "change" and definition.name not in capability.required_gates:
        raise GovernanceError(
            f"gate {definition.name} is not applicable to capability {scope}",
            code="conflict",
        )
    return tuple(dict.fromkeys(
        definition.inputs + (capability.paths if capability else ())
    ))


def _coverage_plan(
    definitions: GateDefinitions,
    state: ChangeState,
    source: GateDefinition,
    source_inputs: tuple[str, ...],
    scope: str,
    candidate_id: str,
) -> tuple[tuple[GateDefinition, tuple[str, ...]], ...]:
    planned = []
    for covered_name in source.covers:
        covered = definitions.gates[covered_name]
        covered_inputs = _scoped_inputs(covered, state, scope)
        if not set(covered_inputs).issubset(set(source_inputs)):
            raise GovernanceError(
                f"gate {source.name} cannot cover {covered_name}: inputs are not a superset",
                code="conflict",
            )
        if not set(covered.artifacts).issubset(set(source.artifacts)):
            raise GovernanceError(
                f"gate {source.name} cannot cover {covered_name}: artifacts are not a superset",
                code="conflict",
            )
        if covered.candidate_bound and not candidate_id:
            raise GovernanceError(
                f"gate {source.name} cannot cover candidate-bound gate {covered_name} "
                "without candidate binding",
                code="conflict",
            )
        planned.append((covered, covered_inputs))
    return tuple(planned)


def _fan_out_coverage(
    root: Path,
    state_path: Path,
    record: EvidenceRecord,
    coverage: tuple[tuple[GateDefinition, tuple[str, ...]], ...],
    retention: int,
) -> None:
    current = ChangeState.load(state_path)
    for covered_definition, covered_inputs in coverage:
        if any(
            item.gate == covered_definition.name
            and item.scope == record.scope
            and item.execution_id == record.execution_id
            for item in current.evidence
        ):
            continue
        covered = replace(
            record,
            gate=covered_definition.name,
            input_digest=path_digest(root, covered_inputs),
            inputs=covered_inputs,
            artifacts={
                name: record.artifacts[name]
                for name in covered_definition.artifacts
                if name in record.artifacts
            },
            reused_from=record.gate,
        )
        _append_evidence(state_path, covered, retention=retention)


def execute_defined_gate(
    project_root: PathInput,
    change_name: str,
    gate_name: str,
    *,
    explicit_command: Optional[Sequence[str]] = None,
    explicit_inputs: Optional[Sequence[str]] = None,
    explicit_artifacts: Optional[Sequence[str]] = None,
    scope: str = "change",
    stream_output: bool = False,
) -> GateExecution:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, change_name)
    definitions = load_gate_definitions(root, required=True)
    try:
        definition = definitions.gates[gate_name]
    except KeyError as exc:
        raise GovernanceError(f"gate is not defined: {gate_name}", code="not_found") from exc
    if explicit_command and tuple(explicit_command) != definition.command:
        raise GovernanceError("explicit command conflicts with canonical gate definition", code="conflict")
    state = ChangeState.load(change / "mase-state.yaml")
    scoped_inputs = _scoped_inputs(definition, state, scope)
    if explicit_inputs and tuple(explicit_inputs) != scoped_inputs:
        raise GovernanceError("explicit inputs conflict with canonical gate definition", code="conflict")
    if explicit_artifacts and tuple(explicit_artifacts) != definition.artifacts:
        raise GovernanceError("explicit artifacts conflict with canonical gate definition", code="conflict")

    candidate_id = ""
    if definition.stage == "final" and definition.candidate_bound:
        if candidate_freshness(root, change_name) != "fresh":
            raise GovernanceError("final gate requires a fresh frozen candidate", code="blocked")
        candidate_id = str(ChangeState.load(change / "mase-state.yaml").candidate.get("id", ""))

    coverage = _coverage_plan(
        definitions, state, definition, scoped_inputs, scope, candidate_id
    )

    current_input_digest = path_digest(root, scoped_inputs)
    tests_digest = _test_digest(definition.tests)
    signature = _execution_signature(
        definition.command, current_input_digest, tests_digest, candidate_id, scope
    )
    state = ChangeState.load(change / "mase-state.yaml")
    for record in reversed(state.evidence):
        if (
            record.gate == gate_name
            and record.scope == scope
            and record.result == "passed"
            and record.execution_signature == signature
            and assess_evidence(record, root, scoped_inputs) == "fresh"
        ):
            _fan_out_coverage(
                root,
                change / "mase-state.yaml",
                record,
                coverage,
                definitions.retention,
            )
            return GateExecution(record, reused=True)

    record = run_gate(
        root,
        change / "mase-state.yaml",
        gate_name,
        definition.command,
        scoped_inputs,
        definition.artifacts,
        scope=scope,
        candidate_id=candidate_id,
        test_digest=tests_digest,
        execution_signature=signature,
        retention=definitions.retention,
        stream_output=stream_output,
    )
    if record.result == "passed":
        _fan_out_coverage(
            root,
            change / "mase-state.yaml",
            record,
            coverage,
            definitions.retention,
        )
    return GateExecution(record, reused=False)
