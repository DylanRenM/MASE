# Review modes

## Diff-only

Trace changed inputs, branches, state mutations, errors and tests. One pass; no parallel reviewers.

## Capability-boundary

Add public API compatibility, integration ownership, cancellation/resource lifecycle, security attack-surface triage and Spec coverage.

## Independent multi-round

Use separate passes for behavior/contracts, concurrency/resources, security/privacy and tests/operations. Deduplicate findings before reporting.

## Language references

Load language-specific standards only for the files in scope. Prefer compiler, formatter and static-analysis evidence over model-generated style commentary.
