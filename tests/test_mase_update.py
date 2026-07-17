"""mase update 命令 — 单元测试（TDD）

运行: python -m pytest tests/test_mase_update.py -v
"""

import os
import sys
import tempfile
import shutil
import pytest
from pathlib import Path

# 确保可以导入 mase_cli
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================================================================
# Fixtures
# ================================================================

@pytest.fixture
def temp_project():
    """创建一个模拟的 MASE 项目临时目录，结构类似 mase init 产物。"""
    tmp = tempfile.mkdtemp(prefix="mase_update_test_")
    old_cwd = os.getcwd()
    os.chdir(tmp)

    # 创建最小的 MASE 项目骨架
    _write(".mase.yaml", "mase:\n  version: \"1.1\"\n  created: \"2026-01-01T00:00:00Z\"\n  project: test-project\n")
    _write("pyproject.toml", "[project]\nname = \"test-project\"\n")
    _write(".gitignore", "__pycache__/\n*.pyc\n.env\n")
    _write("Makefile", ".PHONY: test\n")
    _write("README.md", "# test-project\n")
    _write(".env.example", "# env\n")
    _write("project-rules.md", "# MASE v1.1 Rules\n\nR01: old rule\n")

    for d in ["src", "tests", "tests/e2e", "docs", "scripts", "config", "openspec", ".trae/rules"]:
        os.makedirs(d, exist_ok=True)

    _write("tests/e2e/conftest.py", '"""original conftest"""\nimport pytest\n')

    yield tmp

    os.chdir(old_cwd)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def framework_home(tmp_path):
    """创建一个模拟的 ~/.measures-framework 目录。"""
    fw = tmp_path / "measures-framework"
    templates = fw / "templates"
    templates.mkdir(parents=True)

    # 模拟 project-rules.md v1.3
    (fw / "project-rules.md").write_text(
        "# MASE 九大工程原则 — v1.3\n\n"
        "R01: 需求澄清确认\n"
        "R02: 设计预研\n"
        "R04: TDD 驱动（含 E2E 外循环）\n"
        "R05: 验证与确认检查（E2E 自动化回归 + 人工探索 + 合规）\n"
    )

    # 模拟 sandbox.config.json 模板
    (templates / "sandbox.config.json").write_text(
        '{"snapshot": {"directories": ["data/uploads/"], "files": [".env"], "env_vars": ["APP_ENV"]}}\n'
    )

    # 模拟 E2E conftest 模板
    e2e_dir = templates / "tests" / "e2e"
    e2e_dir.mkdir(parents=True)
    (e2e_dir / "conftest.py").write_text(
        '"""E2E test config — v2.0"""\n'
        'import pytest\n'
        'from playwright.sync_api import Page\n'
    )

    # 模拟 sandbox.js helper
    helpers_dir = templates / "tests" / "e2e" / "helpers"
    helpers_dir.mkdir(parents=True)
    (helpers_dir / "sandbox.js").write_text('// Sandbox helper v1.0\n')

    return str(fw)


# ================================================================
# Helpers
# ================================================================

def _write(path, content):
    """写文件，自动创建父目录。"""
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _read(path):
    with open(path, "r") as f:
        return f.read()


# ================================================================
# Tests: update_project 模块函数
# ================================================================

class TestCheckUpdates:
    """测试 check_updates() — 检测需要更新的组件。"""

    def test_detect_mase_yaml_version_mismatch(self, temp_project, framework_home, monkeypatch):
        monkeypatch.setenv("MASE_FRAMEWORK_HOME", framework_home)
        from mase_cli.commands import update_project

        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)

        # .mase.yaml 版本 1.1 → 应检测到需要升级
        version_changes = [c for c in changes if c["component"] == ".mase.yaml"]
        assert len(version_changes) == 1
        assert version_changes[0]["action"] == "update"

    def test_detect_project_rules_outdated(self, temp_project, framework_home, monkeypatch):
        from mase_cli.commands import update_project

        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)

        rules_changes = [c for c in changes if c["component"] == "project-rules.md"]
        assert len(rules_changes) >= 1  # 可能多个 IDE 目录
        assert all(c["action"] == "update" for c in rules_changes)

    def test_detect_missing_sandbox_config(self, temp_project, framework_home, monkeypatch):
        from mase_cli.commands import update_project

        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)

        sandbox_changes = [c for c in changes if c["component"] == "sandbox.config.json"]
        assert len(sandbox_changes) == 1
        assert sandbox_changes[0]["action"] == "create"

    def test_detect_missing_sandbox_helper(self, temp_project, framework_home, monkeypatch):
        from mase_cli.commands import update_project

        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)

        helper_changes = [c for c in changes if c["component"] == "tests/e2e/helpers/sandbox.js"]
        assert len(helper_changes) == 1
        assert helper_changes[0]["action"] == "create"

    def test_detect_gitignore_missing_entries(self, temp_project, framework_home, monkeypatch):
        from mase_cli.commands import update_project

        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)

        gitignore_changes = [c for c in changes if c["component"] == ".gitignore"]
        # .gitignore 缺少 e2e/sandbox/ 条目
        assert len(gitignore_changes) == 1
        assert gitignore_changes[0]["action"] == "update"

    def test_no_changes_when_already_updated(self, temp_project, framework_home, monkeypatch):
        """已更新到最新版本的项目不应有任何变更。"""
        from mase_cli.commands import update_project

        # 先执行一次更新
        all_changes = update_project.check_updates(project_dir=temp_project,
                                                    framework_home=framework_home)
        update_project.apply_updates(all_changes, project_dir=temp_project,
                                      dry_run=False, framework_home=framework_home)

        # 再次检查 — 应该无变更
        changes = update_project.check_updates(project_dir=temp_project,
                                                framework_home=framework_home)
        assert len(changes) == 0

    def test_not_a_mase_project(self, tmp_path, framework_home):
        """非 MASE 项目目录应报错。"""
        from mase_cli.commands import update_project

        with pytest.raises(SystemExit):
            update_project.check_updates(project_dir=str(tmp_path),
                                          framework_home=framework_home)


class TestApplyUpdates:
    """测试 apply_updates() — 执行实际更新。"""

    def test_update_mase_yaml_version(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == ".mase.yaml"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        content = _read(os.path.join(temp_project, ".mase.yaml"))
        assert 'version: "1.3"' in content

    def test_create_sandbox_config(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == "sandbox.config.json"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        assert os.path.exists(os.path.join(temp_project, "sandbox.config.json"))
        content = _read(os.path.join(temp_project, "sandbox.config.json"))
        assert "snapshot" in content

    def test_create_sandbox_helper(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == "tests/e2e/helpers/sandbox.js"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        helper_path = os.path.join(temp_project, "tests/e2e/helpers/sandbox.js")
        assert os.path.exists(helper_path)

    def test_update_gitignore_append_only(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        # 记录原始内容
        original = _read(os.path.join(temp_project, ".gitignore"))

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == ".gitignore"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        updated = _read(os.path.join(temp_project, ".gitignore"))
        # 原始内容应保留
        assert original.strip() in updated
        # 新内容应追加
        assert "e2e/sandbox/" in updated

    def test_update_project_rules(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == "project-rules.md"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        content = _read(os.path.join(temp_project, "project-rules.md"))
        assert "v1.3" in content

    def test_dry_run_does_not_modify(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        all_changes = update_project.check_updates(project_dir=temp_project,
                                                    framework_home=framework_home)

        # 记录更新前的状态
        mase_yaml_before = _read(os.path.join(temp_project, ".mase.yaml"))
        rules_before = _read(os.path.join(temp_project, "project-rules.md"))
        sandbox_config_exists_before = os.path.exists(
            os.path.join(temp_project, "sandbox.config.json"))

        update_project.apply_updates(all_changes, project_dir=temp_project, dry_run=True, framework_home=framework_home)

        # dry-run 不应修改任何文件
        assert _read(os.path.join(temp_project, ".mase.yaml")) == mase_yaml_before
        assert _read(os.path.join(temp_project, "project-rules.md")) == rules_before
        assert os.path.exists(os.path.join(temp_project, "sandbox.config.json")) == sandbox_config_exists_before

    def test_backup_created_before_update(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        all_changes = update_project.check_updates(project_dir=temp_project,
                                                    framework_home=framework_home)

        update_project.apply_updates(all_changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        # 备份目录应存在
        backup_dir = os.path.join(temp_project, ".mase-backup")
        assert os.path.isdir(backup_dir)

    def test_sandbox_dirs_created(self, temp_project, framework_home):
        from mase_cli.commands import update_project

        changes = [c for c in update_project.check_updates(
            project_dir=temp_project, framework_home=framework_home
        ) if c["component"] == "tests/e2e/sandbox/"]

        update_project.apply_updates(changes, project_dir=temp_project, dry_run=False, framework_home=framework_home)

        sandbox_dir = os.path.join(temp_project, "tests/e2e/sandbox")
        assert os.path.isdir(sandbox_dir)
        for sub in ["uploads", "exports", "logs", "snapshots", "backups"]:
            assert os.path.isdir(os.path.join(sandbox_dir, sub))
