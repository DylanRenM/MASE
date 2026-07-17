"""mase update — 同步框架更新到已有项目

支持:
  - 更新 project-rules.md 到所有 IDE 目录
  - 新增框架模板文件（sandbox.config.json, sandbox.js 等）
  - 升级 .mase.yaml 版本号
  - 增量更新 .gitignore
  - 创建新目录结构
  - dry-run 模式预览变更
  - --check 模式仅检测需更新的组件
"""

import os
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path

# 框架版本号（与 pyproject.toml 保持同步）
FRAMEWORK_VERSION = "1.3"

# 默认框架安装目录
DEFAULT_FRAMEWORK_HOME = os.path.expanduser("~/.measures-framework")

# 需要强制覆盖的框架文件（用户不应修改）
FORCE_OVERWRITE_FILES = [
    "project-rules.md",
]

# IDE 特定规则目录映射
IDE_RULES_DIRS = {
    ".trae/rules": "project-rules.md",
    ".cursor/rules": "project-rules.mdc",
    ".windsurf/rules": "project-rules.md",
}

IDE_ROOT_FILES = {
    "CLAUDE.md": "Claude Code",
    "AGENTS.md": "OpenAI Codex",
    "CONVENTIONS.md": "Aider",
}

# .gitignore 需要确保存在的条目
REQUIRED_GITIGNORE_ENTRIES = [
    "e2e/sandbox/",
    ".mase-backup/",
]

# E2E sandbox 子目录
SANDBOX_SUBDIRS = ["uploads", "exports", "logs", "snapshots", "backups"]


# ================================================================
# 检测可更新组件
# ================================================================

def check_updates(project_dir=".", framework_home=None):
    """检测项目中需要更新的组件。

    Returns:
        list[dict]: 每个 dict 包含 component, action, reason 字段。
    """
    if framework_home is None:
        framework_home = os.environ.get("MASE_FRAMEWORK_HOME", DEFAULT_FRAMEWORK_HOME)

    project_dir = os.path.abspath(project_dir)

    # 验证是否为 MASE 项目
    mase_yaml_path = os.path.join(project_dir, ".mase.yaml")
    if not os.path.exists(mase_yaml_path):
        print("错误: 当前目录不是 MASE 项目（未找到 .mase.yaml）")
        print("提示: 请 cd 到 MASE 项目根目录后重试")
        sys.exit(1)

    changes = []

    # 1. .mase.yaml 版本升级
    _check_mase_yaml_version(project_dir, changes)

    # 2. project-rules.md（项目根 + IDE 目录）
    _check_project_rules(project_dir, framework_home, changes)

    # 3. sandbox.config.json
    _check_file_from_template(project_dir, framework_home,
                               "sandbox.config.json", changes)

    # 4. E2E sandbox helper
    _check_file_from_template(project_dir, framework_home,
                               "tests/e2e/helpers/sandbox.js", changes)

    # 5. E2E sandbox 目录
    _check_sandbox_dirs(project_dir, changes)

    # 6. .gitignore
    _check_gitignore(project_dir, changes)

    # 7. E2E conftest 模板升级
    _check_e2e_conftest(project_dir, framework_home, changes)

    return changes


def _check_mase_yaml_version(project_dir, changes):
    """检查 .mase.yaml 版本是否需要升级。"""
    mase_yaml_path = os.path.join(project_dir, ".mase.yaml")
    with open(mase_yaml_path, "r") as f:
        content = f.read()

    import re
    match = re.search(r'version:\s*"([^"]+)"', content)
    current_version = match.group(1) if match else "0.0"

    if current_version != FRAMEWORK_VERSION:
        changes.append({
            "component": ".mase.yaml",
            "action": "update",
            "reason": f"版本升级: {current_version} → {FRAMEWORK_VERSION}",
            "current_version": current_version,
            "target_version": FRAMEWORK_VERSION,
        })


def _check_project_rules(project_dir, framework_home, changes):
    """检查 project-rules.md 是否需要更新。"""
    src_rules = os.path.join(framework_home, "project-rules.md")
    if not os.path.exists(src_rules):
        return

    # 项目根目录
    dst_rules = os.path.join(project_dir, "project-rules.md")
    if _should_update_file(dst_rules, src_rules):
        changes.append({
            "component": "project-rules.md",
            "action": "update",
            "reason": "框架规则已升级",
            "target": "project-rules.md"
        })

    # IDE 子目录
    for rel_dir, filename in IDE_RULES_DIRS.items():
        rules_file = os.path.join(project_dir, rel_dir, filename)
        if os.path.exists(rules_file) and _should_update_file(rules_file, src_rules):
            changes.append({
                "component": "project-rules.md",
                "action": "update",
                "reason": "框架规则已升级",
                "target": f"{rel_dir}/{filename}"
            })

    # IDE 根目录文件
    for filename, _tool_name in IDE_ROOT_FILES.items():
        rules_file = os.path.join(project_dir, filename)
        if os.path.exists(rules_file) and _should_update_file(rules_file, src_rules):
            changes.append({
                "component": "project-rules.md",
                "action": "update",
                "reason": "框架规则已升级",
                "target": filename
            })


def _check_file_from_template(project_dir, framework_home, rel_path, changes):
    """检查模板文件是否需要新增或更新。"""
    src = os.path.join(framework_home, "templates", rel_path)
    dst = os.path.join(project_dir, rel_path)

    if not os.path.exists(src):
        return

    if not os.path.exists(dst):
        changes.append({
            "component": rel_path,
            "action": "create",
            "reason": "新增框架文件",
        })
    elif _should_update_file(dst, src):
        changes.append({
            "component": rel_path,
            "action": "update",
            "reason": "框架文件已更新",
        })


def _check_sandbox_dirs(project_dir, changes):
    """检查 E2E sandbox 子目录是否存在。"""
    sandbox_root = os.path.join(project_dir, "tests", "e2e", "sandbox")
    missing = []
    for sub in SANDBOX_SUBDIRS:
        if not os.path.isdir(os.path.join(sandbox_root, sub)):
            missing.append(sub)

    if missing:
        changes.append({
            "component": "tests/e2e/sandbox/",
            "action": "create",
            "reason": f"创建 sandbox 子目录: {', '.join(missing)}",
            "missing_dirs": missing,
        })


def _check_gitignore(project_dir, changes):
    """检查 .gitignore 是否包含必需的 sandbox 条目。"""
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        return

    with open(gitignore_path, "r") as f:
        content = f.read()

    missing_entries = []
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in content:
            missing_entries.append(entry)

    if missing_entries:
        changes.append({
            "component": ".gitignore",
            "action": "update",
            "reason": f"追加缺失条目: {', '.join(missing_entries)}",
            "missing_entries": missing_entries,
        })


def _check_e2e_conftest(project_dir, framework_home, changes):
    """检查 E2E conftest.py 是否需要从模板更新。"""
    src = os.path.join(framework_home, "templates", "tests", "e2e", "conftest.py")
    dst = os.path.join(project_dir, "tests", "e2e", "conftest.py")

    if not os.path.exists(src):
        return

    # conftest.py 存在但可能是模板版本 → 可安全覆盖
    if os.path.exists(dst) and _should_update_file(dst, src):
        changes.append({
            "component": "tests/e2e/conftest.py",
            "action": "update",
            "reason": "E2E 测试模板已升级",
        })


def _should_update_file(dst, src):
    """判断目标文件是否应该被源文件更新。

    使用内容哈希比较，不相同则需要更新。
    """
    if not os.path.exists(dst):
        return True
    if not os.path.exists(src):
        return False

    # 比较文件内容
    with open(dst, "r") as f:
        dst_content = f.read()
    with open(src, "r") as f:
        src_content = f.read()

    return dst_content.strip() != src_content.strip()


# ================================================================
# 应用更新
# ================================================================

def apply_updates(changes, project_dir=".", dry_run=False, framework_home=None):
    """应用检测到的变更。

    Args:
        changes: check_updates() 返回的变更列表
        project_dir: 项目根目录
        dry_run: True 时仅打印不修改
        framework_home: 框架安装目录
    """
    if framework_home is None:
        framework_home = os.environ.get("MASE_FRAMEWORK_HOME", DEFAULT_FRAMEWORK_HOME)

    project_dir = os.path.abspath(project_dir)

    if not changes:
        print("✓ 项目已是最新版本，无需更新。")
        return

    mode = "[DRY-RUN] " if dry_run else ""
    print(f"\n{mode}开始更新 MASE 项目...\n")

    # 创建备份目录（非 dry-run 时）
    backup_dir = None
    if not dry_run:
        backup_dir = os.path.join(project_dir, ".mase-backup",
                                   datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_dir, exist_ok=True)

    for change in changes:
        component = change["component"]
        action = change["action"]

        if dry_run:
            print(f"  [{action.upper()}] {component}")
            if "reason" in change:
                print(f"           {change['reason']}")
            continue

        if component == ".mase.yaml":
            _apply_mase_yaml_update(project_dir, change, backup_dir)
        elif component == "project-rules.md":
            _apply_project_rules_update(project_dir, change, backup_dir, framework_home)
        elif component == ".gitignore":
            _apply_gitignore_update(project_dir, change, backup_dir)
        elif component == "tests/e2e/sandbox/":
            _apply_sandbox_dirs_create(project_dir, change)
        elif component.startswith("tests/e2e/"):
            _apply_template_file_update(project_dir, component, change, backup_dir, framework_home)
        elif component == "sandbox.config.json":
            _apply_template_file_update(project_dir, component, change, backup_dir, framework_home)
        else:
            _apply_template_file_update(project_dir, component, change, backup_dir, framework_home)

        print(f"  ✓ [{action}] {component}")

    if not dry_run:
        print(f"\n✓ 更新完成。备份保存在 .mase-backup/")
    else:
        print(f"\n[dry-run] 以上变更不会实际执行。去掉 --dry-run 以应用更新。")


def _backup_file(filepath, backup_dir):
    """备份文件到备份目录。"""
    if not os.path.exists(filepath):
        return
    rel = os.path.relpath(filepath, os.path.dirname(backup_dir))
    dst = os.path.join(backup_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(filepath, dst)


def _apply_mase_yaml_update(project_dir, change, backup_dir):
    """更新 .mase.yaml 版本号。"""
    path = os.path.join(project_dir, ".mase.yaml")
    _backup_file(path, backup_dir)

    with open(path, "r") as f:
        content = f.read()

    import re
    content = re.sub(
        r'version:\s*"[^"]*"',
        f'version: "{change["target_version"]}"',
        content
    )

    with open(path, "w") as f:
        f.write(content)


def _apply_project_rules_update(project_dir, change, backup_dir, framework_home):
    """更新 project-rules.md 到目标位置。"""
    src = os.path.join(framework_home, "project-rules.md")

    if not os.path.exists(src):
        return

    target = change["target"]
    dst = os.path.join(project_dir, target)

    _backup_file(dst, backup_dir)

    with open(src, "r") as f:
        body = f.read()

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w") as f:
        f.write(body)


def _apply_gitignore_update(project_dir, change, backup_dir):
    """向 .gitignore 追加缺失条目。"""
    path = os.path.join(project_dir, ".gitignore")
    _backup_file(path, backup_dir)

    with open(path, "r") as f:
        content = f.read()

    # 确保末尾有换行
    if content and not content.endswith("\n"):
        content += "\n"

    # 追加缺失条目
    for entry in change.get("missing_entries", []):
        if entry not in content:
            content += f"{entry}\n"

    with open(path, "w") as f:
        f.write(content)


def _apply_sandbox_dirs_create(project_dir, change):
    """创建 E2E sandbox 子目录。"""
    sandbox_root = os.path.join(project_dir, "tests", "e2e", "sandbox")
    for sub in change.get("missing_dirs", SANDBOX_SUBDIRS):
        d = os.path.join(sandbox_root, sub)
        os.makedirs(d, exist_ok=True)


def _apply_template_file_update(project_dir, rel_path, change, backup_dir, framework_home):
    """从框架模板目录复制文件。"""
    src = os.path.join(framework_home, "templates", rel_path)
    dst = os.path.join(project_dir, rel_path)

    if not os.path.exists(src):
        print(f"  ⚠ 模板文件不存在: {src}")
        return

    _backup_file(dst, backup_dir)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


# ================================================================
# CLI 入口
# ================================================================

def run(args):
    """mase update 命令入口。"""
    project_dir = os.path.abspath(args.dir) if hasattr(args, 'dir') and args.dir else "."
    framework_home = os.environ.get("MASE_FRAMEWORK_HOME", DEFAULT_FRAMEWORK_HOME)

    # --check 模式：仅检测
    if getattr(args, 'check_only', False):
        print("MASE 项目更新检查\n")
        print(f"  框架版本: v{FRAMEWORK_VERSION}")
        print(f"  框架路径: {framework_home}")
        print(f"  项目路径: {os.path.abspath(project_dir)}\n")

        changes = check_updates(project_dir, framework_home)
        if not changes:
            print("✓ 项目已是最新版本，无需更新。")
        else:
            print(f"发现 {len(changes)} 项可更新:\n")
            for c in changes:
                print(f"  [{c['action'].upper()}] {c['component']}")
                print(f"           {c['reason']}")
        return

    # 正常更新模式
    dry_run = getattr(args, 'dry_run', False)
    changes = check_updates(project_dir, framework_home)
    apply_updates(changes, project_dir, dry_run=dry_run)
