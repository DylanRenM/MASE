# capability-scoped-gate-plan Specification

## Purpose
TBD - created by archiving change optimize-gate-scheduling-and-test-deduplication. Update Purpose after archive.
## Requirements
### Requirement: Capability risk is independently derived
The system SHALL read each `risk.capabilities` entry's profile, triggers and paths and SHALL produce a machine-readable Capability GatePlan without forcing unrelated capabilities to use the same development-stage test scope.

#### Scenario: One capability contains authorization
- **WHEN** a Standard change has a UI capability and a separate authorization capability
- **THEN** the authorization capability receives Strict boundary gates while the UI capability retains its applicable Standard capability gates

### Requirement: Capability-scoped gate inputs
Capability gate instances SHALL use declared capability paths and a validated test manifest to derive their default input scope and actual test selectors, and SHALL identify scope, selected test IDs, selection reasons and conservative fallback in plan and evidence output. A gate that declares dynamic test tiers MUST consume the selected selectors through its canonical command.

#### Scenario: UI-only file changes
- **WHEN** a file changes only within the UI capability paths
- **THEN** authorization capability integration evidence remains fresh while the UI's applicable evidence and selected tests are recalculated

#### Scenario: Dynamic tier is not consumed
- **WHEN** a gate declares `test_tiers` but its canonical command omits the selected-test placeholder
- **THEN** MASE rejects the gate definition instead of recording misleading selected-test evidence

### Requirement: Change-level final risk floor
The system SHALL merge Capability hard-gate requirements into the change's final GatePlan so that local scoping reduces repeated development testing but cannot remove final quality gates triggered by any high-risk capability.

#### Scenario: Strict capability exists in Standard change
- **WHEN** an authorization capability is Strict inside a Standard change
- **THEN** final full regression, security and independent review remain required for the frozen change candidate

### Requirement: Compatible capability declarations
The system SHALL continue accepting existing capability declarations containing only `profile` and projects without a test manifest. It SHALL use conservative change-level inputs and canonical static gate tests for those projects, and SHALL emit actionable diagnostics when triggers, paths, manifest mappings or gate definitions required for precise scoping are absent.

#### Scenario: Legacy capability profile only
- **WHEN** state declares a capability with only `profile: strict` and no test manifest exists
- **THEN** status remains valid, uses conservative change-level scope and static canonical tests, and recommends adding triggers, paths and manifest mappings rather than guessing them

### Requirement: Stable selected-test execution signature
The GatePlan and Gate Runner SHALL calculate the test digest from the ordered selected test IDs, selectors and manifest content relevant to the gate. Changing a selected test, selector, tier or mapping MUST invalidate otherwise fresh evidence.

#### Scenario: Selector changes without product code changes
- **WHEN** a selected P0 journey selector changes after a passed gate
- **THEN** the prior execution signature no longer matches and the gate returns to pending or stale

### Requirement: Capability impact gates are independently derived
The system SHALL derive impact-analysis gates from each Capability's historical-change applicability, impact level, affected paths, uncertainty, and threshold decision without forcing unrelated capabilities to use the same analysis or verification scope. Impact level MUST NOT create a fourth Profile and MUST NOT remove existing Profile/risk gates.

#### Scenario: One capability has an L3 contract change
- **WHEN** a Standard change contains an L3 API capability and an unrelated L1 utility capability
- **THEN** architecture review and full-chain smoke apply to the API capability while the utility retains its L1 impact gates and the change-level final risk floor remains intact

### Requirement: Unmapped affected paths are conservative
When an affected caller or boundary cannot be mapped to a declared Capability, the GatePlan MUST use change-level scope and emit a governance diagnostic rather than omitting impact gates.

#### Scenario: Caller has no Capability mapping
- **WHEN** reconciliation discovers an affected path outside every declared Capability
- **THEN** the plan selects conservative change-level verification and reports the missing mapping

### Requirement: Capability 使用稳定测试选择器
Capability gate SHALL 从 `.mase/tests.yaml` 选择稳定 Test ID 和最小可执行 selector，并 SHALL 在 evidence 中记录实际选择，避免以整个测试文件代替不同语义门禁的范围。

#### Scenario: 修改影响治理 Capability
- **WHEN** 影响路径只命中影响治理实现
- **THEN** 差异契约、冒烟和回滚 gate 分别获得与其语义匹配的 node selector，而不是共同运行完整影响测试文件

### Requirement: 同一边界避免重复测试节点
GatePlan SHALL 报告同一 Capability 边界中一个测试节点被多个 automatic gate 重复选择的次数，并 SHALL 推荐显式覆盖或 selector 分离；最终候选全量回归不计入可删除的边界重复。

#### Scenario: 前置门禁重复节点超过阈值
- **WHEN** capability 阶段多个 gate 的规范化 selector 重复比例超过配置阈值
- **THEN** 计划输出重复节点数量、涉及 gate 和收窄建议

### Requirement: 冗余执行率只统计等价验证对象
MASE SHALL 将冗余定义为相同候选、相同输入、等价环境和相同业务时点下重复执行的测试节点，并 MUST 排除开发聚焦测试与发布候选全量认证之间的合理重复。

#### Scenario: 开发和发布分别运行同一测试
- **WHEN** 一个测试在 development 聚焦门禁和后续 frozen candidate 的 release 全量回归中各执行一次
- **THEN** 该行为不计入同候选冗余执行率
