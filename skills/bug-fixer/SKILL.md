---
name: bug-fixer
description: Diagnose a reproducible defect, repair its root cause, add regression evidence and scan the same failure pattern using a routed playbook.
---

# Bug-fixer router

## Invariants

1. Obtain RED evidence before changing behavior.
2. State a falsifiable root-cause hypothesis.
3. Fix the cause, not only the visible symptom.
4. Add regression coverage and scan the same pattern.
5. Preserve user changes and back up before destructive recovery.

## Triage

| Signal | Load from `references/routes.md` |
|---|---|
| Crash/exception | Crash route |
| Wrong data or state | Logic route |
| Slow/resource leak | Performance route |
| Intermittent/timing | Concurrency route |
| Machine/config-only | Environment route |
| Compile/link/package | Build route |
| Behavior matches code but not need | Requirements route |

Load `references/runtime-debugging.md` only when logs, tests and static tracing cannot isolate runtime state.

## Loop

1. Reproduce with the smallest command/test.
2. Trace input → state transition → observable failure.
3. Test the leading hypothesis against evidence.
4. Compare alternatives when blast radius is material.
5. Implement the systemic fix and run related tests.
6. Run capability regression and scan similar code.
7. Record an incident only for P0/P1, repeated or reusable defects.

After three failed fixes against the same hypothesis, stop modifying code and escalate the missing evidence or invalid design assumption.

## Output

Report root cause, evidence, fix, regression test, same-pattern scan and residual risk. Avoid narrating every unsuccessful thought.
