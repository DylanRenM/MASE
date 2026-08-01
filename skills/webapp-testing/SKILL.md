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

1. Map stable Spec Scenario IDs to `.mase/tests.yaml` IDs, Capability paths and tiers.
2. Drive behavior through user-visible roles, labels or platform accessibility IDs.
3. Classify browser checks as `ui_contract`, `p0_journey` or `p1_regression` before writing them.
4. Use deterministic fixtures and platform adapters for time/system callbacks.
5. Generate tests from Specs only as candidates; require observable business assertions, deterministic data, non-duplicate coverage and review before manifest promotion.

## Browser test tiers

| Tier | Purpose | Boundary |
|---|---|---|
| `ui_contract` | DOM semantics, local interaction, layout and request payload | May mock product APIs; never represents P0 end-to-end coverage |
| `p0_journey` | One critical user-value loop per Capability | Real UI, product routes and controlled persistence; fake only uncontrollable external services |
| `p1_regression` | Error paths, roles, compatibility and lower-frequency flows | Scheduled/PR policy; not a universal hard gate |

Page-load, element-exists and layout-only checks are not P0 journeys. Do not count a browser test that mocks the product's own API as end-to-end.

## Sandbox contract

Each E2E spec snapshots declared files/config/directories before execution, redirects writes where possible, restores afterward and verifies equality. A restore mismatch blocks later tests. Hard gates use a fresh test root and service port, never reuse a development server, and bind fixture `schema_version`, `fixture_digest` and `test_root`. Stateful parallel workers require separate data roots; otherwise run serially.

The runtime implementation belongs in a versioned sandbox package; this Skill describes the contract, not 400 lines of helper code.

## Execution

- Micro loop: no automatic full E2E.
- Capability boundary: related UI contract and journey selected from changed Capability paths.
- Verify: selected P0 journeys are a 100% hard gate when UI changed; an unmapped UI path conservatively selects all P0 journeys. P1 follows Profile/project schedule.
- Failure: write `mase-test-diagnostic/v1`, preserve trace/screenshot/video/log evidence, then route product failures to bug-fixer.
- Retry: a retry pass is `flaky`, not a first-attempt pass. Do not auto-ignore it or silently update selectors/baselines.

## Output

Generate a machine-readable Scenario→test→result mapping plus attempts, first/final result, failure classification and artifacts. Human summaries are derived evidence, not a second status source. Track first-pass rate, flaky rate, P0 duration, Capability journey coverage, classified-failure rate and explicitly sourced manual regression time.
