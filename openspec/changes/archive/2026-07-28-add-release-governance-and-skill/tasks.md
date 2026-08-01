## 1. Contract Tests

- [x] 1.1 Add failing schema/state tests for the optional Release Overlay and release outcomes
- [x] 1.2 Add failing risk and gate-planning tests for release triggers and release gate stages
- [x] 1.3 Add failing CLI tests for read-only release plan/status and contradictory contexts
- [x] 1.4 Add failing Skill package and cross-platform plan-generator tests
- [x] 1.5 Extend failing training/document synchronization tests with release governance topics

## 2. Release Governance Core

- [x] 2.1 Add the standalone release-context schema, state overlay schema, and templates
- [x] 2.2 Extend change state and lifecycle reporting with release metadata and derived outcomes
- [x] 2.3 Add release-specific risk triggers and conditional gate planning
- [x] 2.4 Extend canonical gate stages and preserve candidate/artifact evidence freshness behavior
- [x] 2.5 Implement read-only `mase release plan` and `mase release status` commands

## 3. General Release Skill

- [x] 3.1 Initialize `release-software` with valid metadata, references, scripts, and assets
- [x] 3.2 Implement the invariant workflow, authority boundaries, adapter routing, and hard stops
- [x] 3.3 Implement validated deterministic release-plan generation without platform-specific defaults
- [x] 3.4 Validate the Skill package and synthetic VM/container/registry/app-store contexts

## 4. Framework and Training Synchronization

- [x] 4.1 Update canonical rules, framework guide, user guide, glossary, and project structure guidance
- [x] 4.2 Update manifest/runtime routing and regenerate all IDE adapters from canonical rules
- [x] 4.3 Update the V2.3 training YAML source and topic assertions for release governance
- [x] 4.4 Regenerate and verify the editable V2.3 PPTX without geometry, logo, or editability drift

## 5. Verification

- [x] 5.1 Run focused release governance, Skill, schema, CLI, and training tests
- [x] 5.2 Run the full MASE test suite and fix in-scope regressions
- [x] 5.3 Run OpenSpec validation/status checks and record final implementation evidence
