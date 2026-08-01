# 影响范围说明书

> Source digest: `sha256:1cf08a1b084a958126d94b9cb6953a76892319b71677d8e5aaa9d93d87d53bca`

- 影响等级：L3
- 决策：proceed
- 第一方调用方：3
- 系统边界：2

## 修改点

- mase_cli/gates.py::required_at planning and milestone derivation（business_semantics）
- mase_cli/state.py::verification milestone status（external_contract）
- mase_cli/main.py::gate plan --target（external_contract）

## 批准的文件与符号边界

- mase_cli/gates.py
- mase_cli/state.py
- mase_cli/main.py
- schemas/mase-gates.schema.json
- schemas/mase-state.schema.json
- templates/gates.yaml
- templates/mase-state.yaml
- .mase/gates.yaml
- project-rules.md
- README.md
- docs/MASE-framework.md
- docs/user-guide.md
- docs/glossary.md
- tests/test_mase_gate_planning.py
- tests/test_mase_governance_models.py
- tests/test_release_governance.py
- openspec/changes/separate-development-merge-release-verification

- mase_cli/gates.py:GateDefinition
- mase_cli/gates.py:plan_change
- mase_cli/state.py:inspect_change_status
- mase_cli/main.py:gate plan parser

## 受保护不变量

- 开发验证不得冒充合并或发布就绪
- 候选绑定门禁不得在 development 或 merge 执行
- 发布与观察门禁只在显式发布意图下适用

## 受影响调用方

- L1 · mase_cli/main.py::gate plan dispatch
- L1 · mase_cli/state.py::inspect_change_status
- L2 · mase_cli/release.py::candidate freeze workflow

## 调用图差异（verified）

- 无

## 实现变更声明

### Spec 内变更

- 分离开发、合并、发布和观察的验证时点
- 新增证据派生验证里程碑

### 附带/非 Spec 变更

- 无

## 隐性依赖通道

- serialization: discovered / controlled
- configuration_spi: discovered / controlled
- reflection: checked_empty / controlled
- proxy_aop: checked_empty / controlled
- async_callback: checked_empty / controlled

## 递归终止

- gate-cli: system_boundary（深度 1）
- installed-state-schema: system_boundary（深度 1）

## 诊断与剩余风险

- contract_or_semantic_change
- system_boundary_affected
- core_or_non_low_frequency
- implicit_dependency_or_uncertainty
- L3 独立综合评审仍需由非实现者确认
