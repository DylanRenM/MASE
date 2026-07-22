## MODIFIED Requirements

### Requirement: Backward-compatible ad-hoc operation
Projects without `.mase/gates.yaml` SHALL remain readable and SHALL be allowed to use the legacy explicit-command runner with a compatibility diagnostic that explicitly lists unavailable canonical planning, candidate freeze, exact execution reuse, cross-gate coverage and overlap diagnostics; the project MUST NOT be described as receiving these guarantees until migration.

#### Scenario: Legacy project runs a gate
- **WHEN** an existing project without a gate definition file invokes `mase gate run GATE -- COMMAND`
- **THEN** the command executes with the existing evidence contract and the CLI reports that canonical planning, candidate freeze and execution reuse are not active

#### Scenario: Legacy project runs project check
- **WHEN** `mase check` inspects a project without non-empty canonical gate definitions
- **THEN** the report remains backward compatible but identifies each unavailable optimization capability and points to `mase update --dry-run`
