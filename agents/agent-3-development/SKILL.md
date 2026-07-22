---
name: agent-3-development
description: MASE v2 development agent — risk-driven design and boundary-tiered TDD using minimal task context.
---

# Agent 3 — Development

## Context route

For each work package read only its `reads`: current Spec, related public interfaces, relevant tests, current diff and latest handoff. Load architecture, historical changes or Skill references only when the task routes to them.

## Risk-first design

1. Reuse proven platform/library capability before introducing dependencies.
2. Run a repeatable POC only for unknown toolchains, external dependencies or high-risk behavior.
3. Create artifacts required by the effective Profile:
   - Lite: change + Specs + tasks.
   - Standard: add focused design and API/public protocol contract.
   - Strict: add feasibility, architecture and detailed design.
4. Do not maintain `openspec/master/` during build.

## TDD boundaries

### Micro loop

1. Write the smallest failing behavior or contract test and observe RED.
2. Implement the minimal coherent behavior with required runtime boundary checks.
3. Run related unit and contract tests; refactor while green.

### Capability boundary

Run relevant integration tests, code review and risk-triggered security review. Do not perform a deep security review solely because the base Profile is Standard. Commit a reversible vertical work package.

### Final boundary

Run the Profile's full unit/integration/contract suite and applicable UI P0 E2E. Full E2E is not required after every low-level Scenario unless Strict/risk policy says so.

## Completion evidence

Record command, result, timestamp and report path in `mase-state.yaml`. Generated verification summaries may present this evidence but never replace it.
