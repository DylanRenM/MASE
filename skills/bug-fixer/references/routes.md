# Bug routes

## Crash route

Capture the first meaningful exception, minimal trigger and boundary that allowed invalid state. Test the rejected boundary before repairing it.

## Logic route

Compare expected Spec transition with actual state/data flow. Check stale state, ordering, identity, defaults, serialization and error recovery.

## Performance route

Measure a baseline and isolate CPU, allocation, I/O, contention or algorithmic growth. Require before/after evidence and a regression threshold.

## Concurrency route

Build a timeline. Identify ownership, cancellation, token/identity checks, late callbacks and non-atomic publication. Reproduce with deterministic clocks/adapters where possible.

## Environment route

Compare working and failing environments: executable, version, SDK, permissions, variables, paths and filesystem. Prefer a diagnostic command over code changes.

## Build route

Start with the first compiler/linker/package error. Verify toolchain selection and cached artifacts before changing source.

## Requirements route

When implementation matches the written Spec, stop coding and resolve the requirement conflict. Update acceptance behavior before tests and implementation.
