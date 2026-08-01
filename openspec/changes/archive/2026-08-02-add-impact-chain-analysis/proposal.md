## Why

AI-assisted changes to established code can preserve the edited symbol's local tests while silently breaking direct callers, configuration-driven consumers, serialization formats, callbacks, or system-boundary behavior. MASE needs an enforceable, evidence-backed impact-chain step before design and a reconciliation step after implementation so mature code is not changed without an explicit blast-radius and verification decision.

## What Changes

- **BREAKING (process)**: require every non-exempt modification, deletion, rename, replacement, or rerouting of historical runtime code or contract material to complete impact classification and analysis before design/build proceeds.
- Add language-neutral explicit-caller and implicit-dependency analysis, bounded traversal, uncertainty disclosure, system-boundary detection, and L1/L2/L3 verification routing.
- Block AI-autonomous continuation when more than 10 first-party callers, at least 3 system boundaries, unresolved depth-three traversal, or uncontrolled hidden dependencies are found; require a human architecture decision.
- Require post-implementation reconciliation against the actual diff and make prior analysis/review evidence stale when its bound inputs change.
- Add negative-assurance controls: approved file/symbol envelopes, baseline-versus-actual call-edge diffs, protected pre-change regression tests, declared/observed side-effect budgets, and a structured declaration of non-Spec changes.
- Add a canonical `mase-impact-analysis/v1` artifact and generate the human-readable impact scope, test scope, and rollback views from that single source.
- Extend GatePlan and gate execution with a pre-design `analysis` stage, impact-specific automatic/manual gates, and candidate binding.
- Add `mase impact` CLI commands for classification, validation/status, reconciliation, and document generation while keeping language scanners behind project/toolchain adapters.
- Update MASE rules, Profiles, Agent routing, templates, documentation, distribution manifest, and training source so the new constraint is consistently taught and installed.

## Capabilities

### New Capabilities

- `impact-chain-analysis`: Trigger/exemption semantics, explicit and implicit dependency discovery, bounded traversal, L1/L2/L3 routing, scale thresholds, structured outputs, reconciliation, and framework-neutral adapter contracts.

### Modified Capabilities

- `capability-scoped-gate-plan`: Derive impact gates per Capability without turning impact levels into a fourth Profile.
- `stage-aware-gate-planning`: Add pre-design analysis gates and prevent later work/freeze when required analysis or reconciliation is not fresh.
- `executable-gate-evidence`: Record structured impact artifacts and human decisions without allowing prose to impersonate automatic analysis.
- `evidence-freshness-and-reuse`: Bind impact evidence to baseline, diff, Specs, contracts, scanner rules, and actual affected scope.
- `risk-scoped-review-routing`: Require impact, architecture, and code review according to L2/L3 and threshold decisions.
- `single-source-project-state`: Reference one canonical impact-analysis artifact and expose its effective decision in change state.
- `adaptive-process-profiles`: Apply impact analysis across Lite, Standard, and Strict while permitting concise L1 output and risk-driven escalation.

## Impact

- Framework policy and documentation: `project-rules.md`, `docs/MASE-framework.md`, glossary/design guidance, and Agent skills.
- Governance models: risk registry, Profile schedules, `mase-state` and gate schemas/templates, plus a new impact-analysis schema/template.
- Runtime: GatePlan derivation, gate planning/freeze rules, change-state validation, new `mase impact` CLI command group, and artifact/document generation.
- Verification and distribution: CLI/model tests, repository regression, manifest/install/update coverage, and MASE training source/deck consistency.
- No Pilot product source, product tests, product data, or Pilot-specific dependency graph is added to MASE.
