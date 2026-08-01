# Verification, observation, and recovery

## Verify in layers

Select only layers applicable to declared interfaces and capabilities:

1. Runtime: process/task/container/function is healthy and stable.
2. Identity: live version, digest, build, configuration generation, and route point to the intended artifact.
3. Interface: protocol, status, content type/schema, caching, streaming, binary transfer, or event behavior is correct.
4. Capability: storage, queue, third-party, model/tool, scheduled job, or device behavior works.
5. Consumer path: a real P0 workflow succeeds from a clean consumer state and, where relevant, an upgrade/recovery state.
6. Exposure: intended public/private reachability works without unintentionally exposing management or internal interfaces.

A process, health endpoint, or HTTP 200 proves only its own layer. Record commands/scenarios, target, artifact identity, time, actor, result, bounded logs, and relevant outputs.

## Observe

Define signals before rollout: error/latency/saturation, business success, queue lag, crash/restart, client adoption, data integrity, external dependency failures, and security signals as applicable. Set baseline, threshold, window, sample/cohort, and decision owner.

Do not clean the previous version, backup, failed staging, or recovery controls until the window passes. Mark `observed` only with fresh evidence.

## Diagnose and recover

At failure:

1. Stop expansion and bound impact.
2. Preserve logs, exact identity, failed staging, target state, and observation evidence.
3. Classify the failed layer before choosing restart, roll-forward, traffic reversal, restore, client mitigation, or rollback.
4. Avoid repeating destructive or state-restore steps whose evidence remains valid.
5. Execute the declared recovery with explicit authority.
6. Reverify identity, state integrity, interfaces, capabilities, consumer paths, and exposure.
7. Record `recovered`; keep follow-up observation active.

If recovery is untested or a migration is irreversible, reduce blast radius or block the release rather than pretending rollback exists.
