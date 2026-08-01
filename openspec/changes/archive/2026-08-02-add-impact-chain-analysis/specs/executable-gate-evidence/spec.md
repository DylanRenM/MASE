## ADDED Requirements

### Requirement: Impact gates use structured artifact evidence
Automatic impact gates SHALL bind a validated impact artifact path/digest, comparison identity, adapter identity/version, normalized inputs, affected scope, and decision to their evidence. Human architecture or risk decisions SHALL use a gate declared `mode: manual` and SHALL bind the same subject digest.

#### Scenario: Free text claims analysis completed
- **WHEN** an automatic impact gate has only a hand-written statement that all callers were checked
- **THEN** MASE reports missing valid automatic evidence and does not satisfy the gate

#### Scenario: Human approves excessive scope
- **WHEN** an authorized architecture reviewer disposes an excessive-scope blocker
- **THEN** the manual evidence records actor, subject digest, selected strategy, residual risk, and reference

### Requirement: Impact artifacts are validated during project checks
Project checking MUST validate each referenced `mase-impact-analysis/v1` artifact and MUST report safe paths, field locations, and remediation for malformed, missing, escaping, or digest-mismatched artifacts.

#### Scenario: Referenced impact artifact is missing
- **WHEN** state requires impact analysis but its referenced artifact cannot be read inside the change directory
- **THEN** project check fails that change and continues checking the remaining changes
