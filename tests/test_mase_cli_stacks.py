from argparse import Namespace
from pathlib import Path

import pytest
import yaml

from mase_cli.commands import check_project, init_project


def init_args(tmp_path, name, stack, profile, package=None):
    return Namespace(
        name=name,
        capabilities=["core"],
        package=package,
        stack=stack,
        profile=profile,
        dir=str(tmp_path),
    )


def test_init_swift_lite_does_not_emit_python_skeleton(tmp_path):
    project = init_project.run(init_args(tmp_path, "swift-demo", "swift", "lite"))

    assert project == tmp_path / "swift-demo"
    assert (project / "Package.swift").exists()
    assert (project / "Sources" / "SwiftDemo").is_dir()
    assert not (project / "pyproject.toml").exists()
    assert not (project / "src" / "swift_demo" / "core" / "models").exists()


def test_init_generic_lite_creates_only_common_mase_files(tmp_path):
    project = init_project.run(init_args(tmp_path, "generic-demo", "generic", "lite"))

    assert (project / ".mase.yaml").exists()
    assert (project / "openspec" / "changes").is_dir()
    assert not (project / "pyproject.toml").exists()
    assert not (project / "Package.swift").exists()


def test_legacy_python_arguments_remain_compatible(tmp_path):
    project = init_project.run(init_args(tmp_path, "python-demo", "python", "standard", "demo_pkg"))

    assert (project / "pyproject.toml").exists()
    assert (project / "src" / "demo_pkg" / "core").is_dir()


def test_stack_aware_check_does_not_require_python_files_for_swift(tmp_path):
    project = init_project.run(init_args(tmp_path, "swift-check", "swift", "lite"))

    report = check_project.inspect_project(project)

    assert report.ok is True
    checked = {item.path for item in report.items}
    assert "Package.swift" in checked
    assert "pyproject.toml" not in checked


def test_check_supports_json_serialization(tmp_path):
    project = init_project.run(init_args(tmp_path, "generic-check", "generic", "lite"))

    payload = check_project.inspect_project(project).to_dict()

    assert payload["ok"] is True
    assert payload["stack"] == "generic"
    assert payload["profile"] == "lite"


def test_generic_check_does_not_assume_product_source_directories(tmp_path):
    project = init_project.run(init_args(tmp_path, "framework-check", "generic", "standard"))
    for directory in (project / "src", project / "tests"):
        if directory.exists():
            directory.rmdir()

    report = check_project.inspect_project(project)

    assert report.ok is True
    checked = {item.path for item in report.items}
    assert "src" not in checked
    assert "tests" not in checked


def test_init_rejects_project_name_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="project name"):
        init_project.run(init_args(tmp_path, "../outside", "generic", "lite"))

    assert not (tmp_path.parent / "outside").exists()


def test_swift_check_accepts_manifest_declared_custom_layout(tmp_path):
    project = init_project.run(init_args(tmp_path, "swift-layout", "swift", "standard"))
    metadata = yaml.safe_load((project / ".mase.yaml").read_text())
    metadata["mase"]["layout"] = {"product": "src", "tests": "tests"}
    (project / ".mase.yaml").write_text(yaml.safe_dump(metadata, sort_keys=False))
    (project / "src").mkdir()
    (project / "tests").mkdir(exist_ok=True)

    report = check_project.inspect_project(project)

    assert report.ok is True
    checked = {item.path for item in report.items}
    assert "src" in checked
    assert "tests" in checked
    assert "Sources" not in checked
