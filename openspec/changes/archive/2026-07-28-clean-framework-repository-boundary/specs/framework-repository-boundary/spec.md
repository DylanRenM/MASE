## ADDED Requirements

### Requirement: MASE repository contains only framework-owned roots
The MASE repository MUST enforce an explicit allowlist of top-level files and directories belonging to the process framework and MUST reject embedded products, unrelated archives, demos, and unknown roots.

#### Scenario: Embedded product exists at repository root
- **WHEN** a product directory such as `bazi-encyclopedia` or `story point` exists under MASE
- **THEN** the repository-boundary audit exits non-zero and identifies the unexpected root

#### Scenario: Current framework layout is audited
- **WHEN** only canonical MASE runtime, governance, documentation, training, and test roots remain
- **THEN** the audit exits successfully with no unexpected top-level entries

### Requirement: Repository cleanup is non-destructive
The migration MUST create and verify an external backup and inventory before moving or removing content, MUST preserve tracked and untracked product files, and MUST stop on unexplained destination conflicts.

#### Scenario: Product has untracked state
- **WHEN** an embedded product contains a database, backup, ignored file, or other untracked state
- **THEN** the migration inventory includes it and the destination contains the same file after extraction

#### Scenario: Destination contains meaningful content
- **WHEN** a planned sibling destination contains a regular file not explicitly classified as an empty skeleton artifact
- **THEN** migration stops without overwriting the destination

### Requirement: Non-canonical assets remain recoverable outside MASE
Legacy documentation, research/demo sites, unrelated training families, old presentations, and repository backups MUST be moved to a timestamped extraction archive rather than silently deleted.

#### Scenario: Legacy material is extracted
- **WHEN** cleanup completes
- **THEN** each classified source is absent from MASE, present under the recorded extraction archive, and represented in the migration report

### Requirement: Generated debris does not pollute retained framework roots
The repository MUST reject reproducible local build/cache debris, `.DS_Store`, `__pycache__`, and pytest cache entries from retained framework paths.

#### Scenario: Generated cache reappears
- **WHEN** a rejected generated entry exists during an audit
- **THEN** the audit exits non-zero and reports its repository-relative path

### Requirement: Default validation is framework-scoped
The default root pytest configuration SHALL collect the MASE framework suite from `tests/` and SHALL not depend on external product import environments.

#### Scenario: Developer runs pytest at MASE root
- **WHEN** `python3 -m pytest -q` is executed after cleanup
- **THEN** pytest collects and runs only the MASE framework tests

### Requirement: Framework training and runtime remain intact
Cleanup MUST retain manifest-routed runtime resources and the guarded MASE V2.3 training source, required V1 template, and generated editable PPTX.

#### Scenario: Cleanup validation completes
- **WHEN** products and legacy assets have been extracted
- **THEN** runtime installation tests, MASE tests, Skill validation, and the 37-slide editable deck verification still pass
