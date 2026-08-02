## 1. Contract-first failing evidence

- [x] 1.1 Add framework contract tests for PBT routing, complementary examples, conditional semantics, counterexample replay, and packaged reference coverage
- [x] 1.2 Run the focused tests and confirm they fail because the current framework lacks the new guidance

## 2. Normative framework guidance

- [x] 2.1 Update the core engineering rule and framework document with risk-driven property-testing boundaries
- [x] 2.2 Extend the contract template with traceable property plans, error contracts, conditional semantic properties, and isolation requirements

## 3. Agent and Skill routing

- [x] 3.1 Update development and quality Agent guidance to route applicable properties and verify replayable counterexamples
- [x] 3.2 Update the TDD Skill to preserve deterministic examples and load a property-testing reference only when triggered
- [x] 3.3 Add a stack-neutral property-testing reference with a scoped Python/Hypothesis section and explicit rejected anti-patterns

## 4. Distribution and generated adapters

- [x] 4.1 Verify the new reference is included by runtime/package manifests and add explicit distribution coverage where needed
- [x] 4.2 Regenerate IDE adapters from `project-rules.md` without overwriting unrelated user files

## 5. Verification

- [x] 5.1 Run focused framework contract tests and confirm the new behavior is green
- [x] 5.2 Run the full MASE test suite and OpenSpec validation, then review the final diff for rejected absolute rules and unrelated changes
