from datetime import date, timedelta
from pathlib import Path

import yaml

from mase_cli.commands import update_project
from mase_cli.baseline import approve_candidates, collect_candidates, load_baseline
from mase_cli.gates import load_gate_definitions
from mase_cli.state import ChangeState


FRAMEWORK = Path(__file__).resolve().parents[1]


def legacy_project(tmp_path):
    (tmp_path / ".mase.yaml").write_text(
        yaml.safe_dump(
            {
                "mase": {
                    "version": "1.3",
                    "project": "legacy",
                    "profile": "standard",
                    "stack": "swift-swiftui-flutter-dart-kotlin",
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "mase-project/v2",
                "profile": "standard",
                "stack": "swift-swiftui-flutter-dart-kotlin",
                "phase": "verify",
                "project_type": {"has_ui": True, "ui_platform": "ios"},
                "risk": {"triggers": []},
                "gates": {"related_tests": "passed"},
                "evidence": [
                    {"gate": "related_tests", "result": "passed", "path": "tests passed"}
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
    return change


def migration_changes(tmp_path):
    return [
        item
        for item in update_project.check_updates(tmp_path, FRAMEWORK)
        if item["component"] == ".mase.yaml" or item["component"].endswith("mase-state.yaml")
    ]


def test_governance_migration_dry_run_previews_metadata_state_toolchains_and_evidence(tmp_path):
    legacy_project(tmp_path)
    marker_before = (tmp_path / ".mase.yaml").read_text(encoding="utf-8")

    changes = migration_changes(tmp_path)

    assert {item["component"] for item in changes} == {
        ".mase.yaml",
        "openspec/changes/demo/mase-state.yaml",
    }
    state_change = next(item for item in changes if item["component"].endswith("mase-state.yaml"))
    assert "evidence" in state_change["reason"]
    update_project.apply_updates(changes, tmp_path, dry_run=True, framework_home=FRAMEWORK)
    assert (tmp_path / ".mase.yaml").read_text(encoding="utf-8") == marker_before
    assert not (tmp_path / ".mase-backup").exists()


def test_governance_migration_previews_and_creates_canonical_gate_template(tmp_path):
    legacy_project(tmp_path)

    changes = update_project.check_updates(tmp_path, FRAMEWORK)
    gate_change = next(item for item in changes if item["component"] == ".mase/gates.yaml")
    assert gate_change["action"] == "create"
    assert "legacy mode" in gate_change["reason"]

    update_project.apply_updates([gate_change], tmp_path, framework_home=FRAMEWORK)
    payload = yaml.safe_load((tmp_path / ".mase" / "gates.yaml").read_text())
    assert payload["schema"] == "mase-gates/v1"
    assert load_gate_definitions(tmp_path).legacy is True


def test_governance_migration_is_backed_up_valid_and_idempotent(tmp_path):
    change = legacy_project(tmp_path)
    changes = migration_changes(tmp_path)

    update_project.apply_updates(changes, tmp_path, framework_home=FRAMEWORK)

    marker = yaml.safe_load((tmp_path / ".mase.yaml").read_text(encoding="utf-8"))["mase"]
    assert marker["version"] == "2.4.0"
    assert marker["stack"] == "swift"
    assert marker["toolchains"] == ["dart", "flutter", "kotlin", "swiftui"]
    state = ChangeState.load(change / "mase-state.yaml")
    assert state.stack == "swift"
    assert state.product["has_ui"] is True
    assert state.evidence[0].kind == "legacy"
    assert state.evidence[0].result == "stale"
    assert state.gates["related_tests"] == "stale"
    backups = list((tmp_path / ".mase-backup").glob("*/openspec/changes/demo/mase-state.yaml"))
    assert backups
    assert migration_changes(tmp_path) == []


def test_governance_migration_preserves_malformed_state_as_conflict(tmp_path):
    change = legacy_project(tmp_path)
    state = change / "mase-state.yaml"
    state.write_text("risk: [\n", encoding="utf-8")
    before = state.read_text(encoding="utf-8")

    changes = migration_changes(tmp_path)
    state_change = next(item for item in changes if item["component"].endswith("mase-state.yaml"))
    assert state_change["action"] == "conflict"

    update_project.apply_updates(changes, tmp_path, framework_home=FRAMEWORK)
    assert state.read_text(encoding="utf-8") == before
    assert list((tmp_path / ".mase-backup").glob("*/openspec/changes/demo/mase-state.yaml"))


def test_governance_migration_backup_can_restore_updated_and_created_paths(tmp_path):
    change = legacy_project(tmp_path)
    original_marker = (tmp_path / ".mase.yaml").read_bytes()
    original_state = (change / "mase-state.yaml").read_bytes()
    created = tmp_path / "generated.txt"
    changes = migration_changes(tmp_path) + [
        {
            "component": "generated.txt",
            "action": "create",
            "reason": "rollback fixture",
            "content": "generated\n",
        }
    ]

    backup = update_project.apply_updates(changes, tmp_path, framework_home=FRAMEWORK)
    assert created.exists()
    update_project.rollback_updates(changes, tmp_path, backup)

    assert (tmp_path / ".mase.yaml").read_bytes() == original_marker
    assert (change / "mase-state.yaml").read_bytes() == original_state
    assert not created.exists()


def test_synthetic_brownfield_baseline_survives_governance_migration(tmp_path):
    legacy_project(tmp_path)
    baseline_path = tmp_path / ".mase" / "baseline.yaml"
    candidates = collect_candidates(
        [{"test_id": "legacy::failure", "message": "known debt", "gate": "full_unit"}],
        "python3 -m pytest -q",
    )
    approve_candidates(
        candidates,
        baseline_path,
        owner="legacy-team",
        expires=(date.today() + timedelta(days=30)).isoformat(),
        remediation_change="retire-legacy-failure",
    )
    before = baseline_path.read_bytes()

    changes = migration_changes(tmp_path)
    update_project.apply_updates(changes, tmp_path, framework_home=FRAMEWORK)

    baseline = load_baseline(baseline_path)
    assert baseline.failures[0].owner == "legacy-team"
    assert baseline_path.read_bytes() == before
