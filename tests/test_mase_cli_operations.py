import json
from pathlib import Path

import pytest
import yaml

from mase_cli.commands import check_project, doctor, install_framework, metrics, status, update_project
from mase_cli import main as cli


def test_doctor_allows_swift_command_line_tools_without_full_xcode(monkeypatch):
    available = {"swift": "/usr/bin/swift", "git": "/usr/bin/git", "xcodebuild": None}
    monkeypatch.setattr(doctor.shutil, "which", lambda name: available.get(name))

    report = doctor.inspect_environment(stack="swift")

    assert report.ok is True
    assert report.build_mode == "swiftpm-command-line-tools"
    assert any(item.name == "xcodebuild" and not item.required for item in report.items)


def test_metrics_distinguishes_real_tokens_from_context_proxy(tmp_path):
    source = tmp_path / "a.md"
    source.write_text("hello world")

    proxy = metrics.collect_metrics(files=[source])
    actual = metrics.collect_metrics(
        files=[source],
        token_usage={"input": 100, "output": 20, "cache": 50},
    )

    assert proxy["kind"] == "context_proxy"
    assert proxy["characters"] == 11
    assert actual["kind"] == "actual_tokens"
    assert actual["tokens"]["input"] == 100


def test_metrics_usage_precedence_and_tool_output_proxy(tmp_path, monkeypatch):
    source = tmp_path / "a.md"
    usage = tmp_path / "usage.json"
    source.write_text("hello", encoding="utf-8")
    usage.write_text(
        json.dumps({"input": 30, "output": 4, "cache": 12}), encoding="utf-8"
    )
    monkeypatch.setenv("MASE_INPUT_TOKENS", "99")
    monkeypatch.setenv("MASE_OUTPUT_TOKENS", "88")
    monkeypatch.setenv("MASE_CACHE_TOKENS", "77")

    from_file = metrics.collect_metrics(files=[source], usage_file=usage)
    explicit = metrics.collect_metrics(
        files=[source],
        token_usage={"input": 1, "output": 2, "cache": 3},
        usage_file=usage,
    )
    proxy = metrics.collect_metrics(
        files=[source], tool_output_characters=123, environ={}
    )

    assert from_file["tokens"] == {"input": 30, "output": 4, "cache": 12}
    assert from_file["source"] == "usage_file"
    assert explicit["tokens"]["input"] == 1
    assert explicit["source"] == "explicit"
    assert proxy["tool_output_characters"] == 123


def test_test_automation_metrics_separate_actual_evidence_and_manual_source(tmp_path):
    manifest = tmp_path / ".mase" / "tests.yaml"
    manifest.parent.mkdir()
    manifest.write_text(yaml.safe_dump({
        "schema": "mase-test-manifest/v1",
        "tests": [
            {
                "id": "auth-login", "tier": "p0_journey", "runner": "playwright",
                "selectors": ["e2e/auth.spec.js"], "capabilities": ["auth"],
                "paths": ["templates/login.html"], "acceptance": "用户登录",
            },
            {
                "id": "settings-errors", "tier": "p1_regression", "runner": "playwright",
                "selectors": ["e2e/settings.spec.js"], "capabilities": ["settings"],
                "paths": ["templates/settings.html"],
            },
        ],
    }, sort_keys=False), encoding="utf-8")
    state = tmp_path / "openspec" / "changes" / "demo" / "mase-state.yaml"
    state.parent.mkdir(parents=True)
    state.write_text(yaml.safe_dump({
        "schema": "mase-project/v2", "profile": "lite", "stack": "generic",
        "phase": "verify", "risk": {"triggers": []}, "gates": {"p0_e2e": "passed"},
        "evidence": [
            {
                "gate": "p0_e2e", "kind": "automatic", "result": "passed",
                "at": "2026-01-01T00:00:00Z", "duration_seconds": 4, "exit_code": 0,
                "command": ["test"], "platform": "test", "commit": None,
                "worktree": "x", "input_digest": "x", "log_path": "log",
                "attempts": 1, "first_attempt_result": "passed",
            },
            {
                "gate": "p0_e2e", "kind": "automatic", "result": "passed",
                "at": "2026-01-02T00:00:00Z", "duration_seconds": 6, "exit_code": 0,
                "command": ["test"], "platform": "test", "commit": None,
                "worktree": "x", "input_digest": "x", "log_path": "log",
                "attempts": 2, "first_attempt_result": "failed",
                "failure_classification": "flaky",
            },
        ],
    }, sort_keys=False), encoding="utf-8")

    report = metrics.collect_test_automation_metrics(
        tmp_path,
        manual_regression_minutes=15,
        manual_regression_source="timesheet:demo",
    )

    assert report["kind"] == "actual_test_evidence"
    assert report["p0"]["runs"] == 2
    assert report["p0"]["first_pass_rate"] == 0.5
    assert report["p0"]["flaky_rate"] == 0.5
    assert report["p0"]["duration_seconds"] == 10
    assert report["capability_journey_coverage"] == {
        "covered": 1, "eligible": 2, "rate": 0.5,
    }
    assert report["manual_regression"] == {
        "kind": "actual", "minutes": 15.0, "source": "timesheet:demo",
    }


def test_status_returns_non_success_for_inconsistent_change(tmp_path):
    change = tmp_path / "openspec" / "changes" / "demo"
    change.mkdir(parents=True)
    (change / "mase-state.yaml").write_text(
        "schema: mase-project/v2\nprofile: lite\nstack: generic\nphase: build\nrisk: {triggers: []}\ngates: {}\nevidence: []\n"
    )
    (change / "tasks.md").write_text("- [x] 1.1 done\n")

    report = status.get_status(tmp_path, "demo")

    assert report.consistent is False


def test_update_plan_marks_modified_generated_rule_as_conflict(tmp_path):
    project = tmp_path / "project"
    framework = tmp_path / "framework"
    project.mkdir()
    framework.mkdir()
    (project / ".mase.yaml").write_text("mase:\n  version: '1.3'\n")
    (framework / "project-rules.md").write_text("# new rules\n")
    (project / "AGENTS.md").write_text(
        "<!-- generated source_hash=stale -->\nlocally modified\n"
    )

    changes = update_project.check_updates(project, framework)

    agents = next(change for change in changes if change["component"] == "AGENTS.md")
    assert agents["action"] == "conflict"


def test_update_dry_run_never_creates_backup_or_modifies_project(tmp_path):
    project = tmp_path / "project"
    framework = tmp_path / "framework"
    project.mkdir()
    framework.mkdir()
    (project / ".mase.yaml").write_text("mase:\n  version: '1.3'\n")
    (framework / "project-rules.md").write_text("# new rules\n")
    original = (project / ".mase.yaml").read_text()

    changes = update_project.check_updates(project, framework)
    update_project.apply_updates(changes, project, dry_run=True, framework_home=framework)

    assert (project / ".mase.yaml").read_text() == original
    assert not (project / ".mase-backup").exists()


def test_update_plan_adds_missing_test_manifest_without_overwriting_existing(tmp_path):
    project = tmp_path / "project"
    framework = tmp_path / "framework"
    project.mkdir()
    (framework / "templates").mkdir(parents=True)
    (project / ".mase.yaml").write_text("mase:\n  version: '1.3'\n")
    (framework / "project-rules.md").write_text("# rules\n")
    (framework / "templates" / "tests.yaml").write_text(
        "schema: mase-test-manifest/v1\ntests: []\n", encoding="utf-8"
    )

    changes = update_project.check_updates(project, framework)

    manifest = next(item for item in changes if item["component"] == ".mase/tests.yaml")
    assert manifest["action"] == "create"
    existing = project / ".mase" / "tests.yaml"
    existing.parent.mkdir()
    existing.write_text("schema: mase-test-manifest/v1\ntests: []\n", encoding="utf-8")
    second = update_project.check_updates(project, framework)
    assert not any(item["component"] == ".mase/tests.yaml" for item in second)


def test_update_plan_adds_impact_template_without_touching_change_artifacts(tmp_path):
    project = tmp_path / "project"
    framework = tmp_path / "framework"
    project.mkdir()
    (framework / "templates").mkdir(parents=True)
    (project / ".mase.yaml").write_text("mase:\n  version: '1.3'\n")
    (framework / "project-rules.md").write_text("# rules\n")
    (framework / "templates" / "impact-analysis.yaml").write_text(
        "schema: mase-impact-analysis/v1\napplicability: required\n", encoding="utf-8"
    )

    changes = update_project.check_updates(project, framework)

    template = next(
        item for item in changes
        if item["component"] == ".mase/impact-analysis.template.yaml"
    )
    assert template["action"] == "create"
    assert not any("openspec/changes" in item["component"] for item in changes)


def test_install_runtime_uses_manifest_boundary_and_excludes_content(tmp_path):
    root = Path(__file__).resolve().parents[1]
    destination = tmp_path / "installed"

    installed = install_framework.install_runtime(root, destination)

    assert "profiles" in installed
    assert "templates" in installed
    assert (destination / "framework-manifest.yaml").exists()
    assert not (destination / "training").exists()
    assert not (destination / "src").exists()
    assert not (destination / "docs" / "superpowers").exists()


def test_install_rejects_manifest_path_traversal(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "framework-manifest.yaml").write_text(
        "schema: mase-framework/v2\nversion: 2.0.0\nruntime: ['../secret']\n"
    )

    with pytest.raises(ValueError, match="Unsafe manifest resource"):
        install_framework.install_runtime(source, tmp_path / "destination")


def test_status_rejects_change_name_path_traversal(tmp_path):
    (tmp_path / "openspec" / "changes").mkdir(parents=True)

    with pytest.raises(ValueError, match="change name"):
        status.get_status(tmp_path, "../outside")


def test_cli_reports_expected_state_errors_without_traceback(tmp_path, capsys):
    (tmp_path / "openspec" / "changes").mkdir(parents=True)

    with pytest.raises(SystemExit) as exit_info:
        cli.main(["status", "--dir", str(tmp_path), "--change", "missing"])

    captured = capsys.readouterr()
    assert exit_info.value.code == cli.EXIT_NOT_FOUND
    assert "error[4]" in captured.err
    assert "Traceback" not in captured.err


def test_gate_cli_rejects_unsafe_change_before_running_command(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(
            [
                "gate",
                "run",
                "related_tests",
                "--dir",
                str(tmp_path),
                "--change",
                "../outside",
                "--",
                "python3",
                "-c",
                "raise RuntimeError('must not run')",
            ]
        )

    assert exit_info.value.code == cli.EXIT_NOT_FOUND
    assert "Traceback" not in capsys.readouterr().err


def test_project_check_explains_unavailable_gate_optimizations(tmp_path):
    (tmp_path / ".mase.yaml").write_text(
        "mase:\n  version: 2.2.0\n  project: demo\n  profile: standard\n  stack: generic\n",
        encoding="utf-8",
    )
    for relative in ("README.md", ".gitignore", "project-rules.md"):
        (tmp_path / relative).write_text("ok", encoding="utf-8")
    (tmp_path / "openspec" / "changes").mkdir(parents=True)

    report = check_project.inspect_project(tmp_path)
    item = next(item for item in report.items if item.path == ".mase/gates.yaml")

    assert item.required is False
    assert "candidate freeze" in item.message
    assert "exact reuse" in item.message

    (tmp_path / ".mase").mkdir()
    (tmp_path / ".mase" / "gates.yaml").write_text(
        "schema: mase-gates/v1\ngates: {}\n", encoding="utf-8"
    )
    empty_report = check_project.inspect_project(tmp_path)
    empty_item = next(
        item for item in empty_report.items if item.path == ".mase/gates.yaml"
    )
    assert "candidate freeze" in empty_item.message
    assert "overlap diagnostics" in empty_item.message
