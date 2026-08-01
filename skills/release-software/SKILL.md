---
name: release-software
description: Plan, package, publish, deploy, verify, troubleshoot, or recover software releases across VMs, containers, orchestrators, serverless platforms, registries, desktop/mobile distribution, device fleets, and app stores. Use for release readiness, go/no-go checks, immutable artifacts, rollout strategy, state/config migration, production verification, observation, rollback, or post-release diagnosis on any operating system.
---

# Release Software

Treat release as evidence-backed state progression, not as a deployment command finishing.

## Establish the boundary

1. Capture intent: `plan`, `package`, `publish`, `deploy`, `verify`, or `recover`.
2. Confirm authority separately. With read-only authority, inspect and plan only. Do not build, upload, publish, stop services, switch traffic, mutate state/infrastructure, or recover.
3. Name the exact artifact, target, rollout, state classes, interfaces, external capabilities, recovery strategies, observation signals, and window.
4. Treat any new management port, host reboot, remote-control service, network rule, or infrastructure resource as a separate infrastructure change unless explicitly in scope.

Copy `assets/release-context.yaml` from this Skill into the project as `release-context.yaml`. Generate a deterministic plan from any project directory with the installed MASE CLI:

```bash
mase release plan --context release-context.yaml --date YYYY-MM-DD
```

Use the bundled `scripts/generate_release_plan.py` only by resolving it from this Skill's directory, never as a current-working-directory-relative `scripts/` path. Keep the generated plan pending. Only the project Gate Runner or evidence for a gate declared `mode: manual` in `.mase/gates.yaml` can pass a gate.

## Enforce eight invariants

1. Confirm intent, target scope, authority, and non-goals.
2. Bind source, manifest, and delivered content to one immutable artifact identity and provenance.
3. Verify the final delivered content is equivalent to the tested candidate; inspect nested packages and user-visible/runtime content when relevant.
4. Check state, configuration, secrets, runtime, and consumer compatibility before impact.
5. Run every safe preflight before stopping service, shifting traffic, publishing, or overwriting state.
6. Bound blast radius and define measurable stop conditions for the rollout.
7. Verify the live version, declared capabilities, and real consumer paths; process health alone is insufficient.
8. Keep recovery usable through a defined observation window; verify recovery before destructive cleanup.

## Progress by evidence

Use these outcomes precisely:

`planned → candidate_ready → artifact_ready → target_ready → live_verified → observed`

Use `recovered` only after recovery has run and the restored service/state has fresh verification. Never report `artifact_ready` as deployed or `live_verified` as observed.

Stop when artifact identity drifts, required backup/restore evidence is missing, configuration is incompatible, rollout lacks observation, recovery is not viable, live identity differs, or authority is insufficient. Preserve logs and failed staging before retrying. Resume from the failed stage when inputs remain valid.

## Load only relevant detail

- Read [release-contract.md](references/release-contract.md) for context fields, outcomes, authority, and hard stops.
- Read [artifact-and-state.md](references/artifact-and-state.md) for provenance, forbidden content, configuration, backup, and migration.
- Read [rollout-strategies.md](references/rollout-strategies.md) for in-place, rolling, blue-green, canary, phased, immutable, or store rollout.
- Read [verification-and-recovery.md](references/verification-and-recovery.md) for layered live evidence, observation, diagnosis, and recovery.
- Read [platform-adapters.md](references/platform-adapters.md) only for the target/runtime/interface adapters selected by the context.
