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
