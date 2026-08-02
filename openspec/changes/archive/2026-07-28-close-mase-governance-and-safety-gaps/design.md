## Context

MASE already models Profiles, gates, evidence, candidates, release overlays, Sandboxes, project updates, and distributable resources, but several guarantees exist only in prose or are implemented by disconnected code paths. The repair must preserve brownfield projects and current user changes while converting the canonical YAML/schema definitions into runtime-enforced contracts. It must also keep the framework repository product-free and avoid introducing platform-specific release assumptions.

## Goals / Non-Goals

**Goals:**

- Make a compiled GatePlan the single enforceable view of Profile, risk, capability, schedule, artifact, release-stage, authority, and evidence requirements.
- Make all destructive Sandbox and project-update paths containment-safe and conflict-preserving.
- Make evidence freshness depend on the complete execution or manual-review subject, including candidate and release identity where applicable.
- Make `framework-manifest.yaml` the testable contract for source distribution and wheel runtime resources.
- Keep rules, IDE adapters, Skills, docs, state schema, training source, generated PPTX, and CLI behavior consistent.
- Restore MASE's own check/status/OpenSpec health without resurrecting extracted products or historical material.

**Non-Goals:**

- Add a new process Profile or a deployment provider abstraction.
- Perform a real external production release during framework tests.
- Reintroduce `bazi-encyclopedia/`, `story point/`, historical training, generated previews, build output, or other extracted content.
- Automatically resolve semantic conflicts in project-maintained rule extensions.

## Decisions

### Compile policy into explicit gate definitions

Extend gate definitions with explicit `mode`, authority/effect classification, lifecycle stage, subject binding, and predecessor fields. Compile base Profile and every capability through the same registry-driven escalation and scheduling algorithm, then validate required artifacts and final schedule through the resulting GatePlan. This is preferable to command-name heuristics or scattered special cases because `.mase/gates.yaml` remains the unique execution definition and failures become explainable.

### Treat release as a constrained overlay state machine

Release gates are applicable only when an enabled Release Overlay selects them. Stages progress through artifact, preflight, live, and observe semantics; an intent limits the highest allowed stage, required predecessors must have fresh evidence, and effectful gates require sufficient authority. Every evidence record binds to the immutable candidate/artifact/target/release subject appropriate to its stage.

### Centralize path containment before filesystem mutation

Resolve every configured root and target canonically, reject absolute and traversal inputs, require targets to remain beneath an allowed root after symlink resolution, and apply `never_backup` before snapshot creation. Store backups under collision-resistant relative-path identities and verify/restore nested structures from manifests. The same validator is used by snapshot, backup, restore, and verification so no operation has a weaker boundary.

### Make evidence satisfaction gate-specific

Hard gates accept only fresh evidence from an allowed source and never accept `skipped` or ordinary baselines. Manual gates must be declared by the GateDefinition and their evidence digest includes inputs, scope, candidate, release subject, reviewer, and decision. Raw labels in state are status caches, not proof. Terminal lifecycle states are derived only when every required GatePlan item is satisfied.

### Preserve project rule extensions through structured regeneration

Restore change governance in the core canonical rules and delimit generated core content from project-owned extension content. `mase update` updates the generated core only; unknown edits to generated sections or legacy undelimited divergence produce a conflict and backup instead of overwrite. All IDE adapters are regenerated from the resulting canonical project rule source.

### Validate distribution from the manifest

Remove duplicate runtime declarations, map every manifest runtime resource into wheel data, and compare built-wheel contents with the normalized manifest in a clean temporary tree. Package versions are synchronized. Platform adapter selection is capability/OS neutral, with explicit Windows, macOS, Linux, and generic fallbacks.

### Generate training output from one editable source

Update the versioned training YAML first, explicitly distinguish the compact teaching progression from the full state schema, include `target_ready`, and rebuild the PPTX. Verification asserts source/version/text/geometry invariants so slides cannot silently lag runtime semantics.

## Risks / Trade-offs

- [Existing projects use legacy gate definitions] → provide schema defaults only for non-release automatic gates, surface migration diagnostics, and update templates/tests together.
- [Stricter path resolution rejects previously accepted ambiguous paths] → fail before mutation with the offending configured field and resolved boundary in the error.
- [Evidence becomes stale more often] → normalize and report subject digests so users can see exactly which input, candidate, or release component changed.
- [Rule markers alter generated files] → back up before migration and report conflict when legacy local edits cannot be separated safely.
- [Manifest packaging changes are backend-specific] → keep setuptools mapping explicit and enforce behavior by inspecting a real wheel built outside the repository.
- [Historical OpenSpec cleanup obscures this repair] → only repair malformed validation/state needed for truthful current governance; archive completed historical changes as a separately auditable cleanup step if required.

## Migration Plan

1. Add failing security and semantic tests without changing existing user artifacts.
2. Extend schemas/templates and parsers with explicit gate/release/evidence fields.
3. Implement runtime enforcement and migrate MASE's own gate/profile definitions.
4. Harden Sandbox paths and add the referenced Sandbox config schema.
5. Restore canonical governance rules, implement extension-preserving update behavior, and regenerate IDE adapters.
6. Align manifest/package metadata, Skills, documentation, training source/PPTX, and self-state.
7. Run all focused and full validation in clean/no-bytecode environments; build and inspect the wheel in `/tmp`.

Rollback is file-level: retain pre-migration backups for project rule updates and revert only files introduced by this change if validation fails. No external deployment or destructive migration is part of this change.

## Open Questions

None. The audit evidence and the user's approval define the repair scope; implementation details may be refined if new failing tests expose a schema incompatibility.
