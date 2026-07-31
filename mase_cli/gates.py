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
from mase_cli.test_selection import (
    TestSelection,
    load_test_manifest,
    select_tests,
)


PathInput = Union[str, Path]
DEVELOPMENT_PRE_FINAL_STAGES = {"analysis", "micro", "capability"}


@dataclass(frozen=True)
class GateDefinition:
    name: str
    stage: str
    command: tuple[str, ...]
    inputs: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    test_tiers: tuple[str, ...] = ()
    covers: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    candidate_bound: bool = False
    mode: str = "automatic"
    effect: str = "read-only"
    required_authority: str = "read-only"
    requires: tuple[str, ...] = ()


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
    selected_tests: tuple[str, ...] = ()
    selection_reason: str = ""
    selection_fallback: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.name,
            "scope": self.scope,
            "stage": self.stage,
            "status": self.status,
            "reason": self.reason,
            "next_action": self.next_action,
            "selected_tests": list(self.selected_tests),
            "selection_reason": self.selection_reason,
            "selection_fallback": self.selection_fallback,
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
            test_tiers=tuple(str(item) for item in raw.get("test_tiers", [])),
            covers=tuple(str(item) for item in raw.get("covers", [])),
            capabilities=tuple(str(item) for item in raw.get("capabilities", [])),
            candidate_bound=bool(raw.get("candidate_bound", False)),
            mode=str(raw.get("mode", "automatic")),
            effect=str(raw.get("effect", "read-only")),
            required_authority=str(raw.get("required_authority", "read-only")),
            requires=tuple(str(item) for item in raw.get("requires", [])),
        )
        for relative in definition.inputs + definition.artifacts:
            _validate_relative(root, relative)
        if definition.test_tiers and "{selected_tests}" not in definition.command:
            raise GovernanceError(
                f"gate {definition.name} declares test_tiers but command does not consume "
                "{selected_tests}",
                path=path,
                code="schema",
            )
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
        unknown_requires = [name for name in definition.requires if name not in gates]
        if unknown_requires:
            raise GovernanceError(
                f"gate {definition.name} requires undefined gates: {', '.join(unknown_requires)}",
                path=path,
                code="schema",
            )
        if definition.stage.startswith("release_"):
            raw = payload["gates"][definition.name]
            required_fields = {"mode", "effect", "required_authority", "requires"}
            missing_fields = sorted(required_fields - set(raw))
            if missing_fields:
                raise GovernanceError(
                    f"release gate {definition.name} must explicitly declare: "
                    + ", ".join(missing_fields),
                    path=path,
                    code="schema",
                )
            if definition.effect != "read-only" and definition.required_authority != "release":
                raise GovernanceError(
                    f"effectful release gate {definition.name} must require release authority",
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
    test_schedule = dict(state.gate_plan.test_schedule)
    missing_required_definitions = tuple(
        gate for gate in report.required_gates if gate not in definitions.gates
    )
    incomplete_development = tuple(
        gate
        for gate in report.required_gates
        if gate in definitions.gates
        and definitions.gates[gate].stage in DEVELOPMENT_PRE_FINAL_STAGES
        and report.effective_gates.get(gate) not in PASSING_GATE_STATES
    )
    incomplete_analysis = tuple(
        gate
        for gate in report.required_gates
        if gate in definitions.gates
        and definitions.gates[gate].stage == "analysis"
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
            selection = _selection_for_gate(root, definition, state, scope)
            instance_key = name if scope == "change" else f"{name}@{scope}"
            effective = report.effective_gates.get(instance_key, "pending")
            if definition.stage.startswith("release_") and name not in report.required_gates:
                status, reason = "blocked", "release gate is not selected by the active overlay and intent"
                next_action = "enable an applicable Release Overlay intent"
            elif definition.stage != "analysis" and incomplete_analysis:
                first = incomplete_analysis[0]
                status = "deferred"
                reason = "required analysis gates are not fresh: " + ", ".join(
                    incomplete_analysis
                )
                next_action = f"mase gate run {first} --change {change_name}"
            elif definition.mode == "manual":
                if effective in PASSING_GATE_STATES:
                    status, reason = "reusable", "fresh manual evidence is available"
                    next_action = "none"
                else:
                    status, reason = "manual", "gate requires declared manual evidence"
                    next_action = f"mase evidence add --gate {name} --change {change_name}"
            elif definition.stage == "final" and not report.all_tasks_done:
                status, reason = "deferred", "tasks are not complete"
                next_action = "complete remaining tasks"
            elif definition.stage == "final" and missing_required_definitions:
                status = "blocked"
                reason = (
                    "required gate definitions are missing: "
                    + ", ".join(missing_required_definitions)
                )
                next_action = "define missing gates in .mase/gates.yaml"
            elif definition.stage == "final" and incomplete_development:
                first = incomplete_development[0]
                status = "deferred"
                reason = "required development gates are not fresh: " + ", ".join(
                    incomplete_development
                )
                next_action = f"mase gate run {first} --change {change_name}"
                first_definition = definitions.gates[first]
                if first_definition.capabilities:
                    next_action += f" --scope {first_definition.capabilities[0]}"
            elif definition.candidate_bound:
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
                selected_tests=selection.test_ids if selection else (),
                selection_reason=selection.reason if selection else "",
                selection_fallback=selection.fallback if selection else "",
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
    manifest = root / ".mase" / "tests.yaml"
    if manifest.is_file():
        inputs.add(manifest.relative_to(root).as_posix())
    impact_artifact = change / "impact-analysis.yaml"
    if impact_artifact.is_file():
        inputs.add(impact_artifact.relative_to(root).as_posix())
    return tuple(sorted(inputs))


def freeze_candidate(project_root: PathInput, change_name: str) -> Candidate:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, change_name)
    definitions = load_gate_definitions(root, required=True)
    report = inspect_change_status(change)
    state = ChangeState.load(change / "mase-state.yaml")
    if state.impact_analysis.get("applicability") == "required":
        from mase_cli.impact import impact_status

        impact_report = impact_status(change)
        if not impact_report.consistent:
            raise GovernanceError(
                "cannot freeze candidate; impact analysis is inconsistent: "
                + "; ".join(impact_report.issues),
                code="blocked",
            )
        if impact_report.reconciliation != "matched":
            raise GovernanceError(
                f"cannot freeze candidate; impact reconciliation is {impact_report.reconciliation}",
                code="blocked",
            )
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
    development_gates = {
        gate
        for gate in report.required_gates
        if gate in definitions.gates
        and definitions.gates[gate].stage in DEVELOPMENT_PRE_FINAL_STAGES
    }
    incomplete = [
        gate for gate in sorted(development_gates)
        if report.effective_gates.get(gate) not in PASSING_GATE_STATES
    ]
    if incomplete:
        raise GovernanceError(
            "cannot freeze candidate; development gates are not fresh: " + ", ".join(incomplete),
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
    candidate_id: str, scope: str, release_digest: str = "",
) -> str:
    payload = {
        "command": list(command),
        "input_digest": input_digest,
        "test_digest": test_digest,
        "candidate_id": candidate_id,
        "scope": scope,
        "release_digest": release_digest,
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
    inputs = definition.inputs + (capability.paths if capability else ())
    if state.impact_analysis.get("applicability") == "required":
        from mase_cli.impact import IMPACT_GATES

        if definition.name in IMPACT_GATES:
            relative = state.impact_analysis.get("artifact", "impact-analysis.yaml")
            artifact = state.path.parent / str(relative)
            inputs += (artifact.relative_to(state.path.parents[3]).as_posix(),)
    return tuple(dict.fromkeys(inputs))


def _selection_for_gate(
    root: Path,
    definition: GateDefinition,
    state: ChangeState,
    scope: str,
) -> Optional[TestSelection]:
    if not definition.test_tiers:
        return None
    manifest = load_test_manifest(root, required=False)
    if manifest.legacy:
        return TestSelection(
            test_ids=definition.tests,
            selectors=definition.tests,
            tiers=definition.test_tiers,
            reason="legacy_static_tests",
            fallback="legacy_static_tests",
        )
    return select_tests(
        manifest,
        tiers=definition.test_tiers,
        impact_paths=tuple(str(item) for item in state.impact.get("paths", [])),
        capability_scope=None if scope == "change" else scope,
        ui_changed=bool(state.impact.get("ui_changed", False)),
    )


def _selected_inputs(root: Path, selection: Optional[TestSelection]) -> tuple[str, ...]:
    if selection is None:
        return ()
    values = []
    manifest = root / ".mase" / "tests.yaml"
    if manifest.is_file():
        values.append(manifest.relative_to(root).as_posix())
    for selector in selection.selectors:
        candidate = root / selector
        if candidate.exists():
            values.append(selector)
    return tuple(dict.fromkeys(values))


def _materialize_command(
    definition: GateDefinition,
    selection: Optional[TestSelection],
    change_name: str,
) -> tuple[str, ...]:
    if definition.test_tiers and (selection is None or not selection.selectors):
        raise GovernanceError(
            f"gate {definition.name} selected no tests for tiers: "
            + ", ".join(definition.test_tiers),
            code="blocked",
        )
    command = []
    for item in definition.command:
        if item == "{selected_tests}":
            command.extend(selection.selectors if selection else ())
        else:
            command.append(item.replace("{change}", change_name))
    return tuple(command)


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
    if definition.mode != "automatic":
        raise GovernanceError(
            f"gate {gate_name} is manual and cannot be executed by Gate Runner",
            code="conflict",
        )
    if explicit_command and tuple(explicit_command) != definition.command:
        raise GovernanceError("explicit command conflicts with canonical gate definition", code="conflict")
    state = ChangeState.load(change / "mase-state.yaml")
    if definition.stage != "analysis":
        current_status = inspect_change_status(change)
        incomplete_analysis = [
            required
            for required in state.gate_plan.required_gates
            if required in definitions.gates
            and definitions.gates[required].stage == "analysis"
            and current_status.effective_gates.get(required) not in PASSING_GATE_STATES
        ]
        if incomplete_analysis:
            raise GovernanceError(
                "required analysis gates are not fresh: "
                + ", ".join(sorted(incomplete_analysis)),
                code="blocked",
            )
    if definition.stage.startswith("release_"):
        if not state.release or gate_name not in state.gate_plan.required_gates:
            raise GovernanceError(
                f"release gate {gate_name} is not applicable to the active Release Overlay and intent",
                code="blocked",
            )
        authority = str(state.release.get("authority", "read-only"))
        if definition.required_authority == "release" and authority != "release":
            raise GovernanceError(
                f"release gate {gate_name} requires release authority; current authority is {authority}",
                code="authority",
            )
        if definition.effect != "read-only" and authority == "read-only":
            raise GovernanceError(
                f"read-only authority cannot execute effectful release gate {gate_name}",
                code="authority",
            )
        status = inspect_change_status(change)
        incomplete = [
            required for required in definition.requires
            if status.effective_gates.get(required) not in PASSING_GATE_STATES
        ]
        if incomplete:
            raise GovernanceError(
                f"release gate {gate_name} requires fresh predecessor evidence: "
                + ", ".join(incomplete),
                code="blocked",
            )
    selection = _selection_for_gate(root, definition, state, scope)
    scoped_inputs = tuple(dict.fromkeys(
        _scoped_inputs(definition, state, scope) + _selected_inputs(root, selection)
    ))
    if explicit_inputs and tuple(explicit_inputs) != scoped_inputs:
        raise GovernanceError("explicit inputs conflict with canonical gate definition", code="conflict")
    if explicit_artifacts and tuple(explicit_artifacts) != definition.artifacts:
        raise GovernanceError("explicit artifacts conflict with canonical gate definition", code="conflict")

    candidate_id = ""
    if definition.candidate_bound:
        if candidate_freshness(root, change_name) != "fresh":
            raise GovernanceError(
                f"{definition.stage} gate requires a fresh frozen candidate", code="blocked"
            )
        candidate_id = str(ChangeState.load(change / "mase-state.yaml").candidate.get("id", ""))

    coverage = _coverage_plan(
        definitions, state, definition, scoped_inputs, scope, candidate_id
    )

    current_input_digest = path_digest(root, scoped_inputs)
    tests_digest = selection.digest if selection else _test_digest(definition.tests)
    execution_command = _materialize_command(definition, selection, change_name)
    release_digest = ""
    if definition.stage.startswith("release_"):
        from mase_cli.release import release_context_digest

        release_digest = release_context_digest(state.release)
    signature = _execution_signature(
        execution_command,
        current_input_digest,
        tests_digest,
        candidate_id,
        scope,
        release_digest,
    )
    state = ChangeState.load(change / "mase-state.yaml")
    for record in reversed(state.evidence):
        if (
            record.gate == gate_name
            and record.scope == scope
            and record.result == "passed"
            and record.execution_signature == signature
            and record.release_digest == release_digest
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
        execution_command,
        scoped_inputs,
        definition.artifacts,
        scope=scope,
        candidate_id=candidate_id,
        test_digest=tests_digest,
        execution_signature=signature,
        release_digest=release_digest,
        selected_tests=selection.test_ids if selection else definition.tests,
        selection_reason=selection.reason if selection else "static_gate_tests",
        selection_fallback=selection.fallback if selection else "",
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
