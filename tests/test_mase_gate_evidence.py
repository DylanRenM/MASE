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


def test_manual_evidence_only_satisfies_manual_gate(tmp_path):
    state = state_file(tmp_path)
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

    invalid = record_manual_evidence(
        state,
        gate="api_contract",
        actor="user@example",
        subject="claimed test",
        reference="notes.txt",
    )
    assert invalid.result == "failed"
    assert invalid.freshness == "invalid"


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
