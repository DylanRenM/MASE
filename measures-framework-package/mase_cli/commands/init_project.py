"""mase init — 初始化新项目"""

import os
from datetime import datetime, timezone


MASE_YAML_TEMPLATE = """\
# MASE 项目标识文件
# MASE (Measures AI Software Engineering) v1.0
mase:
  version: "1.0"
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

    # 4. src/{package}/
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

    # 5. tests/
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

    # 6. docs/
    doc_root = os.path.join(project_dir, "docs")
    _ensure_dirs(doc_root, [])
    _write(os.path.join(doc_root, "user-guide.md"),
           f"# {name} — 使用手册\n\n> 由 MASE Release 阶段自动生成\n")
    for sub in ["lessons", "cases/bugs", "cases/patterns", "cases/pitfalls",
                "superpowers/specs"]:
        _ensure_dirs(os.path.join(doc_root, sub), [])

    # 7. scripts/ + config/
    for d in ["scripts", "config"]:
        _ensure_dirs(os.path.join(project_dir, d), [])

    # 8. openspec/changes/_template/
    tmpl = os.path.join(project_dir, "openspec", "changes", "_template")
    _ensure_dirs(tmpl, [])
    for sub in ["specs/_capability_"]:
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
    _write(os.path.join(tmpl, ".openspec.yaml"),
           "status: proposal\n")

    _write(os.path.join(project_dir, "openspec", "changes", "_template",
                        "specs", "_capability_", "spec.md"),
           "# {capability} — 验收规格\n\n"
           "## Feature: ...\n\n```gherkin\n"
           "Scenario: ...\n  Given ...\n  When ...\n  Then ...\n```\n")

    print()
    print(f"  ✓ 项目 '{name}' 初始化完成")
    print(f"  ✓ Capabilities: {', '.join(capabilities)}")
    print(f"  ✓ 包名: {package}")
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


def _ensure_dirs(base, subs):
    os.makedirs(base, exist_ok=True)
    for s in subs:
        if s.endswith(".py"):
            p = os.path.join(base, s)
            if not os.path.exists(p):
                with open(p, "w") as f:
                    f.write("")


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
