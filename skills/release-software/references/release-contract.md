# Release contract

## Compositional context

Record independent dimensions instead of OS-first flags:

- `intent` and `authority`;
- artifact `kind`, immutable `identity`, and `provenance`;
- target `kind`, environment, platform, and identifier;
- rollout strategy and maximum impact;
- state classes and migration policy;
- consumer interfaces and external capabilities;
- recovery strategies;
- observation signals and window.

Identifiers are opaque and platform-native. A digest, signed registry coordinate, package version with registry proof, store build/version, or notarized bundle identity can satisfy immutability.

## Outcomes

- `planned`: contract exists; checks remain pending.
- `candidate_ready`: development candidate is frozen with fresh final evidence.
- `artifact_ready`: the exact artifact has identity, integrity, provenance, and forbidden-content evidence.
- `target_ready`: target/configuration/recovery preflight is fresh.
- `live_verified`: the target serves the exact artifact and real consumer/capability paths pass.
- `observed`: signals remain within stop conditions for the declared window.
- `recovered`: recovery completed and the recovered target/state passed verification.

Do not infer a later state from an earlier state. A local package, successful upload, completed deploy job, running process, or HTTP 200 is not live consumer evidence by itself.

## Authority and stops

Separate analysis permission from release mutation authority. Ask for new authority before upload, publication, service interruption, traffic switch, store submission, state mutation, infrastructure change, or recovery if it was not already granted.

Stop on ambiguous artifact selection, mutable tags without resolved digest, identity mismatch, missing required configuration, unverified backup, incompatible migration, absent recovery path, missing canary/phased signals, exceeded stop condition, or live version mismatch.

## Gate definition contract

Declare every release gate in `.mase/gates.yaml` with its stage and explicit execution semantics:

```yaml
release_live_verification:
  stage: release_live
  mode: automatic
  effect: external-write
  required_authority: release
  requires: [release_target_preflight, release_recovery_readiness]
  command: ["./scripts/deploy-and-verify"]
  inputs: ["release-context.yaml", "scripts/deploy-and-verify"]
  candidate_bound: true
```

Use `effect: read-only` and `required_authority: read-only` only when the command cannot mutate local files, target state, traffic, registries, stores, or infrastructure. Declare a human review as `mode: manual`; its evidence still binds to current inputs, scope, candidate, and release digest. A release gate is not runnable merely because it is defined: it must also be selected by the current Release Overlay intent and GatePlan, have fresh declared predecessors, and meet authority.
