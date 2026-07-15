"""mase check — 合规检查当前项目"""

import os
import sys
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CheckResult:
    category: str
    items: list = field(default_factory=list)
    passed: int = 0
    failed: int = 0


def run():
    results: List[CheckResult] = []
    status_ok = True

    # ── 0. .mase.yaml ──
    r = CheckResult("MASE 标识 (.mase.yaml)")
    if os.path.exists(".mase.yaml"):
        r.passed += 1
        r.items.append("✓ .mase.yaml 存在")
    else:
        r.failed += 1
        r.items.append("✗ .mase.yaml 缺失 — 当前目录不是 MASE 项目")
        status_ok = False
    results.append(r)

    # ── 1. 根目录骨架 ──
    r = CheckResult("根目录")
    for f in ["pyproject.toml", ".gitignore", "Makefile", "README.md",
              ".env.example"]:
        if os.path.exists(f):
            r.passed += 1
            r.items.append(f"✓ {f}")
        else:
            r.failed += 1
            r.items.append(f"✗ {f} 缺失")
            status_ok = False
    for d in ["src", "tests", "docs", "scripts", "config", "openspec"]:
        if os.path.isdir(d):
            r.passed += 1
            r.items.append(f"✓ {d}/")
        else:
            r.failed += 1
            r.items.append(f"✗ {d}/ 目录缺失")
            status_ok = False
    # Check project-rules.md (any IDE location — 7 tools supported)
    found_rules = (
        os.path.exists("project-rules.md")
        or os.path.exists(".trae/rules/project-rules.md")
        or os.path.exists(".cursor/rules/project-rules.mdc")
        or os.path.exists(".windsurf/rules/project-rules.md")
        or os.path.exists("CLAUDE.md")
        or os.path.exists("AGENTS.md")
        or os.path.exists("CONVENTIONS.md")
        or os.path.exists(".github/copilot-instructions.md")
    )
    if found_rules:
        r.passed += 1
        r.items.append("✓ project-rules.md (AI IDE 可自动加载)")
    else:
        r.failed += 1
        r.items.append("✗ project-rules.md 缺失 — AI IDE 无法加载工程规则")
        status_ok = False
    results.append(r)

    # ── 2. src/ ──
    r = CheckResult("src/ 产品代码")
    if os.path.isdir("src"):
        pkgs = [d for d in os.listdir("src")
                if os.path.isdir(os.path.join("src", d))
                and not d.startswith("_") and not d.startswith(".")]
        if pkgs:
            for pkg in pkgs:
                pkg_path = os.path.join("src", pkg)
                caps = [d for d in os.listdir(pkg_path)
                        if os.path.isdir(os.path.join(pkg_path, d))
                        and d not in ("shared", "__pycache__")
                        and not d.startswith(".")]
                r.items.append(f"  ── {pkg}/ (包)")
                for cap in caps:
                    sub_ok = all(
                        os.path.isdir(os.path.join(pkg_path, cap, s))
                        for s in ["models", "services"])
                    r.items.append(
                        f"    {'✓' if sub_ok else '✗'} {cap}/")
                    if sub_ok:
                        r.passed += 1
                    else:
                        r.failed += 1
                        status_ok = False
                # check shared/
                shared = os.path.join(pkg_path, "shared")
                if os.path.isdir(shared):
                    for s in ["config", "database", "utils"]:
                        if os.path.isdir(os.path.join(shared, s)):
                            r.passed += 1
                            r.items.append(f"    ✓ shared/{s}/")
                        else:
                            r.failed += 1
                            r.items.append(f"    ✗ shared/{s}/ 缺失")
                            status_ok = False
        else:
            r.failed += 1
            r.items.append("✗ src/ 下未找到 Python 包")
            status_ok = False
    else:
        r.failed += 1
        r.items.append("✗ src/ 目录缺失")
        status_ok = False
    results.append(r)

    # ── 3. tests/ ──
    r = CheckResult("tests/ 测试代码")
    if os.path.isdir("tests"):
        for f in ["__init__.py", "conftest.py"]:
            tp = os.path.join("tests", f)
            if os.path.exists(tp):
                r.passed += 1
                r.items.append(f"✓ {f}")
            else:
                r.failed += 1
                r.items.append(f"✗ {f} 缺失")
                status_ok = False
        for d in ["unit", "integration", "fixtures"]:
            dp = os.path.join("tests", d)
            if os.path.isdir(dp):
                r.passed += 1
                r.items.append(f"✓ {d}/")
            else:
                r.failed += 1
                r.items.append(f"✗ {d}/ 缺失")
                status_ok = False
        # Check e2e/ directory
        if os.path.isdir(os.path.join("tests", "e2e")):
            r.passed += 1
            r.items.append("✓ e2e/")
        else:
            r.failed += 1
            r.items.append("✗ e2e/ 缺失（如有 UI 请创建）")
            status_ok = False
    else:
        r.failed += 1
        r.items.append("✗ tests/ 目录缺失")
        status_ok = False
    results.append(r)

    # ── 4. docs/ ──
    r = CheckResult("docs/ 文档")
    if os.path.isdir("docs"):
        for d in ["lessons", "cases/bugs", "cases/patterns",
                  "cases/pitfalls", "superpowers/specs"]:
            dp = os.path.join("docs", d)
            if os.path.isdir(dp):
                r.passed += 1
                r.items.append(f"✓ {d}/")
            else:
                r.failed += 1
                r.items.append(f"✗ {d}/ 缺失")
                status_ok = False
    else:
        r.failed += 1
        r.items.append("✗ docs/ 目录缺失")
        status_ok = False
    results.append(r)

    # ── 5. openspec/ ──
    r = CheckResult("openspec/ 规范文档")
    if os.path.isdir("openspec/changes/_template"):
        for f in ["proposal.md", "architecture.md", "detailed-design.md",
                  "tech-feasibility.md", "tasks.md", "contract.md",
                  "mase-state.yaml"]:
            fp = os.path.join("openspec", "changes", "_template", f)
            if os.path.exists(fp):
                r.passed += 1
                r.items.append(f"✓ {f}")
            else:
                r.failed += 1
                r.items.append(f"✗ {f} 缺失")
                status_ok = False
        if os.path.isdir("openspec/changes/_template/specs/_capability_"):
            r.passed += 1
            r.items.append("✓ specs/_capability_/")
        else:
            r.failed += 1
            r.items.append("✗ specs/_capability_/ 缺失")
            status_ok = False

        # ── Content check: mase-state.yaml ──
        openspec_path = os.path.join("openspec", "changes", "_template",
                                      "mase-state.yaml")
        content_results = _check_openspec_content(openspec_path)
        for item in content_results:
            if item.startswith("✓"):
                r.passed += 1
            else:
                r.failed += 1
                status_ok = False
            r.items.append(item)
    else:
        r.failed += 1
        r.items.append("✗ openspec/changes/_template/ 缺失")
        status_ok = False
    results.append(r)

    # ── 6. Phase tracking ──
    r = CheckResult("阶段状态 (phase)")
    phase_info = _read_phase()
    if phase_info:
        r.passed += 1
        r.items.append(f"✓ 当前阶段: {phase_info['phase']}")
        r.items.append(f"  has_ui: {phase_info.get('has_ui', 'N/A')}")
        r.items.append(f"  ui_platform: {phase_info.get('ui_platform', 'N/A')}")
        r.items.append(f"  capabilities: {', '.join(phase_info.get('capabilities', []))}")
        r.items.append("")
        r.items.append(f"  下一步: {_next_step(phase_info['phase'])}")
    else:
        r.failed += 1
        r.items.append("✗ 无法读取阶段状态")
        status_ok = False
    results.append(r)

    # ── Print report ──
    print()
    print("  MASE 合规检查 —", "✓ 通过" if status_ok else "✗ 不通过")
    print()
    total_passed = 0
    total_failed = 0
    for r in results:
        print(f"  [{r.category}]  {r.passed}✓  {r.failed}✗")
        for item in r.items:
            print(f"    {item}")
        print()
        total_passed += r.passed
        total_failed += r.failed

    total = total_passed + total_failed
    pct = (total_passed / total * 100) if total > 0 else 0
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    print(f"  合计: {total_passed}/{total} | [{bar}] {pct:.0f}%")
    print()

    sys.exit(0 if status_ok else 1)


def _check_openspec_content(path: str) -> List[str]:
    """Check mase-state.yaml content for MASE compliance."""
    items = []
    if not os.path.exists(path):
        return ["✗ mase-state.yaml 不存在"]

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except Exception:
        return ["✗ mase-state.yaml 格式无效"]

    if data is None:
        return ["✗ mase-state.yaml 为空"]

    # Check schema
    if "schema" in data:
        items.append(f"✓ schema: {data['schema']}")
    else:
        items.append("✗ 缺少 schema 字段")

    # Check project_type
    pt = data.get("project_type", {})
    if pt:
        has_ui = pt.get("has_ui")
        ui_platform = pt.get("ui_platform")
        items.append(f"✓ project_type: has_ui={has_ui}, ui_platform={ui_platform}")
    else:
        items.append("✗ 缺少 project_type 声明（必须声明 has_ui 和 ui_platform）")

    # Check phase
    phase = data.get("phase")
    if phase:
        valid_phases = ["init", "proposal", "design", "build", "verify", "retro", "release"]
        if phase in valid_phases:
            items.append(f"✓ phase: {phase}")
        else:
            items.append(f"✗ phase 值无效: {phase} (有效值: {', '.join(valid_phases)})")
    else:
        items.append("✗ 缺少 phase 字段")

    # Check capabilities
    capabilities = data.get("capabilities", [])
    if capabilities:
        items.append(f"✓ capabilities ({len(capabilities)}): {', '.join(capabilities)}")
    else:
        items.append("✗ 缺少 capabilities 列表")

    return items


def _read_phase() -> Optional[dict]:
    """Read current phase from mase-state.yaml."""
    openspec_path = os.path.join("openspec", "changes", "_template",
                                  "mase-state.yaml")
    if not os.path.exists(openspec_path):
        return None

    try:
        with open(openspec_path, "r") as f:
            data = yaml.safe_load(f)
        if data is None:
            return None
        pt = data.get("project_type", {})
        return {
            "phase": data.get("phase", "unknown"),
            "has_ui": pt.get("has_ui"),
            "ui_platform": pt.get("ui_platform"),
            "capabilities": data.get("capabilities", []),
        }
    except Exception:
        return None


def _next_step(phase: str) -> str:
    """Return human-readable next step based on current phase."""
    steps = {
        "init": "触发 'brainstorming' → 开始 Proposal 阶段",
        "proposal": "等待 Agent 1 门禁确认 → 进入 Design 阶段",
        "design": "等待 Agent 1 门禁确认 → 进入 Build 阶段",
        "build": "继续 TDD 微循环 → Capability 全部完成后进入 Verify",
        "verify": "全部 BUG 关闭 → 进入 Retro 阶段",
        "retro": "复盘报告确认 → 进入 Release 阶段",
        "release": "发布完成 → 开始新一轮或归档",
    }
    return steps.get(phase, "请检查 phase 字段值")
