# evidence-freshness-and-reuse Specification

## Purpose
TBD - created by archiving change optimize-gate-scheduling-and-test-deduplication. Update Purpose after archive.
## Requirements
### Requirement: Effective gate state from evidence freshness
The system SHALL derive each automatic gate's effective state from its latest applicable structured evidence and current inputs, log and artifacts; a hand-written `passed` field or stale evidence MUST NOT satisfy a required automatic gate.

#### Scenario: Input changes after pass
- **WHEN** a file in the gate's canonical input set changes after a passed execution
- **THEN** `mase status` reports the gate stale, lifecycle is not ready-to-complete, and the next action is a rerun or a new candidate

#### Scenario: Newer failure follows old pass
- **WHEN** a gate passes and a later execution of the same instance fails
- **THEN** the effective state is failed even if the older passed evidence remains in audit history

#### Scenario: Newer fresh pass follows failure
- **WHEN** a later equivalent execution passes with current inputs
- **THEN** the effective state returns to passed and the older failure remains audit-only

### Requirement: Exact execution reuse
The system SHALL skip subprocess execution only when gate instance, normalized command, platform, inputs, declared test set and candidate ID match a fresh prior execution.

#### Scenario: Same gate is invoked twice unchanged
- **WHEN** a fresh gate is invoked again with the identical execution signature
- **THEN** Gate Runner returns a cache hit referencing the prior execution and does not start the test process again

#### Scenario: One execution attribute differs
- **WHEN** command, platform, input digest, test set or candidate ID differs
- **THEN** Gate Runner executes the command and records a new execution

### Requirement: Explicit cross-gate coverage
The system MUST reuse one execution across different gate names only when the canonical source gate declares the target in `covers`; derived evidence SHALL reference the same execution and log.

#### Scenario: Gate explicitly covers another
- **WHEN** a successful canonical gate declares another gate in `covers`
- **THEN** both gate instances receive traceable fresh evidence from one execution

#### Scenario: Identical gates lack covers
- **WHEN** two gate definitions happen to be identical but neither declares coverage
- **THEN** the CLI warns about duplication but does not silently mark the other gate passed

### Requirement: Streaming and redacted evidence log
Gate Runner SHALL always store a complete secret-redacted evidence log and SHALL write passed evidence only after successful completion. It SHALL return concise bounded output by default and SHALL stream subprocess output only when the caller explicitly requests verbose mode.

#### Scenario: Long-running regression uses default output
- **WHEN** a test command produces incremental output and verbose mode is not requested
- **THEN** the caller receives a bounded final summary while the persisted log contains the complete redacted output

#### Scenario: Long-running regression requests verbose output
- **WHEN** a caller explicitly requests verbose mode
- **THEN** the caller receives incremental output before completion and the persisted log contains the redacted equivalent

### Requirement: Bounded state evidence history
The system SHALL compact state evidence per gate instance to a bounded audit set while preserving log references and the latest pass/failure/replacement relationship.

#### Scenario: Gate is rerun many times
- **WHEN** more than the configured retention count exists for one gate instance
- **THEN** `mase-state.yaml` retains only the bounded relevant records and status remains determined by the latest evidence

### Requirement: Impact evidence freshness uses semantic inputs
Impact analysis and review evidence SHALL be fresh only when baseline/diff identity, changed paths/symbols, affected Specs/contracts, scanner adapter/rules, implicit-channel checks, affected scope, test plan, decision, and candidate binding match the current change.

#### Scenario: Scanner rules change after approval
- **WHEN** the adapter or rule-set digest changes after impact review passes
- **THEN** analysis and dependent review evidence become stale even if source files are unchanged

#### Scenario: Unrelated capability changes
- **WHEN** a file outside the impact gate's canonical Capability scope changes
- **THEN** fresh scoped analysis MAY be reused when every execution-signature input remains identical

### Requirement: Reconciliation invalidates planned-only evidence
Planned impact evidence MUST NOT satisfy post-implementation reconciliation. Reconciliation SHALL bind the actual diff and SHALL invalidate dependent test/review evidence when realized scope expands.

#### Scenario: Actual diff adds an affected boundary
- **WHEN** reconciliation finds a system boundary absent from the planned analysis
- **THEN** the prior level, review, and selected verification evidence become stale and the GatePlan is recomputed

### Requirement: Matched reconciliation is continuously revalidated
MASE SHALL recompute the canonical digest of the reconciled actual paths whenever impact status, dependent gate planning, or candidate freeze is evaluated. A previously matched artifact MUST become inconsistent or stale when any bound path changes after reconciliation.

#### Scenario: Source changes after a matched reconciliation
- **WHEN** an approved source file changes after `impact_reconcile` records matched status
- **THEN** impact status reports the actual-diff digest as stale and candidate freeze remains blocked until reconciliation runs again

### Requirement: 缓存键绑定完整验证环境
自动 evidence 的缓存键 MUST 包含 gate 命令、规范化 Test ID/selector 集、源码与测试输入摘要、依赖锁摘要、工具链版本、fixture/config 摘要、候选 ID、scope 和适用 release context。

#### Scenario: 依赖锁变化
- **WHEN** 源码与测试未变但 dependency lock digest 变化
- **THEN** 旧 evidence 不得命中缓存或覆盖新执行

#### Scenario: 完全相同执行对象
- **WHEN** 所有缓存键分量相同且 evidence fresh
- **THEN** Gate Runner 复用已有 execution 并报告 cache hit

### Requirement: 跨 gate 覆盖要求等价或更严格
源 gate 只有在测试集合与输入为目标超集、候选相同、工具链和依赖相同、fixture/config 等价且环境相同或更严格时 SHALL 产生 subsumed evidence。

#### Scenario: Fixture 不等价
- **WHEN** 源 gate 使用 mock fixture 而目标要求受控真实持久化
- **THEN** 覆盖被拒绝，目标 gate 保持待执行
