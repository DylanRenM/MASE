## ADDED Requirements

### Requirement: Canonical release documentation is synchronized
MASE SHALL document the Release Overlay, invariant kernel, state progression, risk triggers, gate stages, Skill routing, and project-adapter boundary consistently in canonical rules and user documentation.

#### Scenario: User reads the framework guide
- **WHEN** a user follows the release section in current MASE documentation
- **THEN** the guide distinguishes artifact readiness from live verification and routes release work to `release-software`

### Requirement: Editable training deck teaches release governance
The V2.3 training source and generated editable PPTX SHALL teach platform-neutral release governance without changing the guarded 37-slide V1 geometry, logo placement, or editability guarantees.

#### Scenario: Training deck is regenerated
- **WHEN** the canonical YAML source is built through the guarded training pipeline
- **THEN** the PPTX contains Release Overlay, immutable artifact, live evidence, observation/recovery, and `release-software` topics while all existing geometry and editability tests pass

### Requirement: Generated IDE adapters remain synchronized
MASE SHALL regenerate IDE adapters from `project-rules.md` so release hard minimums are visible without introducing a second maintained rule source.

#### Scenario: Rules are generated after release update
- **WHEN** the adapter generator runs after canonical release rules change
- **THEN** AGENTS, CLAUDE, CONVENTIONS, and Copilot instructions contain the generated release minimum and matching source hash
