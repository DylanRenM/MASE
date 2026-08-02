# evidence-and-candidate-binding Specification

## Purpose
TBD - created by archiving change close-mase-governance-and-safety-gaps. Update Purpose after archive.
## Requirements
### Requirement: Gate definitions declare evidence mode
Every gate MUST declare or resolve to an explicit `automatic` or `manual` mode, and manual evidence MUST be accepted only for a GateDefinition declared manual.

#### Scenario: Undeclared manual gate evidence is submitted
- **WHEN** manual evidence targets a gate that is absent or automatic in `.mase/gates.yaml`
- **THEN** evidence recording fails without changing gate status

### Requirement: Manual evidence binds to its complete subject
Manual evidence MUST include a normalized digest of relevant inputs, scope, candidate, release subject, reviewer, and decision, and MUST become stale when any bound component changes.

#### Scenario: Source changes after manual review
- **WHEN** a manual review passed and a bound input subsequently changes
- **THEN** the evidence no longer satisfies the gate

#### Scenario: Release candidate changes after approval
- **WHEN** manual release evidence refers to an earlier candidate or release digest
- **THEN** it cannot satisfy the current release gate

### Requirement: Candidate readiness requires final evidence
Candidate readiness MUST require a frozen candidate with fresh final evidence for the same normalized input set and MUST NOT be inferred from the presence of a candidate object alone.

#### Scenario: Candidate object has no final run
- **WHEN** state contains candidate metadata but no fresh final gate evidence bound to it
- **THEN** status does not report `candidate_ready`

### Requirement: Evidence origins are trustworthy
Automatic passed evidence MUST be produced by Gate Runner, stored with the complete execution signature and log identity, and invalidated when command, environment inputs, test set, candidate, artifact, or release subject changes.

#### Scenario: Raw gate label claims passed
- **WHEN** a state file contains `passed` without a corresponding valid evidence record
- **THEN** the gate remains unsatisfied
