"""Risk registry and deterministic GatePlan derivation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

from mase_cli.config import framework_home, load_yaml
from mase_cli.impact import LEVEL_GATES
from mase_cli.profiles import ProfileRegistry, resolve_capability_profile


RELEASE_ARTIFACT_GATES = (
    "release_artifact_identity",
    "release_artifact_integrity",
    "release_forbidden_content",
)
RELEASE_PREFLIGHT_GATES = (
    "release_target_preflight",
    "release_recovery_readiness",
)
RELEASE_LIVE_GATES = ("release_live_verification",)
RELEASE_OBSERVE_GATES = ("release_observation",)


def release_required_gates(release: Optional[Mapping]) -> tuple[str, ...]:
    """Return platform-neutral release gates without changing Profile rigor."""

    intent = str((release or {}).get("intent", "")).lower()
    if not intent or intent == "plan":
        return ()
    gates = list(RELEASE_ARTIFACT_GATES)
    if intent in {"publish", "deploy", "verify", "recover"}:
        gates.extend(RELEASE_PREFLIGHT_GATES)
        gates.extend(RELEASE_LIVE_GATES)
        gates.extend(RELEASE_OBSERVE_GATES)
    return tuple(gates)


@dataclass(frozen=True)
class CapabilityGatePlan:
    name: str
    profile: str
    paths: tuple[str, ...] = ()
    required_gates: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class GatePlan:
    profile: str
    required_gates: tuple[str, ...]
    required_artifacts: tuple[str, ...] = ()
    test_schedule: dict[str, tuple[str, ...]] = field(default_factory=dict)
    review: str = ""
    unknown_triggers: tuple[str, ...] = ()
    missing_gates: tuple[str, ...] = ()
    capability_plans: dict[str, CapabilityGatePlan] = field(default_factory=dict)


def load_risk_registry(path: Optional[Path] = None) -> dict[str, dict]:
    source = path or framework_home() / "profiles" / "risks.yaml"
    payload = load_yaml(source)
    return {str(key): dict(value) for key, value in payload.get("triggers", {}).items()}


def derive_gate_plan(
    registry: ProfileRegistry,
    base_profile: str,
    triggers: Iterable[str],
    product: Optional[Mapping] = None,
    impact: Optional[Mapping] = None,
    declared_gates: Optional[Iterable[str]] = None,
    risk_registry: Optional[dict[str, dict]] = None,
    capabilities: Optional[Mapping[str, Mapping]] = None,
    release: Optional[Mapping] = None,
    impact_analysis: Optional[Mapping] = None,
) -> GatePlan:
    trigger_names = tuple(dict.fromkeys(str(item).lower() for item in triggers))
    definitions = risk_registry or load_risk_registry()
    known = [item for item in trigger_names if item in definitions]
    unknown = tuple(item for item in trigger_names if item not in definitions)
    selected = registry.get(base_profile)
    for trigger in known:
        minimum = str(definitions[trigger].get("minimum_profile", "lite"))
        candidate = registry.get(minimum)
        if candidate.rank > selected.rank:
            selected = candidate

    gates = set(selected.hard_gates) | set(selected.capability_gates)
    if selected.review == "capability-boundary":
        gates.add("code_review")
    gates.update(release_required_gates(release))
    impact_summary = dict(impact_analysis or {})
    if impact_summary.get("applicability") == "undecided":
        gates.add("impact_classification")
    elif impact_summary.get("applicability") == "required":
        impact_level = str(impact_summary.get("level", "L2"))
        gates.update(LEVEL_GATES.get(impact_level, LEVEL_GATES["L2"]))
        if impact_summary.get("decision") == "architecture-review-required":
            gates.add("architecture_review")
    for trigger in known:
        gates.update(str(item) for item in definitions[trigger].get("gates", []))
    capability_definitions = {
        str(name): dict(raw or {}) for name, raw in (capabilities or {}).items()
    }
    for name, impact_definition in impact_summary.get("capabilities", {}).items():
        capability_definitions.setdefault(str(name), {
            "profile": base_profile,
            "paths": list(dict(impact_definition or {}).get("paths", [])),
        })
    capability_plans: dict[str, CapabilityGatePlan] = {}
    for name, raw in capability_definitions.items():
        definition = dict(raw or {})
        cap_triggers = tuple(str(item).lower() for item in definition.get("triggers", []))
        requested_profile = str(definition.get("profile") or base_profile)
        cap_selected = registry.get(requested_profile)
        cap_gates = set(cap_selected.capability_gates)
        diagnostics = []
        for trigger in cap_triggers:
            trigger_definition = definitions.get(trigger)
            if trigger_definition:
                minimum = registry.get(str(trigger_definition.get("minimum_profile", "lite")))
                if minimum.rank > cap_selected.rank:
                    cap_selected = minimum
                cap_gates.update(str(item) for item in trigger_definition.get("gates", []))
            else:
                diagnostics.append(f"unknown risk trigger: {trigger}")
        cap_gates.update(cap_selected.capability_gates)
        if cap_selected.review == "capability-boundary":
            cap_gates.add("code_review")
        cap_gates.update(str(item) for item in definition.get("gates", []))
        cap_impact = dict(impact_summary.get("capabilities", {}).get(str(name), {}))
        if cap_impact:
            cap_gates.update(LEVEL_GATES.get(str(cap_impact.get("level", "L2")), LEVEL_GATES["L2"]))
        declared_paths = tuple(str(item) for item in definition.get("paths", []))
        paths = declared_paths or tuple(
            str(item) for item in (impact or {}).get("paths", [])
        )
        if (not cap_triggers and not cap_impact) or not declared_paths:
            diagnostics.append("legacy capability declaration uses conservative change scope")
        capability_plans[str(name)] = CapabilityGatePlan(
            str(name), cap_selected.name, paths, tuple(sorted(cap_gates)), tuple(diagnostics)
        )
        # Capability scope reduces development-stage repetition, but no high-risk
        # capability may remove the change-level final quality floor.
        gates.update(cap_selected.hard_gates)
        gates.update(cap_gates)
        for trigger in cap_triggers:
            trigger_definition = definitions.get(trigger)
            if trigger_definition:
                gates.update(str(item) for item in trigger_definition.get("gates", []))
        if cap_selected.rank > selected.rank:
            selected = cap_selected

    # Recompile the change-level profile floor after capability escalation.
    gates.update(selected.hard_gates)
    gates.update(selected.capability_gates)
    if selected.review == "capability-boundary":
        gates.add("code_review")

    has_ui = bool((product or {}).get("has_ui", False))
    ui_changed = bool((impact or {}).get("ui_changed", False))
    if not (has_ui and ui_changed):
        gates.discard("p0_e2e")
    elif has_ui and ui_changed:
        gates.add("p0_e2e")
    declared = set(str(item) for item in (declared_gates or []))
    missing = tuple(sorted(gates - declared)) if declared_gates is not None else ()
    capability_unknown = tuple(
        trigger
        for raw in (capabilities or {}).values()
        for trigger in (str(item).lower() for item in dict(raw or {}).get("triggers", []))
        if trigger not in definitions
    )
    schedule = {
        str(stage): tuple(str(item) for item in checks)
        for stage, checks in selected.test_schedule.items()
    }
    return GatePlan(
        profile=selected.name,
        required_gates=tuple(sorted(gates)),
        required_artifacts=selected.required_artifacts,
        test_schedule=schedule,
        review=selected.review,
        unknown_triggers=tuple(dict.fromkeys((*unknown, *capability_unknown))),
        missing_gates=missing,
        capability_plans=capability_plans,
    )
