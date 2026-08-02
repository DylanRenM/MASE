"""Auditable Brownfield failure baselines and regression comparison."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Union

import yaml

from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload


PathInput = Union[str, os.PathLike]
HARD_GATES = frozenset({
    "api_contract", "p0_e2e", "credential_scan", "security_scan",
    "data_integrity", "destructive_migration",
})


def hard_gate_names() -> frozenset[str]:
    """Derive non-baselineable gates from current Profiles and risk policy."""

    from mase_cli.profiles import ProfileRegistry
    from mase_cli.risk import (
        RELEASE_ARTIFACT_GATES, RELEASE_LIVE_GATES, RELEASE_OBSERVE_GATES,
        RELEASE_PREFLIGHT_GATES, load_risk_registry,
    )

    registry = ProfileRegistry()
    names = set(HARD_GATES)
    for profile_name in registry.names:
        names.update(registry.get(profile_name).hard_gates)
    for definition in load_risk_registry().values():
        if registry.get(str(definition.get("minimum_profile", "lite"))).rank >= registry.get("strict").rank:
            names.update(str(item) for item in definition.get("gates", []))
    names.update(RELEASE_ARTIFACT_GATES)
    names.update(RELEASE_PREFLIGHT_GATES)
    names.update(RELEASE_LIVE_GATES)
    names.update(RELEASE_OBSERVE_GATES)
    return frozenset(names)


class BaselineError(GovernanceError):
    """Invalid or unsafe Brownfield baseline operation."""


@dataclass(frozen=True)
class FailureRecord:
    test_id: str
    signature: str
    gate: str
    message: str = ""
    first_seen: str = ""
    owner: str = ""
    expires: str = ""
    remediation_change: str = ""
    reason: str = ""

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "FailureRecord":
        return cls(**{field: str(payload.get(field, "")) for field in cls.__dataclass_fields__})

    def to_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in (
                ("test_id", self.test_id),
                ("signature", self.signature),
                ("gate", self.gate),
                ("message", self.message),
                ("first_seen", self.first_seen),
                ("owner", self.owner),
                ("expires", self.expires),
                ("remediation_change", self.remediation_change),
                ("reason", self.reason),
            )
            if value
        }


@dataclass(frozen=True)
class BaselineCandidates:
    command: str
    failures: tuple[FailureRecord, ...]


@dataclass(frozen=True)
class Baseline:
    path: Path
    command: str
    failures: tuple[FailureRecord, ...]


@dataclass(frozen=True)
class BaselineComparison:
    status: str
    known: tuple[FailureRecord, ...]
    new: tuple[FailureRecord, ...]
    changed: tuple[FailureRecord, ...]
    resolved: tuple[FailureRecord, ...]
    expired: tuple[FailureRecord, ...]


def _signature(test_id: str, message: str) -> str:
    normalized = " ".join(message.split())
    return hashlib.sha256(f"{test_id}\0{normalized}".encode("utf-8")).hexdigest()


def collect_candidates(
    failures: Iterable[Mapping[str, Any]], command: str
) -> BaselineCandidates:
    """Normalize runner failures into deterministic review candidates."""

    if not str(command).strip():
        raise BaselineError("baseline command is required", code="baseline")
    collected: dict[tuple[str, str], FailureRecord] = {}
    for item in failures:
        test_id = str(item.get("test_id", "")).strip()
        message = str(item.get("message", "")).strip()
        gate = str(item.get("gate", "")).strip()
        if not test_id or not gate:
            raise BaselineError("each failure requires test_id and gate", code="baseline")
        record = FailureRecord(test_id, _signature(test_id, message), gate, message)
        collected[(record.test_id, record.signature)] = record
    return BaselineCandidates(
        str(command), tuple(sorted(collected.values(), key=lambda item: (item.test_id, item.signature)))
    )


def _parse_expiry(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise BaselineError("expires must be an ISO date", code="baseline") from exc
    if parsed < date.today():
        raise BaselineError("expires must not be in the past", code="baseline")
    return parsed


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            yaml.safe_dump(dict(payload), handle, sort_keys=False, allow_unicode=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def approve_candidates(
    candidates: BaselineCandidates,
    path: PathInput,
    *,
    owner: str,
    expires: str,
    remediation_change: str,
    reason: str = "pre-existing failure",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Approve candidates with ownership and expiry, preserving existing classifications."""

    if not str(owner).strip():
        raise BaselineError("owner is required", code="baseline")
    if not str(expires).strip():
        raise BaselineError("expires is required", code="baseline")
    _parse_expiry(expires)
    if not str(remediation_change).strip():
        raise BaselineError("remediation change is required", code="baseline")
    hard_gates = hard_gate_names()
    hard = sorted({item.gate for item in candidates.failures if item.gate in hard_gates})
    if hard:
        raise BaselineError(
            "hard gate failures cannot enter a normal baseline: " + ", ".join(hard),
            code="hard_gate",
        )

    target = Path(path).expanduser().resolve()
    today = date.today().isoformat()
    approved = [
        FailureRecord(
            item.test_id,
            item.signature,
            item.gate,
            item.message,
            today,
            str(owner).strip(),
            expires,
            str(remediation_change).strip(),
            str(reason).strip(),
        )
        for item in candidates.failures
    ]
    if target.exists():
        existing = load_baseline(target)
        preserved = {item.test_id: item for item in existing.failures}
        for item in approved:
            prior = preserved.get(item.test_id)
            if prior is not None:
                item = FailureRecord(
                    item.test_id,
                    item.signature,
                    item.gate,
                    item.message,
                    prior.first_seen,
                    prior.owner,
                    prior.expires,
                    prior.remediation_change,
                    prior.reason,
                )
            preserved[item.test_id] = item
        approved = sorted(preserved.values(), key=lambda item: item.test_id)

    payload = {
        "schema": "mase-baseline/v1",
        "command": candidates.command,
        "failures": [item.to_dict() for item in approved],
    }
    validate_payload(payload, "mase-baseline.schema.json", path=target)
    if dry_run:
        return payload
    rendered = yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    if target.exists() and target.read_text(encoding="utf-8") == rendered:
        return payload
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        shutil.copy2(target, target.with_name(f"{target.name}.bak-{stamp}"))
    _atomic_write(target, payload)
    return payload


def load_baseline(path: PathInput) -> Baseline:
    source = Path(path).expanduser().resolve()
    payload = load_yaml_document(source)
    validate_payload(payload, "mase-baseline.schema.json", path=source)
    return Baseline(
        source,
        str(payload["command"]),
        tuple(FailureRecord.from_dict(item) for item in payload["failures"]),
    )


def compare_baseline(
    failures: Iterable[Mapping[str, Any]], baseline: Baseline, *, gate: str
) -> BaselineComparison:
    current = collect_candidates(failures, baseline.command).failures
    current = tuple(item for item in current if item.gate == gate)
    approved = {item.test_id: item for item in baseline.failures if item.gate == gate}
    current_ids = {item.test_id for item in current}
    known: list[FailureRecord] = []
    new: list[FailureRecord] = []
    changed: list[FailureRecord] = []
    expired: list[FailureRecord] = []
    for item in current:
        previous = approved.get(item.test_id)
        if previous is None:
            new.append(item)
        elif item.signature != previous.signature:
            changed.append(item)
        elif date.fromisoformat(previous.expires) < date.today():
            expired.append(previous)
        else:
            known.append(previous)
    resolved = [item for key, item in approved.items() if key not in current_ids]
    if new or changed or expired:
        status = "failed"
    elif known:
        status = "passed_with_baseline"
    else:
        status = "passed"
    return BaselineComparison(
        status,
        tuple(sorted(known, key=lambda item: item.test_id)),
        tuple(sorted(new, key=lambda item: item.test_id)),
        tuple(sorted(changed, key=lambda item: item.test_id)),
        tuple(sorted(resolved, key=lambda item: item.test_id)),
        tuple(sorted(expired, key=lambda item: item.test_id)),
    )
