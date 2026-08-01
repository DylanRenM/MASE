## 1. Boundary Contract Tests

- [x] 1.1 Add failing tests for the explicit MASE top-level allowlist and generated-debris rejection
- [x] 1.2 Add failing tests that embedded product and legacy roots are absent
- [x] 1.3 Add failing test for framework-scoped root pytest configuration

## 2. Dry-run and Backup

- [x] 2.1 Record the complete dry-run classification, sizes, file counts, destinations, and collision checks
- [x] 2.2 Create and verify an external pre-migration backup archive and SHA-256 inventory
- [x] 2.3 Record the verified rollback paths and move manifest before changing repository contents

## 3. Extract Products and Non-framework Content

- [x] 3.1 Back up the pre-existing empty bazi sibling skeleton and move the complete embedded bazi product
- [x] 3.2 Move the complete story point product, including untracked database and HTML backups, to its sibling root
- [x] 3.3 Move legacy demos, history, backups, non-canonical docs/training, and obsolete presentation assets to the extraction archive
- [x] 3.4 Remove backed-up generated caches/build debris from retained MASE roots
- [x] 3.5 Verify pre/post inventories and record source absence plus destination presence

## 4. Enforce the Clean Boundary

- [x] 4.1 Implement the deterministic repository-boundary audit and concise JSON/text output
- [x] 4.2 Configure root pytest to collect only `tests/` and remove obsolete product-specific ignore rules
- [x] 4.3 Update README, framework guide, project structure, and manifest boundary guidance
- [x] 4.4 Run the boundary audit and mark the contract tests green

## 5. Final Verification

- [x] 5.1 Run root pytest and confirm only the MASE framework suite is collected
- [x] 5.2 Verify manifest installation, release Skill, and guarded V2.3 training deck
- [x] 5.3 Run strict OpenSpec validation, diff checks, and finalize the migration report
