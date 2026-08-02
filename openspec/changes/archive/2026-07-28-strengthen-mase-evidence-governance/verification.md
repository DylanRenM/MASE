# Verification evidence

Date: 2026-07-21 (Asia/Shanghai)

## Framework gates

- `python3 -m pytest -q tests`: **86 passed** after the Pilot-driven missing-state and failed-hard-gate diagnostics were added.
- `npm test`: **1 file / 9 tests passed**.
- `openspec validate strengthen-mase-evidence-governance --strict`: **valid**.
- `python3 -m mase_cli.main check --dir .`: **PASS**, both migrated historical states validate.
- `python3 -m mase_cli.main update --dry-run --dir .`: **zero changes** after self-migration.
- `mase status --json`: stable portfolio JSON and exit code **1** because two completed historical changes now correctly expose migrated legacy evidence as stale; no diagnostics or traceback.
- `git diff --check`: **passed**.

## Packaging smoke

- Built `mase-2.1.0-py3-none-any.whl` with Python 3.12 in offline mode.
- Installed that wheel into an isolated Python 3.9 environment with the locally available runtime dependencies.
- Confirmed the imported module came from the isolated environment, `mase --version` returned `2.1.0`, `mase doctor --stack generic` passed, and an installed CLI discovered its packaged `share/mase` runtime for `mase install --dry-run`.
- Direct dependency download through the machine's configured Tsinghua PyPI mirror returned HTTP 403. The successful offline smoke therefore used the local build cache; `requirements-offline.txt` documents the reproducible wheel-bundle path.

## Migration and rollback rehearsals

- MASE self-migration: backup created, schema check passed, second migration plan empty.
- 磨耳朵 isolated copy: 10 governance changes planned; 5 malformed/invalid states preserved as conflicts; all applicable changes became idempotent; rollback restored every updated governance file byte-for-byte.
- Synthetic Brownfield fixture: approved baseline ownership, expiry, remediation and bytes survived metadata/state migration unchanged.

## Repository-boundary note

An unscoped `python3 -m pytest -q` also collects embedded product directories. It currently stops on 14 import/collection errors under `bazi-encyclopedia/` and the concurrently developed `story point/`; those are not MASE framework tests. The authoritative framework gate is the explicit `tests/` suite above, consistent with the repository's product-boundary rule.
