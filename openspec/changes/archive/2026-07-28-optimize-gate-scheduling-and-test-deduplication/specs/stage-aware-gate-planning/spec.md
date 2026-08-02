## ADDED Requirements

### Requirement: Canonical project gate definitions
The system SHALL support a schema-validated `.mase/gates.yaml` that defines each gate's stage, command, inputs, artifacts, test selectors, candidate binding and explicit coverage relationships, and SHALL reject paths escaping the project root or conflicting runtime commands.

#### Scenario: Defined gate is planned
- **WHEN** a project defines a `full_regression` gate with stage `final`
- **THEN** `mase gate plan` shows its configured command, inputs and final-stage status without requiring an Agent to restate them

#### Scenario: Runtime command conflicts with definition
- **WHEN** a caller supplies a command different from the canonical gate definition
- **THEN** Gate Runner rejects the execution before running either command

### Requirement: Stage-aware executable plan
The system SHALL classify gate instances as micro, capability or final and SHALL report each as runnable, reusable, deferred, stale or blocked with an actionable reason.

#### Scenario: Final gate is requested during build
- **WHEN** implementation tasks or required non-final gates remain incomplete
- **THEN** the final gate is deferred and the plan identifies the prerequisite work rather than recommending an early full regression

#### Scenario: Capability boundary is ready
- **WHEN** a capability's related implementation is complete and its inputs changed
- **THEN** the plan recommends only that capability's applicable related, integration and risk gates

### Requirement: Final candidate freeze
For projects using canonical gate definitions, the system SHALL bind candidate-bound final gates to an explicit frozen candidate digest created only after tasks, non-final required gates and blockers permit final verification.

#### Scenario: Candidate freezes successfully
- **WHEN** all tasks and required non-final gate instances are complete and fresh and no blocker remains
- **THEN** `mase gate freeze` records a candidate ID and exact candidate input digest

#### Scenario: Candidate input changes
- **WHEN** implementation, test, specification or gate-definition input changes after freeze
- **THEN** the candidate becomes stale and candidate-bound final gates cannot run until a new candidate is frozen

### Requirement: Duplicate test-set diagnostics
The system SHALL compare declared test selector sets and normalized commands and SHALL warn on exact or high-overlap gate definitions without automatically treating different semantic gates as equivalent.

#### Scenario: Related and integration gates are identical
- **WHEN** related_tests and integration_tests declare the same command and test selectors without an explicit coverage relationship
- **THEN** the plan reports a duplicate-test warning and recommends separating their boundaries

### Requirement: Backward-compatible ad-hoc operation
Projects without `.mase/gates.yaml` SHALL remain readable and SHALL be allowed to use the legacy explicit-command runner with a compatibility warning, while new planning and candidate guarantees remain unavailable until migration.

#### Scenario: Legacy project runs a gate
- **WHEN** an existing project without a gate definition file invokes `mase gate run GATE -- COMMAND`
- **THEN** the command executes with the existing evidence contract and the CLI reports that canonical planning/reuse is not active
