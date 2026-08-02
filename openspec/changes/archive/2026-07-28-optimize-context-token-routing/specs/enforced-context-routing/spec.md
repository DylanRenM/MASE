## ADDED Requirements

### Requirement: Auditable context plan
MASE SHALL generate a context plan before Agent file loading that lists included files, excluded candidates, reasons, Profile budget and proxy measurements without concatenating the file contents.

#### Scenario: Standard change plans relevant context
- **WHEN** a Standard change declares impact paths and the caller supplies related interface and test paths
- **THEN** the plan includes current Specs/tasks, eligible impact files and explicit reads with a reason for each entry

### Requirement: Default exclusion enforcement
MASE MUST exclude framework evidence, OpenSpec archives, generated reports, logs, product data, dependency caches and other manifest exclusions from automatic context discovery.

#### Scenario: Evidence log is discovered through a broad path
- **WHEN** an impact path or explicit glob reaches `.mase/evidence` without an override
- **THEN** the plan rejects the log, reports the matching exclusion rule and does not count its contents in the context pack

### Requirement: Soft Profile context budgets
MASE SHALL provide Profile-specific context budgets and SHALL report budget overflow before Agent loading; proxy-only measurements MUST NOT be labeled as actual Token usage.

#### Scenario: Platform usage is unavailable
- **WHEN** the plan can count files and characters but has no tokenizer or platform usage
- **THEN** it reports a context proxy and an overflow warning without claiming a Token count

### Requirement: Platform token telemetry precedence
MASE SHALL accept actual input, output and cache Token usage from explicit CLI values, a usage JSON file or documented environment variables using deterministic precedence.

#### Scenario: Usage JSON and environment are both present
- **WHEN** a usage JSON file and Token environment variables provide values but no explicit CLI Token values are supplied
- **THEN** metrics uses the usage JSON values and identifies them as actual platform Tokens
