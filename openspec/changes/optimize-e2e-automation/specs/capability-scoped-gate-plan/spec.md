## MODIFIED Requirements

### Requirement: Capability-scoped gate inputs
Capability gate instances SHALL use declared capability paths and a validated test manifest to derive their default input scope and actual test selectors, and SHALL identify scope, selected test IDs, selection reasons and conservative fallback in plan and evidence output. A gate that declares dynamic test tiers MUST consume the selected selectors through its canonical command.

#### Scenario: UI-only file changes
- **WHEN** a file changes only within the UI capability paths
- **THEN** authorization capability integration evidence remains fresh while the UI's applicable evidence and selected tests are recalculated

#### Scenario: Dynamic tier is not consumed
- **WHEN** a gate declares `test_tiers` but its canonical command omits the selected-test placeholder
- **THEN** MASE rejects the gate definition instead of recording misleading selected-test evidence

### Requirement: Compatible capability declarations
The system SHALL continue accepting existing capability declarations containing only `profile` and projects without a test manifest. It SHALL use conservative change-level inputs and canonical static gate tests for those projects, and SHALL emit actionable diagnostics when triggers, paths, manifest mappings or gate definitions required for precise scoping are absent.

#### Scenario: Legacy capability profile only
- **WHEN** state declares a capability with only `profile: strict` and no test manifest exists
- **THEN** status remains valid, uses conservative change-level scope and static canonical tests, and recommends adding triggers, paths and manifest mappings rather than guessing them

## ADDED Requirements

### Requirement: Stable selected-test execution signature
The GatePlan and Gate Runner SHALL calculate the test digest from the ordered selected test IDs, selectors and manifest content relevant to the gate. Changing a selected test, selector, tier or mapping MUST invalidate otherwise fresh evidence.

#### Scenario: Selector changes without product code changes
- **WHEN** a selected P0 journey selector changes after a passed gate
- **THEN** the prior execution signature no longer matches and the gate returns to pending or stale
