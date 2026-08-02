---
name: project-planning-expert
description: Convert approved behavior into 15–25 dependency-aware vertical work packages with minimal context and explicit verification.
---

# Project planning router

## Input

Read the proposal/change, affected Specs, effective Profile and only Profile-required design/contracts.

## Task shape

Each task must deliver a coherent behavior or infrastructure boundary and include:

- stable ID and dependency;
- affected capability;
- `reads`: current Spec, related interfaces/tests and diff;
- `verify`: exact test or evidence command;
- risk/Profile escalation when applicable.

Use OpenSpec-compatible checkboxes:

```markdown
- [ ] 2.1 Implement reload decision behavior
  - reads: specs/source-monitoring/spec.md, related interface/tests, git diff
  - verify: related unit + integration test command
```

## Granularity

Target 15–25 vertical work packages for an MVP. Do not create separate tasks merely to run tests, review, scan, update status or commit; those are verification fields/boundaries unless they produce standalone infrastructure.

Order foundation → behavior slices → integration → final verification. Keep independent capabilities parallelizable without duplicating shared setup.
