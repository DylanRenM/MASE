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
    change_risk_level: str = "L2"
    change_risk_reasons: tuple[str, ...] = ()


CHANGE_RISK_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}
CHANGE_RISK_GATES = {
    "L1": {"related_tests"},
    "L2": {"related_tests"},
    "L3": {"related_tests", "api_contract", "integration_tests", "independent_review"},
    "L4": {
        "related_tests", "api_contract", "integration_tests", "full_regression",
        "security_review", "independent_review", "rollback_verification",
    },
}


def resolve_change_risk(
    change_risk: Optional[Mapping], triggers: Iterable[str]
) -> tuple[str, tuple[str, ...]]:
    """Return an undegradable Change Risk floor and auditable reasons."""

    raw = dict(change_risk or {})
    declared = str(raw.get("level", "L2")).upper()
    if declared not in CHANGE_RISK_ORDER:
        declared = "L4"
    level = declared
    reasons = [f"declared:{declared}"]
    dimensions = dict(raw.get("dimensions", {}))
    trigger_set = {str(item).lower() for item in triggers}

    floors: list[tuple[str, str]] = []
    for name in ("authentication", "authorization", "secrets", "quota"):
        if bool(dimensions.get(name)) or name in trigger_set:
            floors.append(("L4", name))
    if "migration" in trigger_set:
        floors.append(("L4", "migration"))
    if "irreversible_write" in trigger_set or (
        bool(dimensions.get("data_write")) and dimensions.get("reversible") is False
    ):
        floors.append(("L4", "irreversible_data_write"))
    for name in (
        "public_contract", "core_calculation", "concurrency", "cross_system",
        "persistent_state_machine",
    ):
        if bool(dimensions.get(name)):
            floors.append(("L3", name))
    trigger_floors = {
        "public_contract_change": "L3",
        "core_algorithm": "L3",
        "concurrency": "L3",
        "persistence": "L3",
        "multi_service_release": "L3",
    }
    floors.extend(
        (floor, trigger) for trigger, floor in trigger_floors.items()
        if trigger in trigger_set
    )
    if "migration" in trigger_set and (
        bool(dimensions.get("concurrency"))
        or bool(dimensions.get("persistent_state_machine"))
    ):
        floors.append(("L4", "migration_with_state_or_concurrency"))
    for floor, reason in floors:
        if CHANGE_RISK_ORDER[floor] > CHANGE_RISK_ORDER[level]:
            level = floor
        reasons.append(f"hard_floor:{reason}:{floor}")
    return level, tuple(dict.fromkeys(reasons))


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
    change_risk: Optional[Mapping] = None,
) -> GatePlan:
    trigger_names = tuple(dict.fromkeys(str(item).lower() for item in triggers))
    definitions = risk_registry or load_risk_registry()
    known = [item for item in trigger_names if item in definitions]
    unknown = tuple(item for item in trigger_names if item not in definitions)
    selected = registry.get(base_profile)
    change_risk_level, change_risk_reasons = resolve_change_risk(change_risk, trigger_names)
    explicit_change_risk = change_risk is not None
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

    gates.update(CHANGE_RISK_GATES[change_risk_level])
    if explicit_change_risk and change_risk_level in {"L1", "L2"} and selected.name != "strict":
        gates.discard("code_review")
        gates.discard("independent_review")
    elif explicit_change_risk and change_risk_level == "L3":
        gates.discard("code_review")
        gates.add("independent_review")

    all_capability_triggers = {
        str(item).lower()
        for raw in (capabilities or {}).values()
        for item in dict(raw or {}).get("triggers", [])
    }
    contract_triggers = {
        "public_contract_change", "authentication", "authorization", "payment"
    }
    contract_applicable = not (
        (product or {}).get("has_public_contract") is False
        and not (set(known) | all_capability_triggers) & contract_triggers
    )
    if not contract_applicable:
        gates.discard("api_contract")

    has_ui = bool((product or {}).get("has_ui", False))
    impact_payload = dict(impact or {})
    ui_kind = str(impact_payload.get("ui_change_kind", "")).lower()
    if not ui_kind:
        ui_kind = "journey" if impact_payload.get("ui_changed", False) else "none"
    if not has_ui or ui_kind == "none":
        gates.discard("p0_e2e")
        gates.discard("ui_contract")
    elif ui_kind == "presentation":
        gates.discard("p0_e2e")
        gates.add("ui_contract")
    elif ui_kind == "interaction":
        gates.add("ui_contract")
        if impact_payload.get("critical_journey", False):
            gates.add("p0_e2e")
        else:
            gates.discard("p0_e2e")
    elif ui_kind == "journey":
        gates.add("p0_e2e")
    else:
        gates.add("p0_e2e")
        change_risk_reasons = (*change_risk_reasons, f"unknown_ui_change_kind:{ui_kind}")
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
        required_artifacts=tuple(
            item for item in selected.required_artifacts
            if item != "api_contract" or contract_applicable
        ),
        test_schedule=schedule,
        review=selected.review,
        unknown_triggers=tuple(dict.fromkeys((*unknown, *capability_unknown))),
        missing_gates=missing,
        capability_plans=capability_plans,
        change_risk_level=change_risk_level,
        change_risk_reasons=change_risk_reasons,
    )
