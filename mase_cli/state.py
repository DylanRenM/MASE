"""Validated single-source MASE change state and derived lifecycle reports."""

from __future__ import annotations

import json
import hashlib
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Union

from mase_cli.profiles import ProfileRegistry
from mase_cli.risk import (
    GatePlan,
    RELEASE_ARTIFACT_GATES,
    RELEASE_LIVE_GATES,
    RELEASE_OBSERVE_GATES,
    RELEASE_PREFLIGHT_GATES,
    derive_gate_plan,
)
from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


TASK_PATTERN = re.compile(r"^- \[(?P<done>[ xX])\] ", re.MULTILINE)
TERMINAL_PHASES = {"complete", "archived"}
PASSING_GATE_STATES = {"passed", "subsumed"}


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
    review_kind: str = ""
    path: str = ""
    legacy: bool = False
    freshness: str = "fresh"
    scope: str = "change"
    candidate_id: str = ""
    test_digest: str = ""
    execution_signature: str = ""
    environment_digest: str = ""
    execution_id: str = ""
    reused_from: str = ""
    release_digest: str = ""
    selected_tests: tuple[str, ...] = ()
    selection_reason: str = ""
    selection_fallback: str = ""
    diagnostic_path: str = ""
    failure_classification: str = ""
    first_attempt_result: str = ""
    attempts: int = 0
    evidence_path: str = ""
    evidence_digest: str = ""
    sidecar_status: str = ""

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
            review_kind=str(payload.get("review_kind", "")),
            path=str(payload.get("path", "")),
            legacy=legacy,
            freshness=freshness,
            scope=str(payload.get("scope", "change")),
            candidate_id=str(payload.get("candidate_id", "")),
            test_digest=str(payload.get("test_digest", "")),
            execution_signature=str(payload.get("execution_signature", "")),
            environment_digest=str(payload.get("environment_digest", "")),
            execution_id=str(payload.get("execution_id", "")),
            reused_from=str(payload.get("reused_from", "")),
            release_digest=str(payload.get("release_digest", "")),
            selected_tests=tuple(str(item) for item in payload.get("selected_tests", [])),
            selection_reason=str(payload.get("selection_reason", "")),
            selection_fallback=str(payload.get("selection_fallback", "")),
            diagnostic_path=str(payload.get("diagnostic_path", "")),
            failure_classification=str(payload.get("failure_classification", "")),
            first_attempt_result=str(payload.get("first_attempt_result", "")),
            attempts=int(payload.get("attempts", 0) or 0),
            evidence_path=str(payload.get("evidence_path", "")),
            evidence_digest=str(payload.get("evidence_digest", "")),
            sidecar_status=str(payload.get("sidecar_status", "")),
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
            "review_kind": self.review_kind,
            "path": self.path,
            "scope": self.scope if self.scope != "change" else "",
            "candidate_id": self.candidate_id,
            "test_digest": self.test_digest,
            "execution_signature": self.execution_signature,
            "environment_digest": self.environment_digest,
            "execution_id": self.execution_id,
            "reused_from": self.reused_from,
            "release_digest": self.release_digest,
            "selected_tests": list(self.selected_tests),
            "selection_reason": self.selection_reason,
            "selection_fallback": self.selection_fallback,
            "diagnostic_path": self.diagnostic_path,
            "failure_classification": self.failure_classification,
            "first_attempt_result": self.first_attempt_result,
            "attempts": self.attempts if self.attempts > 0 else None,
            "evidence_path": self.evidence_path,
            "evidence_digest": self.evidence_digest,
        }
        data.update({key: value for key, value in optional.items() if value not in (None, "", (), [], {})})
        if self.kind == "automatic":
            data["commit"] = self.commit
        return data

    def to_summary_dict(self) -> dict[str, Any]:
        """Return the bounded active-state index for a sidecar-backed record."""

        if not self.evidence_path:
            return self.to_dict()
        values = {
            "gate": self.gate,
            "kind": self.kind,
            "result": self.result,
            "at": self.at,
            "duration_seconds": self.duration_seconds,
            "input_digest": self.input_digest,
            "log_path": self.log_path,
            "scope": self.scope if self.scope != "change" else "",
            "candidate_id": self.candidate_id,
            "execution_signature": self.execution_signature,
            "environment_digest": self.environment_digest,
            "execution_id": self.execution_id,
            "reused_from": self.reused_from,
            "release_digest": self.release_digest,
            "evidence_path": self.evidence_path,
            "evidence_digest": self.evidence_digest,
        }
        return {key: value for key, value in values.items() if value not in (None, "", 0.0)}

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
    framework_contract: dict[str, str]
    phase: str
    release: dict[str, Any]
    product: dict[str, Any]
    impact: dict[str, Any]
    impact_analysis: dict[str, Any]
    change_risk: dict[str, Any]
    risk: dict[str, Any]
    gates: dict[str, str]
    evidence: tuple[EvidenceRecord, ...]
    dependencies: tuple[dict[str, str], ...]
    conflicts_with: tuple[str, ...]
    blockers: tuple[dict[str, Any], ...]
    gate_plan: GatePlan
    candidate: dict[str, Any]
    legacy: bool = False

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ChangeState":
        source = Path(path)
        payload = load_yaml_document(source)
        validate_payload(payload, "mase-state.schema.json", path=source)
        if payload.get("release"):
            from mase_cli.release import validate_release_context

            validate_release_context(payload["release"], path=source)
        product = payload.get("product")
        legacy = False
        if not isinstance(product, dict):
            legacy_project_type = payload.get("project_type", {})
            product = dict(legacy_project_type) if isinstance(legacy_project_type, dict) else {}
            legacy = bool(legacy_project_type)
        impact = payload.get("impact", {})
        impact = dict(impact) if isinstance(impact, dict) else {}
        impact_analysis = payload.get("impact_analysis", {})
        impact_analysis = dict(impact_analysis) if isinstance(impact_analysis, dict) else {}
        evidence_payloads = []
        root = source.parents[3]
        for raw in payload.get("evidence", []):
            item = dict(raw)
            relative = str(item.get("evidence_path", ""))
            if relative:
                candidate = (root / relative).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    item["sidecar_status"] = "invalid"
                else:
                    if not candidate.is_file():
                        item["sidecar_status"] = "missing"
                    else:
                        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
                        if actual != str(item.get("evidence_digest", "")):
                            item["sidecar_status"] = "invalid"
                        else:
                            try:
                                detail = json.loads(candidate.read_text(encoding="utf-8"))
                            except (OSError, json.JSONDecodeError):
                                item["sidecar_status"] = "invalid"
                            else:
                                if isinstance(detail, dict):
                                    detail.update({
                                        "evidence_path": relative,
                                        "evidence_digest": actual,
                                        "sidecar_status": "fresh",
                                    })
                                    item = detail
                                else:
                                    item["sidecar_status"] = "invalid"
            evidence_payloads.append(item)
        evidence = tuple(EvidenceRecord.from_dict(item) for item in evidence_payloads)
        legacy = legacy or any(item.legacy for item in evidence)
        gates = {str(key): str(value) for key, value in payload.get("gates", {}).items()}
        risk = dict(payload.get("risk", {}))
        change_risk = dict(payload.get("change_risk", {}))
        release = dict(payload.get("release", {}))
        registry = ProfileRegistry()
        gate_plan = derive_gate_plan(
            registry,
            str(payload["profile"]),
            risk.get("triggers", []),
            product,
            impact,
            gates,
            capabilities=risk.get("capabilities", {}),
            release=release,
            impact_analysis=impact_analysis,
            change_risk=change_risk or None,
        )
        return cls(
            path=source,
            schema=str(payload["schema"]),
            profile=str(payload["profile"]),
            stack=str(payload["stack"]),
            toolchains=tuple(str(item) for item in payload.get("toolchains", [])),
            framework_contract={
                str(key): str(value)
                for key, value in payload.get("framework_contract", {}).items()
            },
            phase=str(payload["phase"]),
            release=release,
            product=product,
            impact=impact,
            impact_analysis=impact_analysis,
            change_risk=change_risk,
            risk=risk,
            gates=gates,
            evidence=evidence,
            dependencies=tuple(dict(item) for item in payload.get("dependencies", [])),
            conflicts_with=tuple(str(item) for item in payload.get("conflicts_with", [])),
            blockers=tuple(dict(item) for item in payload.get("blockers", [])),
            gate_plan=gate_plan,
            candidate=dict(payload.get("candidate", {})),
            legacy=legacy,
        )


@dataclass(frozen=True)
class StatusReport:
    change: str
    profile: str
    stack: str
    phase: str
    framework_contract: dict[str, str]
    release: dict[str, Any]
    release_outcome: str
    complete: int
    total: int
    lifecycle: str
    verification_milestone: str
    consistent: bool
    issues: tuple[str, ...]
    evidence: tuple[EvidenceRecord, ...]
    required_gates: tuple[str, ...] = ()
    dependencies: tuple[dict[str, str], ...] = ()
    impact_paths: tuple[str, ...] = ()
    impact_analysis: dict[str, Any] = field(default_factory=dict)
    change_risk: dict[str, Any] = field(default_factory=dict)
    blockers: tuple[dict[str, Any], ...] = ()
    conflicts_with: tuple[str, ...] = ()
    effective_gates: dict[str, str] = field(default_factory=dict)

    @property
    def all_tasks_done(self) -> bool:
        return self.total > 0 and self.complete == self.total

    def to_dict(self) -> dict[str, Any]:
        return {
            "change": self.change,
            "profile": self.profile,
            "stack": self.stack,
            "phase": self.phase,
            "framework_contract": dict(self.framework_contract),
            "release": dict(self.release),
            "release_outcome": self.release_outcome,
            "lifecycle": self.lifecycle,
            "verification_milestone": self.verification_milestone,
            "tasks": {"complete": self.complete, "total": self.total},
            "consistent": self.consistent,
            "issues": list(self.issues),
            "required_gates": list(self.required_gates),
            "dependencies": list(self.dependencies),
            "impact_paths": list(self.impact_paths),
            "impact_analysis": dict(self.impact_analysis),
            "change_risk": dict(self.change_risk),
            "blockers": list(self.blockers),
            "conflicts_with": list(self.conflicts_with),
            "evidence": [item.to_summary_dict() for item in self.evidence],
            "effective_gates": dict(self.effective_gates),
        }


def _lifecycle(
    state: ChangeState, complete: int, total: int, effective_gates: Mapping[str, str]
) -> str:
    all_done = total > 0 and complete == total
    required = state.gate_plan.required_gates
    gates_done = all(effective_gates.get(gate) in PASSING_GATE_STATES for gate in required)
    if state.phase in TERMINAL_PHASES and all_done and gates_done:
        return state.phase
    if all_done and not gates_done:
        return "ready_for_gate"
    if all_done and gates_done and state.phase in {"verify", "retro", "release"}:
        return "ready_to_complete"
    return "active"


def _verification_milestone(
    state: ChangeState, effective_gates: Mapping[str, str], release_outcome: str
) -> str:
    """Derive the highest verification milestone from canonical fresh evidence."""

    from mase_cli.evidence import path_digest
    from mase_cli.gates import REQUIRED_AT_ORDER, load_gate_definitions

    root = state.path.parents[3]
    try:
        definitions = load_gate_definitions(root, required=False)
    except (GovernanceError, ValueError, OSError):
        return "working"
    required = {
        name: definitions.gates[name]
        for name in state.gate_plan.required_gates
        if name in definitions.gates
    }

    def gates_passed(target: str, *, exclude_live: bool = False) -> bool:
        applicable = [
            name for name, definition in required.items()
            if REQUIRED_AT_ORDER[definition.required_at] <= REQUIRED_AT_ORDER[target]
            and not (
                exclude_live
                and definition.stage in {"release_live", "release_observe"}
            )
        ]
        return bool(applicable) and all(
            effective_gates.get(name) in PASSING_GATE_STATES for name in applicable
        )

    if release_outcome == "observed":
        return "observed"
    if release_outcome == "live_verified":
        return "live_verified"
    development_ready = gates_passed("development")
    if not development_ready:
        return "working"
    user_confirmation_selected = "user_confirmation" in required
    user_confirmed = (
        user_confirmation_selected
        and effective_gates.get("user_confirmation") in PASSING_GATE_STATES
    )
    merge_ready = gates_passed("merge")
    if not merge_ready:
        return "user_confirmed" if user_confirmed else "dev_verified"
    candidate_fresh = bool(state.candidate) and (
        path_digest(root, state.candidate.get("inputs", []))
        == state.candidate.get("input_digest")
    )
    if not candidate_fresh:
        return "merge_verified"
    release_gates = [
        name for name, definition in required.items()
        if definition.required_at == "release"
        and definition.stage not in {"release_live", "release_observe"}
    ]
    if release_gates and all(
        effective_gates.get(name) in PASSING_GATE_STATES for name in release_gates
    ):
        return "release_ready"
    return "candidate_frozen"


def _release_outcome(
    state: ChangeState, effective_gates: Mapping[str, str]
) -> str:
    """Derive release readiness from fresh evidence; never trust raw labels."""

    if not state.release:
        return "not_requested"
    if str(state.release.get("intent", "")) == "plan":
        return "planned"

    required = set(state.gate_plan.required_gates)

    def complete(group: tuple[str, ...]) -> bool:
        applicable = [gate for gate in group if gate in required]
        return bool(applicable) and all(
            effective_gates.get(gate) in PASSING_GATE_STATES for gate in applicable
        )

    if not complete(RELEASE_ARTIFACT_GATES):
        return "candidate_ready" if _candidate_ready(state, effective_gates) else "planned"
    if not any(gate in required for gate in RELEASE_PREFLIGHT_GATES):
        return "artifact_ready"
    if not complete(RELEASE_PREFLIGHT_GATES):
        return "artifact_ready"
    if not complete(RELEASE_LIVE_GATES):
        return "target_ready"
    if not complete(RELEASE_OBSERVE_GATES):
        return "live_verified"
    return "recovered" if state.release.get("intent") == "recover" else "observed"


def _candidate_ready(state: ChangeState, effective_gates: Mapping[str, str]) -> bool:
    """Require a fresh freeze and fresh candidate-bound final evidence."""

    if not state.candidate:
        return False
    from mase_cli.evidence import path_digest
    from mase_cli.gates import load_gate_definitions

    root = state.path.parents[3]
    if path_digest(root, state.candidate.get("inputs", [])) != state.candidate.get("input_digest"):
        return False
    try:
        definitions = load_gate_definitions(root, required=False)
    except (GovernanceError, ValueError, OSError):
        return False
    final_gates = [
        name for name, definition in definitions.gates.items()
        if definition.stage == "final"
        and definition.candidate_bound
        and name in state.gate_plan.required_gates
    ]
    return bool(final_gates) and all(
        effective_gates.get(name) in PASSING_GATE_STATES for name in final_gates
    )


def _effective_gate_states(change: Path, state: ChangeState) -> dict[str, str]:
    """Derive current gate states from the latest applicable evidence."""

    from mase_cli.evidence import assess_evidence

    root = change.parents[2]
    canonical_inputs: dict[str, tuple[str, ...]] = {}
    definition_scopes: dict[str, tuple[str, ...]] = {}
    candidate_bound_gates: set[str] = set()
    manual_gates: set[str] = set()
    try:
        from mase_cli.gates import load_gate_definitions

        definitions = load_gate_definitions(root, required=False)
        for name, definition in definitions.gates.items():
            inputs = set(definition.inputs)
            if state.impact_analysis.get("applicability") == "required":
                from mase_cli.impact import IMPACT_GATES

                if name in IMPACT_GATES:
                    relative = str(
                        state.impact_analysis.get("artifact", "impact-analysis.yaml")
                    )
                    artifact = state.path.parent / relative
                    try:
                        inputs.add(artifact.relative_to(root).as_posix())
                    except ValueError:
                        pass
            if definition.mode == "manual":
                inputs.update(str(item) for item in state.impact.get("paths", []))
                for artifact in ("proposal.md", "design.md", "tasks.md", "specs"):
                    target = change / artifact
                    if target.exists():
                        inputs.add(target.relative_to(root).as_posix())
            canonical_inputs[name] = tuple(sorted(inputs))
            applicable_scopes = tuple(
                scope
                for scope in definition.capabilities
                if scope in state.gate_plan.capability_plans
                and name in state.gate_plan.capability_plans[scope].required_gates
            )
            definition_scopes[name] = applicable_scopes
            if definition.candidate_bound:
                candidate_bound_gates.add(name)
            if definition.mode == "manual":
                manual_gates.add(name)
            for scope in applicable_scopes:
                capability = state.gate_plan.capability_plans.get(scope)
                scoped = tuple(dict.fromkeys(definition.inputs + (capability.paths if capability else ())))
                canonical_inputs[f"{name}@{scope}"] = scoped
    except (GovernanceError, ValueError, OSError):
        # Gate-definition diagnostics are surfaced by gate plan/check. Evidence
        # inspection remains available for legacy projects.
        canonical_inputs = {}

    candidate_is_fresh = False
    if state.candidate:
        from mase_cli.evidence import path_digest

        candidate_is_fresh = (
            path_digest(root, state.candidate.get("inputs", []))
            == state.candidate.get("input_digest")
        )

    latest: dict[str, EvidenceRecord] = {}
    for record in state.evidence:
        key = record.gate if record.scope in {"", "change"} else f"{record.gate}@{record.scope}"
        latest[key] = record

    names = set(state.gates) | set(state.gate_plan.required_gates) | set(latest)
    current_release_digest = ""
    if state.release:
        from mase_cli.release import release_context_digest

        current_release_digest = release_context_digest(state.release)
    effective: dict[str, str] = {}
    for gate in sorted(names):
        record = latest.get(gate)
        if record is None:
            raw = state.gates.get(gate, "pending")
            effective[gate] = "stale" if raw == "passed" else raw
            continue
        if record.result in {"failed", "pending", "stale"}:
            effective[gate] = record.result
            continue
        base_gate = gate.split("@", 1)[0]
        if record.kind == "manual" and base_gate not in manual_gates:
            effective[gate] = "invalid"
            continue
        inputs = canonical_inputs.get(gate, record.inputs)
        freshness = assess_evidence(record, root, inputs)
        if freshness != "fresh":
            effective[gate] = freshness
        elif base_gate.startswith("release_") and (
            not record.release_digest or record.release_digest != current_release_digest
        ):
            effective[gate] = "stale"
        elif base_gate in candidate_bound_gates and (
            not candidate_is_fresh
            or not record.candidate_id
            or record.candidate_id != state.candidate.get("id")
        ):
            effective[gate] = "stale"
        else:
            effective[gate] = record.result

    # A capability-scoped gate satisfies its change-level requirement only
    # when every declared scope is fresh. Individual scope states remain
    # visible as gate@capability entries.
    for gate, scopes in definition_scopes.items():
        if not scopes:
            continue
        scoped_states = [effective.get(f"{gate}@{scope}", "pending") for scope in scopes]
        if all(item in PASSING_GATE_STATES for item in scoped_states):
            effective[gate] = "passed"
        elif any(item == "failed" for item in scoped_states):
            effective[gate] = "failed"
        elif any(item in {"stale", "missing", "invalid"} for item in scoped_states):
            effective[gate] = next(
                item for item in scoped_states if item in {"stale", "missing", "invalid"}
            )
        else:
            effective[gate] = "pending"
    return effective


def inspect_change_status(change_dir: Union[str, Path]) -> StatusReport:
    change = Path(change_dir)
    state = ChangeState.load(change / "mase-state.yaml")
    tasks_path = change / "tasks.md"
    matches = TASK_PATTERN.findall(tasks_path.read_text(encoding="utf-8")) if tasks_path.exists() else []
    total = len(matches)
    complete = sum(marker.lower() == "x" for marker in matches)
    effective_gates = _effective_gate_states(change, state)
    issues: list[str] = []
    if state.impact_analysis:
        if state.impact_analysis.get("applicability") == "undecided":
            if state.phase not in {"draft", "proposal"}:
                issues.append("impact classification is undecided")
        elif state.impact_analysis.get("applicability") == "required":
            try:
                from mase_cli.impact import impact_status

                impact_report = impact_status(change)
            except (GovernanceError, ValueError, OSError) as exc:
                issues.append(f"impact analysis invalid: {exc}")
            else:
                issues.extend(f"impact analysis: {item}" for item in impact_report.issues)
                if impact_report.reconciliation == "expanded":
                    issues.append("impact reconciliation is expanded")
                elif impact_report.reconciliation != "matched" and state.phase in {
                    "verify", "retro", "release", "complete", "archived"
                }:
                    issues.append(
                        f"impact reconciliation is {impact_report.reconciliation}"
                    )
    if total and complete == total and state.phase in {"draft", "proposal", "design", "build"}:
        issues.append(f"all tasks are complete but phase is {state.phase}")
    if complete < total and state.phase in TERMINAL_PHASES:
        issues.append(f"phase is {state.phase} but {total - complete} tasks remain")
    if state.gate_plan.missing_gates:
        issues.append("missing required gates: " + ", ".join(state.gate_plan.missing_gates))
    if state.gate_plan.unknown_triggers:
        issues.append("unknown risk triggers: " + ", ".join(state.gate_plan.unknown_triggers))
    artifact_paths = {
        "change": change,
        "proposal": change / "proposal.md",
        "design": change / "design.md",
        "specs": change / "specs",
        "tasks": change / "tasks.md",
        "tech_feasibility": change / "tech-feasibility.md",
        "architecture": change / "architecture.md",
        "detailed_design": change / "detailed-design.md",
    }
    missing_artifacts = [
        artifact for artifact in state.gate_plan.required_artifacts
        if artifact not in state.gate_plan.required_gates
        and (artifact not in artifact_paths or not artifact_paths[artifact].exists())
    ]
    if missing_artifacts:
        issues.append("missing required artifacts: " + ", ".join(missing_artifacts))
    blocking_gates = [
        f"{gate}={effective_gates.get(gate)}"
        for gate in state.gate_plan.required_gates
        if effective_gates.get(gate) in {"failed", "blocked", "stale", "missing", "invalid"}
    ]
    if blocking_gates:
        issues.append("blocking required gates: " + ", ".join(blocking_gates))
    if state.phase in TERMINAL_PHASES:
        incomplete_gates = [
            f"{gate}={effective_gates.get(gate, 'pending')}"
            for gate in state.gate_plan.required_gates
            if effective_gates.get(gate) not in PASSING_GATE_STATES
        ]
        if incomplete_gates:
            issues.append("terminal phase has incomplete required gates: " + ", ".join(incomplete_gates))
    if state.blockers:
        issues.append(f"{len(state.blockers)} blocker(s) remain")
    lifecycle = _lifecycle(state, complete, total, effective_gates)
    release_outcome = _release_outcome(state, effective_gates)
    if missing_artifacts and total > 0 and complete == total:
        lifecycle = "ready_for_gate"
    return StatusReport(
        change=change.name,
        profile=state.gate_plan.profile,
        stack=state.stack,
        phase=state.phase,
        framework_contract=state.framework_contract,
        release=state.release,
        release_outcome=release_outcome,
        complete=complete,
        total=total,
        lifecycle=lifecycle,
        verification_milestone=_verification_milestone(
            state, effective_gates, release_outcome
        ),
        consistent=not issues,
        issues=tuple(issues),
        evidence=state.evidence,
        required_gates=state.gate_plan.required_gates,
        dependencies=state.dependencies,
        impact_paths=tuple(str(item) for item in state.impact.get("paths", [])),
        impact_analysis=state.impact_analysis,
        change_risk={
            "declared": dict(state.change_risk),
            "effective_level": state.gate_plan.change_risk_level,
            "reasons": list(state.gate_plan.change_risk_reasons),
        },
        blockers=state.blockers,
        conflicts_with=state.conflicts_with,
        effective_gates=effective_gates,
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
