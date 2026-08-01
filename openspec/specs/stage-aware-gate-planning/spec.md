# stage-aware-gate-planning Specification

## Purpose
TBD - created by archiving change optimize-gate-scheduling-and-test-deduplication. Update Purpose after archive.
## Requirements
### Requirement: Canonical project gate definitions
The system SHALL support a schema-validated `.mase/gates.yaml` that defines each gate's stage, command, inputs, artifacts, test selectors, candidate binding and explicit coverage relationships, and SHALL reject paths escaping the project root or conflicting runtime commands.

#### Scenario: Defined gate is planned
- **WHEN** a project defines a `full_regression` gate with stage `final`
- **THEN** `mase gate plan` shows its configured command, inputs and final-stage status without requiring an Agent to restate them

#### Scenario: Runtime command conflicts with definition
- **WHEN** a caller supplies a command different from the canonical gate definition
- **THEN** Gate Runner rejects the execution before running either command

### Requirement: Stage-aware executable plan
The system SHALL classify gate instances as analysis, micro, capability, final, or release stage and SHALL report each as runnable, reusable, deferred, stale, or blocked with an actionable reason. Required pre-design analysis MUST be fresh before design/build work is routed, and required reconciliation MUST be fresh before verification or candidate freeze.

#### Scenario: Final gate is requested during build
- **WHEN** implementation tasks or required non-final gates remain incomplete
- **THEN** the final gate is deferred and the plan identifies the prerequisite work rather than recommending an early full regression

#### Scenario: Capability boundary is ready
- **WHEN** a capability's related implementation is complete and its inputs changed
- **THEN** the plan recommends only that capability's applicable related, integration and risk gates

#### Scenario: Design requested before impact analysis
- **WHEN** a historical behavior change has missing or stale analysis-stage evidence
- **THEN** the plan blocks design/build routing and identifies the required impact action

### Requirement: Final candidate freeze
For projects using canonical gate definitions, the system SHALL bind candidate-bound final gates to an explicit frozen candidate digest created only after tasks, required analysis/reconciliation gates, other non-final gates, and blockers permit final verification.

#### Scenario: Candidate freezes successfully
- **WHEN** all tasks and required non-final gate instances including impact reconciliation are complete and fresh and no blocker remains
- **THEN** `mase gate freeze` records a candidate ID and exact candidate input digest including the impact artifact

#### Scenario: Candidate input changes
- **WHEN** implementation, impact artifact, test, specification, or gate-definition input changes after freeze
- **THEN** the candidate becomes stale and candidate-bound final gates cannot run until a new candidate is frozen

### Requirement: Duplicate test-set diagnostics
The system SHALL compare declared test selector sets and normalized commands and SHALL warn on exact or high-overlap gate definitions without automatically treating different semantic gates as equivalent.

#### Scenario: Related and integration gates are identical
- **WHEN** related_tests and integration_tests declare the same command and test selectors without an explicit coverage relationship
- **THEN** the plan reports a duplicate-test warning and recommends separating their boundaries

### Requirement: Backward-compatible ad-hoc operation
Projects without `.mase/gates.yaml` SHALL remain readable and SHALL be allowed to use the legacy explicit-command runner with a compatibility diagnostic that explicitly lists unavailable canonical planning, candidate freeze, exact execution reuse, cross-gate coverage and overlap diagnostics; the project MUST NOT be described as receiving these guarantees until migration.

#### Scenario: Legacy project runs a gate
- **WHEN** an existing project without a gate definition file invokes `mase gate run GATE -- COMMAND`
- **THEN** the command executes with the existing evidence contract and the CLI reports that canonical planning, candidate freeze and execution reuse are not active

#### Scenario: Legacy project runs project check
- **WHEN** `mase check` inspects a project without non-empty canonical gate definitions
- **THEN** the report remains backward compatible but identifies each unavailable optimization capability and points to `mase update --dry-run`

### Requirement: 测试包含关系诊断
MASE SHALL 对 gate 的稳定 Test ID 或规范化 selector 同时计算 Jaccard 和双向包含率，并 SHALL 在任一集合被另一集合高比例包含且没有显式覆盖关系时报告重复风险。

#### Scenario: 冒烟集合完全包含于契约集合
- **WHEN** `full_chain_smoke` 的全部 selector 都存在于更大的 `api_contract` 集合且未声明 covers
- **THEN** GatePlan 报告 100% 小集合包含率并要求拆分语义 selector 或证明覆盖

#### Scenario: 两个 gate 仅少量交集
- **WHEN** gate 只共享基础 fixture 或少量测试
- **THEN** 系统不因低包含率自动宣称重复或等价

### Requirement: 默认计划只展示必需门禁
`mase gate plan` SHALL 默认展示当前 GatePlan 必需 gate、必要前序和阻塞项；未触发的项目 gate SHALL 仅在显式完整视图中展示。

#### Scenario: Standard change 未触发安全风险
- **WHEN** 项目定义 security 和 independent gate 但当前 change 不要求它们
- **THEN** 默认计划不把这些 gate 显示为 runnable 或 manual

#### Scenario: 请求完整计划
- **WHEN** 调用者使用 `--all`
- **THEN** 输出包含未触发 gate，并明确标记 optional/not-selected

### Requirement: 下一步命令匹配 gate 模式
GatePlan SHALL 根据前序 gate 的 automatic/manual 模式生成可执行的下一步命令。

#### Scenario: Final 被人工架构评审阻塞
- **WHEN** 候选冻结前缺少 manual architecture review
- **THEN** 下一步为 `mase gate manual` 而不是尝试自动运行该 gate

### Requirement: Gate 声明最晚要求时点
每个 canonical gate SHALL 支持 `required_at: development|merge|release|observe`，GatePlan SHALL 只把不晚于当前目标时点的适用 gate 作为阻塞项。

#### Scenario: 请求开发验证计划
- **WHEN** 调用者为一个 change 请求 development 目标 GatePlan
- **THEN** 计划不要求生产构建、候选冻结、全量回归或发布审计 gate

#### Scenario: 旧 gate 配置
- **WHEN** gate 只有旧 `stage` 而没有 `required_at`
- **THEN** 系统使用记录在兼容规则中的确定性映射，并报告可迁移诊断

### Requirement: 候选绑定门禁不得提前
候选绑定 gate MUST 只在 release 或 observe 时点执行，Schema 或加载器 MUST 拒绝将其声明为 development 或 merge。

#### Scenario: 非法提前全量回归
- **WHEN** `full_regression` 同时声明 `candidate_bound: true` 和 `required_at: development`
- **THEN** MASE 在执行前拒绝该 gate 定义

### Requirement: GatePlan 遵循显式 DAG 前序
GatePlan SHALL 在阶段和 required_at 筛选后，对选中的 gate 及其传递前序做拓扑排序，并 SHALL 把必要前序包含在默认视图中。

#### Scenario: 可选 gate 是必需前序
- **WHEN** 一个当前必需 gate requires 一个未被风险直接选择的 gate
- **THEN** 默认计划仍包含该前序，并标记其被包含的依赖原因

### Requirement: GatePlan 成本按目标时点分组
GatePlan SHALL 将 development、merge、release、observe 的预计成本分别展示，并 SHALL 对尚未请求的发布阶段标记为延迟执行而非当前阻塞。

#### Scenario: 只请求开发验证
- **WHEN** 调用者目标为 development
- **THEN** 计划显示开发预计耗时，并将合并和发布成本作为后续信息而非当前必做项
