from datetime import date, timedelta
from pathlib import Path

import pytest
import yaml

from mase_cli.baseline import (
    BaselineError,
    approve_candidates,
    collect_candidates,
    compare_baseline,
    load_baseline,
)
from mase_cli.commands import status


def failure(test_id, message, gate="full_unit"):
    return {"test_id": test_id, "message": message, "gate": gate}


def write_state(change, phase="build", dependencies=None, paths=None, gates=None):
    change.mkdir(parents=True)
    payload = {
        "schema": "mase-project/v2",
        "profile": "lite",
        "stack": "generic",
        "phase": phase,
        "risk": {"triggers": []},
        "impact": {"paths": paths or []},
        "gates": gates or {"api_contract": "pending"},
        "evidence": [],
        "dependencies": dependencies or [],
    }
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")


def test_baseline_requires_owner_expiry_and_remediation(tmp_path):
    candidates = collect_candidates([failure("a", "boom")], "pytest -q")

    with pytest.raises(BaselineError, match="owner"):
        approve_candidates(candidates, tmp_path / ".mase" / "baseline.yaml", owner="", expires="", remediation_change="")


def test_baseline_comparison_detects_known_new_changed_resolved_and_expired(tmp_path):
    candidates = collect_candidates(
        [failure("known", "same"), failure("resolved", "old")], "pytest -q"
    )
    baseline_path = tmp_path / ".mase" / "baseline.yaml"
    approve_candidates(
        candidates,
        baseline_path,
        owner="team",
        expires=(date.today() + timedelta(days=30)).isoformat(),
        remediation_change="fix-debt",
    )
    baseline = load_baseline(baseline_path)

    comparison = compare_baseline(
        [failure("known", "same"), failure("new", "new failure")], baseline, gate="full_unit"
    )

    assert comparison.status == "failed"
    assert [item.test_id for item in comparison.known] == ["known"]
    assert [item.test_id for item in comparison.new] == ["new"]
    assert [item.test_id for item in comparison.resolved] == ["resolved"]


def test_hard_gate_failure_cannot_be_approved(tmp_path):
    candidates = collect_candidates(
        [failure("tenant-owner", "cross tenant", gate="api_contract")], "pytest contract"
    )

    with pytest.raises(BaselineError, match="hard gate"):
        approve_candidates(
            candidates,
            tmp_path / "baseline.yaml",
            owner="security",
            expires=(date.today() + timedelta(days=1)).isoformat(),
            remediation_change="fix-contract",
        )


def test_baseline_dry_run_and_repeat_are_non_destructive(tmp_path):
    path = tmp_path / ".mase" / "baseline.yaml"
    candidates = collect_candidates([failure("a", "boom")], "pytest -q")
    kwargs = dict(
        owner="team",
        expires=(date.today() + timedelta(days=5)).isoformat(),
        remediation_change="fix-a",
    )

    approve_candidates(candidates, path, dry_run=True, **kwargs)
    assert not path.exists()
    approve_candidates(candidates, path, **kwargs)
    first = path.read_text(encoding="utf-8")
    approve_candidates(candidates, path, **kwargs)
    assert path.read_text(encoding="utf-8") == first


def test_baseline_detects_changed_and_expired_failures_and_backs_up_updates(tmp_path):
    path = tmp_path / ".mase" / "baseline.yaml"
    original = collect_candidates([failure("a", "old")], "pytest -q")
    approve_candidates(
        original,
        path,
        owner="team",
        expires=(date.today() + timedelta(days=5)).isoformat(),
        remediation_change="fix-a",
    )
    changed = compare_baseline([failure("a", "new")], load_baseline(path), gate="full_unit")
    assert changed.status == "failed"
    assert [item.test_id for item in changed.changed] == ["a"]

    updated = collect_candidates([failure("a", "new")], "pytest -q")
    approve_candidates(
        updated,
        path,
        owner="new-owner",
        expires=(date.today() + timedelta(days=10)).isoformat(),
        remediation_change="replace-a",
    )
    assert list(path.parent.glob("baseline.yaml.bak-*"))

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["failures"][0]["expires"] = (date.today() - timedelta(days=1)).isoformat()
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    expired = compare_baseline([failure("a", "new")], load_baseline(path), gate="full_unit")
    assert expired.status == "failed"
    assert [item.test_id for item in expired.expired] == ["a"]


def test_status_without_change_returns_portfolio_and_detects_dependencies_conflicts(tmp_path):
    changes = tmp_path / "openspec" / "changes"
    write_state(changes / "base", phase="build", paths=["src/auth/**"])
    write_state(
        changes / "consumer",
        dependencies=[{"change": "base", "phase": "complete"}],
        paths=["src/auth/routes.py"],
    )

    portfolio = status.get_status(tmp_path)

    assert len(portfolio.changes) == 2
    consumer = next(item for item in portfolio.changes if item.change == "consumer")
    assert any("dependency" in issue for issue in consumer.issues)
    assert portfolio.conflicts
    assert portfolio.consistent is False


def test_status_handles_zero_changes_and_broken_state_without_traceback(tmp_path):
    (tmp_path / "openspec" / "changes").mkdir(parents=True)
    empty = status.get_status(tmp_path)
    assert empty.changes == ()
    assert empty.consistent is True

    broken = tmp_path / "openspec" / "changes" / "broken"
    broken.mkdir()
    (broken / "mase-state.yaml").write_text("gates: [\n", encoding="utf-8")
    report = status.get_status(tmp_path)
    assert report.consistent is False
    assert report.diagnostics


def test_status_reports_active_change_missing_state(tmp_path):
    change = tmp_path / "openspec" / "changes" / "missing-state"
    change.mkdir(parents=True)
    (change / "proposal.md").write_text("# proposal\n", encoding="utf-8")

    report = status.get_status(tmp_path)

    assert report.consistent is False
    assert report.diagnostics[0].code == "missing_state"


def test_all_tasks_with_pending_gates_is_ready_for_gate(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    write_state(change, phase="verify", gates={"api_contract": "pending"})

    report = status.get_status(tmp_path, "demo")

    assert report.lifecycle == "ready_for_gate"
    assert report.complete == report.total == 1


def test_handwritten_passed_gate_in_release_requires_fresh_evidence(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    write_state(change, phase="release", gates={"api_contract": "passed"})

    report = status.get_status(tmp_path, "demo")

    assert report.lifecycle == "ready_for_gate"
    assert report.effective_gates["api_contract"] == "stale"


def test_status_rejects_unsafe_change_path(tmp_path):
    (tmp_path / "openspec" / "changes").mkdir(parents=True)
    with pytest.raises(ValueError, match="change name"):
        status.get_status(tmp_path, "../outside")


def test_status_detects_missing_and_cyclic_dependencies(tmp_path):
    changes = tmp_path / "openspec" / "changes"
    write_state(changes / "a", dependencies=[{"change": "b"}])
    write_state(changes / "b", dependencies=[{"change": "a"}])
    write_state(changes / "missing-consumer", dependencies=[{"change": "absent"}])

    portfolio = status.get_status(tmp_path)

    a = next(item for item in portfolio.changes if item.change == "a")
    missing = next(item for item in portfolio.changes if item.change == "missing-consumer")
    assert any("cycle" in issue for issue in a.issues)
    assert any("missing" in issue for issue in missing.issues)


def test_status_detects_explicit_conflict_without_path_overlap(tmp_path):
    changes = tmp_path / "openspec" / "changes"
    write_state(changes / "left", paths=["src/left.py"])
    write_state(changes / "right", paths=["src/right.py"])
    path = changes / "left" / "mase-state.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    payload["conflicts_with"] = ["right"]
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    portfolio = status.get_status(tmp_path)

    assert any(item.reason == "declared conflict" for item in portfolio.conflicts)
