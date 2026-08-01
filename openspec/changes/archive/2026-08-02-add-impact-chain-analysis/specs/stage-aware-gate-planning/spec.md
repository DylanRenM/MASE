## MODIFIED Requirements

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
