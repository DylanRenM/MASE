## ADDED Requirements

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
