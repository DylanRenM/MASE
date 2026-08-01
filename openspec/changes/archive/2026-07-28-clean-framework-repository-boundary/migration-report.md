# Repository boundary migration report

Date: 2026-07-28

## Dry-run

Destination root: `/Users/dylanren/Documents/trae_projects`

| Class | Source | Destination | Dry-run result |
|---|---|---|---|
| Product | `MASE/bazi-encyclopedia` (40 files, 348 KiB) | `bazi-encyclopedia` | Destination contains only empty directories and `.DS_Store`; safe after skeleton backup |
| Product | `MASE/story point` (106 files, 880 KiB) | `story point` | Destination absent; includes untracked DB and two HTML backups |
| Legacy/archive | `.backup`, `.frontend-slides`, `.mase-backup`, `framework`, `history`, `index.html` | `MASE-repository-extract-20260728/repository/` | Destination absent |
| Non-canonical docs | `docs/archive`, `docs/superpowers`, two obsolete articles | `MASE-repository-extract-20260728/repository/docs/` | Destination absent |
| Non-MASE/old training | `training/ai4se`, `training/skills`, `training/measures-training.html`, three obsolete deck variants | `MASE-repository-extract-20260728/repository/training/` | Destination absent |
| Generated | `build`, `mase.egg-info`, `node_modules`, `.pytest_cache`, `.DS_Store`, nested `.DS_Store`/`__pycache__`/`.pyc` | `MASE-repository-extract-20260728/generated/` | Reproducible; externally preserved before removal |

Dry-run collision checks passed. The pre-existing sibling bazi skeleton has zero regular files other than `.DS_Store`.

## Backup and rollback readiness

- Backup: `/Users/dylanren/Documents/trae_projects/MASE-pre-cleanup-20260728.tar.gz`
- Backup size: 53 MiB
- Backup SHA-256: `5ce73300c5d21c44bb74639d2ab4904227180f9b40cb13abf693d2e22f2c9e86`
- Archive verification: `tar -tzf` passed; 2,378 entries
- Pre-migration inventory: 1,942 files at `MASE-repository-extract-20260728/migration/pre-migration-files.sha256`
- Inventory-file SHA-256: `25845ce7340c0c3aa5697552461591d901a008b58ee0a6c9e16431eefc96c387`

Rollback: stop if a MASE source path or product destination is unexpectedly populated; move extracted relative paths back only into empty targets. If a moved source cannot be restored directly, extract the verified backup into a separate staging directory, validate its inventory, and copy only the required path. Never overwrite either sibling product.

## Move results

- `bazi-encyclopedia`: moved to sibling root; 40/40 files; pre/post per-file SHA-256 manifests are identical. Manifest SHA-256: `b9770c7d57767ef312176712a498e0c150479c5d61cb2d3ca14e90c3979a5e5a`.
- Pre-existing empty bazi skeleton: preserved at `MASE-repository-extract-20260728/preexisting-bazi-skeleton`.
- `story point`: moved to sibling root; 106/106 files; pre/post per-file SHA-256 manifests are identical, including `data/story_point.db` and two HTML backups. Manifest SHA-256: `e17e640c8e76682f9c95cc35461f7330f5807526590f25ff1f77cf9860434f31`.
- Non-canonical repository assets: 779/779 files moved with identical per-file SHA-256 values. Manifest SHA-256: `6af66ccd3d6dc91a92a300d03e2e82f495c838619c3c8eae2b8c6dd788098257`.
- Generated debris: 814 files preserved under `MASE-repository-extract-20260728/generated`; pytest cache generation is disabled for the framework suite.
- External extraction archive size: 113 MiB. Both original MASE product roots and every classified legacy source are absent; all recorded destinations are present.
- Repository-boundary audit after migration: `ok=true`, zero issues.

## Validation

- Default root command `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q`: 150 passed; collection is limited to MASE `tests/`.
- Repository-boundary contract tests: 4 passed, including unknown-root and strict generated-debris rejection.
- Strict repository audit after final metadata extraction: `ok=true`, zero issues.
- Manifest installation + release governance + training focused set: 24 passed.
- `release-software` Skill validation: valid; deterministic generator smoke passed.
- V2.3 deck verification: 37 slides, 416 editable text shapes, zero geometry/logo/canvas issues.
- `openspec validate clean-framework-repository-boundary --strict`: valid.
- `git diff --check`: passed.
