## Context

The MASE root mixes the process framework with two products, an ignored product backup, non-canonical research/presentation trees, unrelated training families, historical documentation, and reproducible caches/build outputs. Root `pytest` therefore discovers product tests and fails before running the framework suite. Some paths are tracked (`story point/`, `framework/`, `history/`, `.frontend-slides/`, legacy documentation); others are ignored or untracked (`bazi-encyclopedia/`, `.backup/`, product databases/backups, caches).

The sibling `/Users/dylanren/Documents/trae_projects/bazi-encyclopedia/` already exists but contains only empty directories and `.DS_Store`; `/Users/dylanren/Documents/trae_projects/story point/` is available. The migration must preserve dirty product files and must not overwrite an unexplained destination.

## Goals / Non-Goals

**Goals:**

- Leave MASE with only its current process-framework runtime, canonical documentation, framework training pipeline/materials, tests, and governance metadata.
- Preserve embedded products and non-canonical source assets outside MASE with checksums and a rollback path.
- Make repository scope executable through an allowlist audit and root test-discovery configuration.
- Keep all unrelated pre-existing MASE changes intact.

**Non-Goals:**

- Refactor, test, rename, or initialize Git repositories for the extracted products.
- Delete extracted legacy assets or decide their long-term archival policy.
- Remove MASE-specific training, OpenSpec history, local gate evidence, or required V1/V2.3 training sources.
- Archive unrelated completed OpenSpec changes.

## Decisions

### 1. Use an explicit top-level allowlist

Add a deterministic audit that allows only MASE roots: `.git`, `.github`, `.mase`, `agents`, `docs`, `mase_cli`, `openspec`, `profiles`, `schemas`, `scripts`, `skills`, `templates`, `tests`, and `training`, plus named framework files. Reject every unknown top-level entry and recursively reject generated debris such as `.DS_Store`, `__pycache__`, and `.pytest_cache`.

Alternative considered: deny only known product names. Rejected because a new unrelated project could return under a different name without failing.

### 2. Preserve only canonical/current material inside broad documentation roots

Keep manifest-routed documentation and `training/mase-framework/` resources required by the guarded deck pipeline. Extract legacy `docs/archive`, `docs/superpowers`, obsolete articles, non-MASE `training/ai4se`, general `training/skills`, and the legacy training HTML. Keep the V1 PPTX template, V2.3 YAML/PPTX, current outline, and supporting MASE deck files required or intentionally current; extract redundant pre-V1 deck variants that are not referenced by tests/build scripts.

Alternative considered: retain all content because it is loosely related to AI engineering. Rejected because the requested boundary is the MASE framework itself, not a general knowledge archive.

### 3. Move products to sibling project roots and everything else to an extraction archive

- Move embedded `bazi-encyclopedia/` to `../bazi-encyclopedia/` after moving the pre-existing empty skeleton into the extraction archive.
- Move `story point/` to `../story point/`, preserving its untracked database and HTML backups.
- Move non-canonical and generated roots into `../MASE-repository-extract-20260728/` with their relative paths preserved.
- Create a compressed pre-migration backup and SHA-256 inventory outside MASE before the first move.

Alternative considered: delete tracked product paths and trust Git. Rejected because ignored/untracked product state would be lost and Git does not protect it.

### 4. Make root pytest framework-scoped

Set pytest `testpaths = ["tests"]` in `pyproject.toml`. This expresses the framework boundary even if a developer temporarily places another directory beside it and makes the default test command deterministic.

Alternative considered: rely only on physical cleanup. Rejected because test discovery should encode ownership rather than depend on perpetual manual discipline.

### 5. Record migration evidence in the change

Store a small migration report in this OpenSpec change containing source/destination paths, backup archive/checksum, inventory checksum, move results, post-move audit, and framework test results. Do not store product content or large generated logs in MASE.

## Risks / Trade-offs

- [Risk] The sibling bazi skeleton hides meaningful files. → Require it to contain no regular files except `.DS_Store`; otherwise stop. Back it up before replacement.
- [Risk] Moving tracked paths creates a large deletion diff. → Expected and auditable; preserve content externally and verify file inventories before/after.
- [Risk] A legacy document is still useful. → Preserve it in the extraction archive and record the destination; do not delete it.
- [Risk] Generated caches contain transient state. → Include them in the pre-migration backup or extraction archive, while relying on package managers/build tools for future regeneration.
- [Risk] Dirty framework work overlaps cleanup. → Move only classified paths and make minimal edits to `.gitignore`, `pyproject.toml`, docs, tests, and the new audit script.

## Migration Plan

1. Add failing allowlist/test-discovery tests.
2. Produce a dry-run inventory with file counts, sizes, destination collision checks, and planned actions.
3. Create an external compressed backup and SHA-256 inventory for every source path; verify the archive is readable.
4. Back up the empty sibling bazi skeleton, then move both products and verify source absence/destination inventories.
5. Move non-canonical sources to the extraction archive; remove backed-up generated debris from all retained roots.
6. Add the boundary auditor, update repository guidance/configuration, and run it.
7. Run root pytest, the guarded training verifier, Skill validation, manifest installation tests, and OpenSpec validation.

Rollback moves extracted paths back to their recorded relative locations after confirming MASE targets are empty, or restores them from the verified backup archive. Product destinations must never be overwritten during rollback.

## Open Questions

None. The sibling project root and timestamped extraction archive provide deterministic destinations without changing product content.
