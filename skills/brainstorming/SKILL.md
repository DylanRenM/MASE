---
name: brainstorming
description: Reconcile supplied requirements and turn unresolved product decisions into a concise, confirmed behavior model.
---

# Requirements discovery router

## Use when

- User intent or success criteria are unclear.
- Uploaded requirement, prototype and test sources conflict.
- A decision materially changes scope, behavior, risk or architecture.

Do not use for a pure refactor, already-specified implementation or simple Bug diagnosis.

## Process

1. Read all supplied sources first; record which source has precedence.
2. Summarize known behavior, contradictions and missing boundaries.
3. Separate blocking decisions from defaults that can be safely documented.
4. Ask 3–5 related questions in one batch, recommended option first.
5. For UI behavior, produce a reference prototype and obtain confirmation.
6. Capture acceptance behavior once in Specs with stable IDs.

## Question budget

- Do not ask for information available in the repository or environment.
- Do not ask one question per turn when decisions are independent.
- Continue with stated defaults for non-blocking choices.
- Stop and wait only when guessing would materially change the result or require new authority.

## Output

- Confirmed goal and out-of-scope.
- Decision/default log.
- Stable acceptance IDs and priority.
- Risks that upgrade the effective Profile.

Never duplicate complete test scenarios in both Proposal and Specs.
