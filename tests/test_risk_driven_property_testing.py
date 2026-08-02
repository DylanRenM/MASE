from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_core_rules_route_property_testing_without_a_global_gate():
    rules = read("project-rules.md")
    framework = read("docs/MASE-framework.md")
    profiles = "\n".join(
        read(f"profiles/{name}.yaml") for name in ("lite", "standard", "strict")
    )

    assert "属性测试" in rules
    assert "复杂输入空间" in rules
    assert "补充而不替代" in framework
    assert "Spec" in framework
    assert "property_testing" not in profiles
    assert "pbt" not in profiles.lower()


def test_contract_template_makes_property_plans_traceable_and_conditional():
    contract = read("templates/contract.md")

    for field in (
        "Property ID",
        "来源 Spec/Scenario",
        "合法域",
        "非法域",
        "显式边界",
        "Oracle",
        "隔离/清理",
        "对应测试",
    ):
        assert field in contract
    for semantic in ("幂等", "Round-trip", "后向兼容", "分页", "时区", "并发"):
        assert semantic in contract
    assert "仅当 Spec" in contract
    assert "错误响应" in contract


def test_tdd_and_agents_preserve_examples_and_replay_counterexamples():
    tdd = read("skills/test-driven-development/SKILL.md")
    development = read("agents/agent-3-development/SKILL.md")
    quality = read("agents/agent-4-quality/SKILL.md")

    assert "property-based-testing.md" in tdd
    assert "deterministic" in tdd.lower()
    assert "replace" in tdd.lower()
    assert "Property ID" in development
    assert "seed" in quality
    assert "counterexample" in quality.lower()


def test_property_testing_reference_is_packaged_and_rejects_blanket_rules():
    reference_path = ROOT / "skills/test-driven-development/references/property-based-testing.md"
    reference = reference_path.read_text(encoding="utf-8")
    manifest = yaml.safe_load(read("framework-manifest.yaml"))
    pyproject = read("pyproject.toml")

    assert "skills" in manifest["runtime"]
    assert '"share/mase/skills/test-driven-development/references"' in pyproject
    assert '"skills/test-driven-development/references/*.md"' in pyproject
    assert "Hypothesis" in reference
    assert "金额" in reference and "Decimal" in reference
    assert "固定幂等键" in reference
    assert "所有 POST" in reference
    assert "替代样例测试" in reference
    dependencies = pyproject.split("dependencies =", 1)[1].split("\n", 1)[0]
    assert "Hypothesis" not in dependencies
