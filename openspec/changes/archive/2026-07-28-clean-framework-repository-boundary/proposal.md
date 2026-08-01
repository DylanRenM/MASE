## Why

MASE is a process-framework repository, but it currently contains complete product projects, product data, legacy research/demo assets, backups, and generated build/cache directories. These unrelated roots contaminate test discovery, make repository scope ambiguous, and contradict the framework rule that adopting products live in independent project roots and Git repositories.

## What Changes

- **BREAKING**: Move the embedded `bazi-encyclopedia/` and `story point/` products out of the MASE repository into sibling project roots, preserving all tracked and untracked product files.
- Move non-canonical legacy/demo/backup roots (`framework/`, `history/`, `.frontend-slides/`, `.backup/`, and the legacy top-level presentation) to a timestamped sibling extraction archive rather than deleting them.
- Move reproducible local build/cache artifacts out of the repository during migration so the resulting working tree is physically clean.
- Add a deterministic repository-boundary audit with an explicit allowlist for MASE top-level files/directories and tests that prevent products or unrelated roots from returning.
- Update repository guidance and test discovery so root-level validation executes only the MASE framework suite.
- Perform a dry-run inventory, collision check, backup manifest, post-move checksums, framework tests, and destination verification before considering the migration complete.

## Capabilities

### New Capabilities

- `framework-repository-boundary`: Define and automatically enforce which top-level files and directories belong in the MASE process-framework repository, including safe extraction behavior for embedded products and non-canonical assets.

### Modified Capabilities

None.

## Impact

- Removes product and non-canonical tracked paths from the MASE Git worktree while preserving their contents outside it.
- Affects repository layout, `.gitignore`, `pyproject.toml`, framework documentation, boundary-audit scripts/tests, and Git status.
- Uses `/Users/dylanren/Documents/trae_projects/` as the sibling project/extraction root. The pre-existing empty `bazi-encyclopedia/` skeleton must be backed up before the complete embedded project replaces it; existing non-empty destinations must block migration.
- Does not alter MASE runtime APIs, release governance, training materials, or the content of extracted product projects.
