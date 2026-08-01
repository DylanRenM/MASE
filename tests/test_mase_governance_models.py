from pathlib import Path

import pytest
import yaml

from mase_cli.commands import check_project
from mase_cli.profiles import ProfileRegistry
from mase_cli.state import ChangeState, inspect_change_status


ROOT = Path(__file__).resolve().parents[1]


def write_project_marker(root, **overrides):
    metadata = {
        "version": "2.1.0",
        "project": "demo",
        "profile": "standard",
        "stack": "python",
        "toolchains": ["flask"],
    }
    metadata.update(overrides)
    (root / ".mase.yaml").write_text(
        yaml.safe_dump({"mase": metadata}, sort_keys=False), encoding="utf-8"
    )


def write_state(change, **overrides):
    payload = {
        "schema": "mase-project/v2",
        "profile": "standard",
        "stack": "python",
        "toolchains": ["flask"],
        "phase": "build",
        "product": {"has_ui": True},
        "impact": {"ui_changed": False, "paths": ["src/demo/**"]},
        "risk": {"triggers": ["authentication"], "capabilities": {}},
        "gates": {
            "api_contract": "pending",
            "security_review": "pending",
            "full_regression": "pending",
            "independent_review": "pending",
        },
        "evidence": [],
        "dependencies": [],
    }
    payload.update(overrides)
    change.mkdir(parents=True)
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    (change / "tasks.md").write_text("- [ ] 1.1 pending\n", encoding="utf-8")


def test_change_state_supports_toolchains_product_impact_and_dependencies(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    write_state(change, dependencies=[{"change": "base", "phase": "complete"}])

    state = ChangeState.load(change / "mase-state.yaml")

    assert state.toolchains == ("flask",)
    assert state.product["has_ui"] is True
    assert state.impact["ui_changed"] is False
    assert state.dependencies[0]["change"] == "base"
    assert state.legacy is False


def test_change_state_preserves_a_versioned_external_framework_contract(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    contract = {
        "name": "MASE",
        "version": "2.4.0",
        "interface": "installed-cli-and-versioned-schemas",
    }
    write_state(change, framework_contract=contract)

    state = ChangeState.load(change / "mase-state.yaml")
    report = inspect_change_status(change)

    assert state.framework_contract == contract
    assert report.to_dict()["framework_contract"] == contract


def test_framework_contract_rejects_a_source_repository_interface(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    write_state(
        change,
        framework_contract={
            "name": "MASE",
            "version": "2.4.0",
            "interface": "sibling-source-repository",
        },
    )

    with pytest.raises(ValueError, match="framework_contract"):
        ChangeState.load(change / "mase-state.yaml")


def test_legacy_evidence_is_loaded_but_marked_legacy_and_stale(tmp_path):
    change = tmp_path / "change"
    write_state(
        change,
        evidence=[{"gate": "unit", "result": "passed", "path": "tests (4 passed)"}],
    )

    state = ChangeState.load(change / "mase-state.yaml")

    assert state.evidence[0].legacy is True
    assert state.evidence[0].freshness == "stale"


def test_illegal_composite_stack_fails_schema_validation(tmp_path):
    change = tmp_path / "change"
    write_state(change, stack="python-flutter-dart")

    with pytest.raises(ValueError, match="stack"):
        ChangeState.load(change / "mase-state.yaml")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"schema": "mase-project/v99"}, "schema"),
        ({"profile": None}, "profile"),
        ({"phase": "shipping"}, "phase"),
    ],
)
def test_unknown_schema_missing_or_invalid_enums_are_rejected(tmp_path, overrides, message):
    change = tmp_path / "change"
    write_state(change, **overrides)

    with pytest.raises(ValueError, match=message):
        ChangeState.load(change / "mase-state.yaml")


def test_check_reports_broken_change_and_continues(tmp_path):
    write_project_marker(tmp_path, stack="generic", toolchains=[])
    for relative in ("README.md", ".gitignore", "project-rules.md"):
        (tmp_path / relative).write_text("ok\n", encoding="utf-8")
    changes = tmp_path / "openspec" / "changes"
    good = changes / "good"
    write_state(good, stack="generic", toolchains=[])
    broken = changes / "broken"
    broken.mkdir(parents=True)
    (broken / "mase-state.yaml").write_text("risk: [\n", encoding="utf-8")

    report = check_project.inspect_project(tmp_path)

    assert report.ok is False
    messages = {item.path: item.message for item in report.items}
    assert "openspec/changes/broken/mase-state.yaml" in messages
    assert "openspec/changes/good/mase-state.yaml" in messages


def test_check_reports_active_change_missing_state(tmp_path):
    write_project_marker(tmp_path, stack="generic", toolchains=[])
    for relative in ("README.md", ".gitignore", "project-rules.md"):
        (tmp_path / relative).write_text("ok\n", encoding="utf-8")
    change = tmp_path / "openspec" / "changes" / "missing-state"
    change.mkdir(parents=True)
    (change / "tasks.md").write_text("- [ ] pending\n", encoding="utf-8")

    report = check_project.inspect_project(tmp_path)

    assert report.ok is False
    item = next(item for item in report.items if item.path.endswith("mase-state.yaml"))
    assert item.message == "missing change state"


def test_gate_plan_escalates_authentication_without_unrelated_ui_gate():
    from mase_cli.risk import derive_gate_plan

    registry = ProfileRegistry(ROOT / "profiles")
    plan = derive_gate_plan(
        registry=registry,
        base_profile="standard",
        triggers=["authentication"],
        product={"has_ui": True},
        impact={"ui_changed": False},
    )

    assert plan.profile == "strict"
    assert "security_review" in plan.required_gates
    assert "api_contract" in plan.required_gates
    assert "p0_e2e" not in plan.required_gates


def test_missing_derived_hard_gate_is_reported(tmp_path):
    change = tmp_path / "change"
    write_state(change, gates={"api_contract": "pending"})

    state = ChangeState.load(change / "mase-state.yaml")

    assert "security_review" in state.gate_plan.missing_gates


def test_skipped_hard_gate_and_pending_terminal_state_are_inconsistent(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    write_state(
        change,
        profile="lite",
        phase="complete",
        product={"has_ui": False},
        risk={"triggers": [], "capabilities": {}},
        gates={
            "api_contract": "skipped",
            "related_tests": "pending",
            "full_regression": "pending",
        },
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
    (change / "specs").mkdir()

    report = inspect_change_status(change)

    assert report.effective_gates["api_contract"] == "skipped"
    assert report.lifecycle == "ready_for_gate"
    assert report.consistent is False
    assert any("terminal phase has incomplete" in issue for issue in report.issues)
