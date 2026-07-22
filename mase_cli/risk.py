"""Risk registry and deterministic GatePlan derivation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

from mase_cli.config import framework_home, load_yaml
from mase_cli.profiles import ProfileRegistry, resolve_capability_profile


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
) -> GatePlan:
    trigger_names = tuple(dict.fromkeys(str(item).lower() for item in triggers))
    definitions = risk_registry or load_risk_registry()
    known = [item for item in trigger_names if item in definitions]
    unknown = tuple(item for item in trigger_names if item not in definitions)
    selected = resolve_capability_profile(registry, base_profile, known)
    for trigger in known:
        minimum = str(definitions[trigger].get("minimum_profile", "lite"))
        candidate = registry.get(minimum)
        if candidate.rank > selected.rank:
            selected = candidate

    gates = set(selected.hard_gates)
    for trigger in known:
        gates.update(str(item) for item in definitions[trigger].get("gates", []))
    capability_plans: dict[str, CapabilityGatePlan] = {}
    for name, raw in (capabilities or {}).items():
        definition = dict(raw or {})
        cap_triggers = tuple(str(item).lower() for item in definition.get("triggers", []))
        requested_profile = str(definition.get("profile") or base_profile)
        cap_selected = resolve_capability_profile(registry, requested_profile, cap_triggers)
        cap_gates = set(cap_selected.capability_gates)
        diagnostics = []
        for trigger in cap_triggers:
            trigger_definition = definitions.get(trigger)
            if trigger_definition:
                cap_gates.update(str(item) for item in trigger_definition.get("gates", []))
        cap_gates.update(str(item) for item in definition.get("gates", []))
        declared_paths = tuple(str(item) for item in definition.get("paths", []))
        paths = declared_paths or tuple(
            str(item) for item in (impact or {}).get("paths", [])
        )
        if not cap_triggers or not declared_paths:
            diagnostics.append("legacy capability declaration uses conservative change scope")
        capability_plans[str(name)] = CapabilityGatePlan(
            str(name), cap_selected.name, paths, tuple(sorted(cap_gates)), tuple(diagnostics)
        )
        # Capability scope reduces development-stage repetition, but no high-risk
        # capability may remove the change-level final quality floor.
        gates.update(cap_selected.hard_gates)
        for trigger in cap_triggers:
            trigger_definition = definitions.get(trigger)
            if trigger_definition:
                gates.update(str(item) for item in trigger_definition.get("gates", []))
        if cap_selected.rank > selected.rank:
            selected = cap_selected

    has_ui = bool((product or {}).get("has_ui", False))
    ui_changed = bool((impact or {}).get("ui_changed", False))
    if not (has_ui and ui_changed):
        gates.discard("p0_e2e")
    elif has_ui and ui_changed:
        gates.add("p0_e2e")
    declared = set(str(item) for item in (declared_gates or []))
    missing = tuple(sorted(gates - declared)) if declared_gates is not None else ()
    return GatePlan(
        selected.name,
        tuple(sorted(gates)),
        unknown,
        missing,
        capability_plans,
    )
