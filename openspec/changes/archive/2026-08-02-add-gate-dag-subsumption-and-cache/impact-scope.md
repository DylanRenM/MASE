# 影响范围说明书

> Source digest: `sha256:80062e81f4403ea3940d676ea7bfbfce26cb7c568dd657738f6ce60c26bc999f`

- 影响等级：L3
- 决策：proceed
- 第一方调用方：3
- 系统边界：2

## 修改点

- mase_cli/gates.py::requires DAG and topological planning（business_semantics）
- mase_cli/evidence.py::execution environment digest and subsumed evidence（external_contract）
- schemas/mase-gates.schema.json::dependency and execution environment fields（external_contract）

## 批准的文件与符号边界

- mase_cli/gates.py
- mase_cli/evidence.py
- mase_cli/state.py
- schemas/mase-gates.schema.json
- schemas/mase-evidence.schema.json
- .mase/gates.yaml
- project-rules.md
- docs/MASE-framework.md
- docs/user-guide.md
- docs/glossary.md
- tests/test_mase_gate_planning.py
- tests/test_mase_gate_evidence.py
- openspec/changes/add-gate-dag-subsumption-and-cache

- mase_cli/gates.py:GateDefinition
- mase_cli/gates.py:load_gate_definitions
- mase_cli/gates.py:plan_change
- mase_cli/gates.py:execute_defined_gate
- mase_cli/evidence.py:run_gate

## 受保护不变量

- requires、covers、cache 和 candidate_bound 语义不得混用
- subsumed 不得伪装为独立 passed
- 开发聚焦测试与发布候选全量认证不计为冗余

## 受影响调用方

- L1 · mase_cli/main.py::gate plan dispatch
- L1 · mase_cli/gates.py::execute_defined_gate
- L2 · mase_cli/state.py::evidence status derivation

## 调用图差异（verified）

- 无

## 实现变更声明

### Spec 内变更

- 通用 requires DAG 与拓扑计划
- 可审计 subsumed 证据
- 精确环境缓存键与冗余指标

### 附带/非 Spec 变更

- 无

## 隐性依赖通道

- serialization: discovered / controlled
- configuration_spi: discovered / controlled
- generated_registration: checked_empty / controlled
- reflection: checked_empty / controlled
- async_callback: checked_empty / controlled

## 递归终止

- gate-cli: system_boundary（深度 1）
- installed-gate-schema: system_boundary（深度 1）

## 诊断与剩余风险

- contract_or_semantic_change
- system_boundary_affected
- core_or_non_low_frequency
- implicit_dependency_or_uncertainty
- L3 独立综合评审仍需由非实现者确认
