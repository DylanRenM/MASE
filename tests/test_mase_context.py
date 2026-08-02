import json
from pathlib import Path

import yaml

from mase_cli.context import build_context_plan
from mase_cli import main as cli


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    change = root / "openspec" / "changes" / "demo"
    (change / "specs" / "demo").mkdir(parents=True)
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / ".mase" / "evidence" / "demo").mkdir(parents=True)
    (change / "specs" / "demo" / "spec.md").write_text("spec", encoding="utf-8")
    (change / "tasks.md").write_text("- [ ] task", encoding="utf-8")
    (root / "src" / "feature.py").write_text("print('feature')", encoding="utf-8")
    (root / "tests" / "test_feature.py").write_text("def test_feature(): pass", encoding="utf-8")
    (root / ".mase" / "evidence" / "demo" / "full.log").write_text(
        "very large evidence", encoding="utf-8"
    )
    (change / "mase-state.yaml").write_text(
        yaml.safe_dump(
            {
                "schema": "mase-project/v2",
                "profile": "standard",
                "stack": "python",
                "phase": "build",
                "impact": {"ui_changed": False, "paths": ["src/**"]},
                "risk": {"triggers": []},
                "gates": {},
                "evidence": [],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return root


def test_context_plan_includes_relevant_files_and_rejects_evidence(tmp_path):
    root = _project(tmp_path)

    plan = build_context_plan(
        root,
        "demo",
        explicit_reads=["tests/test_feature.py", ".mase/evidence/demo/full.log"],
    )

    included = {item.path: item.reason for item in plan.included}
    excluded = {item.path: item.reason for item in plan.excluded}
    assert "openspec/changes/demo/specs/demo/spec.md" in included
    assert included["src/feature.py"] == "change impact"
    assert included["tests/test_feature.py"] == "explicit read"
    assert ".mase/evidence/demo/full.log" in excluded
    assert ".mase/evidence" in excluded[".mase/evidence/demo/full.log"]
    assert plan.measurement_kind == "context_proxy"


def test_context_plan_override_is_audited_and_budget_overflow_is_reported(tmp_path):
    root = _project(tmp_path)
    manifest = {
        "default_context_excludes": [".mase/evidence"],
        "context_budgets": {
            "standard": {"input_tokens": 16000, "max_files": 2, "max_characters": 8}
        },
    }

    plan = build_context_plan(
        root,
        "demo",
        explicit_reads=[".mase/evidence/demo/full.log"],
        allow_excluded=True,
        manifest=manifest,
    )

    override = next(item for item in plan.included if item.path.endswith("full.log"))
    assert override.override is True
    assert plan.over_budget is True
    assert plan.token_budget == 16000
    assert "characters" in plan.budget_reasons


def test_context_plan_cli_emits_json_without_file_contents(tmp_path, capsys):
    root = _project(tmp_path)

    cli.main([
        "context", "plan", "--dir", str(root), "--change", "demo",
        "--read", "tests/test_feature.py", "--json",
    ])

    payload = json.loads(capsys.readouterr().out)
    assert payload["change"] == "demo"
    assert payload["characters"] > 0
    assert "print('feature')" not in json.dumps(payload)


def test_context_plan_task_scope_uses_declared_reads_only(tmp_path):
    root = _project(tmp_path)
    change = root / "openspec" / "changes" / "demo"
    (root / "src" / "unrelated.py").write_text("unrelated", encoding="utf-8")
    (change / "tasks.md").write_text(
        "- [ ] 1.1 implement feature\n  reads: src/feature.py, tests/test_feature.py\n"
        "- [ ] 1.2 unrelated\n  reads: src/unrelated.py\n",
        encoding="utf-8",
    )

    plan = build_context_plan(root, "demo", task="1.1")

    included = {item.path for item in plan.included}
    assert "src/feature.py" in included
    assert "tests/test_feature.py" in included
    assert "src/unrelated.py" not in included
    assert plan.scope_kind == "task" and plan.scope_name == "1.1"


def test_task_reads_can_include_canonical_hidden_governance_files(tmp_path):
    root = _project(tmp_path)
    change = root / "openspec" / "changes" / "demo"
    (root / ".mase" / "gates.yaml").write_text("schema: mase-gates/v1\n", encoding="utf-8")
    (root / ".mase" / "tests.yaml").write_text("schema: mase-test-manifest/v1\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=do-not-load\n", encoding="utf-8")
    (change / "tasks.md").write_text(
        "- [ ] 1.1 inspect plan\n  reads: .mase/gates.yaml, .mase/tests.yaml, .env\n",
        encoding="utf-8",
    )

    plan = build_context_plan(root, "demo", task="1.1")

    included = {item.path for item in plan.included}
    excluded = {item.path for item in plan.excluded}
    assert {".mase/gates.yaml", ".mase/tests.yaml"} <= included
    assert ".env" in excluded


def test_context_plan_change_scope_does_not_expand_broad_directory(tmp_path):
    root = _project(tmp_path)
    state = root / "openspec" / "changes" / "demo" / "mase-state.yaml"
    payload = yaml.safe_load(state.read_text())
    payload["impact"]["paths"] = ["src"]
    state.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    plan = build_context_plan(root, "demo")

    assert "src/feature.py" not in {item.path for item in plan.included}
    assert any(item.startswith("broad_scope:src:") for item in plan.diagnostics)


def test_context_plan_capability_scope_and_budget_override_reason(tmp_path):
    root = _project(tmp_path)
    state = root / "openspec" / "changes" / "demo" / "mase-state.yaml"
    payload = yaml.safe_load(state.read_text())
    payload["risk"]["capabilities"] = {
        "feature": {"profile": "standard", "paths": ["src/feature.py"]}
    }
    state.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    manifest = {
        "default_context_excludes": [],
        "context_budgets": {"standard": {"input_tokens": 10, "max_files": 1, "max_characters": 1}},
    }

    plan = build_context_plan(
        root, "demo", capability="feature", allow_over_budget=True,
        budget_reason="人工调试单个能力", manifest=manifest,
    )

    assert plan.over_budget is True
    assert plan.budget_override_reason == "人工调试单个能力"


def test_context_plan_excludes_hidden_binary_files(tmp_path):
    root = _project(tmp_path)
    hidden = root / "src" / ".DS_Store"
    hidden.write_bytes(b"\x00binary")

    plan = build_context_plan(root, "demo", explicit_reads=["src"])

    assert "src/.DS_Store" not in {item.path for item in plan.included}
