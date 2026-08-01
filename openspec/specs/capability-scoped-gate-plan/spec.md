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
Capability gate instances SHALL use declared capability paths and relevant test selectors as their default input scope, and SHALL identify scope in evidence and status output.

#### Scenario: UI-only file changes
- **WHEN** a file changes only within the UI capability paths
- **THEN** authorization capability integration evidence remains fresh while the UI's applicable evidence becomes stale

### Requirement: Change-level final risk floor
The system SHALL merge Capability hard-gate requirements into the change's final GatePlan so that local scoping reduces repeated development testing but cannot remove final quality gates triggered by any high-risk capability.

#### Scenario: Strict capability exists in Standard change
- **WHEN** an authorization capability is Strict inside a Standard change
- **THEN** final full regression, security and independent review remain required for the frozen change candidate

### Requirement: Compatible capability declarations
The system SHALL continue accepting existing capability declarations containing only `profile`, and SHALL emit actionable diagnostics when triggers, paths or gate definitions required for precise scoping are absent.

#### Scenario: Legacy capability profile only
- **WHEN** state declares a capability with only `profile: strict`
- **THEN** status remains valid, uses conservative change-level scope and recommends adding triggers and paths rather than guessing them
