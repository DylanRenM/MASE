---
name: test-driven-development
description: Implement behavior through observable RED-GREEN-REFACTOR cycles with test breadth selected at task, capability and final boundaries.
---

# TDD router

## Iron rule

Do not add production behavior before observing a relevant test fail for the expected reason. POC and generated-code exceptions must be explicitly identified and followed by behavior tests before acceptance.

## Micro boundary

1. Read the current Requirement/Scenario, public interface, related tests and diff.
2. Write the smallest failing behavior or contract test.
3. Run it and confirm RED is caused by missing behavior, not a broken fixture.
4. Implement the minimum coherent behavior.
5. Run related unit/contract tests and refactor while green.

Load `references/red-green-refactor.md` only when test design or cycle discipline is unclear.

## Capability boundary

Run relevant integration tests, concurrency/resource tests and risk-triggered review. Do not run unrelated UI E2E after every pure-function change.

## Final boundary

Run all tests required by the effective Profile, including applicable API contracts and UI P0 E2E. Record structured evidence in canonical state.

## Good tests

Test observable behavior, boundary values, failure atomicity and deterministic state. Avoid asserting implementation trivia, sleeps, order without a contract, or mocks that merely reproduce the implementation.
