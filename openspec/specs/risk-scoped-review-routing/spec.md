# risk-scoped-review-routing Specification

## Purpose
TBD - created by archiving change optimize-context-token-routing. Update Purpose after archive.
## Requirements
### Requirement: Risk-triggered Standard security review
MASE MUST require deep security review for a Standard change only when a registered attack-surface trigger or an explicit project gate requires it.

#### Scenario: Ordinary non-security Standard change
- **WHEN** a Standard change modifies persistence-neutral internal behavior and declares no security trigger
- **THEN** its plan does not add deep security review solely because the base Profile is Standard

#### Scenario: Untrusted file input
- **WHEN** a Standard change handles untrusted upload or archive parsing
- **THEN** the risk registry adds security review and related attack-surface tests

### Requirement: Independent review stopping condition
Strict independent review SHALL require one review pass and SHALL require another pass only after an objection, candidate input change or stale/invalid review evidence.

#### Scenario: Reviewer has no objection
- **WHEN** the reviewer is shown the subject and evidence and confirms no objection
- **THEN** the independent review gate is satisfied without a mandatory formal report or additional review round

### Requirement: Impact review is routed by level and threshold
MASE SHALL require a human impact/code review for L2, an architecture review for L3 or threshold escalation, and another review round only after an objection, subject/input change, scope expansion, or stale/invalid evidence.

#### Scenario: L2 review has no objection
- **WHEN** the reviewer confirms the AI impact/diff summary, affected callers, tests, and residual risks without objection
- **THEN** the impact review gate is satisfied without a mandatory second unchanged review

#### Scenario: Reconciliation expands scope after review
- **WHEN** actual-diff reconciliation discovers an additional caller after review
- **THEN** the existing review becomes stale and a new round is required on the expanded subject

### Requirement: AI cannot satisfy architecture authority
An AI-generated recommendation MUST NOT satisfy the manual architecture-review gate for excessive scope or L3 disposition.

#### Scenario: AI recommends version isolation
- **WHEN** the caller threshold is exceeded and only an AI recommendation exists
- **THEN** implementation remains blocked until an authorized human records the disposition

### Requirement: 形式化人工审查按 Change Risk 路由
L1/L2 SHALL NOT 要求形式化 manual evidence；L3 SHALL 选择一次独立综合审查；L4 SHALL 仅按命中的安全、数据恢复和发布批准风险选择对应人工 gate。

#### Scenario: L2 自动化修复
- **WHEN** Change Risk 为 L2 且未命中人工硬触发
- **THEN** GatePlan 不要求 code_review 或 independent_review 的形式化人工证据

#### Scenario: 实现者自查
- **WHEN** 实现 Agent 提交自己的 review 记录
- **THEN** 记录只能标记 self review，不能满足 independent manual gate
