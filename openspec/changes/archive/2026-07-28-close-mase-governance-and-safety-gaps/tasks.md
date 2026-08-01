## 1. Characterization and schema contracts

- [x] 1.1 Add failing Python tests for release overlay applicability, intent, read-only authority, stage predecessors, and candidate/artifact/release binding.
- [x] 1.2 Add failing JavaScript tests for traversal, absolute paths, symlink escape, `never_backup`, basename collisions, and nested Sandbox restore/verification.
- [x] 1.3 Add failing Python tests for hard-gate bypasses, terminal inconsistency, executable Profile artifacts/schedules/reviews, registry escalation, unknown risks, and evidence freshness.
- [x] 1.4 Extend gate, state, release, and Sandbox schemas/templates with explicit execution, authority, stage, evidence mode, subject binding, and path policy fields.

## 2. Release and evidence enforcement

- [x] 2.1 Compile Release Overlay membership and intent into GatePlan applicability and reject non-applicable release gates before command execution.
- [x] 2.2 Enforce declared execution effects, authority requirements, ordered release-stage predecessors, and immutable subject bindings in Gate Runner.
- [x] 2.3 Make automatic/manual evidence gate-definition-aware and bind manual evidence freshness to inputs, scope, reviewer, candidate, and release subject.
- [x] 2.4 Require frozen candidate metadata plus fresh bound final evidence before reporting `candidate_ready` and preserve distinct release progression states.

## 3. Sandbox containment

- [x] 3.1 Centralize canonical allowed-root containment and reject traversal, absolute, and symlink-escaping paths before every Sandbox filesystem operation.
- [x] 3.2 Implement `never_backup`, collision-free relative backup identities, manifest-based nested restore, and exact verification.
- [x] 3.3 Ship and validate the Sandbox configuration schema and pass all malicious-path JavaScript tests.

## 4. Profiles, risk, and hard gates

- [x] 4.1 Compile Profile and capability required artifacts, gates, reviews, and test schedules into an enforceable GatePlan used by check/status/runner.
- [x] 4.2 Resolve top-level and capability risks through the shared registry, apply `minimum_profile`, and diagnose unknown identifiers.
- [x] 4.3 Derive hard gates dynamically and reject skipped, baseline, raw-label, stale, or wrong-origin satisfaction; reject terminal states with pending requirements.

## 5. Distribution and portable Skills

- [x] 5.1 Normalize `framework-manifest.yaml`, package every runtime resource including the complete release Skill, synchronize package versions, and add a clean-wheel contract test.
- [x] 5.2 Correct release Skill invocation and Windows/macOS/Linux/Unix/generic adapter selection, repair distributed Skill links, regenerate `agents/openai.yaml` if needed, and run Skill quick validation.

## 6. Rules, self-governance, and training

- [x] 6.1 Restore OpenSpec change governance in canonical rules, preserve project extension sections during update, conflict safely on ambiguous legacy edits, and regenerate all IDE adapters.
- [x] 6.2 Make boundary checks deterministic for OS metadata and test caches while continuing to reject extracted products, history, build output, and unknown content.
- [x] 6.3 Repair MASE change states and malformed historical OpenSpec data needed for `mase check`, `mase status`, and strict validation without restoring migrated content.
- [x] 6.4 Align docs and training YAML with full state/release vocabulary, rebuild the editable PPTX, and pass deck verification.

## 7. Full verification

- [x] 7.1 Run focused tests after each repair and full Python and JavaScript suites with repository-safe cache settings.
- [x] 7.2 Run strict OpenSpec, MASE check/status, repository boundary, adapter/source-hash, documentation-link, package-version, and `git diff --check` validation.
- [x] 7.3 Build a wheel in a clean temporary copy, compare its contents with the manifest contract, and record final validation results.
