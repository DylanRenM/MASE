"""mase check — 合规检查当前项目"""

import os
import sys
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    category: str
    items: list = field(default_factory=list)
    passed: int = 0
    failed: int = 0


def run():
    results = []
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
                  "tech-feasibility.md", "tasks.md", ".openspec.yaml"]:
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
    else:
        r.failed += 1
        r.items.append("✗ openspec/changes/_template/ 缺失")
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
