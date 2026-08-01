## ADDED Requirements

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
