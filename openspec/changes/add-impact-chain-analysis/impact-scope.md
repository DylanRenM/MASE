# 影响范围说明书

> Source digest: `sha256:2ab76a85604cdfb789a1012cd38e10ce083fd373a793dbe1bf16e447e1b2a321`

- 影响等级：L3
- 决策：proceed
- 第一方调用方：7
- 系统边界：2

## 修改点

- mase_cli/impact.py::impact policy and artifact workflow（external_contract）
- mase_cli/main.py::mase impact command group（external_contract）
- mase_cli/state.py::ChangeState and status derivation（business_semantics）
- mase_cli/gates.py::analysis-stage planning and candidate freeze（business_semantics）
- schemas/mase-state.schema.json::impact_analysis state contract（external_contract）
- project-rules.md::R13 impact-chain governance（business_semantics）

## 受影响调用方

- L1 · mase_cli/main.py::build_parser/_dispatch
- L1 · mase_cli/state.py::ChangeState.load/inspect_change_status
- L1 · mase_cli/gates.py::plan_change/freeze_candidate/execute_defined_gate
- L2 · mase_cli/commands/check_project.py::inspect_project
- L2 · mase_cli/commands/init_project.py::_common_project_files
- L2 · mase_cli/commands/update_project.py::check_updates
- L2 · mase_cli/rules.py::RuleSynchronizer

## 隐性依赖通道

- serialization: discovered / controlled
- configuration_spi: discovered / controlled
- generated_registration: discovered / controlled
- reflection: checked_empty / controlled
- proxy_aop: checked_empty / controlled
- message_event: checked_empty / controlled
- scheduled_job: checked_empty / controlled
- async_callback: checked_empty / controlled

## 递归终止

- cli-dispatch: system_boundary（深度 1）
- installed-schema-interface: system_boundary（深度 1）
- generated-project-files: repository_boundary（深度 2）

## 诊断与剩余风险

- contract_or_semantic_change
- system_boundary_affected
- core_or_non_low_frequency
- implicit_dependency_or_uncertainty
- language-specific call-graph completeness remains the responsibility of project adapters
- generic/manual fallback reports lower confidence and cannot prove dynamic callers
