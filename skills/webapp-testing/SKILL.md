---
name: webapp-testing
description: Cross-platform UI E2E router for Web Playwright, macOS Accessibility and future platform adapters, with P0 gates and sandbox restoration.
---

# UI E2E testing router

The directory name remains `webapp-testing` for compatibility; behavior is platform-neutral.

## Select adapter

| `ui_platform` | Reference/driver |
|---|---|
| Web | `playwright-standards.md`, Playwright page objects |
| macOS | `references/macos-accessibility.md`, AXIdentifier page objects |
| Other | Create an explicit platform adapter before E2E implementation |

Do not load Playwright guidance for macOS or native projects.

## Authoring

1. Map stable Spec Scenario IDs to P0/P1/P2 tests.
2. Drive behavior through user-visible roles, labels or platform accessibility IDs.
3. Use deterministic fixtures and platform adapters for time/system callbacks.
4. Keep P0 focused on core user value; avoid duplicating every unit boundary in E2E.

## Sandbox contract

Each E2E spec snapshots declared files/config/directories before execution, redirects writes where possible, restores afterward and verifies equality. A restore mismatch blocks later tests.

The runtime implementation belongs in a versioned sandbox package; this Skill describes the contract, not 400 lines of helper code.

## Execution

- Micro loop: no automatic full E2E.
- Capability boundary: related UI scenario when useful.
- Verify: P0 100% hard gate; P1 according to Profile/project policy.
- Failure: preserve trace/screenshot/log evidence, then route to bug-fixer.

## Output

Generate a machine-readable Scenario→test→result mapping. Human summaries are derived evidence, not a second status source.
