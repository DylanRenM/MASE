## Why

MASE currently treats `release` as a phase label after development gates, but it does not model the immutable artifact, target environment, rollout strategy, live evidence, observation window, or recovery path that determine whether software is actually released safely. Repeated Pilot and Numerology incidents show that source tests and HTTP 200 are insufficient when the wrong artifact, stale build, incompatible configuration, unsafe state handling, or unverified production behavior can still reach users.

## What Changes

- Add a platform-neutral Release Overlay that distinguishes planning, packaging, publishing, deployment, verification, and recovery from ordinary change completion.
- Add release risk triggers, state/schema fields, release-stage gates, templates, and CLI planning/status support without forcing every development change into Strict.
- Add a general `release-software` Skill covering servers, containers, orchestrators, serverless targets, registries, desktop/mobile distribution, and app stores through a small invariant core plus conditional adapters.
- Add deterministic release-context validation and runbook generation that does not assume Windows, ZIP files, HTTP, browsers, databases, or LLMs.
- Update the canonical framework documentation, user guidance, generated IDE adapters, and the editable V2.3 training source/PPTX so release governance is taught consistently.

## Capabilities

### New Capabilities

- `release-governance`: Model release intent, artifact identity, target, rollout, state impact, gates, live verification, observation, and recovery as auditable MASE behavior.
- `release-software-skill`: Provide a progressively disclosed, platform-neutral Skill and deterministic tooling for release planning, go/no-go evaluation, troubleshooting, and recovery.
- `release-training-materials`: Keep the canonical documentation and editable training deck synchronized with the release governance model and Skill routing.

### Modified Capabilities

None.

## Impact

- Affects `project-rules.md`, `docs/`, `profiles/`, `schemas/`, `templates/`, `mase_cli/`, `skills/`, `framework-manifest.yaml`, generated IDE adapters, and tests.
- Extends the release-related state and gate contracts while preserving legacy changes that do not declare a Release Overlay.
- Updates `training/mase-framework/mase-training-v2.3.yaml` and regenerates the editable V2.3 PPTX through the existing guarded build pipeline.
- Adds no production deployment transport and does not authorize infrastructure or production mutations; project-specific deployment adapters remain owned by adopting projects.
