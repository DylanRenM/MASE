# RED-GREEN-REFACTOR reference

## RED

Use one behavior and a descriptive name. Confirm the assertion fails for the intended missing behavior.

## GREEN

Implement the smallest coherent production path. Do not weaken the assertion, skip the test or special-case the fixture.

## REFACTOR

Remove duplication, clarify ownership and preserve public behavior. Re-run the related suite after each structural step.

## When stuck

Shrink the behavior, replace time/I/O with deterministic adapters, verify test ownership and inspect the first failure rather than adding broad mocks.
