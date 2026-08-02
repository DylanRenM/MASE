---
name: git-commit
description: Create a safe Conventional Commit for one reversible work package while preserving unrelated user changes.
license: MIT
allowed-tools: Bash
---

# Git commit router

## Boundary

Commit after a vertical work package or Capability is verified—not after an arbitrary number of conversations. Keep unrelated user changes unstaged.

## Procedure

1. Inspect status, staged diff and unstaged diff.
2. Identify the exact files belonging to the verified work package.
3. Scan for secrets, generated artifacts and accidental large binaries.
4. Stage only those paths.
5. Use `<type>(<scope>): <imperative description>` with a concise body when behavior, migration or evidence needs explanation.
6. Run relevant hooks/tests; never use `--no-verify` without explicit user instruction.

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `ci`, `chore`, `revert`.

## Safety

- Never change Git configuration, force push, hard reset or amend published history without authority.
- Never stage `.env`, credentials, private keys, local telemetry or user files outside scope.
- If hooks fail, fix the cause and create a new commit attempt; do not hide the failure.
