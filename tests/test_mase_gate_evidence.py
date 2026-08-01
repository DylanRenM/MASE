import json
import os
from pathlib import Path

import yaml
import pytest

from mase_cli import main as cli
from mase_cli.evidence import (
    assess_evidence,
    record_manual_evidence,
    redact_secrets,
    run_gate,
)
from mase_cli.schema import GovernanceError
from mase_cli.state import ChangeState


def state_file(tmp_path):
    path = tmp_path / "openspec" / "changes" / "demo" / "mase-state.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(
        yaml.safe_dump({
            "schema": "mase-project/v2",
            "profile": "lite",
            "stack": "generic",
            "phase": "build",
            "risk": {"triggers": []},
            "gates": {"related_tests": "pending", "reference_prototype": "pending"},
            "evidence": [],
        }, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_gate_runner_records_reproducible_evidence(tmp_path):
    state = state_file(tmp_path)
    source = tmp_path / "src.txt"
    source.write_text("before", encoding="utf-8")

    result = run_gate(
        project_root=tmp_path,
        state_path=state,
        gate="related_tests",
        command=["python3", "-c", "print('ok')"],
        inputs=["src.txt"],
    )

    assert result.result == "passed"
    assert result.exit_code == 0
    loaded = ChangeState.load(state)
    evidence = loaded.evidence[-1]
    assert evidence.kind == "automatic"
    assert evidence.command[:2] == ("python3", "-c")
    assert evidence.log_path
    assert assess_evidence(evidence, tmp_path, ["src.txt"]) == "fresh"

    source.write_text("after", encoding="utf-8")
    assert assess_evidence(evidence, tmp_path, ["src.txt"]) == "stale"


def test_gate_runner_detects_replaced_artifact(tmp_path):
    state = state_file(tmp_path)
    artifact = tmp_path / "dist.bin"
    artifact.write_bytes(b"v1")
    result = run_gate(
        tmp_path,
        state,
        "related_tests",
        ["python3", "-c", "pass"],
        artifacts=["dist.bin"],
    )
    artifact.write_bytes(b"v2")

    assert assess_evidence(result, tmp_path, []) == "invalid"


def test_failed_gate_and_missing_log_are_not_fresh(tmp_path):
    state = state_file(tmp_path)
    failed = run_gate(
        tmp_path,
        state,
        "related_tests",
        ["python3", "-c", "raise SystemExit(7)"],
    )
    assert failed.result == "failed"
    assert failed.exit_code == 7
    assert assess_evidence(failed, tmp_path, []) == "invalid"

    passed = run_gate(tmp_path, state, "related_tests", ["python3", "-c", "pass"])
    (tmp_path / passed.log_path).unlink()
    assert assess_evidence(passed, tmp_path, []) == "missing"


def test_redaction_covers_commands_and_logs():
    text = "OPENAI_API_KEY=secret-value Authorization: Bearer abc123 password=hunter2"
    redacted = redact_secrets(text)

    assert "secret-value" not in redacted
    assert "abc123" not in redacted
    assert "hunter2" not in redacted


def test_gate_runner_redacts_persisted_command_environment_and_log(tmp_path, monkeypatch):
    state = state_file(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-secret")
    record = run_gate(
        tmp_path,
        state,
        "related_tests",
        [
            "python3",
            "-c",
            "import os; print('OPENAI_API_KEY=' + os.environ['OPENAI_API_KEY'])",
            "password=command-secret",
        ],
    )

    assert "command-secret" not in " ".join(record.command)
    log = (tmp_path / record.log_path).read_text(encoding="utf-8")
    assert "environment-secret" not in log


def test_gate_runner_binds_adapter_retry_and_flaky_diagnostic(tmp_path):
    state = state_file(tmp_path)
    script = (
        "import json,os,pathlib; "
        "pathlib.Path(os.environ['MASE_TEST_DIAGNOSTIC_PATH']).write_text("
        "json.dumps({'schema':'mase-test-diagnostic/v1','attempts':2,"
        "'first_attempt_result':'failed','final_result':'passed',"
        "'classification':'flaky','failed_tests':['journey-a'],"
        "'artifacts':['trace.zip']}))"
    )

    record = run_gate(
        tmp_path,
        state,
        "p0_e2e",
        ["python3", "-c", script],
        test_digest="digest",
        selected_tests=["journey-a"],
        selection_reason="impact_path_match",
    )

    assert record.result == "passed"
    assert record.first_attempt_result == "failed"
    assert record.attempts == 2
    assert record.failure_classification == "flaky"
    assert record.selected_tests == ("journey-a",)
    assert record.selection_reason == "impact_path_match"
    assert record.diagnostic_path
    assert record.diagnostic_path in record.artifacts
    assert assess_evidence(record, tmp_path, []) == "fresh"


def test_failed_gate_without_adapter_diagnostic_gets_unknown_summary(tmp_path):
    state = state_file(tmp_path)

    record = run_gate(
        tmp_path,
        state,
        "p0_e2e",
        ["python3", "-c", "raise SystemExit(4)"],
        test_digest="digest",
        selected_tests=["journey-a"],
        selection_reason="conservative_all_tier",
        selection_fallback="conservative_all_tier",
    )

    assert record.result == "failed"
    assert record.first_attempt_result == "failed"
    assert record.attempts == 1
    assert record.failure_classification == "unknown"
    diagnostic = Path(tmp_path, record.diagnostic_path)
    assert diagnostic.is_file()
    assert '"classification": "unknown"' in diagnostic.read_text(encoding="utf-8")


def test_diagnostic_secrets_are_redacted_before_binding(tmp_path):
    state = state_file(tmp_path)
    script = (
        "import json,os,pathlib; "
        "pathlib.Path(os.environ['MASE_TEST_DIAGNOSTIC_PATH']).write_text("
        "json.dumps({'schema':'mase-test-diagnostic/v1','attempts':1,"
        "'first_attempt_result':'failed','final_result':'failed',"
        "'classification':'product','failed_tests':['password=hunter2']}))"
        "; raise SystemExit(2)"
    )

    record = run_gate(tmp_path, state, "p0_e2e", ["python3", "-c", script])

    persisted = Path(tmp_path, record.diagnostic_path).read_text(encoding="utf-8")
    assert "hunter2" not in persisted
    assert "[REDACTED]" in persisted


def test_manual_evidence_only_satisfies_manual_gate(tmp_path):
    state = state_file(tmp_path)
    gates = tmp_path / ".mase" / "gates.yaml"
    gates.parent.mkdir(parents=True)
    gates.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "reference_prototype": {
                "stage": "capability", "command": ["manual"], "mode": "manual",
                "inputs": ["src.txt"],
            },
            "api_contract": {
                "stage": "capability", "command": ["python3", "-c", "pass"],
            },
        },
    }, sort_keys=False), encoding="utf-8")
    (tmp_path / "src.txt").write_text("reviewed", encoding="utf-8")
    manual = record_manual_evidence(
        state,
        gate="reference_prototype",
        actor="user@example",
        subject="prototype-v2.html",
        reference="docs/prototype-v2.html",
    )

    assert manual.kind == "manual"
    assert manual.result == "passed"
    assert manual.actor == "user@example"
    (tmp_path / "src.txt").write_text("changed", encoding="utf-8")
    assert assess_evidence(manual, tmp_path, ["src.txt"]) == "stale"

    invalid = record_manual_evidence(
        state,
        gate="api_contract",
        actor="user@example",
        subject="claimed test",
        reference="notes.txt",
    )
    assert invalid.result == "failed"
    assert invalid.freshness == "invalid"


def test_manual_evidence_does_not_invalidate_itself_when_state_is_in_scope(tmp_path):
    state = state_file(tmp_path)
    gates = tmp_path / ".mase" / "gates.yaml"
    gates.parent.mkdir(parents=True)
    gates.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "reference_prototype": {
                "stage": "capability", "command": ["manual"], "mode": "manual",
                "inputs": ["openspec/**"],
            },
        },
    }, sort_keys=False), encoding="utf-8")

    record = record_manual_evidence(
        state, "reference_prototype", "reviewer", "current change", "review-1"
    )

    loaded = ChangeState.load(state).evidence[-1]
    assert assess_evidence(loaded, tmp_path, loaded.inputs) == "fresh"

    (tmp_path / "openspec" / ".DS_Store").write_text("finder", encoding="utf-8")
    cache = tmp_path / "openspec" / "__pycache__"
    cache.mkdir()
    (cache / "generated.pyc").write_bytes(b"cache")
    assert assess_evidence(loaded, tmp_path, loaded.inputs) == "fresh"


def test_gate_cli_is_concise_by_default_and_keeps_complete_log(tmp_path, capsys):
    state = state_file(tmp_path)
    marker = "NOISY_OUTPUT_" * 500

    cli.main([
        "gate", "run", "related_tests", "--dir", str(tmp_path),
        "--change", "demo", "--", "python3", "-c", f"print('{marker}')",
    ])

    captured = capsys.readouterr()
    assert marker not in captured.out
    record = ChangeState.load(state).evidence[-1]
    assert marker in (tmp_path / record.log_path).read_text(encoding="utf-8")
    assert record.log_path in captured.out


def test_gate_cli_failure_prints_bounded_excerpt_and_verbose_streams(tmp_path, capsys):
    state = state_file(tmp_path)
    marker = "FAILURE_DETAIL_" * 600

    with pytest.raises(SystemExit):
        cli.main([
            "gate", "run", "related_tests", "--dir", str(tmp_path),
            "--change", "demo", "--", "python3", "-c",
            f"print('{marker}'); raise SystemExit(2)",
        ])
    concise = capsys.readouterr().out
    assert "FAILURE_DETAIL_" in concise
    assert len(concise) < 6000

    cli.main([
        "gate", "run", "related_tests", "--dir", str(tmp_path),
        "--change", "demo", "--verbose", "--", "python3", "-c",
        "print('LIVE_PROGRESS')",
    ])
    assert "LIVE_PROGRESS" in capsys.readouterr().out


def test_new_evidence_uses_compact_state_index_and_hydrates_sidecar(tmp_path):
    state = state_file(tmp_path)
    record = run_gate(
        tmp_path, state, "related_tests", ["python3", "-c", "print('ok')"],
        inputs=[], selected_tests=["unit.demo"],
    )

    payload = yaml.safe_load(state.read_text())
    summary = payload["evidence"][-1]
    assert summary["evidence_path"] == record.evidence_path
    assert summary["evidence_digest"] == record.evidence_digest
    assert "command" not in summary and "selected_tests" not in summary
    hydrated = ChangeState.load(state).evidence[-1]
    assert hydrated.command[-1] == "print('ok')"
    assert hydrated.selected_tests == ("unit.demo",)
    assert hydrated.sidecar_status == "fresh"


def test_old_embedded_evidence_remains_readable_without_sidecar(tmp_path):
    state = state_file(tmp_path)
    record = run_gate(
        tmp_path, state, "related_tests", ["python3", "-c", "print('legacy ok')"],
        inputs=[], selected_tests=["unit.legacy"],
    )
    sidecar = tmp_path / record.evidence_path
    full_record = json.loads(sidecar.read_text(encoding="utf-8"))
    payload = yaml.safe_load(state.read_text(encoding="utf-8"))
    payload["evidence"][-1] = full_record
    state.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    sidecar.unlink()

    loaded = ChangeState.load(state).evidence[-1]
    assert loaded.command[-1] == "print('legacy ok')"
    assert loaded.selected_tests == ("unit.legacy",)
    assert loaded.evidence_path == ""
    assert assess_evidence(loaded, tmp_path, []) == "fresh"


def test_missing_or_modified_evidence_sidecar_invalidates_gate(tmp_path):
    state = state_file(tmp_path)
    record = run_gate(
        tmp_path, state, "related_tests", ["python3", "-c", "print('ok')"], inputs=[]
    )
    sidecar = tmp_path / record.evidence_path
    sidecar.unlink()
    missing = ChangeState.load(state).evidence[-1]
    assert assess_evidence(missing, tmp_path) == "missing"

    replacement = run_gate(
        tmp_path, state, "related_tests", ["python3", "-c", "print('ok')"], inputs=[]
    )
    (tmp_path / replacement.evidence_path).write_text("{}\n", encoding="utf-8")
    invalid = ChangeState.load(state).evidence[-1]
    assert assess_evidence(invalid, tmp_path) == "invalid"


def test_self_review_cannot_satisfy_independent_manual_gate(tmp_path):
    state = state_file(tmp_path)
    gates = tmp_path / ".mase" / "gates.yaml"
    gates.parent.mkdir(parents=True)
    gates.write_text(yaml.safe_dump({
        "schema": "mase-gates/v1",
        "gates": {
            "independent_review": {
                "stage": "capability", "required_at": "merge",
                "mode": "manual", "command": ["manual"],
            }
        },
    }, sort_keys=False), encoding="utf-8")

    with pytest.raises(GovernanceError, match="self review"):
        record_manual_evidence(
            state, "independent_review", "implementer", "diff", "self-check",
            review_kind="self",
        )
