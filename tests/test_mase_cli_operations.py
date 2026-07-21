from pathlib import Path

import pytest

from mase_cli.commands import doctor, install_framework, metrics, status, update_project
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
