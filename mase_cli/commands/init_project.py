"""mase init — 初始化新项目"""

import os
from datetime import datetime, timezone


FRAMEWORK_HOME = os.path.expanduser("~/.measures-framework")

MASE_YAML_TEMPLATE = """\
# MASE 项目标识文件
# MASE (Measures AI Software Engineering) v1.1
mase:
  version: "1.1"
  created: "{created}"
  project: "{name}"
"""

GITIGNORE = """\
__pycache__/
*.pyc
*.pyo
.venv/
venv/
.env
dist/
*.egg-info/
.idea/
.vscode/
*.DS_Store
"""

MAKEFILE = """\
.PHONY: test lint clean install

install:
\tpip install -e ".[dev]"

test:
\tpytest tests/ -v --tb=short

lint:
\truffle check src/ tests/

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
\tfind . -type f -name "*.pyc" -delete
\trm -rf .pytest_cache dist *.egg-info
"""

OPENSPEC_YAML = """\
# MASE OpenSpec 配置
schema: "mase-project/v1"

# 项目类型声明
project_type:
  has_ui: false
  ui_platform: null

# 当前开发阶段: proposal | design | build | verify | retro | release
phase: init

# Capability 列表（由 mase init 自动填充）
capabilities:
{capabilities}
"""

PROJECT_RULES_HEADER = """\
# MASE 九大工程原则 — 项目副本

> 本文件为 MASE 框架九大工程原则的项目级副本，供 AI IDE 自动加载。
> 源文件: ~/.measures-framework/project-rules.md
> 更新时间: {updated}

---
"""


def run(args):
    name = args.name
    package = args.package
    capabilities = args.capabilities
    base_dir = os.path.abspath(args.dir)
    project_dir = os.path.join(base_dir, name)

    # 1. Create project root
    os.makedirs(project_dir, exist_ok=True)
    print(f"  ✓ 创建项目目录: {project_dir}")

    # 2. .mase.yaml
    mase_yaml = MASE_YAML_TEMPLATE.format(
        created=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        name=name,
    )
    _write(os.path.join(project_dir, ".mase.yaml"), mase_yaml)

    # 3. pyproject.toml
    _write(os.path.join(project_dir, "pyproject.toml"),
           _pyproject_toml(name, package))
    _write(os.path.join(project_dir, ".gitignore"), GITIGNORE)
    _write(os.path.join(project_dir, "Makefile"), MAKEFILE)
    _write(os.path.join(project_dir, ".env.example"), "# 环境变量模板\n")
    _write(os.path.join(project_dir, "README.md"), f"# {name}\n\n> MASE 项目\n")

    # 4. Deploy project-rules.md to project root (for AI IDE auto-loading)
    _deploy_project_rules(project_dir)

    # 5. src/{package}/
    pkg_root = os.path.join(project_dir, "src", package)
    _ensure_dirs(pkg_root, ["__init__.py"])

    for cap in capabilities:
        _ensure_dirs(pkg_root, [cap])
        _ensure_dirs(os.path.join(pkg_root, cap), ["__init__.py"])
        for sub in ["models", "services", "routes", "schemas"]:
            _ensure_dirs(os.path.join(pkg_root, cap, sub), ["__init__.py"])

    # shared/
    shared = os.path.join(pkg_root, "shared")
    _ensure_dirs(shared, ["__init__.py"])
    for sub in ["config", "database", "utils"]:
        _ensure_dirs(os.path.join(shared, sub), ["__init__.py"])
    _write(os.path.join(shared, "config", "settings.py"),
           '"""全局配置"""\n')

    # 6. tests/
    tests_root = os.path.join(project_dir, "tests")
    _ensure_dirs(tests_root, ["__init__.py"])
    _write(os.path.join(tests_root, "conftest.py"),
           '"""pytest 共享 fixtures"""\n')

    for cap in capabilities:
        _ensure_dirs(os.path.join(tests_root, "unit", cap), ["__init__.py"])
        for sub in ["models", "services", "routes"]:
            _ensure_dirs(os.path.join(tests_root, "unit", cap, sub),
                         ["__init__.py"])

        _ensure_dirs(os.path.join(tests_root, "fixtures", cap), [])
        for sub in ["models", "services"]:
            _ensure_dirs(os.path.join(tests_root, "fixtures", cap, sub), [])

    # shared tests
    _ensure_dirs(os.path.join(tests_root, "unit", "shared"), ["__init__.py"])
    for sub in ["config", "database", "utils"]:
        _ensure_dirs(os.path.join(tests_root, "unit", "shared", sub),
                     ["__init__.py"])

    _ensure_dirs(os.path.join(tests_root, "integration"), ["__init__.py"])
    _ensure_dirs(os.path.join(tests_root, "e2e"), ["__init__.py"])

    # 7. docs/
    doc_root = os.path.join(project_dir, "docs")
    _ensure_dirs(doc_root, [])
    _write(os.path.join(doc_root, "user-guide.md"),
           f"# {name} — 使用手册\n\n> 由 MASE Release 阶段自动生成\n")
    for sub in ["lessons", "cases/bugs", "cases/patterns", "cases/pitfalls",
                "superpowers/specs"]:
        _ensure_dirs(os.path.join(doc_root, sub), [])

    # 7b. Deploy docs template files (lessons + cases templates)
    _deploy_docs_templates(project_dir)

    # 8. scripts/ + config/
    for d in ["scripts", "config"]:
        _ensure_dirs(os.path.join(project_dir, d), [])

    # 9. openspec/changes/_template/
    tmpl = os.path.join(project_dir, "openspec", "changes", "_template")
    _ensure_dirs(tmpl, [])
    for sub in ["specs/_capability_", "docs/lessons", "docs/cases/bugs",
                "docs/cases/patterns", "docs/cases/pitfalls", "e2e"]:
        _ensure_dirs(os.path.join(tmpl, sub), [])
    _write(os.path.join(tmpl, "proposal.md"),
           _openspec_tmpl("proposal"))
    _write(os.path.join(tmpl, "architecture.md"),
           _openspec_tmpl("architecture"))
    _write(os.path.join(tmpl, "detailed-design.md"),
           _openspec_tmpl("detailed-design"))
    _write(os.path.join(tmpl, "tech-feasibility.md"),
           _openspec_tmpl("tech-feasibility"))
    _write(os.path.join(tmpl, "tasks.md"),
           _openspec_tmpl("tasks"))
    _write(os.path.join(tmpl, "contract.md"),
           _openspec_tmpl("contract"))
    _write(os.path.join(tmpl, "mase-state.yaml"),
           OPENSPEC_YAML.format(
               capabilities="\n".join(f"  - {c}" for c in capabilities)))

    _write(os.path.join(project_dir, "openspec", "changes", "_template",
                        "specs", "_capability_", "spec.md"),
           "# {capability} — 验收规格\n\n"
           "## Feature: ...\n\n```gherkin\n"
           "Scenario: ...\n  Given ...\n  When ...\n  Then ...\n```\n")

    # 10. E2E test template
    _write_e2e_template(project_dir, tmpl)

    print()
    print(f"  ✓ 项目 '{name}' 初始化完成")
    print(f"  ✓ Capabilities: {', '.join(capabilities)}")
    print(f"  ✓ 包名: {package}")
    print(f"  ✓ project-rules.md 已部署到 7 款 AI 工具规则目录")
    print()
    print(f"  下一步:")
    print(f"    cd {name}")
    print(f"    pip install -e .        # 安装开发依赖")
    print(f"    mase check              # 合规检查")
    print(f"    对 AI 说: '创建新项目 {name}' → MASE 六阶段流程启动")


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def _read_file(path):
    """Read file content."""
    with open(path, "r") as f:
        return f.read()


def _ensure_dirs(base, subs):
    os.makedirs(base, exist_ok=True)
    for s in subs:
        if s.endswith(".py"):
            p = os.path.join(base, s)
            if not os.path.exists(p):
                with open(p, "w") as f:
                    f.write("")


def _deploy_project_rules(project_dir):
    """Deploy project-rules.md from framework home to project root and IDE rules dirs."""
    src = os.path.join(FRAMEWORK_HOME, "project-rules.md")

    if not os.path.exists(src):
        print(f"  ⚠ {src} 未找到，跳过 project-rules.md 部署")
        print(f"    请先运行: cd measures-framework-package && ./install.sh")
        return

    header = PROJECT_RULES_HEADER.format(
        updated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    with open(src, "r") as f:
        content = header + "\n" + f.read()

    # 1. 项目根目录（通用兜底）
    _write(os.path.join(project_dir, "project-rules.md"), content)
    print(f"  ✓ project-rules.md → 项目根目录")

    # 2. IDE 特定规则目录（确保 AI IDE 自动加载）
    _deploy_to_ide_rules(project_dir, content)


def _deploy_to_ide_rules(project_dir, content):
    """Deploy project-rules.md to IDE-specific rules directories.

    Supports 7 popular AI coding tools:
      - Trae IDE        → .trae/rules/project-rules.md
      - Cursor IDE      → .cursor/rules/project-rules.mdc
      - Windsurf IDE    → .windsurf/rules/project-rules.md
      - Claude Code     → CLAUDE.md (项目根目录)
      - OpenAI Codex    → AGENTS.md (项目根目录)
      - Aider           → CONVENTIONS.md (项目根目录)
      - GitHub Copilot  → .github/copilot-instructions.md
    """

    # IDE 子目录规则（需要创建子目录）
    subdir_rules = {
        ".trae/rules": "project-rules.md",
        ".cursor/rules": "project-rules.mdc",
        ".windsurf/rules": "project-rules.md",
    }

    for rel_dir, filename in subdir_rules.items():
        rules_dir = os.path.join(project_dir, rel_dir)
        rules_file = os.path.join(rules_dir, filename)
        try:
            os.makedirs(rules_dir, exist_ok=True)
            with open(rules_file, "w") as f:
                f.write(content)
            print(f"  ✓ project-rules.md → {rel_dir}/{filename}")
        except OSError:
            pass

    # 项目根目录规则文件（无需子目录）
    root_files = {
        "CLAUDE.md": "Claude Code",
        "AGENTS.md": "OpenAI Codex",
        "CONVENTIONS.md": "Aider",
    }

    for filename, tool_name in root_files.items():
        rules_file = os.path.join(project_dir, filename)
        try:
            with open(rules_file, "w") as f:
                f.write(content)
            print(f"  ✓ project-rules.md → {filename} ({tool_name})")
        except OSError:
            pass

    # GitHub Copilot（需要 .github 子目录）
    copilot_dir = os.path.join(project_dir, ".github")
    copilot_file = os.path.join(copilot_dir, "copilot-instructions.md")
    try:
        os.makedirs(copilot_dir, exist_ok=True)
        with open(copilot_file, "w") as f:
            f.write(content)
        print(f"  ✓ project-rules.md → .github/copilot-instructions.md (GitHub Copilot)")
    except OSError:
        pass


def _write_e2e_template(project_dir, tmpl_dir):
    """Write E2E test template (Playwright)."""
    e2e_conftest = '''"""E2E 测试共享配置 — Playwright + pytest"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="session")
def browser_context(browser):
    """创建浏览器上下文。"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="zh-CN",
    )
    yield context
    context.close()


@pytest.fixture
def page(browser_context):
    """每个测试独立页面。"""
    page = browser_context.new_page()
    yield page
    page.close()
'''

    e2e_example = '''"""E2E 测试示例 — {capability} 模块 P0 场景"""
import re
from playwright.sync_api import Page, expect


def test_homepage_loads(page: Page):
    """P0: 首页正确加载。"""
    page.goto("http://localhost:5173")
    expect(page).to_have_title(re.compile(".+"))
    expect(page.locator("body")).to_be_visible()


def test_core_flow(page: Page):
    """P0: 核心业务流程端到端验证。"""
    page.goto("http://localhost:5173")
    # TODO: 替换为实际的核心操作流程
    # 1. 定位关键元素
    # 2. 执行用户操作
    # 3. 断言预期结果
    pass
'''

    # Write to template dir
    e2e_dir = os.path.join(tmpl_dir, "e2e")
    _write(os.path.join(e2e_dir, "conftest.py"), e2e_conftest)
    _write(os.path.join(e2e_dir, "test_p0_example.py"), e2e_example)

    # Write to project tests/e2e/
    proj_e2e_dir = os.path.join(project_dir, "tests", "e2e")
    _write(os.path.join(proj_e2e_dir, "conftest.py"), e2e_conftest)
    _write(os.path.join(proj_e2e_dir, "test_p0_example.py"), e2e_example)
    print(f"  ✓ E2E 测试模板 → tests/e2e/")


def _pyproject_toml(name, package):
    return f"""\
[project]
name = "{name}"
version = "0.1.0"
description = "MASE Project — {name}"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.9",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
"""


def _openspec_tmpl(name):
    return f"# {name}\n\n> MASE 阶段产出 — 待 Agent 填写\n"


def _deploy_docs_templates(project_dir):
    """Copy docs template files (lessons, cases) from framework."""
    src_base = os.path.join(FRAMEWORK_HOME, "templates", "docs")
    dst_base = os.path.join(project_dir, "docs")

    templates = [
        ("cases/bugs/_TEMPLATE.md", "cases/bugs/_TEMPLATE.md"),
        ("cases/patterns/_TEMPLATE.md", "cases/patterns/_TEMPLATE.md"),
        ("cases/pitfalls/_TEMPLATE.md", "cases/pitfalls/_TEMPLATE.md"),
        ("lessons/_TEMPLATE.md", "lessons/_TEMPLATE.md"),
        ("lessons/_RETRO_TEMPLATE.md", "lessons/_RETRO_TEMPLATE.md"),
    ]

    copied = 0
    for src_rel, dst_rel in templates:
        src = os.path.join(src_base, src_rel)
        dst = os.path.join(dst_base, dst_rel)
        if os.path.exists(src):
            _write(dst, _read_file(src))
            copied += 1

    if copied > 0:
        print(f"  ✓ docs 模板文件 → docs/ ({copied} files)")

