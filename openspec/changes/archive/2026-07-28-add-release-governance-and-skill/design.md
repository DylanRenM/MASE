## Context

MASE v2.3 freezes a development candidate and binds final test evidence to inputs and artifacts, but `release` remains only a lifecycle label. The state model cannot distinguish a package-only result from a production deployment, the risk registry has no release-specific triggers, and gate stages stop at `final`. The runtime also excludes `dist`, logs, and evidence by default, so a release task needs explicit context routing to the exact current artifact rather than broad historical loading.

Pilot and Numerology provide repeated evidence for a stable release abstraction: candidate identity, actual artifact identity, target readiness, state/configuration policy, controlled rollout, live consumer evidence, observation, and recovery. Their Windows details are useful adapters but must not define the core model.

The workspace already contains an uncommitted but complete V2.3 training-deck refresh. This change must preserve its guarded 37-slide editable template and update only its canonical YAML source before regenerating the derived PPTX.

## Goals / Non-Goals

**Goals:**

- Add an optional, backward-compatible Release Overlay to MASE state and gate planning.
- Separate `artifact_ready` from `live_verified` and `observed` release outcomes.
- Make release gates composable across artifact, target, rollout, state, interface, and recovery dimensions.
- Provide read-only CLI planning/status commands; retain project ownership of deployment execution.
- Create a concise `release-software` Skill with conditional references and deterministic, data-driven planning tooling.
- Keep canonical docs, generated adapters, and the editable V2.3 training deck synchronized.

**Non-Goals:**

- Implement a universal production deployer, remote transport, secret manager, cloud adapter, or traffic controller.
- Encode Windows, Docker, Kubernetes, LLM, browser, or SQLite assumptions in the core release contract.
- Automatically authorize service stops, traffic changes, infrastructure changes, store submissions, or production writes.
- Force release artifacts or gates on changes that do not declare release intent.

## Decisions

### 1. Use an optional Release Overlay instead of a fourth Profile

Add a `release` object to `mase-state.yaml`. It records intent, outcome, artifact, target, rollout, state impact, interfaces, recovery, and evidence-facing identifiers. Release intent activates additional gates while the existing Lite/Standard/Strict Profile continues to express engineering rigor.

This avoids making every deployment Strict and avoids burdening changes that end at code completion. Release risks can still raise the minimum Profile through the normal risk registry.

Alternative considered: add a `release` Profile. Rejected because deployment topology and change risk are orthogonal; a low-risk package publication and a regulated state migration should not share one process weight.

### 2. Model a generic target and artifact, not OS-first flags

Use independent dimensions:

- intent: plan, package, publish, deploy, verify, recover;
- artifact kind: archive, image, package, binary, bundle, store submission, or project-defined extension;
- target kind: VM, container, orchestrator, serverless, registry, app store, device fleet, or project-defined extension;
- rollout strategy: in-place, rolling, blue-green, canary, phased, immutable, or project-defined extension;
- state classes and consumer interfaces as arrays.

Identifiers remain opaque strings. A digest, signature, registry coordinate, store version, or other platform-native immutable identity can satisfy the artifact identity contract.

Alternative considered: `--os`, `--docker`, `--db`, and `--llm` flags. Rejected because they encode one web-server deployment family and create invalid checklists for other targets.

### 3. Extend gate stages only for release evidence

Extend canonical gate stage values with `release_artifact`, `release_preflight`, `release_live`, and `release_observe`. Add conditional release gate names through risk/overlay planning:

- artifact identity/integrity and forbidden-content checks;
- target/configuration preflight and recovery readiness;
- live version/capability/consumer-path verification;
- observation completion.

Development final gates remain unchanged. Candidate-bound and artifact-bound evidence becomes stale through existing digest mechanisms when configured inputs or artifacts change.

Alternative considered: reuse `final` for every release check. Rejected because it conflates build readiness with target-environment evidence and encourages a package-ready result to be reported as deployed.

### 4. Keep the CLI diagnostic and non-mutating

Add `mase release plan` and `mase release status` commands that load and validate release context, derive required invariant/gate groups, and emit text or JSON. They do not build, upload, stop, switch, publish, or roll back software.

Project-specific commands remain canonical gate definitions in `.mase/gates.yaml` and require the user's release authority. Infrastructure expansion remains a separate change.

### 5. Make the Skill a small invariant kernel with one-level references

Create `skills/release-software/` with:

- a concise imperative `SKILL.md` containing eight invariants, intent/authority handling, state progression, and hard stops;
- `agents/openai.yaml` generated from the Skill;
- one-level references for the release contract, artifact/state handling, rollout strategies, verification/recovery, and platform adapters;
- a deterministic `generate_release_plan.py` that consumes validated YAML and writes stdout unless an output path is explicitly requested;
- a reusable release-context asset.

Windows/PowerShell lessons remain available in the platform-adapter reference and are loaded only when the target matches.

### 6. Preserve generated-source ownership for training

Update the canonical V2.3 training YAML and topic assertions, then regenerate the editable PPTX with the existing checksum-guarded V1 template. Do not manually edit PPTX XML or the preserved V1 deck. Add release governance to existing slide slots rather than changing slide count or geometry.

## Risks / Trade-offs

- [Risk] A broad release schema becomes an unbounded platform ontology. → Keep core identifiers extensible strings, require only stable invariants, and place examples/adapters in references.
- [Risk] Release gates duplicate project CI/CD behavior. → Treat `.mase/gates.yaml` as the execution source and the overlay as planning/evidence metadata, not another deploy engine.
- [Risk] Existing state files fail validation. → Make `release` optional and keep all existing enum values and behavior valid.
- [Risk] A checklist is mistaken for passing evidence. → CLI and Skill label plans as pending; only Gate Runner/manual evidence can satisfy gates.
- [Risk] Training edits damage an existing user-generated deck. → Modify only the YAML source, rebuild through the guarded script, and retain geometry/logo/editability tests.
- [Risk] Live forward-tests could mutate production. → Limit automated validation to synthetic contexts and local artifacts; require explicit user authority for any live release exercise.

## Migration Plan

1. Add failing schema, risk, CLI, Skill, and training tests.
2. Add optional release schema/state support and release-stage gate values.
3. Add read-only release planning/status logic and templates.
4. Initialize and implement `release-software`, then validate its scripts and metadata.
5. Update rules, docs, generated adapters, and training YAML; regenerate and verify the PPTX.
6. Run focused tests, the complete MASE suite, Skill validation, and synthetic cross-platform release-plan cases.

Rollback removes the optional overlay, new commands, Skill, templates, references, and training-source updates. Existing state files remain valid throughout because no required legacy field changes.

## Open Questions

None blocking. Platform-specific execution adapters can be added later only after repeated evidence justifies them.
