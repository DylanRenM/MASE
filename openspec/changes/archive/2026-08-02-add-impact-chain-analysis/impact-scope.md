# 影响范围说明书

> Source digest: `sha256:edb05581908202fe5757e5e8f2462c2479474dad98b8c40c915443513eea823c`

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

## 批准的文件与符号边界

- .mase/gates.yaml
- README.md
- AGENTS.md
- CLAUDE.md
- CONVENTIONS.md
- .github/copilot-instructions.md
- agents/agent-1-orchestrator/SKILL.md
- agents/agent-2-requirements/SKILL.md
- agents/agent-3-development/SKILL.md
- agents/agent-4-quality/SKILL.md
- docs/MASE-framework.md
- docs/design-principles.md
- docs/glossary.md
- docs/project-structure-spec.md
- docs/user-guide.md
- framework-manifest.yaml
- mase_cli/impact.py
- mase_cli/main.py
- mase_cli/risk.py
- mase_cli/state.py
- mase_cli/gates.py
- mase_cli/rules.py
- mase_cli/commands/check_project.py
- mase_cli/commands/init_project.py
- mase_cli/commands/update_project.py
- profiles/lite.yaml
- profiles/standard.yaml
- profiles/strict.yaml
- profiles/risks.yaml
- project-rules.md
- schemas/mase-impact-analysis.schema.json
- schemas/mase-impact-scan.schema.json
- schemas/mase-state.schema.json
- schemas/mase-gates.schema.json
- scripts/verify_mase_training_deck.py
- templates/impact-analysis.yaml
- templates/mase-state.yaml
- templates/gates.yaml
- templates/contract.md
- tests/test_mase_impact_analysis.py
- tests/test_mase_cli_operations.py
- tests/test_mase_cli_stacks.py
- tests/test_mase_training_deck.py
- training/mase-framework/mase-training-v2.3.yaml
- training/mase-framework/MASE框架培训讲义V2.3.pptx
- openspec/changes/add-impact-chain-analysis/proposal.md
- openspec/changes/add-impact-chain-analysis/design.md
- openspec/changes/add-impact-chain-analysis/specs
- openspec/changes/add-impact-chain-analysis/tasks.md
- openspec/changes/add-impact-chain-analysis/verification.md

- mase_cli/impact.py:assess_impact
- mase_cli/impact.py:_validate_impact_policy
- mase_cli/impact.py:impact_status
- mase_cli/impact.py:reconcile_impact
- mase_cli/impact.py:render_impact_views
- mase_cli/main.py:impact reconcile command
- mase_cli/rules.py:RuleSynchronizer.render

## 受保护不变量

- MASE 与 Pilot 保持独立仓库、状态、测试和数据生命周期
- L1/L2/L3 仍是与 Lite/Standard/Strict 正交的影响等级
- AI 自述和新增测试不能替代人工审批或受保护历史回归
- 已匹配复扫在任一绑定路径变化后必须立即失效

## 受影响调用方

- L1 · mase_cli/main.py::build_parser/_dispatch
- L1 · mase_cli/state.py::ChangeState.load/inspect_change_status
- L1 · mase_cli/gates.py::plan_change/freeze_candidate/execute_defined_gate
- L2 · mase_cli/commands/check_project.py::inspect_project
- L2 · mase_cli/commands/init_project.py::_common_project_files
- L2 · mase_cli/commands/update_project.py::check_updates
- L2 · mase_cli/rules.py::RuleSynchronizer

## 调用图差异（unverified）

- 无

## 实现变更声明

### Spec 内变更

- 增加变更文件/符号边界和当前差异摘要新鲜度
- 增加调用图边差异、受保护历史测试、副作用预算和结构化非 Spec 声明
- 修改六项开发原则并同步 MASE 文档、Agent、培训源和可编辑 PPT

### 附带/非 Spec 变更

- 无

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
- call_graph_diff_unverified
- effect_budget_unverified
- implicit_dependency_or_uncertainty
- language-specific call-graph completeness remains the responsibility of project adapters
- generic/manual fallback reports lower confidence and cannot prove dynamic callers
- generic adapter does not yet provide baseline/actual call-edge or runtime effect observation
