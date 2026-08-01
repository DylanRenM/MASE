"""Executable and manual gate evidence with reproducible freshness checks."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
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


def load_evidence_detail(
    state_path: PathInput, *, execution_id: str = "", gate: str = ""
) -> EvidenceRecord:
    """Load one hydrated evidence record without expanding the full history in output."""

    from mase_cli.state import ChangeState

    state = ChangeState.load(Path(state_path).expanduser().resolve())
    matches = [
        item for item in state.evidence
        if (not execution_id or item.execution_id == execution_id)
        and (not gate or item.gate == gate)
    ]
    if not matches:
        key = execution_id or gate or "latest"
        raise GovernanceError(f"evidence not found: {key}", code="not_found")
    return matches[-1]


def _inside(root: Path, relative: str) -> Path:
    normalized_parts = str(relative).replace("\\", "/").split("/")
    if Path(relative).is_absolute():
        raise GovernanceError(f"path must be project-relative: {relative}", code="path")
    if ".." in normalized_parts:
        raise GovernanceError(f"path escapes project root: {relative}", code="path")
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
        digest.update(relative.encode("utf-8"))
        wildcard = min(
            (relative.find(char) for char in "*[?" if char in relative),
            default=len(relative),
        )
        prefix = relative[:wildcard].rstrip("/") or "."
        base = _inside(root, prefix)
        if wildcard < len(relative):
            candidates = []
            if base.exists():
                search_root = base if base.is_dir() else base.parent
                candidates = [
                    item
                    for item in (search_root, *search_root.rglob("*"))
                    if fnmatch.fnmatchcase(item.relative_to(root).as_posix(), relative)
                ]
        else:
            candidates = [base] if base.exists() else []
        if not candidates:
            digest.update(b"\0missing\0")
            continue
        entries = []
        for candidate in candidates:
            entries.append(candidate)
            if candidate.is_dir():
                entries.extend(candidate.rglob("*"))
        for entry in sorted(set(
            item for item in entries
            if ".git" not in item.parts
            and not ({"__pycache__", ".pytest_cache", "node_modules"} & set(item.parts))
            and item.name != ".DS_Store"
            and item.suffix != ".pyc"
            and item.name != "mase-state.yaml"
            and not ({".mase", "evidence"} <= set(item.parts))
        )):
            resolved_relative = entry.relative_to(root).as_posix()
            digest.update(b"\0" + resolved_relative.encode("utf-8") + b"\0")
            if entry.is_symlink():
                digest.update(b"link:" + os.readlink(entry).encode("utf-8"))
            elif entry.is_file():
                digest.update(_hash_file(entry).encode("ascii"))
            elif entry.is_dir():
                digest.update(b"directory")
    return digest.hexdigest()


def path_digest(root: PathInput, relative_paths: Iterable[str]) -> str:
    """Public safe digest used by gate planning and candidate freezing."""

    return _path_digest(Path(root).expanduser().resolve(), relative_paths)


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


def _atomic_write_json(path: Path, payload: Mapping) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(dict(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _append_evidence(state_path: Path, record: EvidenceRecord, retention: int = 3) -> EvidenceRecord:
    root = state_path.parents[3]
    execution_id = record.execution_id or uuid.uuid4().hex
    safe_gate = re.sub(r"[^A-Za-z0-9_.-]+", "-", record.gate).strip("-") or "gate"
    relative_sidecar = (
        Path(".mase") / "evidence" / state_path.parent.name
        / f"{safe_gate}-{execution_id}.json"
    )
    sidecar = _inside(root, relative_sidecar.as_posix())
    full_record = replace(record, execution_id=execution_id)
    detail = full_record.to_dict()
    validate_payload(detail, "mase-evidence.schema.json", path=sidecar)
    sidecar_digest = _atomic_write_json(sidecar, detail)
    indexed_record = replace(
        full_record,
        evidence_path=relative_sidecar.as_posix(),
        evidence_digest=sidecar_digest,
        sidecar_status="fresh",
    )
    payload = load_yaml_document(state_path)
    evidence = payload.setdefault("evidence", [])
    if not isinstance(evidence, list):
        raise GovernanceError("evidence must be an array", path=state_path, code="schema")
    evidence.append(indexed_record.to_summary_dict())
    scope = indexed_record.scope or "change"
    matching = [
        index
        for index, item in enumerate(evidence)
        if str(item.get("gate", "")) == indexed_record.gate
        and str(item.get("scope", "change")) == scope
    ]
    limit = max(1, int(retention))
    if len(matching) > limit:
        selected = {matching[-1]}
        latest_pass = next(
            (
                index for index in reversed(matching)
                if str(evidence[index].get("result", ""))
                in {"passed", "subsumed", "passed_with_baseline", "skipped"}
            ),
            None,
        )
        latest_failure = next(
            (
                index for index in reversed(matching)
                if str(evidence[index].get("result", "")) == "failed"
            ),
            None,
        )
        for index in (latest_pass, latest_failure):
            if index is not None and len(selected) < limit:
                selected.add(index)
        for index in reversed(matching):
            if len(selected) >= limit:
                break
            selected.add(index)
        for index in reversed([item for item in matching if item not in selected]):
            evidence.pop(index)
    gates = payload.setdefault("gates", {})
    if not isinstance(gates, dict):
        raise GovernanceError("gates must be a mapping", path=state_path, code="schema")
    gates[indexed_record.gate] = indexed_record.result
    validate_payload(payload, "mase-state.schema.json", path=state_path)
    _atomic_write_yaml(state_path, payload)
    return indexed_record


def run_gate(
    project_root: PathInput,
    state_path: PathInput,
    gate: str,
    command: Sequence[str],
    inputs: Optional[Iterable[str]] = None,
    artifacts: Optional[Iterable[str]] = None,
    *,
    scope: str = "change",
    candidate_id: str = "",
    test_digest: str = "",
    execution_signature: str = "",
    environment_digest: str = "",
    execution_id: Optional[str] = None,
    reused_from: str = "",
    release_digest: str = "",
    selected_tests: Optional[Iterable[str]] = None,
    selection_reason: str = "",
    selection_fallback: str = "",
    retention: int = 3,
    stream_output: bool = False,
) -> EvidenceRecord:
    """Execute a gate and atomically append its evidence to the change state."""

    root = Path(project_root).expanduser().resolve()
    state = Path(state_path).expanduser().resolve()
    if not command:
        raise GovernanceError("gate command cannot be empty", code="command")
    current = load_yaml_document(state)
    validate_payload(current, "mase-state.schema.json", path=state)
    if str(gate).startswith("release_") and current.get("release") and not release_digest:
        from mase_cli.release import release_context_digest

        release_digest = release_context_digest(current["release"])
    input_paths = tuple(str(item) for item in (inputs or ()))
    artifact_paths = tuple(str(item) for item in (artifacts or ()))
    selected_test_ids = tuple(str(item) for item in (selected_tests or ()))
    # Validate paths before executing a potentially expensive command.
    input_digest = _path_digest(root, input_paths)
    for relative in artifact_paths:
        _inside(root, relative)

    actual_execution_id = str(execution_id or uuid.uuid4().hex)
    safe_gate = re.sub(r"[^A-Za-z0-9_.-]+", "-", gate).strip("-") or "gate"
    change_name = state.parent.name
    diagnostic_relative = Path(".mase") / "evidence" / change_name / (
        f"{safe_gate}-{actual_execution_id[:12]}.diagnostic.json"
    )
    diagnostic_path = _inside(root, diagnostic_relative.as_posix())
    diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
    command_environment = dict(os.environ)
    command_environment["MASE_TEST_DIAGNOSTIC_PATH"] = str(diagnostic_path)

    started = time.monotonic()
    if stream_output:
        process = subprocess.Popen(
            [str(item) for item in command],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
            env=command_environment,
        )
        chunks = []
        assert process.stdout is not None
        for chunk in process.stdout:
            chunks.append(chunk)
            sys.stdout.write(chunk)
            sys.stdout.flush()
        returncode = process.wait()
        output = "".join(chunks)
    else:
        completed = subprocess.run(
            [str(item) for item in command],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env=command_environment,
        )
        returncode = completed.returncode
        output = completed.stdout or ""
    duration = time.monotonic() - started
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    relative_log = Path(".mase") / "evidence" / change_name / (
        f"{safe_gate}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}.log"
    )
    log_path = _inside(root, relative_log.as_posix())
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(redact_secrets(output), encoding="utf-8")

    diagnostic = None
    if diagnostic_path.is_file():
        try:
            diagnostic = json.loads(diagnostic_path.read_text(encoding="utf-8"))
            if not isinstance(diagnostic, dict):
                raise ValueError("diagnostic must be an object")
            validate_payload(
                diagnostic,
                "mase-test-diagnostic.schema.json",
                path=diagnostic_path,
            )
            expected_final = "passed" if returncode == 0 else "failed"
            if diagnostic.get("final_result") != expected_final:
                raise ValueError("diagnostic final_result conflicts with command exit status")
        except (GovernanceError, ValueError, json.JSONDecodeError) as exc:
            diagnostic = {
                "schema": "mase-test-diagnostic/v1",
                "attempts": 1,
                "first_attempt_result": "failed" if returncode else "passed",
                "final_result": "failed" if returncode else "passed",
                "classification": "unknown",
                "failed_tests": [f"invalid adapter diagnostic: {type(exc).__name__}"],
                "artifacts": [relative_log.as_posix()],
            }
    elif returncode != 0:
        diagnostic = {
            "schema": "mase-test-diagnostic/v1",
            "attempts": 1,
            "first_attempt_result": "failed",
            "final_result": "failed",
            "classification": "unknown",
            "failed_tests": list(selected_test_ids),
            "artifacts": [relative_log.as_posix()],
        }

    diagnostic_relative_value = ""
    failure_classification = ""
    first_attempt_result = "passed" if returncode == 0 else "failed"
    attempts = 1
    if diagnostic is not None:
        serialized = redact_secrets(json.dumps(diagnostic, ensure_ascii=False, indent=2))
        diagnostic_path.write_text(serialized + "\n", encoding="utf-8")
        diagnostic_relative_value = diagnostic_relative.as_posix()
        failure_classification = str(diagnostic.get("classification", ""))
        first_attempt_result = str(diagnostic.get("first_attempt_result", first_attempt_result))
        attempts = int(diagnostic.get("attempts", 1))

    commit, worktree = _git_snapshot(root)
    artifact_digests: dict[str, str] = {}
    for relative in artifact_paths:
        artifact = _inside(root, relative)
        if artifact.exists():
            artifact_digests[relative] = _path_digest(root, [relative])
    if diagnostic_relative_value:
        artifact_digests[diagnostic_relative_value] = _path_digest(
            root, [diagnostic_relative_value]
        )

    record = EvidenceRecord(
        gate=str(gate),
        kind="automatic",
        result="passed" if returncode == 0 else "failed",
        at=timestamp,
        duration_seconds=duration,
        exit_code=returncode,
        command=tuple(redact_secrets(str(item)) for item in command),
        platform=f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
        commit=commit,
        worktree=worktree,
        input_digest=input_digest,
        inputs=input_paths,
        log_path=relative_log.as_posix(),
        artifacts=artifact_digests,
        scope=str(scope or "change"),
        candidate_id=str(candidate_id or ""),
        test_digest=str(test_digest or ""),
        execution_signature=str(execution_signature or ""),
        environment_digest=str(environment_digest or ""),
        execution_id=actual_execution_id,
        reused_from=str(reused_from or ""),
        release_digest=str(release_digest or ""),
        selected_tests=selected_test_ids,
        selection_reason=str(selection_reason or ""),
        selection_fallback=str(selection_fallback or ""),
        diagnostic_path=diagnostic_relative_value,
        failure_classification=failure_classification,
        first_attempt_result=first_attempt_result,
        attempts=attempts,
    )
    return _append_evidence(state, record, retention=retention)


def assess_evidence(
    evidence: EvidenceRecord,
    project_root: PathInput,
    input_paths: Optional[Iterable[str]] = None,
) -> str:
    """Return fresh, stale, missing, or invalid for one evidence record."""

    root = Path(project_root).expanduser().resolve()
    if evidence.sidecar_status in {"missing", "invalid"}:
        return evidence.sidecar_status
    if evidence.legacy:
        return "stale"
    if evidence.kind == "manual":
        required = (
            evidence.actor, evidence.subject, evidence.reference, evidence.at,
            evidence.input_digest, evidence.execution_signature,
        )
        if evidence.result != "passed" or not all(required):
            return "invalid"
        paths = tuple(str(item) for item in input_paths) if input_paths is not None else evidence.inputs
        return "fresh" if _path_digest(root, paths) == evidence.input_digest else "stale"
    if (
        evidence.kind != "automatic"
        or evidence.result not in {"passed", "subsumed"}
        or evidence.exit_code != 0
    ):
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
    review_kind: str = "independent",
) -> EvidenceRecord:
    """Append subject-bound manual evidence for a canonically manual gate."""

    state = Path(state_path).expanduser().resolve()
    root = state.parents[3]
    from mase_cli.gates import load_gate_definitions
    from mase_cli.release import release_context_digest

    definitions = load_gate_definitions(root, required=False)
    definition = definitions.gates.get(str(gate))
    normalized_review_kind = str(review_kind or "independent").lower()
    if normalized_review_kind not in {"self", "independent"}:
        raise GovernanceError("review kind must be self or independent", code="schema")
    if str(gate) in {"independent_review", "security_review", "architecture_review"} and normalized_review_kind != "independent":
        raise GovernanceError(
            f"self review cannot satisfy independent manual gate {gate}", code="conflict"
        )
    current = load_yaml_document(state)
    bound_inputs = set(definition.inputs if definition else ())
    bound_inputs.update(str(item) for item in dict(current.get("impact", {})).get("paths", []))
    change = state.parent
    for name in ("proposal.md", "design.md", "tasks.md", "specs"):
        target = change / name
        if target.exists():
            bound_inputs.add(target.relative_to(root).as_posix())
    inputs = tuple(sorted(bound_inputs))
    input_digest = _path_digest(root, inputs)
    candidate_id = str(dict(current.get("candidate", {})).get("id", ""))
    release_digest = (
        release_context_digest(current["release"])
        if str(gate).startswith("release_") and current.get("release") else ""
    )
    valid = (
        definition is not None
        and definition.mode == "manual"
        and all(str(item).strip() for item in (actor, subject, reference))
    )
    signature_payload = {
        "gate": str(gate),
        "inputs": list(inputs),
        "input_digest": input_digest,
        "scope": "change",
        "candidate_id": candidate_id,
        "release_digest": release_digest,
        "actor": str(actor).strip(),
        "subject": str(subject).strip(),
        "reference": str(reference).strip(),
        "review_kind": normalized_review_kind,
        "decision": "passed" if valid else "failed",
    }
    execution_signature = hashlib.sha256(json.dumps(
        signature_payload, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    record = EvidenceRecord(
        gate=str(gate),
        kind="manual",
        result="passed" if valid else "failed",
        at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        actor=redact_secrets(str(actor)),
        subject=redact_secrets(str(subject)),
        reference=str(reference),
        review_kind=normalized_review_kind,
        input_digest=input_digest,
        inputs=inputs,
        candidate_id=candidate_id,
        release_digest=release_digest,
        execution_signature=execution_signature,
        freshness="fresh" if valid else "invalid",
    )
    indexed = _append_evidence(state, replace(record, execution_id=uuid.uuid4().hex))
    return replace(indexed, freshness="fresh" if valid else "invalid")
