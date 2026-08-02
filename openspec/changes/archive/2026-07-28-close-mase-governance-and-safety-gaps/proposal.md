## Why

The MASE v2.3 audit found that several documented guarantees are not enforced by the runtime: release commands can execute without sufficient authority, Sandbox restore can escape the project boundary, hard gates and Profiles can be bypassed, and packaged/framework-generated artifacts can drift from their canonical sources. These gaps affect safety and trust in MASE itself, so the framework, Skill, documentation, training deck, distribution, and self-governance need one coherent repair.

## What Changes

- **BREAKING**: require release gates to declare execution mode, authority, stage, Release Overlay membership, immutable subject binding, and predecessor evidence before Gate Runner may execute or accept them.
- **BREAKING**: reject Sandbox snapshot, backup, restore, and verification paths that are absolute, traversing, symlink-escaping, outside configured roots, or forbidden by `never_backup`.
- Compile Profile artifacts, capability gates, reviews, test schedules, and registry-driven risk escalation into an executable GatePlan; reject unknown risks and invalid terminal states.
- Tighten hard-gate, baseline, manual-evidence, candidate-readiness, freshness, and input/candidate/release binding semantics.
- Restore OpenSpec change governance to the canonical rules and prevent `mase update` from silently overwriting project-maintained rule extensions.
- Make the framework manifest the distribution contract, include the complete release Skill and runtime resources in wheels, and align package metadata.
- Bring release Skill guidance, platform adapter selection, documentation links, state vocabulary, training YAML/PPT, IDE adapters, and repository-boundary checks into agreement with runtime behavior.
- Repair MASE's own active/completed change state and strict OpenSpec validation so `mase check`, `mase status`, and repository validation give truthful results.

## Capabilities

### New Capabilities

- `release-authority-and-stage-safety`: Defines authorization, applicability, stage ordering, and immutable binding requirements for release gates.
- `sandbox-path-safety`: Defines containment, exclusion, collision-free backup, nested restore, and malicious-path rejection requirements.
- `executable-profile-and-hard-gate-semantics`: Defines how Profiles and risk registries compile into enforceable GatePlans and how hard gates reach valid terminal states.
- `evidence-and-candidate-binding`: Defines trusted evidence origins, manual evidence binding/freshness, and candidate readiness semantics.
- `framework-distribution-integrity`: Defines manifest-driven wheel contents, package metadata consistency, portable Skill/adapters, and runtime resource contracts.
- `framework-self-governance-and-training-consistency`: Defines canonical/extended rule preservation, IDE adapter regeneration, OpenSpec state health, repository boundaries, and training/documentation consistency.

### Modified Capabilities

None. `openspec/specs/` has no current capability specifications; this change establishes the audited behaviors as canonical specifications.

## Impact

The change affects `mase_cli` gate, release, evidence, state, risk, profile, baseline, update, and packaging logic; the webapp-testing Sandbox; schemas, templates, Profiles, manifest and package metadata; the release Skill and platform references; project rules and generated IDE adapters; repository/OpenSpec governance; Python and JavaScript tests; framework docs; and the editable MASE training source and generated PPTX.
