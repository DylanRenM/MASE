## ADDED Requirements

### Requirement: Profiles compile into executable GatePlans
The system MUST compile base and capability Profile requirements for artifacts, gates, reviews, test schedules, and final verification into one GatePlan and MUST use that plan for check, status, and execution decisions.

#### Scenario: Standard capability reaches final verification
- **WHEN** a Standard change has related, integration, review, and final schedule requirements
- **THEN** completion remains blocked until each applicable requirement has fresh evidence or a valid required artifact

### Requirement: Risk escalation uses one registry
Top-level and capability risks MUST resolve through the same risk registry, apply each trigger's `minimum_profile`, and reject unknown risk identifiers with a diagnostic.

#### Scenario: Capability infrastructure change requires Strict
- **WHEN** a Lite capability declares `infrastructure_change` and the registry sets its minimum Profile to Strict
- **THEN** the effective capability and change Profile are at least Strict

#### Scenario: Risk identifier is misspelled
- **WHEN** a state file declares an identifier not present in the risk registry
- **THEN** validation fails and identifies the unknown trigger

### Requirement: Hard gates cannot be bypassed
A required hard gate MUST accept only fresh evidence from an allowed source for its complete signature and MUST NOT be satisfied by `skipped`, `passed_with_baseline`, a raw gate label, or an ordinary baseline record.

#### Scenario: API contract is skipped
- **WHEN** `api_contract` is required and state labels it `skipped`
- **THEN** consistency and lifecycle completion fail

#### Scenario: Security hard gate is offered for baseline
- **WHEN** a triggered security hard gate fails
- **THEN** baseline creation rejects it regardless of a static allow-list omission

### Requirement: Terminal lifecycle states are internally consistent
A change MUST NOT be complete or otherwise terminal while any GatePlan requirement is pending, stale, invalid, or absent.

#### Scenario: Complete phase has a pending gate
- **WHEN** phase is terminal but a required gate lacks satisfying evidence
- **THEN** status reports inconsistency and does not treat the change as complete
