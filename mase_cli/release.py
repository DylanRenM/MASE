"""Read-only, platform-neutral release planning and validation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from mase_cli.risk import release_required_gates
from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


PathInput = Union[str, Path]

INVARIANTS = (
    ("authority_scope", "Confirm intent, target scope, authority, and explicit non-goals."),
    ("immutable_identity", "Bind the release to an immutable artifact identity and provenance."),
    ("content_equivalence", "Verify delivered content is the content that passed candidate checks."),
    ("compatibility", "Check state, configuration, secret, and consumer compatibility."),
    ("pre_impact", "Run every safely precomputable check before user or target impact."),
    ("blast_radius", "Bound blast radius and define measurable stop conditions."),
    ("live_evidence", "Verify the live version, capabilities, and real consumer paths."),
    ("recovery_observation", "Keep recovery available through observation and cleanup."),
)


def release_context_digest(context: Mapping[str, Any]) -> str:
    """Return a stable digest that binds evidence to the full release contract."""

    encoded = json.dumps(
        dict(context), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_release_context(
    payload: Mapping[str, Any], *, path: Optional[PathInput] = None
) -> dict[str, Any]:
    """Validate structural and cross-field release constraints."""

    context = dict(payload)
    validate_payload(context, "mase-release.schema.json", path=path)
    rollout = context["rollout"]
    observation = context["observation"]
    state = context["state"]
    recovery = context["recovery"]

    if str(rollout["strategy"]).lower() in {"canary", "phased"} and not observation["signals"]:
        raise GovernanceError(
            "observation.signals must not be empty for canary or phased rollout",
            path=path,
            code="schema",
        )
    if str(state["migration"]).lower() not in {"none", "not-applicable"} and not recovery["strategies"]:
        raise GovernanceError(
            "recovery.strategies must include rollback or roll-forward for a state migration",
            path=path,
            code="schema",
        )
    if context["intent"] in {"package", "publish", "deploy", "recover"} and not str(
        context["artifact"]["identity"]
    ).strip():
        raise GovernanceError(
            "artifact.identity is required for a mutating release intent",
            path=path,
            code="schema",
        )
    return context


def load_release_context(path: PathInput) -> dict[str, Any]:
    source = Path(path)
    return validate_release_context(load_yaml_document(source), path=source)


def select_adapters(context: Mapping[str, Any]) -> tuple[str, ...]:
    """Select only adapters implied by independent context dimensions."""

    artifact_kind = str(context["artifact"]["kind"]).lower()
    target = context["target"]
    target_kind = str(target["kind"]).lower()
    platform = str(target.get("platform", "")).lower()
    adapters: list[str] = []

    if target_kind in {"container", "orchestrator", "kubernetes"} or artifact_kind == "image":
        adapters.append("container-orchestrator")
    if target_kind in {"registry", "package-registry"} or artifact_kind in {"package", "library"}:
        adapters.append("package-registry")
    if target_kind in {"app-store", "device-fleet", "desktop", "mobile"}:
        adapters.append("distributed-client")
    if target_kind in {"serverless", "function"}:
        adapters.append("serverless")
    if target_kind in {"vm", "host", "service"}:
        adapters.append("vm-service")
    if "windows" in platform:
        adapters.append("windows-powershell")
    elif any(name in platform for name in ("macos", "darwin", "osx")):
        adapters.append("macos-unix")
    elif "linux" in platform:
        adapters.append("linux-unix")
    elif any(name in platform for name in ("unix", "freebsd", "openbsd", "netbsd")):
        adapters.append("unix")
    else:
        adapters.append("generic-platform")
    for interface in context.get("interfaces", []):
        normalized = str(interface).lower().replace("_", "-")
        adapters.append(f"{normalized}-interface")
    return tuple(dict.fromkeys(adapters))


@dataclass(frozen=True)
class ReleasePlan:
    context: dict[str, Any]
    generated_on: str
    adapters: tuple[str, ...]
    hard_stops: tuple[str, ...]

    @property
    def gates(self) -> dict[str, str]:
        return {gate: "pending" for gate in release_required_gates(self.context)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "mase-release-plan/v1",
            "generated_on": self.generated_on,
            "intent": self.context["intent"],
            "authority": self.context["authority"],
            "release_outcome": "planned",
            "artifact": dict(self.context["artifact"]),
            "target": dict(self.context["target"]),
            "rollout": dict(self.context["rollout"]),
            "invariants": [
                {"id": identifier, "check": check, "status": "pending"}
                for identifier, check in INVARIANTS
            ],
            "adapters": list(self.adapters),
            "gates": self.gates,
            "hard_stops": list(self.hard_stops),
        }

    def to_markdown(self) -> str:
        artifact = self.context["artifact"]
        target = self.context["target"]
        rollout = self.context["rollout"]
        artifact_label = str(artifact["kind"])
        if artifact_label.lower() == "image" and "container-orchestrator" in self.adapters:
            artifact_label = "container image"
        lines = [
            "# Release plan",
            "",
            f"Generated: {self.generated_on}",
            f"Intent / authority: {self.context['intent']} / {self.context['authority']}",
            f"Artifact: {artifact_label} `{artifact['identity']}`",
            f"Target: {target['kind']} / {target['environment']}",
            f"Rollout: {rollout['strategy']}",
            "",
            "## Invariant checks",
            "",
        ]
        lines.extend(f"- [ ] {check}" for _, check in INVARIANTS)
        lines.extend(["", "## Selected adapters", ""])
        lines.extend(f"- {adapter}" for adapter in self.adapters)
        lines.extend(["", "## Pending evidence gates", ""])
        if self.gates:
            lines.extend(f"- [ ] {gate}: pending" for gate in self.gates)
        else:
            lines.append("- No executable release gate is required for plan-only intent.")
        if self.hard_stops:
            lines.extend(["", "## Hard stops", ""])
            lines.extend(f"- {item}" for item in self.hard_stops)
        lines.extend(
            [
                "",
                "> This plan is not passing evidence. Record fresh evidence through the project Gate Runner.",
                "",
            ]
        )
        return "\n".join(lines)


def build_release_plan(
    context: Mapping[str, Any], *, generated_on: Optional[str] = None
) -> ReleasePlan:
    validated = validate_release_context(context)
    hard_stops = []
    if validated["authority"] == "read-only" and validated["intent"] in {
        "package", "publish", "deploy", "recover"
    }:
        hard_stops.append(
            "Read-only authority: do not build, upload, publish, deploy, switch traffic, or recover."
        )
    if not validated["artifact"].get("provenance"):
        hard_stops.append("Artifact provenance is missing; do not promote the artifact.")
    return ReleasePlan(
        validated,
        generated_on or date.today().isoformat(),
        select_adapters(validated),
        tuple(hard_stops),
    )
