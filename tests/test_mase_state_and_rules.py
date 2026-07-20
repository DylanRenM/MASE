from pathlib import Path

import yaml

from mase_cli.rules import RuleSynchronizer
from mase_cli.state import ChangeState, inspect_change_status


def test_completed_tasks_with_build_phase_is_reported_inconsistent(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "mase-project/v2",
                "profile": "lite",
                "stack": "generic",
                "phase": "build",
                "risk": {"triggers": []},
                "gates": {},
                "evidence": [],
            },
            sort_keys=False,
            allow_unicode=True,
        )
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n- [x] 1.2 done\n")

    report = inspect_change_status(change)

    assert report.complete == 2
    assert report.total == 2
    assert report.consistent is False
    assert "phase" in report.issues[0]


def test_state_collects_structured_gate_evidence(tmp_path):
    state_file = tmp_path / "mase-state.yaml"
    state_file.write_text(
        yaml.safe_dump(
            {
                "schema": "mase-project/v2",
                "profile": "standard",
                "stack": "swift",
                "phase": "verify",
                "risk": {"triggers": ["concurrency"]},
                "gates": {"unit": "passed"},
                "evidence": [
                    {"gate": "unit", "result": "passed", "path": "reports/unit.json"}
                ],
            },
            sort_keys=False,
        )
    )

    state = ChangeState.load(state_file)

    assert state.profile == "standard"
    assert state.evidence[0]["path"] == "reports/unit.json"


def test_rule_adapters_share_source_hash_and_are_deterministic(tmp_path):
    source = tmp_path / "project-rules.md"
    source.write_text("# Core rules\n\nR01: confirm requirements\n")
    sync = RuleSynchronizer(source)

    first = sync.render_all()
    second = sync.render_all()

    assert first == second
    hashes = {sync.extract_source_hash(content) for content in first.values()}
    assert hashes == {sync.source_hash}
    assert set(first) == {
        "AGENTS.md",
        "CLAUDE.md",
        "CONVENTIONS.md",
        ".github/copilot-instructions.md",
    }


def test_rule_sync_detects_user_modified_generated_file(tmp_path):
    source = tmp_path / "project-rules.md"
    source.write_text("# Core rules\n")
    sync = RuleSynchronizer(source)
    target = tmp_path / "AGENTS.md"
    target.write_text("<!-- generated source_hash=old -->\nchanged by user\n")

    plan = sync.plan(tmp_path)

    agents_change = next(item for item in plan if item.path.name == "AGENTS.md")
    assert agents_change.action == "conflict"


def test_rule_sync_can_upgrade_an_unmodified_stale_adapter(tmp_path):
    source = tmp_path / "project-rules.md"
    source.write_text("# Rules v1\n")
    old_sync = RuleSynchronizer(source)
    target = tmp_path / "AGENTS.md"
    target.write_text(old_sync.render("AGENTS.md"))
    source.write_text("# Rules v2\n")

    plan = RuleSynchronizer(source).plan(tmp_path)

    agents_change = next(item for item in plan if item.path.name == "AGENTS.md")
    assert agents_change.action == "update"
