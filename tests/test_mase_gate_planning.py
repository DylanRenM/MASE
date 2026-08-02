import json
import sqlite3
from pathlib import Path

import pytest
import yaml

from mase_cli import main as cli
from mase_cli.commands import status
from mase_cli.evidence import record_manual_evidence, run_gate
from mase_cli.gates import (
    candidate_freshness,
    execute_defined_gate,
    freeze_candidate,
    load_gate_definitions,
    plan_change,
)
from mase_cli.profiles import ProfileRegistry
from mase_cli.risk import derive_gate_plan
from mase_cli.schema import GovernanceError
from mase_cli.state import ChangeState


ROOT = Path(__file__).resolve().parents[1]


def _write_change(root: Path, *, tasks_done=True, profile="lite", capabilities=None):
    change = root / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    payload = {
        "schema": "mase-project/v2",
        "profile": profile,
        "stack": "generic",
        "phase": "verify",
        "product": {"has_ui": False, "ui_platform": None},
        "impact": {"ui_changed": False, "paths": ["src/**"]},
        "risk": {"triggers": [], "capabilities": capabilities or {}},
        "gates": {"api_contract": "pending"},
        "evidence": [],
        "dependencies": [],
        "conflicts_with": [],
        "blockers": [],
    }
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    marker = "x" if tasks_done else " "
    (change / "tasks.md").write_text(f"- [{marker}] 1.1 task\n", encoding="utf-8")
    (change / "specs").mkdir()
    (change / "specs" / "spec.md").write_text("spec\n", encoding="utf-8")
    if profile in {"standard", "strict"}:
        (change / "design.md").write_text("design\n", encoding="utf-8")
    if profile == "strict":
        for artifact in ("proposal.md", "tech-feasibility.md", "architecture.md", "detailed-design.md"):
            (change / artifact).write_text(f"{artifact}\n", encoding="utf-8")
    (root / "src").mkdir()
    (root / "src" / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
    return change


def _write_gates(root: Path, gates: dict):
    target = root / ".mase" / "gates.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump({"schema": "mase-gates/v1", "gates": gates}, sort_keys=False),
        encoding="utf-8",
    )
    return target


def _write_test_manifest(root: Path, tests: list):
    target = root / ".mase" / "tests.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(yaml.safe_dump({
        "schema": "mase-test-manifest/v1",
        "tests": tests,
    }, sort_keys=False), encoding="utf-8")
    return target


def _pass_api(root: Path, change: Path):
    return run_gate(
        root,
        change / "mase-state.yaml",
        "api_contract",
        ["python3", "-c", "print('ok')"],
        inputs=["src/feature.py"],
    )


def test_status_uses_evidence_freshness_instead_of_raw_passed(tmp_path):
    change = _write_change(tmp_path)
    _pass_api(tmp_path, change)
    first = status.get_status(tmp_path, "demo")
    assert first.effective_gates["api_contract"] == "passed"

    (tmp_path / "src" / "feature.py").write_text("VALUE = 2\n", encoding="utf-8")
    stale = status.get_status(tmp_path, "demo")

    assert stale.effective_gates["api_contract"] == "stale"
    assert stale.lifecycle == "ready_for_gate"
    assert any("api_contract=stale" in issue for issue in stale.issues)


def test_status_reports_missing_log_and_invalid_artifact(tmp_path):
    change = _write_change(tmp_path)
    passed = _pass_api(tmp_path, change)
    (tmp_path / passed.log_path).unlink()
    assert status.get_status(tmp_path, "demo").effective_gates["api_contract"] == "missing"

    artifact = tmp_path / "contract.json"
    artifact.write_text("v1\n", encoding="utf-8")
    run_gate(
        tmp_path,
        change / "mase-state.yaml",
        "api_contract",
        ["python3", "-c", "print('ok')"],
        inputs=["src/feature.py"],
        artifacts=["contract.json"],
    )
    artifact.write_text("v2\n", encoding="utf-8")
    assert status.get_status(tmp_path, "demo").effective_gates["api_contract"] == "invalid"


def test_status_accepts_fresh_manual_evidence_only_for_manual_gate(tmp_path):
    change = _write_change(tmp_path, profile="standard")
    _write_gates(tmp_path, {
        "security_review": {
            "stage": "capability", "command": ["manual"], "mode": "manual",
            "inputs": ["src/feature.py"],
        },
    })
    _pass_api(tmp_path, change)
    record_manual_evidence(
        change / "mase-state.yaml",
        "security_review",
        "reviewer@example",
        "demo change",
        "review-thread-1",
    )

    report = status.get_status(tmp_path, "demo")

    assert report.effective_gates["security_review"] == "passed"
    assert report.lifecycle == "ready_for_gate"


def test_latest_failure_and_recovery_determine_effective_state(tmp_path):
    change = _write_change(tmp_path)
    _pass_api(tmp_path, change)
    run_gate(
        tmp_path, change / "mase-state.yaml", "api_contract",
        ["python3", "-c", "raise SystemExit(2)"], inputs=["src/feature.py"],
    )
    assert status.get_status(tmp_path, "demo").effective_gates["api_contract"] == "failed"

    _pass_api(tmp_path, change)
    assert status.get_status(tmp_path, "demo").effective_gates["api_contract"] == "passed"


def test_raw_passed_without_structured_evidence_is_stale(tmp_path):
    change = _write_change(tmp_path)
    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    payload["gates"]["api_contract"] = "passed"
    (change / "mase-state.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))

    report = status.get_status(tmp_path, "demo")
    assert report.effective_gates["api_contract"] == "stale"
    assert report.lifecycle == "ready_for_gate"


def test_gate_loader_validates_schema_and_rejects_escaping_inputs(tmp_path):
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability",
            "command": ["python3", "-m", "pytest", "tests/unit"],
            "inputs": ["src", "tests/unit"],
            "tests": ["tests/unit"],
        }
    })
    definitions = load_gate_definitions(tmp_path)
    assert definitions.gates["related_tests"].stage == "capability"

    _write_gates(tmp_path, {
        "bad": {"stage": "micro", "command": ["true"], "inputs": ["../outside"]}
    })
    with pytest.raises(GovernanceError, match="escapes project root"):
        load_gate_definitions(tmp_path)

    _write_gates(tmp_path, {
        "same": {
            "stage": "micro", "command": ["true"], "covers": ["same"],
        }
    })
    with pytest.raises(GovernanceError, match="cannot cover itself"):
        load_gate_definitions(tmp_path)

    _write_gates(tmp_path, {
        "a": {"stage": "micro", "command": ["true"], "requires": ["b"]},
        "b": {"stage": "micro", "command": ["true"], "requires": ["a"]},
    })
    with pytest.raises(GovernanceError, match="cycle"):
        load_gate_definitions(tmp_path)


def test_gate_required_at_targets_separate_development_merge_and_release(tmp_path):
    change = _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": ["python3", "-c", "print('focused')"],
            "inputs": ["src/feature.py"],
        },
        "api_contract": {
            "stage": "capability", "required_at": "merge",
            "command": ["python3", "-c", "print('contract')"],
            "inputs": ["src/feature.py"],
        },
        "full_regression": {
            "stage": "final", "required_at": "release", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
            "inputs": ["src"],
        },
    })
    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    payload["gates"] = {
        "related_tests": "pending", "api_contract": "pending", "full_regression": "pending"
    }
    (change / "mase-state.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))

    development = plan_change(tmp_path, "demo", target="development")
    merge = plan_change(tmp_path, "demo", target="merge")

    assert tuple(development.instances) == ("related_tests",)
    assert set(merge.instances) == {"related_tests", "api_contract"}
    assert development.instances["related_tests"].required_at == "development"

    execute_defined_gate(tmp_path, "demo", "related_tests")
    report = status.get_status(tmp_path, "demo")
    assert report.verification_milestone == "dev_verified"
    assert report.lifecycle == "ready_for_gate"


def test_legacy_stage_maps_to_required_at_and_candidate_bound_cannot_be_early(tmp_path):
    _write_gates(tmp_path, {
        "related_tests": {"stage": "micro", "command": ["true"]},
        "api_contract": {"stage": "capability", "command": ["true"]},
        "full_regression": {
            "stage": "final", "candidate_bound": True, "command": ["true"]
        },
    })
    definitions = load_gate_definitions(tmp_path)
    assert definitions.gates["related_tests"].required_at == "development"
    assert definitions.gates["api_contract"].required_at == "merge"
    assert definitions.gates["full_regression"].required_at == "release"

    _write_gates(tmp_path, {
        "full_regression": {
            "stage": "final", "required_at": "development",
            "candidate_bound": True, "command": ["true"],
        },
    })
    with pytest.raises(GovernanceError, match="candidate-bound"):
        load_gate_definitions(tmp_path)


def test_candidate_freeze_requires_merge_but_not_release_gates(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "required_at": "merge",
            "command": ["python3", "-c", "print('api')"],
            "inputs": ["src/feature.py"],
        },
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": ["python3", "-c", "print('related')"],
            "inputs": ["src/feature.py"],
        },
        "full_regression": {
            "stage": "final", "required_at": "release", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
            "inputs": ["src"],
        },
    })
    execute_defined_gate(tmp_path, "demo", "related_tests")
    execute_defined_gate(tmp_path, "demo", "api_contract")

    candidate = freeze_candidate(tmp_path, "demo")

    assert candidate.id
    assert status.get_status(tmp_path, "demo").verification_milestone == "candidate_frozen"


def test_dynamic_gate_requires_selected_tests_placeholder(tmp_path):
    _write_gates(tmp_path, {
        "p0_e2e": {
            "stage": "capability",
            "command": ["python3", "-c", "pass"],
            "test_tiers": ["p0_journey"],
        },
    })

    with pytest.raises(GovernanceError, match="selected_tests"):
        load_gate_definitions(tmp_path)


def test_gate_can_select_explicit_stable_test_ids(tmp_path):
    _write_change(tmp_path)
    _write_test_manifest(tmp_path, [{
        "id": "contract.one",
        "tier": "contract",
        "runner": "pytest",
        "selectors": ["tests/test_contract.py::test_one"],
        "paths": ["src/**"],
    }])
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability",
            "command": ["python3", "-c", "print('ok')", "{selected_tests}"],
            "test_ids": ["contract.one"],
        }
    })

    report = plan_change(tmp_path, "demo")

    assert report.instances["related_tests"].selected_tests == ("contract.one",)
    execution = execute_defined_gate(tmp_path, "demo", "related_tests")
    assert execution.record.selected_tests == ("contract.one",)


def test_plan_and_runner_consume_impact_selected_tests(tmp_path):
    change = _write_change(tmp_path)
    payload = yaml.safe_load((change / "mase-state.yaml").read_text(encoding="utf-8"))
    payload["product"] = {"has_ui": True, "ui_platform": "web"}
    payload["impact"] = {"ui_changed": True, "paths": ["templates/testcase.html"]}
    payload["risk"] = {
        "triggers": ["ui_change"],
        "capabilities": {
            "testcase_generation": {
                "profile": "lite",
                "paths": ["templates/testcase.html"],
            },
        },
    }
    payload["gates"]["p0_e2e"] = "pending"
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "testcase.html").write_text("ui", encoding="utf-8")
    (tmp_path / "e2e" / "tests").mkdir(parents=True)
    selected_test = tmp_path / "e2e" / "tests" / "testcase.spec.js"
    selected_test.write_text("test", encoding="utf-8")
    _write_test_manifest(tmp_path, [{
        "id": "testcase-generate-download",
        "tier": "p0_journey",
        "runner": "playwright",
        "selectors": ["e2e/tests/testcase.spec.js"],
        "capabilities": ["testcase_generation"],
        "paths": ["templates/testcase.html"],
        "acceptance": "上传、生成并下载测试用例",
    }])
    _write_gates(tmp_path, {
        "p0_e2e": {
            "stage": "capability",
            "command": [
                "python3", "-c",
                "import pathlib,sys; pathlib.Path('selected.txt').write_text('|'.join(sys.argv[1:]))",
                "{selected_tests}",
            ],
            "inputs": ["templates"],
            "test_tiers": ["p0_journey"],
        },
    })

    plan = plan_change(tmp_path, "demo")
    planned = plan.instances["p0_e2e"]
    assert planned.selected_tests == ("testcase-generate-download",)
    assert planned.selection_reason.endswith("impact_path_match")
    assert planned.selection_fallback == ""

    execution = execute_defined_gate(tmp_path, "demo", "p0_e2e")
    assert (tmp_path / "selected.txt").read_text(encoding="utf-8") == "e2e/tests/testcase.spec.js"
    assert execution.record.command[-1] == "e2e/tests/testcase.spec.js"
    assert execution.record.test_digest
    assert ".mase/tests.yaml" in execution.record.inputs
    assert "e2e/tests/testcase.spec.js" in execution.record.inputs


def test_dynamic_gate_without_manifest_uses_static_tests_compatibly(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability",
            "command": ["python3", "-c", "pass", "{selected_tests}"],
            "tests": ["tests/unit"],
            "test_tiers": ["unit"],
        },
    })

    plan = plan_change(tmp_path, "demo")

    assert plan.instances["related_tests"].selected_tests == ("tests/unit",)
    assert plan.instances["related_tests"].selection_fallback == "legacy_static_tests"
    record = execute_defined_gate(tmp_path, "demo", "related_tests").record
    assert record.command[-1] == "tests/unit"


def test_plan_defers_final_and_reports_duplicate_test_sets(tmp_path):
    _write_change(tmp_path, tasks_done=False)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-m", "pytest", "tests/shared"],
            "inputs": ["src", "tests"], "tests": ["tests/shared"],
        },
        "integration_tests": {
            "stage": "capability", "command": ["python3", "-m", "pytest", "tests/shared"],
            "inputs": ["src", "tests"], "tests": ["tests/shared"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-m", "pytest"], "inputs": ["src", "tests"],
            "tests": ["tests"],
        },
    })

    report = plan_change(tmp_path, "demo", include_all=True)

    assert report.instances["full_regression"].status == "deferred"
    assert "tasks" in report.instances["full_regression"].reason
    assert report.instances["full_regression"].next_action == "complete remaining tasks"
    assert report.profile == "lite"
    assert report.test_schedule["micro"] == ("related_unit", "related_contract")
    assert any(item.code == "duplicate_test_set" for item in report.diagnostics)


def test_plan_reports_high_overlap_without_treating_gates_as_equivalent(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-m", "pytest", "tests/unit"],
            "tests": ["a", "b", "c", "d"],
        },
        "integration_tests": {
            "stage": "capability", "command": ["python3", "-m", "pytest", "tests/integration"],
            "tests": ["a", "b", "c", "d", "e"],
        },
    })

    report = plan_change(tmp_path, "demo", include_all=True)

    assert any(item.code == "high_test_overlap" for item in report.diagnostics)
    assert report.instances["related_tests"].status == "runnable"
    assert report.instances["integration_tests"].status == "optional"


def test_default_plan_hides_unselected_gates_and_containment_is_diagnosed(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-m", "pytest"],
            "tests": ["a", "b", "c", "d", "e", "f", "g", "h"],
        },
        "security_review": {
            "stage": "capability", "command": ["python3", "-m", "pytest"],
            "tests": ["a", "b", "c"],
        },
    })

    default = plan_change(tmp_path, "demo")
    complete = plan_change(tmp_path, "demo", include_all=True)

    assert "security_review" not in default.instances
    assert complete.instances["security_review"].status == "optional"
    diagnostic = next(item for item in complete.diagnostics if item.code == "high_test_overlap")
    assert "containment=100%" in diagnostic.message


def test_final_blocked_by_manual_gate_recommends_manual_command(tmp_path):
    _write_change(tmp_path, profile="standard")
    _write_gates(tmp_path, {
        "api_contract": {"stage": "capability", "command": ["true"]},
        "related_tests": {"stage": "capability", "command": ["true"]},
        "integration_tests": {"stage": "capability", "command": ["true"]},
        "code_review": {
            "stage": "capability", "command": ["manual"], "mode": "manual",
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True, "command": ["true"],
        },
    })
    for gate in ("api_contract", "related_tests", "integration_tests"):
        execute_defined_gate(tmp_path, "demo", gate)

    report = plan_change(tmp_path, "demo")

    assert report.instances["code_review"].status == "manual"
    assert report.instances["full_regression"].next_action.startswith(
        "mase gate manual code_review"
    )


def test_plan_defers_final_until_required_non_final_gate_is_fresh(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('api')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('related')"],
            "inputs": ["src/feature.py"], "tests": ["related"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
            "inputs": ["src", "tests"], "tests": ["tests"],
        },
    })

    report = plan_change(tmp_path, "demo")

    assert report.instances["full_regression"].status == "deferred"
    assert "api_contract" in report.instances["full_regression"].reason
    assert report.instances["full_regression"].next_action.startswith(
        "mase gate run api_contract"
    )


def test_general_gate_requires_is_planned_and_enforced(tmp_path):
    _write_change(tmp_path, profile="standard")
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "required_at": "merge",
            "command": ["python3", "-c", "print('api')"],
        },
        "integration_tests": {
            "stage": "capability", "required_at": "merge",
            "command": ["python3", "-c", "print('integration')"],
            "requires": ["api_contract"],
        },
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": ["python3", "-c", "print('related')"],
        },
        "code_review": {
            "stage": "capability", "required_at": "merge",
            "mode": "manual", "command": ["manual"],
        },
        "full_regression": {
            "stage": "final", "required_at": "release", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
        },
    })

    plan = plan_change(tmp_path, "demo", target="merge")

    assert list(plan.instances).index("api_contract") < list(plan.instances).index("integration_tests")
    assert plan.instances["integration_tests"].status == "deferred"
    assert plan.instances["integration_tests"].next_action.startswith("mase gate run api_contract")
    with pytest.raises(GovernanceError, match="predecessor"):
        execute_defined_gate(tmp_path, "demo", "integration_tests")


def test_freeze_is_stable_then_stale_after_candidate_input_change(tmp_path):
    change = _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('ok')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('related')"],
            "inputs": ["src/feature.py"], "tests": ["related"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-m", "pytest"],
            "inputs": ["src", "tests"], "tests": ["tests"],
        },
    })
    _pass_api(tmp_path, change)
    execute_defined_gate(tmp_path, "demo", "related_tests")

    candidate = freeze_candidate(tmp_path, "demo")
    assert candidate_freshness(tmp_path, "demo") == "fresh"
    assert freeze_candidate(tmp_path, "demo").id == candidate.id

    (tmp_path / "src" / "feature.py").write_text("VALUE = 9\n", encoding="utf-8")
    assert candidate_freshness(tmp_path, "demo") == "stale"


def test_candidate_bound_final_evidence_becomes_stale_when_candidate_changes(tmp_path):
    _write_change(tmp_path, profile="strict")
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('api')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('related')"],
            "inputs": ["src/feature.py"], "tests": ["related"],
        },
        "integration_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('integration')"],
            "inputs": ["src/feature.py"], "tests": ["integration"],
        },
        "p0_e2e": {
            "stage": "capability", "command": ["python3", "-c", "print('p0')"],
            "inputs": ["src/feature.py"], "tests": ["p0"],
        },
        "security_review": {
            "stage": "capability", "command": ["python3", "-c", "print('security')"],
            "inputs": ["src/feature.py"], "tests": ["security"],
        },
        "independent_review": {
            "stage": "capability", "command": ["python3", "-c", "print('review')"],
            "inputs": ["src/feature.py"], "tests": ["review"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
            "inputs": ["src", "tests"], "tests": ["tests"],
        },
    })
    for gate in ("api_contract", "p0_e2e", "security_review", "independent_review", "related_tests", "integration_tests"):
        execute_defined_gate(tmp_path, "demo", gate)

    freeze_candidate(tmp_path, "demo")
    execute_defined_gate(tmp_path, "demo", "full_regression")
    passed = status.get_status(tmp_path, "demo")
    assert passed.effective_gates["full_regression"] == "passed"
    assert passed.lifecycle == "ready_to_complete"

    (tmp_path / "src" / "feature.py").write_text("VALUE = 10\n", encoding="utf-8")
    stale = status.get_status(tmp_path, "demo")
    assert stale.effective_gates["full_regression"] == "stale"
    assert stale.lifecycle == "ready_for_gate"


def test_freeze_rejects_missing_definitions_for_required_gates(tmp_path):
    _write_change(tmp_path, profile="strict")
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('api')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
    })
    execute_defined_gate(tmp_path, "demo", "api_contract")

    with pytest.raises(GovernanceError, match="required gate definitions are missing"):
        freeze_candidate(tmp_path, "demo")


def test_exact_defined_execution_is_reused_and_covers_are_explicit(tmp_path):
    change = _write_change(tmp_path)
    counter = tmp_path / "counter.txt"
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability",
            "command": [
                "python3", "-c",
                "from pathlib import Path; p=Path('counter.txt'); p.write_text(str(int(p.read_text())+1))",
            ],
            "inputs": ["src/feature.py", "tests"], "tests": ["unit", "integration"],
            "covers": ["integration_tests"],
        },
        "integration_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('integration')"],
            "inputs": ["src/feature.py"], "tests": ["integration"],
        },
    })
    counter.write_text("0", encoding="utf-8")

    first = execute_defined_gate(tmp_path, "demo", "related_tests")
    second = execute_defined_gate(tmp_path, "demo", "related_tests")

    assert first.reused is False
    assert second.reused is True
    assert counter.read_text() == "1"
    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    related = next(item for item in payload["evidence"] if item["gate"] == "related_tests")
    covered = next(item for item in payload["evidence"] if item["gate"] == "integration_tests")
    assert related["execution_id"] == covered["execution_id"]
    assert covered["reused_from"] == "related_tests"
    assert covered["result"] == "subsumed"
    assert status.get_status(tmp_path, "demo").effective_gates["integration_tests"] == "subsumed"


def test_dependency_lock_and_environment_are_part_of_cache_and_cover_equivalence(tmp_path):
    _write_change(tmp_path)
    (tmp_path / "lock.txt").write_text("v1\n", encoding="utf-8")
    (tmp_path / "fixture.json").write_text("{}\n", encoding="utf-8")
    counter = tmp_path / "counter.txt"
    counter.write_text("0", encoding="utf-8")
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": [
                "python3", "-c",
                "from pathlib import Path; p=Path('counter.txt'); p.write_text(str(int(p.read_text())+1))",
            ],
            "inputs": ["src/feature.py"], "tests": ["unit"],
            "dependency_locks": ["lock.txt"], "fixture_inputs": ["fixture.json"],
            "toolchain": "python-3", "environment": "standard",
        },
    })
    first = execute_defined_gate(tmp_path, "demo", "related_tests")
    cached = execute_defined_gate(tmp_path, "demo", "related_tests")
    (tmp_path / "lock.txt").write_text("v2\n", encoding="utf-8")
    changed = execute_defined_gate(tmp_path, "demo", "related_tests")

    assert first.reused is False and cached.reused is True and changed.reused is False
    assert counter.read_text(encoding="utf-8") == "2"
    assert changed.record.environment_digest != first.record.environment_digest


def test_gate_plan_reports_p50_p90_budget_and_unknown_stage_costs(tmp_path):
    change = _write_change(tmp_path)
    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    payload["change_risk"] = {"level": "L1", "dimensions": {}}
    (change / "mase-state.yaml").write_text(yaml.safe_dump(payload, sort_keys=False))
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": ["python3", "-c", "print('related')"],
        },
        "api_contract": {
            "stage": "capability", "required_at": "merge",
            "command": ["python3", "-c", "print('api')"],
        },
        "full_regression": {
            "stage": "final", "required_at": "release", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
        },
    })
    history = tmp_path / ".mase" / "evidence" / "history"
    history.mkdir(parents=True)
    for index, duration in enumerate((360.0, 420.0, 480.0)):
        (history / f"related-{index}.json").write_text(json.dumps({
            "gate": "related_tests", "kind": "automatic", "result": "passed",
            "at": f"2026-08-01T00:0{index}:00Z", "execution_id": f"history{index:02d}",
            "duration_seconds": duration, "platform": "",
        }), encoding="utf-8")

    plan = plan_change(tmp_path, "demo", target="development")
    development = plan.costs["development"]

    assert development.sample_status == "estimated"
    assert development.p50_seconds == 420.0
    assert development.p90_seconds > 420.0
    assert development.budget_seconds == 300.0
    assert development.budget_exceeded is True
    assert plan.costs["release"].sample_status == "unknown"
    assert any(item.code == "budget_exceeded" for item in plan.diagnostics)
    assert "costs" in plan.to_dict() and "metrics" in plan.to_dict()


def test_gate_plan_reports_unknown_efficiency_rates_without_execution_events(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "micro", "required_at": "development",
            "command": ["python3", "-c", "print('related')"],
        },
    })

    metrics = plan_change(tmp_path, "demo", target="development").metrics

    assert metrics["cache_hit_rate"] is None
    assert metrics["equivalent_redundant_execution_rate"] is None


def test_invalid_cover_is_rejected_before_source_command_executes(tmp_path):
    _write_change(tmp_path)
    counter = tmp_path / "counter.txt"
    counter.write_text("0", encoding="utf-8")
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability",
            "command": [
                "python3", "-c",
                "from pathlib import Path; Path('counter.txt').write_text('1')",
            ],
            "inputs": ["src/feature.py"], "tests": ["unit"],
            "covers": ["integration_tests"],
        },
        "integration_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('integration')"],
            "inputs": ["src/feature.py", "tests"], "tests": ["integration"],
        },
    })

    with pytest.raises(GovernanceError, match="inputs are not a superset"):
        execute_defined_gate(tmp_path, "demo", "related_tests")
    assert counter.read_text(encoding="utf-8") == "0"


def test_changed_canonical_execution_signature_runs_again(tmp_path):
    _write_change(tmp_path)
    counter = tmp_path / "counter.txt"
    counter.write_text("0", encoding="utf-8")
    gates = {
        "related_tests": {
            "stage": "capability",
            "command": [
                "python3", "-c",
                "from pathlib import Path; p=Path('counter.txt'); p.write_text(str(int(p.read_text())+1))",
            ],
            "inputs": ["src/feature.py"], "tests": ["unit"],
        },
    }
    _write_gates(tmp_path, gates)
    first = execute_defined_gate(tmp_path, "demo", "related_tests")
    gates["related_tests"]["command"] = [
        "python3", "-c",
        "from pathlib import Path; p=Path('counter.txt'); p.write_text(str(int(p.read_text())+10))",
    ]
    _write_gates(tmp_path, gates)
    second = execute_defined_gate(tmp_path, "demo", "related_tests")

    assert first.reused is False
    assert second.reused is False
    assert counter.read_text(encoding="utf-8") == "11"


def test_evidence_history_is_bounded_per_gate(tmp_path):
    change = _write_change(tmp_path)
    for index in range(6):
        run_gate(
            tmp_path,
            change / "mase-state.yaml",
            "api_contract",
            ["python3", "-c", f"print({index})"],
            inputs=["src/feature.py"],
            retention=3,
        )

    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    records = [item for item in payload["evidence"] if item["gate"] == "api_contract"]
    assert len(records) <= 3


def test_evidence_retention_preserves_latest_pass_failure_and_replacement(tmp_path):
    change = _write_change(tmp_path)
    commands = [
        ["python3", "-c", "print('pass-1')"],
        ["python3", "-c", "raise SystemExit(2)"],
        ["python3", "-c", "print('pass-2')"],
        ["python3", "-c", "print('pass-3')"],
        ["python3", "-c", "print('pass-4')"],
    ]
    for command in commands:
        run_gate(
            tmp_path,
            change / "mase-state.yaml",
            "api_contract",
            command,
            inputs=["src/feature.py"],
            retention=3,
        )

    payload = yaml.safe_load((change / "mase-state.yaml").read_text())
    records = [item for item in payload["evidence"] if item["gate"] == "api_contract"]
    assert [item["result"] for item in records] == ["failed", "passed", "passed"]
    assert all("command" not in item and item.get("evidence_path") for item in records)
    hydrated = [
        item for item in ChangeState.load(change / "mase-state.yaml").evidence
        if item.gate == "api_contract"
    ]
    assert "pass-3" in " ".join(hydrated[-2].command)
    assert "pass-4" in " ".join(hydrated[-1].command)


def test_capability_plans_are_local_but_strict_final_floor_is_preserved():
    registry = ProfileRegistry(ROOT / "profiles")
    plan = derive_gate_plan(
        registry,
        "standard",
        [],
        product={"has_ui": True},
        impact={"ui_changed": True},
        capabilities={
            "home": {"profile": "standard", "paths": ["templates/**"]},
            "auth": {
                "profile": "standard", "triggers": ["authorization"],
                "paths": ["src/auth/**"],
            },
        },
    )

    assert plan.capability_plans["home"].profile == "standard"
    assert plan.capability_plans["auth"].profile == "strict"
    assert plan.capability_plans["auth"].paths == ("src/auth/**",)
    assert "full_regression" in plan.required_gates
    assert "independent_review" in plan.required_gates


def test_legacy_capability_uses_conservative_change_paths_with_diagnostic():
    registry = ProfileRegistry(ROOT / "profiles")
    plan = derive_gate_plan(
        registry,
        "standard",
        [],
        impact={"paths": ["src/**", "tests/**"]},
        capabilities={"legacy": {"profile": "strict"}},
    )

    capability = plan.capability_plans["legacy"]
    assert capability.paths == ("src/**", "tests/**")
    assert capability.diagnostics == (
        "legacy capability declaration uses conservative change scope",
    )


def test_gate_plan_omits_capability_gate_that_is_not_applicable_to_scope(tmp_path):
    capabilities = {
        "home": {"profile": "standard", "paths": ["src/home/**"]},
        "auth": {"profile": "strict", "paths": ["src/auth/**"]},
    }
    _write_change(tmp_path, profile="standard", capabilities=capabilities)
    _write_gates(tmp_path, {
        "independent_review": {
            "stage": "capability", "command": ["python3", "-c", "print('review')"],
            "inputs": ["src"], "tests": ["review"],
            "capabilities": ["home", "auth"],
        },
    })

    report = plan_change(tmp_path, "demo")

    assert "independent_review@home" not in report.instances
    assert report.instances["independent_review@auth"].scope == "auth"
    with pytest.raises(GovernanceError, match="not applicable"):
        execute_defined_gate(tmp_path, "demo", "independent_review", scope="home")
    execute_defined_gate(tmp_path, "demo", "independent_review", scope="auth")
    assert status.get_status(tmp_path, "demo").effective_gates["independent_review"] == "passed"


def test_cli_plan_and_freeze_json_contract(tmp_path, capsys):
    change = _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('ok')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('related')"],
            "inputs": ["src/feature.py"], "tests": ["related"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-c", "print('full')"],
            "inputs": ["src", "tests"], "tests": ["tests"],
        },
    })
    _pass_api(tmp_path, change)
    execute_defined_gate(tmp_path, "demo", "related_tests")

    assert cli.main(["gate", "plan", "--dir", str(tmp_path), "--change", "demo", "--json"]) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["change"] == "demo"
    assert planned["profile"] == "lite"
    assert planned["test_schedule"]["final"]

    assert cli.main(["gate", "freeze", "--dir", str(tmp_path), "--change", "demo", "--json"]) == 0
    frozen = json.loads(capsys.readouterr().out)
    assert frozen["candidate_id"]


def test_defined_runner_streams_output_and_rejects_command_drift(tmp_path, capsys):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('streamed')"],
            "inputs": ["src/feature.py"], "tests": ["unit"],
        }
    })

    execute_defined_gate(tmp_path, "demo", "related_tests", stream_output=True)
    assert "streamed" in capsys.readouterr().out

    with pytest.raises(GovernanceError, match="conflicts"):
        execute_defined_gate(
            tmp_path, "demo", "related_tests",
            explicit_command=["python3", "-c", "print('different')"],
        )


def test_cli_reports_legacy_warning_and_canonical_cache_hit(tmp_path, capsys):
    _write_change(tmp_path)
    assert cli.main([
        "gate", "run", "api_contract", "--dir", str(tmp_path), "--change", "demo",
        "--", "python3", "-c", "print('legacy')",
    ]) == 0
    legacy = capsys.readouterr()
    assert "ad-hoc compatibility mode" in legacy.err

    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('canonical')"],
            "inputs": ["src/feature.py"], "tests": ["unit"],
        },
    })
    assert cli.main([
        "gate", "run", "related_tests", "--dir", str(tmp_path), "--change", "demo",
    ]) == 0
    capsys.readouterr()
    assert cli.main([
        "gate", "run", "related_tests", "--dir", str(tmp_path), "--change", "demo",
    ]) == 0
    assert "[cache hit]" in capsys.readouterr().out


def test_capability_scope_is_visible_and_does_not_stale_other_scope(tmp_path):
    capabilities = {
        "home": {"profile": "standard", "paths": ["src/home/**"]},
        "auth": {"profile": "strict", "paths": ["src/auth/**"]},
    }
    change = _write_change(tmp_path, capabilities=capabilities)
    (tmp_path / "src" / "home").mkdir()
    (tmp_path / "src" / "auth").mkdir()
    (tmp_path / "src" / "home" / "view.py").write_text("HOME=1\n")
    (tmp_path / "src" / "auth" / "policy.py").write_text("AUTH=1\n")
    _write_gates(tmp_path, {
        "related_tests": {
            "stage": "capability", "command": ["python3", "-c", "print('ok')"],
            "inputs": ["tests/unit"], "tests": ["unit"],
            "capabilities": ["home", "auth"],
        }
    })

    execute_defined_gate(tmp_path, "demo", "related_tests", scope="home")
    execute_defined_gate(tmp_path, "demo", "related_tests", scope="auth")
    (tmp_path / "src" / "home" / "view.py").write_text("HOME=2\n")

    report = status.get_status(tmp_path, "demo")
    assert report.effective_gates["related_tests@home"] == "stale"
    assert report.effective_gates["related_tests@auth"] == "passed"
