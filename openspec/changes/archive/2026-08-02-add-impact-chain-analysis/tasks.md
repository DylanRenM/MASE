## 1. Baseline and contracts

- [x] 1.1 Run and record the pre-change focused governance/CLI baseline without modifying implementation.
- [x] 1.2 Add failing tests for impact artifact schema validation, state references, exemption and L1/L2/L3 policy.
- [x] 1.3 Add failing tests for analysis-stage planning, threshold blockers, reconciliation freshness, and candidate freeze.
- [x] 1.4 Add failing CLI tests for impact validation/status/reconciliation and three generated views.
- [x] 1.5 Add failing tests for live reconciliation freshness, change envelopes, call-edge diffs, protected regression tests, side-effect budgets, and non-Spec declarations.

## 2. Governance models

- [x] 2.1 Add `mase-impact-analysis/v1` and scanner-adapter schemas plus canonical templates.
- [x] 2.2 Extend `mase-state` and gate schemas/templates for impact summaries, references, and the analysis stage.
- [x] 2.3 Implement impact artifact loading, safe-path/digest validation, level/threshold policy, and state diagnostics.
- [x] 2.4 Extend risk and Capability GatePlan derivation with impact gates while preserving Profile floors.
- [x] 2.5 Extend the impact schemas/templates with negative-assurance controls while preserving legacy artifact readability.

## 3. Executable workflow

- [x] 3.1 Implement `mase impact validate`, `status`, `reconcile`, and `render` commands with concise JSON/text output.
- [x] 3.2 Implement planned-versus-actual scope reconciliation and deterministic stale/blocking diagnostics.
- [x] 3.3 Extend gate planning and candidate freeze to enforce fresh pre-design analysis and post-build reconciliation.
- [x] 3.4 Bind impact artifact inputs/digests to gate evidence and candidate identity.
- [x] 3.5 Recompute reconciliation digests from current paths and reject unplanned call edges, protected-test weakening, excess effects, and undisposed non-Spec changes.

## 4. Framework integration

- [x] 4.1 Update core rules, process guide, glossary, and design guidance with triggers, exemptions, traversal, levels, outputs, and excessive-scope decisions.
- [x] 4.2 Update Lite/Standard/Strict schedules, risk registry, and all four Agent skills with impact responsibilities and review authority.
- [x] 4.3 Update project templates, framework manifest, init/update behavior, and user guidance for safe adoption.
- [x] 4.4 Update the MASE training source/deck content and verification expectations without adding product-specific material.
- [x] 4.5 Update MASE principles, Agent responsibilities, documentation, training source, and editable PPT with historical-behavior invariance and negative assurance.

## 5. Verification

- [x] 5.1 Run focused schema, governance, GatePlan, evidence, CLI, update, and distribution tests and resolve root causes.
- [x] 5.2 Run the full framework regression, repository-boundary audit, wheel-manifest verification, and training-deck verification.
- [x] 5.3 Record structured verification results, confirm no Pilot dependency was introduced, and complete all OpenSpec tasks.
