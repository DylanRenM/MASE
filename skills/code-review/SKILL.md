---
name: code-review
description: Evidence-based review of a scoped diff against affected Specs, contracts and repository conventions, with depth selected by Profile and risk.
---

# Code review router

## Context first

Read the user scope, current diff, affected Spec/contract, related interfaces and tests. Do not load unrelated capabilities, history or training material.

## Review mode

| Effective Profile/risk | Mode |
|---|---|
| Lite, small low-risk diff | diff-only single pass |
| Standard or upgraded capability | capability-boundary review |
| Strict/security/irreversible change | independent multi-round review |

Mode details are in `references/review-modes.md`; load only the selected section.

## Finding requirements

A finding must include:

- severity and confidence;
- exact file/line;
- concrete failing behavior or reachable risk;
- violated Spec, contract or invariant;
- smallest coherent remedy and missing test.

Do not report style preferences, pre-existing out-of-scope issues, speculative vulnerabilities or behavior already enforced by the language/framework.

## Severity

- P0: data loss, security compromise, crash/core acceptance failure.
- P1: reachable incorrect behavior, race, resource leak or contract breach.
- P2: maintainability issue with concrete future failure path.

## Output

Lead with findings ordered P0→P2. If clean, say so and list residual validation limits. Do not rewrite the diff or repeat the entire design.
