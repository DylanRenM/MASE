## ADDED Requirements

### Requirement: Historical behavior changes require impact classification
MASE MUST classify modification, deletion, rename, replacement, or rerouting of historical runtime code, contract material, configuration, schema, message, or persistence behavior before design/build. Only comments, formatting, and non-machine-consumed wording with no behavioral effect MAY be exempt, and the exemption MUST be evidence-backed.

#### Scenario: Historical implementation is modified
- **WHEN** a change modifies runtime code present in the comparison baseline
- **THEN** MASE requires impact analysis before design/build proceeds

#### Scenario: Pure formatting change is exempt
- **WHEN** a classifier proves the diff contains only formatting with no runtime, contract, observability, or test-coverage effect
- **THEN** MASE records a structured exemption and does not require caller traversal

#### Scenario: Machine-consumed log text changes
- **WHEN** modified log content is used by monitoring, audit, alerting, or another program
- **THEN** MASE treats the change as behavioral and does not allow the wording exemption

### Requirement: Explicit and implicit dependency channels are recorded
Impact analysis SHALL record discovered explicit callers and SHALL separately report checks for serialization, proxy/AOP, reflection, configuration/SPI, dependency injection, messages/events, scheduled jobs, asynchronous callbacks, persistence formats, cache keys, templates, and generated registrations. It MUST distinguish discovered, checked-empty, unverified, and out-of-repository channels.

#### Scenario: Reflection cannot be resolved statically
- **WHEN** a modified type may be loaded from a runtime-computed class name
- **THEN** the artifact records the reflection channel as unverified with residual risk instead of claiming all callers were found

### Requirement: Traversal is bounded with explicit termination
Internal implementation changes that preserve signature, business semantics, exceptions, side effects, idempotency, concurrency, transaction, cache, persistence, timeout, and retry behavior MAY stop at direct callers. Contract or semantic changes MUST traverse toward system boundaries and MUST record the termination reason for every branch.

#### Scenario: Business semantics change without signature change
- **WHEN** identical inputs can produce different business results after the modification
- **THEN** MASE classifies the edit as a semantic contract change and recursively traces affected callers

#### Scenario: Depth three does not reach a boundary
- **WHEN** traversal reaches depth three without reaching a system or repository boundary
- **THEN** MASE stops automatic recursion, emits an architecture-coupling alert, upgrades the impact to at least L2, and requires human disposition

### Requirement: Impact level deterministically selects verification
MASE SHALL classify each affected scope as L1, L2, or L3 and SHALL derive mandatory tests/reviews without reducing Profile or risk gates. Unknown call frequency or unresolved implicit channels MUST NOT qualify as L1.

#### Scenario: Non-core internal implementation change
- **WHEN** semantics and side effects are unchanged, low frequency is evidenced, and no implicit channel is unresolved
- **THEN** L1 requires affected-caller unit tests and differential contract tests

#### Scenario: Core-path implementation change
- **WHEN** an internal change affects a core path or has unknown frequency
- **THEN** L2 additionally requires applicable integration verification plus AI impact summary and human review

#### Scenario: Public contract reaches a system boundary
- **WHEN** a public contract or business semantic change affects a system boundary
- **THEN** L3 additionally requires architecture review, full-chain smoke, rollout/stop conditions, and rollback readiness

### Requirement: Excessive scope blocks AI-autonomous continuation
MASE MUST require human architecture disposition when unique first-party callers exceed 10, system boundaries are at least 3, depth-three traversal remains unresolved, or hidden dependency risk is uncontrolled. AI MUST NOT approve or continue implementation autonomously in this state.

#### Scenario: DTO affects many consumers
- **WHEN** one data-contract edit affects 11 first-party callers
- **THEN** the decision becomes `architecture-review-required` and offers version isolation, feature flag, split change, or termination

### Requirement: Planned impact is reconciled with the actual diff
MASE MUST perform impact reconciliation after implementation and before verification. New change points, callers, boundaries, semantic differences, or implicit channels not covered by the approved plan MUST make prior analysis and review evidence stale.

#### Scenario: Implementation changes an additional helper
- **WHEN** the actual diff modifies a historical helper absent from the approved analysis
- **THEN** reconciliation blocks verification and routes the change back to analysis/design

### Requirement: Impact outputs have one canonical source
Each analyzed change SHALL use a schema-validated `mase-impact-analysis/v1` artifact as the canonical fact source and SHALL generate an impact scope statement, test scope confirmation, and rollback plan carrying the source digest.

#### Scenario: Human-readable views are generated
- **WHEN** a valid impact artifact is rendered
- **THEN** all three views contain consistent classification, affected scope, decision, tests/recovery data, and the same source digest

### Requirement: Differential contract samples are controlled
Old/new behavior comparison MUST record fixture provenance, authorization for production-derived data, sanitization, nondeterminism normalization, side-effect isolation, and whether each difference is expected by an accepted Spec.

#### Scenario: Unexpected old/new output difference
- **WHEN** a comparison produces a difference not allowed by an accepted Spec
- **THEN** the contract-differential gate fails and reports the result as suspected collateral damage

### Requirement: Scanner adapters are language neutral
MASE SHALL validate scanner results through a versioned adapter contract and SHALL compute policy level and blockers itself. An adapter MUST NOT be able to downgrade mandatory gates by declaring a lower level.

#### Scenario: Project has no native scanner
- **WHEN** the project stack has no registered scanner adapter
- **THEN** MASE provides a structured manual/generic fallback and reports reduced confidence rather than silently passing automatic analysis
