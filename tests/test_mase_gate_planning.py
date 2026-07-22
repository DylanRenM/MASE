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
    assert report.lifecycle == "ready_to_complete"


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

    report = plan_change(tmp_path, "demo")

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

    report = plan_change(tmp_path, "demo")

    assert any(item.code == "high_test_overlap" for item in report.diagnostics)
    assert report.instances["related_tests"].status == "runnable"
    assert report.instances["integration_tests"].status == "runnable"


def test_plan_defers_final_until_required_non_final_gate_is_fresh(tmp_path):
    _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('api')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
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


def test_freeze_is_stable_then_stale_after_candidate_input_change(tmp_path):
    change = _write_change(tmp_path)
    _write_gates(tmp_path, {
        "api_contract": {
            "stage": "capability", "command": ["python3", "-c", "print('ok')"],
            "inputs": ["src/feature.py"], "tests": ["contract"],
        },
        "full_regression": {
            "stage": "final", "candidate_bound": True,
            "command": ["python3", "-m", "pytest"],
            "inputs": ["src", "tests"], "tests": ["tests"],
        },
    })
    _pass_api(tmp_path, change)

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
    for gate in ("api_contract", "p0_e2e", "security_review", "independent_review"):
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
            "inputs": ["src/feature.py", "tests"], "tests": ["unit"],
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
    assert status.get_status(tmp_path, "demo").effective_gates["integration_tests"] == "passed"


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
    assert "pass-3" in " ".join(records[-2]["command"])
    assert "pass-4" in " ".join(records[-1]["command"])


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
        }
    })
    _pass_api(tmp_path, change)

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
