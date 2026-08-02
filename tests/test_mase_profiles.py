from pathlib import Path
import json
import re

import mase_cli
import yaml
from mase_cli.profiles import ProfileRegistry, resolve_capability_profile
from mase_cli.risk import derive_gate_plan


ROOT = Path(__file__).resolve().parents[1]


def test_registry_loads_three_profiles_with_increasing_rigor():
    registry = ProfileRegistry(ROOT / "profiles")

    assert registry.names == ("lite", "standard", "strict")
    assert registry.get("lite").rank < registry.get("standard").rank
    assert registry.get("standard").rank < registry.get("strict").rank
    assert "p0_e2e" in registry.get("lite").hard_gates
    assert "api_contract" in registry.get("lite").hard_gates
    assert "independent_review" in registry.get("strict").hard_gates


def test_untrusted_file_input_escalates_only_the_capability():
    registry = ProfileRegistry(ROOT / "profiles")

    selected = resolve_capability_profile(
        registry=registry,
        base_profile="lite",
        risk_triggers=["untrusted_input", "archive_parsing"],
    )

    assert selected.name == "standard"
    assert "security_review" in derive_gate_plan(
        registry, "lite", ["untrusted_input", "archive_parsing"]
    ).required_gates
    assert registry.get("lite").name == "lite"


def test_strict_profile_cannot_be_downgraded_by_empty_risk_list():
    registry = ProfileRegistry(ROOT / "profiles")

    selected = resolve_capability_profile(registry, "strict", [])

    assert selected.name == "strict"


def test_lite_uses_boundary_test_schedule_not_per_scenario_full_suite():
    registry = ProfileRegistry(ROOT / "profiles")
    lite = registry.get("lite")

    assert lite.test_schedule["micro"] == ["related_unit", "related_contract"]
    assert "full_e2e" not in lite.test_schedule["micro"]
    assert "p0_journey" in lite.test_schedule["final"]
    assert "related_ui_contract" in lite.test_schedule["capability"]


def test_standard_security_review_is_risk_triggered():
    registry = ProfileRegistry(ROOT / "profiles")
    standard = registry.get("standard")

    ordinary = derive_gate_plan(registry, "standard", [])
    untrusted = derive_gate_plan(registry, "standard", ["untrusted_input"])

    assert "security_review" not in standard.hard_gates
    assert "security_review" not in standard.capability_gates
    assert "security_review" not in ordinary.required_gates
    assert "security_review" in untrusted.required_gates
    assert registry.get("strict").review == "independent-single-pass-on-objection"


def test_standard_compiles_related_integration_and_final_gates():
    plan = derive_gate_plan(ProfileRegistry(ROOT / "profiles"), "standard", [])

    assert {"api_contract", "related_tests", "integration_tests", "full_regression", "code_review"}.issubset(
        plan.required_gates
    )
    assert plan.required_artifacts == ("change", "design", "specs", "api_contract", "tasks")
    assert plan.test_schedule["final"]


def test_change_risk_is_independent_and_hard_dimensions_raise_floor():
    registry = ProfileRegistry(ROOT / "profiles")
    presentation = derive_gate_plan(
        registry,
        "standard",
        [],
        product={"has_ui": True},
        impact={"ui_changed": True, "ui_change_kind": "presentation"},
        change_risk={
            "level": "L1",
            "dimensions": {"reversible": True, "stable_regression": True},
        },
    )
    assert presentation.change_risk_level == "L1"
    assert "p0_e2e" not in presentation.required_gates
    assert "ui_contract" in presentation.required_gates
    assert "code_review" not in presentation.required_gates

    authentication = derive_gate_plan(
        registry,
        "lite",
        [],
        change_risk={
            "level": "L1",
            "dimensions": {"authentication": True, "reversible": True},
        },
    )
    assert authentication.change_risk_level == "L4"
    assert "security_review" in authentication.required_gates
    assert "independent_review" in authentication.required_gates
    assert any("authentication" in item for item in authentication.change_risk_reasons)


def test_ui_change_kind_only_routes_key_interaction_or_journey_to_p0():
    registry = ProfileRegistry(ROOT / "profiles")
    interaction = derive_gate_plan(
        registry, "lite", [], product={"has_ui": True},
        impact={"ui_change_kind": "interaction", "critical_journey": False},
        change_risk={"level": "L2", "dimensions": {}},
    )
    journey = derive_gate_plan(
        registry, "lite", [], product={"has_ui": True},
        impact={"ui_change_kind": "journey"},
        change_risk={"level": "L2", "dimensions": {}},
    )
    legacy = derive_gate_plan(
        registry, "lite", [], product={"has_ui": True},
        impact={"ui_changed": True},
    )

    assert "ui_contract" in interaction.required_gates
    assert "p0_e2e" not in interaction.required_gates
    assert "p0_e2e" in journey.required_gates
    assert "p0_e2e" in legacy.required_gates


def test_project_without_public_contract_omits_only_inapplicable_contract_gate():
    plan = derive_gate_plan(
        ProfileRegistry(ROOT / "profiles"), "lite", [],
        product={"has_ui": False, "has_public_contract": False},
    )

    assert "api_contract" not in plan.required_gates
    assert "api_contract" not in plan.required_artifacts
    assert "related_tests" in plan.required_gates
    assert "full_regression" in plan.required_gates


def test_contract_risk_overrides_incorrect_non_applicable_declaration():
    plan = derive_gate_plan(
        ProfileRegistry(ROOT / "profiles"), "lite", ["public_contract_change"],
        product={"has_ui": False, "has_public_contract": False},
    )

    assert "api_contract" in plan.required_gates


def test_capability_risk_uses_registry_minimum_and_reports_unknown():
    plan = derive_gate_plan(
        ProfileRegistry(ROOT / "profiles"),
        "lite",
        [],
        capabilities={
            "infra": {"profile": "lite", "triggers": ["infrastructure_change"], "paths": ["infra/**"]},
            "typo": {"profile": "lite", "triggers": ["authenticaton"], "paths": ["src/**"]},
        },
    )

    assert plan.profile == "strict"
    assert plan.capability_plans["infra"].profile == "strict"
    assert "authenticaton" in plan.unknown_triggers


def test_release_surfaces_share_version_and_mit_license():
    manifest = yaml.safe_load((ROOT / "framework-manifest.yaml").read_text())
    pyproject = (ROOT / "pyproject.toml").read_text()
    package = json.loads((ROOT / "package.json").read_text())
    project_version = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE).group(1)

    assert mase_cli.__version__ == project_version == manifest["version"] == package["version"]
    assert manifest["license"] == package["license"] == "MIT"
    assert 'license = { text = "MIT" }' in pyproject
