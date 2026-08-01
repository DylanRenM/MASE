# 影响范围说明书

> Source digest: `sha256:c9aa45f2b59d87ebe89e055f896797ecc17e73d7b4660c2bbdee76d0c2635bb8`

- 影响等级：L3
- 决策：proceed
- 第一方调用方：3
- 系统边界：2

## 修改点

- mase_cli/risk.py::Change Risk resolution and UI routing（business_semantics）
- mase_cli/fix.py::fix start and promote workflow（external_contract）
- schemas/mase-state.schema.json::change_risk and ui_change_kind（external_contract）

## 批准的文件与符号边界

- mase_cli/risk.py
- mase_cli/fix.py
- mase_cli/state.py
- mase_cli/main.py
- profiles/risks.yaml
- profiles/strict.yaml
- schemas/mase-state.schema.json
- templates/mase-state.yaml
- project-rules.md
- README.md
- docs/MASE-framework.md
- docs/user-guide.md
- docs/glossary.md
- agents/agent-1-orchestrator/SKILL.md
- agents/agent-2-requirements/SKILL.md
- agents/agent-3-development/SKILL.md
- agents/agent-4-quality/SKILL.md
- skills/code-quality-controller/SKILL.md
- tests/test_mase_profiles.py
- tests/test_mase_lite_workflow.py
- tests/test_mase_governance_models.py
- openspec/changes/add-risk-adaptive-lite-change-workflow

- mase_cli/risk.py:resolve_change_risk
- mase_cli/risk.py:ui gate routing
- mase_cli/fix.py:start_fix
- mase_cli/fix.py:promote_fix
- mase_cli/main.py:fix commands

## 受保护不变量

- Profile 与 Change Risk 与影响等级分开
- 硬风险下限不得降级
- 旧 ui_changed true 保守映射为 journey
- promote 不覆盖未知目标

## 受影响调用方

- L1 · mase_cli/state.py::ChangeState loading
- L2 · mase_cli/gates.py::risk-selected gates
- L1 · mase_cli/main.py::fix command dispatch

## 调用图差异（verified）

- 无

## 实现变更声明

### Spec 内变更

- 新增 Change Risk L1-L4 与 UI 三分类
- 新增 OpenSpec Lite 创建和无损提升
- 精简 L1/L2 人工证据

### 附带/非 Spec 变更

- 无

## 隐性依赖通道

- serialization: discovered / controlled
- configuration_spi: discovered / controlled
- generated_registration: discovered / controlled
- reflection: checked_empty / controlled
- async_callback: checked_empty / controlled

## 递归终止

- mase-fix-cli: system_boundary（深度 1）
- installed-state-schema: system_boundary（深度 1）

## 诊断与剩余风险

- contract_or_semantic_change
- system_boundary_affected
- core_or_non_low_frequency
- implicit_dependency_or_uncertainty
- L3 独立综合评审仍需由非实现者确认
