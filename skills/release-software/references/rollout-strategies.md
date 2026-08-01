# Rollout strategies

Choose the strategy from target capabilities and failure economics. Always specify maximum impact, stop conditions, authority, identity verification, recovery, and observation.

## In-place

Use only when replacement is necessary or parallel capacity is unavailable. Front-load runtime, disk, configuration, staging/import, artifact, backup, and recovery checks. Minimize the interval between stop and verified restart.

## Rolling

Require compatible mixed versions, readiness that tests serving ability, bounded unavailable/surge capacity, and per-wave observation. Stop on identity mismatch, readiness failure, or threshold breach.

## Blue-green / immutable

Verify the inactive environment with the final artifact, then switch a reversible routing pointer. Preserve the prior environment until observation completes. Account for shared state and irreversible migrations.

## Canary

Define cohort, percentage/capacity, comparison baseline, signals, thresholds, window, and automatic/manual stop owner. No observation signals means no canary.

## Phased clients or stores

Account for review delay, propagation, offline clients, version skew, protocol compatibility, and limited rollback. Prefer server-side compatibility and kill switches. Verify store/build identity and each phase before expansion.

## Registry publication

Resolve name/version/digest, attest package contents, test installation/consumption from the registry, and define yanking/deprecation policy. Publication is not consumer verification.
