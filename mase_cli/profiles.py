"""Risk-adaptive MASE process profiles."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Union

from mase_cli.config import framework_home, load_yaml


PROFILE_ORDER = ("lite", "standard", "strict")
STANDARD_RISKS = {
    "untrusted_input",
    "archive_parsing",
    "concurrency",
    "external_dependency",
    "persistence",
    "irreversible_write",
}
STRICT_RISKS = {"authentication", "authorization", "secrets", "payment", "regulated", "migration"}


@dataclass(frozen=True)
class ProcessProfile:
    name: str
    rank: int
    description: str
    required_artifacts: tuple[str, ...]
    hard_gates: tuple[str, ...]
    capability_gates: tuple[str, ...]
    test_schedule: dict[str, list[str]]
    review: str

    @classmethod
    def from_dict(cls, payload: dict) -> "ProcessProfile":
        return cls(
            name=str(payload["name"]),
            rank=int(payload["rank"]),
            description=str(payload.get("description", "")),
            required_artifacts=tuple(payload.get("required_artifacts", [])),
            hard_gates=tuple(payload.get("hard_gates", [])),
            capability_gates=tuple(payload.get("capability_gates", [])),
            test_schedule=dict(payload.get("test_schedule", {})),
            review=str(payload.get("review", "")),
        )


class ProfileRegistry:
    def __init__(self, directory: Optional[Union[str, Path]] = None):
        self.directory = Path(directory) if directory else framework_home() / "profiles"
        loaded = {
            path.stem: ProcessProfile.from_dict(load_yaml(path))
            for path in sorted(self.directory.glob("*.yaml"))
        }
        missing = [name for name in PROFILE_ORDER if name not in loaded]
        if missing:
            raise ValueError(f"Missing MASE profiles: {', '.join(missing)}")
        self._profiles = loaded

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(name for name in PROFILE_ORDER if name in self._profiles)

    def get(self, name: str) -> ProcessProfile:
        try:
            return self._profiles[name.lower()]
        except KeyError as exc:
            raise ValueError(f"Unknown MASE profile: {name}") from exc


def resolve_capability_profile(
    registry: ProfileRegistry,
    base_profile: str,
    risk_triggers: Iterable[str],
) -> ProcessProfile:
    base = registry.get(base_profile)
    risks = {str(item).lower() for item in risk_triggers}
    target_rank = base.rank
    if risks & STANDARD_RISKS:
        target_rank = max(target_rank, registry.get("standard").rank)
    if risks & STRICT_RISKS:
        target_rank = max(target_rank, registry.get("strict").rank)
    return next(profile for profile in registry._profiles.values() if profile.rank == target_rank)
