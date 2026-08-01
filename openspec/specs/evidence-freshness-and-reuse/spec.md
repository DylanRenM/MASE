# evidence-freshness-and-reuse Specification

## Purpose
TBD - created by archiving change optimize-gate-scheduling-and-test-deduplication. Update Purpose after archive.
## Requirements
### Requirement: Effective gate state from evidence freshness
The system SHALL derive each automatic gate's effective state from its latest applicable structured evidence and current inputs, log and artifacts; a hand-written `passed` field or stale evidence MUST NOT satisfy a required automatic gate.

#### Scenario: Input changes after pass
- **WHEN** a file in the gate's canonical input set changes after a passed execution
- **THEN** `mase status` reports the gate stale, lifecycle is not ready-to-complete, and the next action is a rerun or a new candidate

#### Scenario: Newer failure follows old pass
- **WHEN** a gate passes and a later execution of the same instance fails
- **THEN** the effective state is failed even if the older passed evidence remains in audit history

#### Scenario: Newer fresh pass follows failure
- **WHEN** a later equivalent execution passes with current inputs
- **THEN** the effective state returns to passed and the older failure remains audit-only

### Requirement: Exact execution reuse
The system SHALL skip subprocess execution only when gate instance, normalized command, platform, inputs, declared test set and candidate ID match a fresh prior execution.

#### Scenario: Same gate is invoked twice unchanged
- **WHEN** a fresh gate is invoked again with the identical execution signature
- **THEN** Gate Runner returns a cache hit referencing the prior execution and does not start the test process again

#### Scenario: One execution attribute differs
- **WHEN** command, platform, input digest, test set or candidate ID differs
- **THEN** Gate Runner executes the command and records a new execution

### Requirement: Explicit cross-gate coverage
The system MUST reuse one execution across different gate names only when the canonical source gate declares the target in `covers`; derived evidence SHALL reference the same execution and log.

#### Scenario: Gate explicitly covers another
- **WHEN** a successful canonical gate declares another gate in `covers`
- **THEN** both gate instances receive traceable fresh evidence from one execution

#### Scenario: Identical gates lack covers
- **WHEN** two gate definitions happen to be identical but neither declares coverage
- **THEN** the CLI warns about duplication but does not silently mark the other gate passed

### Requirement: Streaming and redacted evidence log
Gate Runner SHALL always store a complete secret-redacted evidence log and SHALL write passed evidence only after successful completion. It SHALL return concise bounded output by default and SHALL stream subprocess output only when the caller explicitly requests verbose mode.

#### Scenario: Long-running regression uses default output
- **WHEN** a test command produces incremental output and verbose mode is not requested
- **THEN** the caller receives a bounded final summary while the persisted log contains the complete redacted output

#### Scenario: Long-running regression requests verbose output
- **WHEN** a caller explicitly requests verbose mode
- **THEN** the caller receives incremental output before completion and the persisted log contains the redacted equivalent

### Requirement: Bounded state evidence history
The system SHALL compact state evidence per gate instance to a bounded audit set while preserving log references and the latest pass/failure/replacement relationship.

#### Scenario: Gate is rerun many times
- **WHEN** more than the configured retention count exists for one gate instance
- **THEN** `mase-state.yaml` retains only the bounded relevant records and status remains determined by the latest evidence
