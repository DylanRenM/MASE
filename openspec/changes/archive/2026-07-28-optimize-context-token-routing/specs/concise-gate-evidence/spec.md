## ADDED Requirements

### Requirement: Concise Agent gate output
Gate Runner SHALL persist the complete secret-redacted output while returning only status, duration, log path and a bounded failure excerpt by default.

#### Scenario: Successful full regression in concise mode
- **WHEN** a long-running gate succeeds without verbose output requested
- **THEN** the caller receives a short completion summary and the full output remains available at the evidence log path

#### Scenario: Failed gate in concise mode
- **WHEN** a gate fails after producing a long traceback
- **THEN** the caller receives a bounded tail excerpt sufficient to route diagnosis plus the complete evidence log path

### Requirement: Explicit verbose streaming
Gate Runner SHALL support an explicit verbose mode that streams incremental output without changing evidence freshness or persisted logs.

#### Scenario: Human requests live progress
- **WHEN** the caller runs a gate with `--verbose`
- **THEN** output is streamed incrementally and the final evidence record is equivalent to concise execution of the same command
