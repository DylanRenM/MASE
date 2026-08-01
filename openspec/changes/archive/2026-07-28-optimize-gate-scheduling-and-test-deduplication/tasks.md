## 1. Failure-first contract coverage

- [x] 1.1 Add status tests proving stale/missing/invalid evidence cannot satisfy a required automatic gate
- [x] 1.2 Add gate-definition Schema and loader tests for stages, safe paths, commands, selectors and covers
- [x] 1.3 Add plan tests for deferred final gates, duplicate/high-overlap selectors and actionable next steps
- [x] 1.4 Add candidate freeze tests for prerequisites, digest stability and post-freeze invalidation
- [x] 1.5 Add runner tests for exact cache hit, changed signature execution, explicit cross-gate covers and bounded evidence retention
- [x] 1.6 Add Capability plan tests for independent profiles, scoped paths, legacy declarations and final risk floor
- [x] 1.7 Add CLI contract tests for `gate plan`, `gate freeze`, compatibility warnings and incremental runner output

## 2. Gate definitions and planning model

- [x] 2.1 Add `mase-gates/v1` JSON Schema, Python models and safe `.mase/gates.yaml` loader
- [x] 2.2 Add GateInstance/effective-state/diagnostic models and JSON-safe status serialization
- [x] 2.3 Implement normalized execution and test-set signatures plus exact/high-overlap diagnostics
- [x] 2.4 Implement stage-aware plan derivation from Profile schedule, required gates and canonical definitions

## 3. Evidence freshness and lifecycle

- [x] 3.1 Resolve the latest evidence per gate instance and call `assess_evidence()` from status/check
- [x] 3.2 Compute lifecycle and blocking diagnostics from effective states instead of raw hand-written gate values
- [x] 3.3 Preserve legacy states as compatible stale diagnostics without treating free-text passed as fresh
- [x] 3.4 Compact state evidence to the bounded latest pass/failure/replacement audit set

## 4. Candidate freeze and efficient execution

- [x] 4.1 Add candidate state model/Schema and deterministic digest across final inputs, Specs, tasks and gate definitions
- [x] 4.2 Implement freeze prerequisite validation, candidate persistence and automatic stale detection
- [x] 4.3 Require current candidate binding for canonical candidate-bound final gates
- [x] 4.4 Reuse exact fresh execution signatures without spawning a subprocess
- [x] 4.5 Implement explicit `covers` evidence fan-out with shared execution/log references
- [x] 4.6 Stream command output while retaining complete secret-redacted evidence logs

## 5. Capability-scoped gate plans

- [x] 5.1 Extend Capability state parsing for triggers, paths and optional gates while accepting profile-only legacy entries
- [x] 5.2 Derive per-Capability Profile, scoped development gates and conservative diagnostics
- [x] 5.3 Merge Capability hard-gate requirements into the change final floor without expanding unrelated capability inputs

## 6. CLI, templates and migration guidance

- [x] 6.1 Add `mase gate plan` human/JSON output and `mase gate freeze` commands
- [x] 6.2 Make canonical gate run resolve definitions and reject conflicting explicit commands
- [x] 6.3 Add default gate-definition template, manifest distribution entry and project initialization support
- [x] 6.4 Update update dry-run diagnostics for projects missing canonical definitions or using legacy evidence
- [x] 6.5 Update project rules, framework guide and user guide with freeze-first final verification and reuse constraints

## 7. Verification

- [x] 7.1 Run focused evidence, status, profile, CLI, initialization and migration tests
- [x] 7.2 Run complete Python framework regression and JavaScript sandbox regression
- [x] 7.3 Run strict OpenSpec validation and `mase check/status` consistency checks
- [x] 7.4 Record automatic gate evidence and request lightweight independent confirmation
