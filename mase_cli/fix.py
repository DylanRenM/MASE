"""Single-source low-risk bugfix workflow with lossless promotion."""

from __future__ import annotations

import re
import shutil
import tempfile
from pathlib import Path

import yaml

from mase_cli import __version__
from mase_cli.schema import GovernanceError


LITE_TEMPLATE = """# 原因

<!-- 描述问题和为什么现在修复。 -->

# 验收行为

<!-- 使用可验证的行为描述。 -->

# 影响范围

<!-- 文件、接口、调用方和明确不修改的范围。 -->

# 根因假设与 RED 证据

<!-- 可证伪的根因假设与修复前失败测试/复现。 -->

# 测试方法

<!-- 聚焦测试、必要契约和手测方法。 -->

# 回滚方式

<!-- 如何恢复以及数据兼容性。 -->

# Tasks

- [ ] 1.1 建立 RED 证据
- [ ] 1.2 实现最小修复并运行聚焦测试
"""

REQUIRED_SECTIONS = (
    "原因", "验收行为", "影响范围", "根因假设与 RED 证据", "测试方法", "回滚方式", "Tasks"
)


def _safe_change(root: Path, name: str) -> Path:
    if Path(name).name != name or name in {"", ".", ".."}:
        raise GovernanceError("change name must be a single safe path component", code="invalid_name")
    return root / "openspec" / "changes" / name


def _sections(text: str) -> dict[str, str]:
    matches = list(re.finditer(r"(?m)^# ([^#\n]+)\s*$", text))
    values: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        values[match.group(1).strip()] = text[match.end():end].strip()
    missing = [name for name in REQUIRED_SECTIONS if name not in values]
    if missing:
        raise GovernanceError(
            "bugfix-lite change is missing sections: " + ", ".join(missing), code="schema"
        )
    return values


def start_lite_change(project_root: Path | str, name: str) -> Path:
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, name)
    if change.exists():
        raise GovernanceError(f"change already exists: {name}", path=change, code="conflict")
    change.mkdir(parents=True)
    source = change / "change.md"
    source.write_text(LITE_TEMPLATE, encoding="utf-8")
    return source


def promote_lite_change(
    project_root: Path | str, name: str, *, target: str = "standard"
) -> tuple[Path, ...]:
    if target != "standard":
        raise GovernanceError(f"unsupported promotion target: {target}", code="schema")
    root = Path(project_root).expanduser().resolve()
    change = _safe_change(root, name)
    source = change / "change.md"
    if not source.is_file():
        raise GovernanceError("bugfix-lite source change.md is missing", path=source, code="not_found")
    text = source.read_text(encoding="utf-8")
    sections = _sections(text)
    relative_payloads = {
        ".openspec.yaml": "schema: spec-driven\nprovenance: bugfix-lite/v1\n",
        "proposal.md": (
            f"## Why\n\n{sections['原因']}\n\n## What Changes\n\n"
            f"- 完成 `{name}` 的验收行为：{sections['验收行为']}\n\n"
            "## Capabilities\n\n### New Capabilities\n\n"
            f"- `behavior`: {name} 的可验收行为。\n\n"
            "### Modified Capabilities\n\n- 无。\n\n"
            f"## Impact\n\n{sections['影响范围']}\n\n"
            "> Provenance: promoted from `change.md` (`bugfix-lite/v1`).\n"
        ),
        "design.md": (
            f"## Context\n\n{sections['根因假设与 RED 证据']}\n\n"
            "## Goals / Non-Goals\n\n**Goals:**\n\n"
            f"- {sections['验收行为']}\n\n**Non-Goals:**\n\n- 超出已声明影响范围的变更。\n\n"
            f"## Decisions\n\n测试方法：{sections['测试方法']}\n\n"
            f"## Risks / Trade-offs\n\n回滚方式：{sections['回滚方式']}\n"
        ),
        "specs/behavior/spec.md": (
            "## ADDED Requirements\n\n"
            f"### Requirement: {name} 验收行为\n{sections['验收行为']}\n\n"
            "#### Scenario: 验收行为成立\n"
            "- **WHEN** change 实现并执行声明的测试方法\n"
            f"- **THEN** {sections['验收行为']}\n"
        ),
        "tasks.md": sections["Tasks"].rstrip() + "\n",
        "mase-state.yaml": yaml.safe_dump({
            "schema": "mase-project/v2",
            "profile": "standard",
            "stack": "generic",
            "toolchains": [],
            "framework_contract": {
                "name": "MASE", "version": __version__,
                "interface": "installed-cli-and-versioned-schemas",
            },
            "phase": "proposal",
            "product": {"has_ui": False, "has_public_contract": True, "ui_platform": None},
            "impact": {"ui_changed": False, "ui_change_kind": "none", "paths": []},
            "change_risk": {"level": "L3", "dimensions": {
                "public_contract": False, "core_calculation": False,
                "data_write": False, "authentication": False,
                "authorization": False, "secrets": False, "quota": False,
                "concurrency": False, "cross_system": False,
                "persistent_state_machine": False,
                "reversible": True, "stable_regression": True,
            }},
            "impact_analysis": {"applicability": "undecided", "reconciliation": "pending"},
            "risk": {"triggers": [], "capabilities": {}},
            "gates": {}, "evidence": [], "dependencies": [],
            "conflicts_with": [], "blockers": [], "capabilities": ["behavior"],
        }, sort_keys=False, allow_unicode=True),
    }
    conflicts = [relative for relative in relative_payloads if (change / relative).exists()]
    if conflicts:
        raise GovernanceError(
            "promotion conflict; target files already exist: " + ", ".join(conflicts),
            path=change,
            code="conflict",
        )

    created: list[Path] = []
    staging = Path(tempfile.mkdtemp(prefix=".mase-promote-", dir=change))
    try:
        for relative, payload in relative_payloads.items():
            staged = staging / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_text(payload, encoding="utf-8")
        for relative in relative_payloads:
            target_path = change / relative
            target_path.parent.mkdir(parents=True, exist_ok=True)
            (staging / relative).replace(target_path)
            created.append(target_path)
    except Exception:
        for path in reversed(created):
            if path.is_file():
                path.unlink()
        raise
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    return tuple(created)
