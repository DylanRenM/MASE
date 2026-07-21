"""Risk registry and deterministic GatePlan derivation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

from mase_cli.config import framework_home, load_yaml
from mase_cli.profiles import ProfileRegistry, resolve_capability_profile


@dataclass(frozen=True)
class GatePlan:
    profile: str
    required_gates: tuple[str, ...]
    unknown_triggers: tuple[str, ...] = ()
    missing_gates: tuple[str, ...] = ()


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
    has_ui = bool((product or {}).get("has_ui", False))
    ui_changed = bool((impact or {}).get("ui_changed", False))
    if not (has_ui and ui_changed):
        gates.discard("p0_e2e")
    elif has_ui and ui_changed:
        gates.add("p0_e2e")
    declared = set(str(item) for item in (declared_gates or []))
    missing = tuple(sorted(gates - declared)) if declared_gates is not None else ()
    return GatePlan(selected.name, tuple(sorted(gates)), unknown, missing)
