## MODIFIED Requirements

### Requirement: Streaming and redacted evidence log
Gate Runner SHALL always store a complete secret-redacted evidence log and SHALL write passed evidence only after successful completion. It SHALL return concise bounded output by default and SHALL stream subprocess output only when the caller explicitly requests verbose mode.

#### Scenario: Long-running regression uses default output
- **WHEN** a test command produces incremental output and verbose mode is not requested
- **THEN** the caller receives a bounded final summary while the persisted log contains the complete redacted output

#### Scenario: Long-running regression requests verbose output
- **WHEN** a caller explicitly requests verbose mode
- **THEN** the caller receives incremental output before completion and the persisted log contains the redacted equivalent
