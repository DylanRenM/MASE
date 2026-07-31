## Context

MASE currently derives gates from Profile, Capability risks, product attributes, and change impact paths. It has canonical gate execution, evidence freshness, candidate freeze, and test selection, but `impact.paths` is a manually supplied flat list and there is no governed way to prove how a historical-code edit affects callers. Static-only analysis also cannot prove completeness for reflection, generated registration, runtime routing, or configuration-driven dispatch.

This change therefore needs both a process contract and a machine-readable exchange format. MASE must remain language/product neutral: project adapters discover language-specific relationships, while the framework validates, classifies, plans gates, records decisions, and generates auditable views.

## Goals / Non-Goals

**Goals:**

- Require a fresh pre-design impact decision for non-exempt historical behavior changes.
- Reconcile the planned analysis against the actual implementation diff before verification.
- Represent explicit callers, implicit channels, traversal boundaries, uncertainty, L1/L2/L3 level, tests, rollout, and rollback in one canonical artifact.
- Derive mandatory gates and human escalation from deterministic policy.
- Keep impact levels orthogonal to Lite/Standard/Strict and preserve existing hard-gate floors.
- Make analysis/review evidence stale when its baseline, diff, rules, Specs, contracts, or affected scope changes.
- Support language-specific scanners through a versioned adapter result rather than embedding Java/Python/TypeScript logic in MASE.

**Non-Goals:**

- Proving that every runtime caller has been found when dynamic dispatch makes that impossible.
- Shipping a universal source-code indexer or production tracing agent.
- Modifying or validating Pilot product code from the MASE repository.
- Treating impact analysis as a fourth Profile or replacing existing TDD, contract, integration, E2E, review, or release gates.
- Executing production writes, rollout, or rollback from the impact CLI.

## Decisions

### 1. One structured source with three generated views

Each triggered change uses `impact-analysis.yaml` with schema `mase-impact-analysis/v1`. It contains comparison identity, change points, explicit/implicit relationships, boundaries, termination reasons, uncertainty, classification, test scope, decision, and recovery. `impact-scope.md`, `test-scope.md`, and `rollback.md` are generated views containing the source digest.

This avoids three manually synchronized facts while preserving the required review documents. Storing the whole graph inside `mase-state.yaml` was rejected because state is an orchestration summary and would become noisy and expensive to load.

### 2. State stores applicability and a bound artifact reference

`mase-state.yaml` gains an optional `impact_analysis` summary containing applicability, level, decision, artifact path/digest, baseline/diff digests, and reconciliation status. Existing changes remain readable. A change declaring a historical behavior change must populate it; exempt changes must record a machine-checkable exemption reason.

### 3. Two checkpoints and a new analysis gate stage

The gate schema adds `analysis`. `impact_analysis` runs before design/build and `impact_reconcile` runs after implementation. Gate planning reports later stages blocked or deferred when required analysis evidence is missing/stale. Candidate freeze requires the reconciliation artifact to be fresh.

Using only the existing `capability` stage was rejected because it cannot express the requested pre-design constraint.

### 4. L1/L2/L3 is an impact dimension, not a Profile

- L1: internal implementation, semantics/side effects unchanged, non-core path, explicit low-frequency evidence, no unresolved implicit channel.
- L2: core path, material side effect, unknown frequency, implicit dependency, or analysis uncertainty.
- L3: public contract/business semantics change, system-boundary impact, or architecture threshold.

L2 adds impact review and applicable integration validation. L3 adds architecture review, full-chain smoke, rollout/rollback planning, and applicable rollback verification. Existing risk triggers can still upgrade the Capability Profile independently.

### 5. Bounded traversal stops scanning but does not erase uncertainty

Traversal stops at a declared system boundary, repository boundary, or depth three. Depth three without a system boundary creates a coupling alert and human blocker. The artifact distinguishes discovered callers, checked-empty channels, unverified channels, confidence, and residual risks. “All callers found” is not a valid automatic claim when an unverified dynamic channel remains.

### 6. Threshold decisions require human authority

More than 10 unique first-party callers, at least 3 system boundaries, an unresolved depth-three chain, or uncontrolled hidden dependencies set decision `architecture-review-required`. AI may generate evidence and alternatives but cannot record approval. Allowed decisions are proceed, version isolation/adapter, feature flag, split change, or terminate.

### 7. Adapter contract, not framework-specific scanners

Projects may configure a scanner command whose redacted output validates as `mase-impact-scan/v1`. MASE provides a generic manifest/manual adapter for unsupported stacks. Adapter output includes tool/version, inputs, nodes, edges, implicit-channel checks, boundaries, and diagnostics. Framework policy computes the final level and thresholds so adapters cannot downgrade gates.

### 8. Differential contracts are side-effect isolated

Old/new comparison uses authorized, minimized fixtures and records normalization rules for nondeterministic fields. Production-derived samples must be authorized and sanitized. The test plan must identify side-effect isolation; MASE never runs old/new code against production state as part of this feature.

### 9. Scope expansion invalidates prior decisions

The artifact digest binds baseline, changed symbols/paths, Spec and contract inputs, scanner version/rules, tests, and decisions. Actual diff reconciliation compares planned and realized change points. Any unapproved addition makes analysis/review evidence stale and routes work back to analysis/design.

## Risks / Trade-offs

- [False confidence from static analysis] → expose unverified channels, confidence, scanner coverage, and residual risks; upgrade unknowns to L2.
- [Too much process for small changes] → allow evidence-backed non-behavior exemptions and concise generated L1 views.
- [Scanner output differs by language] → normalize through one adapter schema and keep policy decisions in MASE core.
- [Large graphs inflate state/context] → store only a digest/reference/summary in state and load the artifact on routed tasks.
- [Production samples leak sensitive data] → require authorization, sanitization, minimization, and persisted provenance without raw secrets.
- [Existing projects lack analysis gates] → keep old states readable, emit migration diagnostics, and provide a manual structured fallback until adapters are installed.
- [Analysis becomes stale frequently] → use scoped input digests and exact reuse rather than rerunning unrelated Capability analysis.

## Migration Plan

1. Add schemas/templates and read-compatible state fields.
2. Add failing governance and CLI tests for trigger, exemption, level, threshold, generation, freshness, and candidate blocking.
3. Implement artifact validation, policy evaluation, document generation, CLI routing, and gate planning.
4. Update rules, Profiles, Agents, docs, manifest, and training source.
5. Run in diagnostic mode for existing states; require structured analysis for newly declared historical behavior changes.
6. Verify focused tests, full framework regression, repository boundary, wheel manifest, and training consistency.

Rollback is a code revert of this framework change. The additions are schema-compatible for old states; generated project files are updated through the existing dry-run/conflict-preserving update flow.

## Open Questions

- No blocking product decision remains. The first implementation provides the generic adapter contract and structured/manual fallback; language-specific scanner packages can be added independently without changing the core schema.
