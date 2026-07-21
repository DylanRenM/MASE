"""Executable and manual gate evidence with reproducible freshness checks."""

from __future__ import annotations

import hashlib
import os
import platform
import re
import subprocess
import tempfile
import time
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence, Union

import yaml

from mase_cli.schema import GovernanceError, load_yaml_document, validate_payload
from mase_cli.state import EvidenceRecord


PathInput = Union[str, os.PathLike]
MANUAL_GATES = frozenset(
    {
        "reference_prototype",
        "device_acceptance",
        "manual_acceptance",
        "risk_acceptance",
        "security_review",
        "independent_review",
        "code_review",
    }
)

_SECRET_PATTERNS = (
    re.compile(
        r"(?i)(\b[A-Za-z0-9_-]*(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)\b\s*[:=]\s*)([^\s,;]+)"
    ),
    re.compile(r"(?i)(\bAuthorization\s*:\s*Bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(\bBearer\s+)([A-Za-z0-9._~+/=-]{6,})"),
)


def redact_secrets(value: str) -> str:
    """Remove common credential forms from persisted commands and logs."""

    redacted = str(value)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(1) + "[REDACTED]", redacted)
    return redacted


def _inside(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise GovernanceError(f"path escapes project root: {relative}", code="path") from exc
    return candidate


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _path_digest(root: Path, relative_paths: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(dict.fromkeys(str(item) for item in relative_paths)):
        path = _inside(root, relative)
        digest.update(relative.encode("utf-8"))
        if not path.exists():
            digest.update(b"\0missing\0")
            continue
        entries = [path]
        if path.is_dir():
            entries = sorted(item for item in path.rglob("*") if ".git" not in item.parts)
        for entry in entries:
            resolved_relative = entry.relative_to(root).as_posix()
            digest.update(b"\0" + resolved_relative.encode("utf-8") + b"\0")
            if entry.is_symlink():
                digest.update(b"link:" + os.readlink(entry).encode("utf-8"))
            elif entry.is_file():
                digest.update(_hash_file(entry).encode("ascii"))
            elif entry.is_dir():
                digest.update(b"directory")
    return digest.hexdigest()


def _git_value(root: Path, args: Sequence[str]) -> Optional[str]:
    completed = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def _git_snapshot(root: Path) -> tuple[Optional[str], str]:
    commit = _git_value(root, ["rev-parse", "HEAD"])
    status = _git_value(root, ["status", "--porcelain=v1", "--untracked-files=all"])
    if status is None:
        return None, "not-a-git-worktree"
    return commit, hashlib.sha256(status.encode("utf-8")).hexdigest()


def _atomic_write_yaml(path: Path, payload: Mapping) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def _append_evidence(state_path: Path, record: EvidenceRecord) -> None:
    payload = load_yaml_document(state_path)
    evidence = payload.setdefault("evidence", [])
    if not isinstance(evidence, list):
        raise GovernanceError("evidence must be an array", path=state_path, code="schema")
    evidence.append(record.to_dict())
    gates = payload.setdefault("gates", {})
    if not isinstance(gates, dict):
        raise GovernanceError("gates must be a mapping", path=state_path, code="schema")
    gates[record.gate] = record.result
    validate_payload(payload, "mase-state.schema.json", path=state_path)
    _atomic_write_yaml(state_path, payload)


def run_gate(
    project_root: PathInput,
    state_path: PathInput,
    gate: str,
    command: Sequence[str],
    inputs: Optional[Iterable[str]] = None,
    artifacts: Optional[Iterable[str]] = None,
) -> EvidenceRecord:
    """Execute a gate and atomically append its evidence to the change state."""

    root = Path(project_root).expanduser().resolve()
    state = Path(state_path).expanduser().resolve()
    if not command:
        raise GovernanceError("gate command cannot be empty", code="command")
    current = load_yaml_document(state)
    validate_payload(current, "mase-state.schema.json", path=state)
    input_paths = tuple(str(item) for item in (inputs or ()))
    artifact_paths = tuple(str(item) for item in (artifacts or ()))
    # Validate paths before executing a potentially expensive command.
    input_digest = _path_digest(root, input_paths)
    for relative in artifact_paths:
        _inside(root, relative)

    started = time.monotonic()
    completed = subprocess.run(
        [str(item) for item in command],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    duration = time.monotonic() - started
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    safe_gate = re.sub(r"[^A-Za-z0-9_.-]+", "-", gate).strip("-") or "gate"
    change_name = state.parent.name
    relative_log = Path(".mase") / "evidence" / change_name / (
        f"{safe_gate}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.log"
    )
    log_path = _inside(root, relative_log.as_posix())
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(redact_secrets(completed.stdout or ""), encoding="utf-8")

    commit, worktree = _git_snapshot(root)
    artifact_digests: dict[str, str] = {}
    for relative in artifact_paths:
        artifact = _inside(root, relative)
        if artifact.exists():
            artifact_digests[relative] = _path_digest(root, [relative])

    record = EvidenceRecord(
        gate=str(gate),
        kind="automatic",
        result="passed" if completed.returncode == 0 else "failed",
        at=timestamp,
        duration_seconds=duration,
        exit_code=completed.returncode,
        command=tuple(redact_secrets(str(item)) for item in command),
        platform=f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
        commit=commit,
        worktree=worktree,
        input_digest=input_digest,
        inputs=input_paths,
        log_path=relative_log.as_posix(),
        artifacts=artifact_digests,
    )
    _append_evidence(state, record)
    return record


def assess_evidence(
    evidence: EvidenceRecord,
    project_root: PathInput,
    input_paths: Optional[Iterable[str]] = None,
) -> str:
    """Return fresh, stale, missing, or invalid for one evidence record."""

    root = Path(project_root).expanduser().resolve()
    if evidence.legacy:
        return "stale"
    if evidence.kind == "manual":
        required = (evidence.actor, evidence.subject, evidence.reference, evidence.at)
        return "fresh" if evidence.gate in MANUAL_GATES and all(required) else "invalid"
    if evidence.kind != "automatic" or evidence.result != "passed" or evidence.exit_code != 0:
        return "invalid"
    if not evidence.log_path or not _inside(root, evidence.log_path).is_file():
        return "missing"
    paths = tuple(str(item) for item in input_paths) if input_paths is not None else evidence.inputs
    if _path_digest(root, paths) != evidence.input_digest:
        return "stale"
    for relative, expected in evidence.artifacts.items():
        path = _inside(root, relative)
        if not path.exists() or _path_digest(root, [relative]) != expected:
            return "invalid"
    return "fresh"


def record_manual_evidence(
    state_path: PathInput,
    gate: str,
    actor: str,
    subject: str,
    reference: str,
) -> EvidenceRecord:
    """Append traceable manual evidence, rejecting automatic-only gate claims."""

    valid = gate in MANUAL_GATES and all(str(item).strip() for item in (actor, subject, reference))
    record = EvidenceRecord(
        gate=str(gate),
        kind="manual",
        result="passed" if valid else "failed",
        at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        actor=redact_secrets(str(actor)),
        subject=redact_secrets(str(subject)),
        reference=str(reference),
        freshness="fresh" if valid else "invalid",
    )
    _append_evidence(Path(state_path).expanduser().resolve(), record)
    return replace(record, freshness="fresh" if valid else "invalid")
