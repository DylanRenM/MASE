from pathlib import Path

import pytest
import yaml

from mase_cli import main as cli
from mase_cli.evidence import path_digest
from mase_cli.gates import execute_defined_gate, freeze_candidate, plan_change
from mase_cli.impact import (
    assess_impact,
    impact_status,
    load_impact_analysis,
    reconcile_impact,
    render_impact_views,
)
from mase_cli.schema import GovernanceError
from mase_cli.profiles import ProfileRegistry
from mase_cli.risk import derive_gate_plan
from mase_cli.state import ChangeState


def impact_payload(**overrides):
    payload = {
        "schema": "mase-impact-analysis/v1",
        "applicability": "required",
        "comparison": {"baseline": "commit:base", "diff_digest": "diff-1"},
        "adapter": {
            "name": "generic-manifest",
            "version": "1.0",
            "rules_digest": "rules-1",
            "confidence": "high",
        },
        "change_points": [
            {
                "id": "cp-1",
                "path": "src/core.py",
                "symbol": "calculate",
                "change_type": "internal_implementation",
                "core_path": False,
                "call_frequency": "low",
                "semantics_preserved": True,
                "side_effects_preserved": True,
            }
        ],
        "callers": [
            {
                "id": "caller-1",
                "path": "src/service.py",
                "symbol": "serve",
                "depth": 1,
                "first_party": True,
            }
        ],
        "implicit_channels": [
            {"kind": "serialization", "status": "checked_empty", "risk": "controlled"}
        ],
        "boundaries": [],
        "terminations": [
            {"branch": "caller-1", "reason": "direct_caller", "depth": 1}
        ],
        "classification": {"level": "L1", "reasons": ["internal non-core change"]},
        "decision": {"status": "proceed", "strategy": "direct-change"},
        "verification": {
            "test_types": ["unit", "contract_differential"],
            "tests": ["tests/test_service.py"],
            "fixture_sources": ["historical-test"],
            "expected_differences": [],
            "side_effect_isolation": "in-memory fixture",
        },
        "recovery": {"strategy": "revert commit", "data_compatibility": "no data change"},
        "reconciliation": {
            "status": "matched",
            "actual_diff_digest": "diff-1",
            "actual_paths": ["src/core.py"],
            "unplanned_paths": [],
        },
    }
    payload.update(overrides)
    return payload


def write_change(root: Path, payload=None, *, reconciliation="matched"):
    change = root / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    artifact_payload = payload or impact_payload()
    artifact_payload["reconciliation"]["status"] = reconciliation
    (root / "src").mkdir()
    (root / "src" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    current_diff_digest = path_digest(
        root, artifact_payload["reconciliation"]["actual_paths"]
    )
    artifact_payload["comparison"]["diff_digest"] = current_diff_digest
    artifact_payload["reconciliation"]["actual_diff_digest"] = current_diff_digest
    artifact = change / "impact-analysis.yaml"
    artifact.write_text(yaml.safe_dump(artifact_payload, sort_keys=False), encoding="utf-8")
    from mase_cli.impact import file_digest

    summary = {
        "applicability": "required",
        "level": artifact_payload["classification"]["level"],
        "decision": artifact_payload["decision"]["status"],
        "artifact": "impact-analysis.yaml",
        "artifact_digest": file_digest(artifact),
        "baseline_digest": "commit:base",
        "diff_digest": artifact_payload["comparison"]["diff_digest"],
        "reconciliation": reconciliation,
    }
    state = {
        "schema": "mase-project/v2",
        "profile": "lite",
        "stack": "generic",
        "phase": "verify",
        "product": {"has_ui": False},
        "impact": {"ui_changed": False, "paths": ["src/core.py"]},
        "impact_analysis": summary,
        "risk": {"triggers": [], "capabilities": {}},
        "gates": {
            "impact_analysis": "pending",
            "impact_reconcile": "pending",
            "contract_differential": "pending",
            "related_tests": "pending",
            "api_contract": "pending",
            "full_regression": "pending",
        },
        "evidence": [],
        "dependencies": [],
        "blockers": [],
    }
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(state, sort_keys=False), encoding="utf-8"
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n", encoding="utf-8")
    (change / "specs").mkdir()
    (change / "specs" / "spec.md").write_text("spec\n", encoding="utf-8")
    return change


def write_gates(root: Path):
    target = root / ".mase" / "gates.yaml"
    target.parent.mkdir(parents=True)
    target.write_text(
        yaml.safe_dump(
            {
                "schema": "mase-gates/v1",
                "gates": {
                    "impact_analysis": {
                        "stage": "analysis",
                        "command": ["python3", "-c", "print('analysis')"],
                        "inputs": ["openspec/changes/demo/impact-analysis.yaml"],
                    },
                    "impact_reconcile": {
                        "stage": "capability",
                        "command": ["python3", "-c", "print('reconcile')"],
                        "inputs": ["openspec/changes/demo/impact-analysis.yaml", "src"],
                    },
                    "contract_differential": {
                        "stage": "micro",
                        "command": ["python3", "-c", "print('contract')"],
                        "inputs": ["src"],
                    },
                    "related_tests": {
                        "stage": "micro",
                        "command": ["python3", "-c", "print('related')"],
                        "inputs": ["src"],
                    },
                    "api_contract": {
                        "stage": "capability",
                        "command": ["python3", "-c", "print('api')"],
                        "inputs": ["src"],
                    },
                    "full_regression": {
                        "stage": "final",
                        "candidate_bound": True,
                        "command": ["python3", "-c", "print('full')"],
                        "inputs": ["src"],
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_schema_and_policy_accept_l1_and_reject_adapter_downgrade(tmp_path):
    artifact = tmp_path / "impact-analysis.yaml"
    artifact.write_text(yaml.safe_dump(impact_payload(), sort_keys=False), encoding="utf-8")

    loaded = load_impact_analysis(artifact)
    assessment = assess_impact(loaded)

    assert assessment.level == "L1"
    assert assessment.required_gates == (
        "contract_differential",
        "impact_analysis",
        "impact_reconcile",
        "related_tests",
    )

    downgraded = impact_payload()
    downgraded["change_points"][0]["call_frequency"] = "unknown"
    artifact.write_text(yaml.safe_dump(downgraded, sort_keys=False), encoding="utf-8")
    with pytest.raises(GovernanceError, match="cannot be lower than computed L2"):
        load_impact_analysis(artifact)


def test_policy_upgrades_hidden_uncertainty_and_contract_boundaries():
    hidden = impact_payload()
    hidden["implicit_channels"] = [
        {"kind": "reflection", "status": "unverified", "risk": "controlled"}
    ]
    hidden["classification"]["level"] = "L2"
    assert assess_impact(hidden).level == "L2"
    assert "impact_review" in assess_impact(hidden).required_gates

    contract = impact_payload()
    contract["change_points"][0]["change_type"] = "external_contract"
    contract["boundaries"] = [
        {"id": "api", "kind": "rest", "path": "src/api.py", "depth": 2}
    ]
    contract["classification"]["level"] = "L3"
    assessment = assess_impact(contract)
    assert assessment.level == "L3"
    assert "architecture_review" in assessment.required_gates
    assert "full_chain_smoke" in assessment.required_gates


def test_excessive_callers_require_human_architecture_decision():
    payload = impact_payload()
    payload["callers"] = [
        {
            "id": f"caller-{index}",
            "path": f"src/caller_{index}.py",
            "symbol": "call",
            "depth": 1,
            "first_party": True,
        }
        for index in range(11)
    ]
    payload["classification"]["level"] = "L3"
    payload["decision"] = {
        "status": "architecture-review-required",
        "strategy": "pending",
    }

    assessment = assess_impact(payload)

    assert assessment.caller_count == 11
    assert assessment.architecture_review_required is True
    assert "caller_threshold_exceeded" in assessment.diagnostics


def test_state_derives_impact_gates_without_fourth_profile(tmp_path):
    change = write_change(tmp_path)

    state = ChangeState.load(change / "mase-state.yaml")

    assert state.profile == "lite"
    assert state.impact_analysis["level"] == "L1"
    assert "impact_analysis" in state.gate_plan.required_gates
    assert "contract_differential" in state.gate_plan.required_gates


def test_capability_impact_is_scoped_without_creating_a_profile():
    root = Path(__file__).resolve().parents[1]
    plan = derive_gate_plan(
        ProfileRegistry(root / "profiles"),
        "lite",
        [],
        impact_analysis={
            "applicability": "required",
            "level": "L1",
            "decision": "proceed",
            "capabilities": {
                "public_api": {
                    "level": "L3",
                    "paths": ["src/api/**"],
                    "decision": "proceed",
                }
            },
        },
    )

    assert plan.profile == "lite"
    assert plan.capability_plans["public_api"].profile == "lite"
    assert "architecture_review" in plan.capability_plans["public_api"].required_gates
    assert "full_chain_smoke" in plan.required_gates


def test_analysis_stage_defers_later_gates_until_fresh(tmp_path):
    write_change(tmp_path)
    write_gates(tmp_path)

    report = plan_change(tmp_path, "demo")

    assert report.instances["impact_analysis"].stage == "analysis"
    assert report.instances["impact_analysis"].status == "runnable"
    assert report.instances["related_tests"].status == "deferred"
    assert "impact_analysis" in report.instances["related_tests"].reason
    with pytest.raises(GovernanceError, match="analysis gates are not fresh"):
        execute_defined_gate(tmp_path, "demo", "related_tests")


def test_gate_runner_materializes_change_placeholder(tmp_path):
    write_change(tmp_path)
    target = tmp_path / ".mase" / "gates.yaml"
    target.parent.mkdir(parents=True)
    target.write_text(
        yaml.safe_dump(
            {
                "schema": "mase-gates/v1",
                "gates": {
                    "impact_analysis": {
                        "stage": "analysis",
                        "command": ["python3", "-c", "print('ok')", "{change}"],
                        "inputs": ["openspec/changes"],
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    record = execute_defined_gate(tmp_path, "demo", "impact_analysis").record

    assert record.command[-1] == "demo"


def test_expanded_reconciliation_blocks_candidate_freeze(tmp_path):
    write_change(tmp_path, reconciliation="expanded")
    write_gates(tmp_path)

    with pytest.raises(GovernanceError, match="impact reconciliation is expanded"):
        freeze_candidate(tmp_path, "demo")


def test_impact_artifact_is_bound_to_gate_evidence_and_candidate(tmp_path):
    change = write_change(tmp_path)
    write_gates(tmp_path)
    for gate in (
        "impact_analysis",
        "impact_reconcile",
        "contract_differential",
        "related_tests",
        "api_contract",
    ):
        execute_defined_gate(tmp_path, "demo", gate)

    state = ChangeState.load(change / "mase-state.yaml")
    analysis = next(item for item in state.evidence if item.gate == "impact_analysis")
    artifact_input = "openspec/changes/demo/impact-analysis.yaml"
    assert artifact_input in analysis.inputs

    candidate = freeze_candidate(tmp_path, "demo")
    assert artifact_input in candidate.inputs


def test_reconcile_updates_scope_and_render_generates_three_bound_views(tmp_path):
    change = write_change(tmp_path)
    actual_paths = ["src/core.py", "src/unplanned.py"]

    result = reconcile_impact(
        change,
        actual_paths=actual_paths,
        actual_diff_digest=path_digest(tmp_path, actual_paths),
    )
    assert result.reconciliation == "expanded"
    state = ChangeState.load(change / "mase-state.yaml")
    assert state.impact_analysis["reconciliation"] == "expanded"

    views = render_impact_views(change)
    assert {item.name for item in views} == {
        "impact-scope.md",
        "test-scope.md",
        "rollback.md",
    }
    digests = {
        next(line for line in item.read_text(encoding="utf-8").splitlines() if "Source digest" in line)
        for item in views
    }
    assert len(digests) == 1


def test_matched_reconciliation_becomes_stale_when_bound_source_changes(tmp_path):
    change = write_change(tmp_path)

    assert impact_status(change).consistent is True
    (tmp_path / "src" / "core.py").write_text("VALUE = 2\n", encoding="utf-8")

    report = impact_status(change)

    assert report.consistent is False
    assert any("actual diff digest is stale" in issue for issue in report.issues)


def test_reconciliation_expands_for_symbol_outside_change_envelope(tmp_path):
    payload = impact_payload(
        approved_paths=["src/core.py"],
        approved_symbols=["src/core.py:calculate"],
    )
    change = write_change(tmp_path, payload=payload)
    actual_paths = ["src/core.py"]

    report = reconcile_impact(
        change,
        actual_paths=actual_paths,
        actual_diff_digest=path_digest(tmp_path, actual_paths),
        actual_symbols=["src/core.py:calculate", "src/core.py:rewrite_cache"],
    )

    assert report.reconciliation == "expanded"
    artifact = yaml.safe_load((change / "impact-analysis.yaml").read_text(encoding="utf-8"))
    assert artifact["reconciliation"]["unplanned_symbols"] == [
        "src/core.py:rewrite_cache"
    ]


def test_negative_assurance_rejects_unplanned_call_edges(tmp_path):
    payload = impact_payload()
    payload["call_graph"] = {
        "status": "verified",
        "baseline_edges": [],
        "planned_changes": [],
        "actual_changes": [
            {
                "operation": "add",
                "caller": "src/core.py:calculate",
                "callee": "src/audit.py:flush",
                "via": "direct",
            }
        ],
        "unplanned_changes": [
            {
                "operation": "add",
                "caller": "src/core.py:calculate",
                "callee": "src/audit.py:flush",
                "via": "direct",
            }
        ],
    }
    artifact = tmp_path / "impact-analysis.yaml"
    artifact.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(GovernanceError, match="unplanned call-graph edge"):
        load_impact_analysis(artifact)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        (
            "protected_tests",
            {
                "baseline": "commit:base",
                "selectors": ["tests/test_service.py"],
                "manifest_digest": "sha256:baseline-tests",
                "changes": [
                    {
                        "selector": "tests/test_service.py",
                        "action": "weakened",
                        "rationale": "make generated implementation pass",
                    }
                ],
            },
            "protected test change requires approval",
        ),
        (
            "effect_budget",
            {
                "status": "verified",
                "allowed": {
                    "file_reads": ["config/tax.yaml"],
                    "file_writes": [],
                    "persistence_writes": [],
                    "external_calls": [],
                    "messages": [],
                },
                "forbidden": ["audit configuration"],
                "observed_extra": ["file_write:/var/log/audit.log"],
            },
            "observed effects exceed declared budget",
        ),
        (
            "change_declaration",
            {
                "spec_changes": ["increase tax precision"],
                "incidental_changes": ["changed audit flush behavior"],
                "non_spec_changes": [],
            },
            "incidental or non-Spec changes require human disposition",
        ),
    ],
)
def test_negative_assurance_rejects_unapproved_reductions(
    tmp_path, field, value, message
):
    payload = impact_payload(**{field: value})
    artifact = tmp_path / "impact-analysis.yaml"
    artifact.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    with pytest.raises(GovernanceError, match=message):
        load_impact_analysis(artifact)


def test_impact_cli_reports_status_and_rejects_unsafe_change(tmp_path, capsys):
    write_change(tmp_path)

    assert cli.main(["impact", "status", "--dir", str(tmp_path), "--change", "demo", "--json"]) == 0
    assert '"level": "L1"' in capsys.readouterr().out

    with pytest.raises(SystemExit) as exit_info:
        cli.main(
            ["impact", "status", "--dir", str(tmp_path), "--change", "../outside"]
        )
    assert exit_info.value.code == cli.EXIT_NOT_FOUND


def test_cli_classification_resolves_new_change_and_machine_log_is_not_exempt(
    tmp_path, capsys
):
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    state = {
        "schema": "mase-project/v2",
        "profile": "lite",
        "stack": "generic",
        "phase": "proposal",
        "impact_analysis": {"applicability": "undecided", "reconciliation": "pending"},
        "risk": {"triggers": []},
        "gates": {"impact_classification": "pending"},
        "evidence": [],
    }
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(state, sort_keys=False), encoding="utf-8"
    )

    assert cli.main(
        [
            "impact", "classify", "formatting", "--change", "demo",
            "--dir", str(tmp_path), "--json",
        ]
    ) == 0
    assert '"applicability": "exempt"' in capsys.readouterr().out
    loaded = ChangeState.load(change / "mase-state.yaml")
    assert loaded.impact_analysis["exemption"]["kind"] == "formatting"
    assert "impact_analysis" not in loaded.gate_plan.required_gates

    required = cli.main(
        ["impact", "classify", "log-wording", "--machine-consumed", "--json"]
    )
    assert required == 0
    assert '"applicability": "required"' in capsys.readouterr().out
