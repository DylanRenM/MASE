## ADDED Requirements

### Requirement: Release gates require an applicable overlay
The Gate Runner MUST treat a release gate as runnable only when the active change has a valid Release Overlay, the gate is selected by that overlay and current GatePlan, and the overlay intent permits the gate stage.

#### Scenario: Gate is absent from the overlay
- **WHEN** a release gate exists in `.mase/gates.yaml` but is not selected by the active Release Overlay
- **THEN** the Gate Runner rejects execution without invoking the command

#### Scenario: Intent stops before live release
- **WHEN** the overlay intent permits artifact or preflight work but a live or observe gate is requested
- **THEN** the Gate Runner rejects execution and reports the incompatible intent and stage

### Requirement: Effectful release gates require authority
Every release GateDefinition MUST explicitly declare its execution effect and required authority, and the Gate Runner MUST reject an effectful gate when the current authority is insufficient.

#### Scenario: Read-only authority requests a live gate
- **WHEN** current authority is `read-only` and a live release gate can modify files, infrastructure, traffic, or external state
- **THEN** the Gate Runner does not execute the command and records no passed evidence

### Requirement: Release stages are ordered and bound
The Gate Runner MUST enforce artifact, preflight, live, and observe predecessor requirements and MUST bind each accepted result to the required immutable candidate, artifact, target, and release subject digests.

#### Scenario: Live gate lacks preflight evidence
- **WHEN** a live gate is requested without fresh required artifact and preflight evidence for the same release subject
- **THEN** execution is rejected as not ready

#### Scenario: Candidate or artifact changes
- **WHEN** a predecessor result refers to a different candidate or artifact digest
- **THEN** it does not satisfy the requested release gate

### Requirement: Release completion uses distinct states
The system MUST preserve the distinct meanings of `candidate_ready`, `artifact_ready`, `target_ready`, `live_verified`, and `observed`, and MUST NOT report release success from process or health-check liveness alone.

#### Scenario: Artifact exists but target is not verified
- **WHEN** artifact evidence is fresh but target, live, or observation evidence is absent
- **THEN** status reports only the stages actually satisfied
