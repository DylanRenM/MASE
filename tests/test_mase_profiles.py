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
    assert "p0_e2e" in lite.test_schedule["final"]


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


def test_release_surfaces_share_version_and_mit_license():
    manifest = yaml.safe_load((ROOT / "framework-manifest.yaml").read_text())
    pyproject = (ROOT / "pyproject.toml").read_text()
    package = json.loads((ROOT / "package.json").read_text())
    project_version = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE).group(1)

    assert mase_cli.__version__ == project_version == manifest["version"] == package["version"]
    assert manifest["license"] == package["license"] == "MIT"
    assert 'license = { text = "MIT" }' in pyproject
