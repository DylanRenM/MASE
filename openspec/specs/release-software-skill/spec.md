# release-software-skill Specification

## Purpose
TBD - created by archiving change add-release-governance-and-skill. Update Purpose after archive.
## Requirements
### Requirement: Platform-neutral Skill triggering
The `release-software` Skill SHALL trigger for planning, packaging, publishing, deploying, verifying, troubleshooting, or recovering software releases across server, container, orchestrator, serverless, registry, desktop/mobile, and app-store targets.

#### Scenario: Non-Windows release request
- **WHEN** a user asks for a Kubernetes canary, a package-registry publication, or an app-store phased release
- **THEN** the Skill applies the same invariant kernel and loads only the relevant adapter guidance

### Requirement: Skill enforces release invariants and authority
The Skill MUST enforce explicit scope/authority, immutable artifact identity, content equivalence, state/config compatibility, pre-impact checks, controlled blast radius, live consumer evidence, and verified recovery/observation.

#### Scenario: User asks only for a readiness review
- **WHEN** the user authorizes analysis but not deployment
- **THEN** the Skill performs read-only checks and does not upload, publish, stop services, switch traffic, or mutate infrastructure

#### Scenario: Release requests infrastructure expansion
- **WHEN** completing an application release would require opening management ports, rebooting a shared host, or installing a new remote-control service
- **THEN** the Skill reports a separate infrastructure change and does not silently broaden the release

### Requirement: Data-driven release plan generation
The Skill SHALL generate release plans from a validated compositional context rather than OS-first boolean flags.

#### Scenario: Linux container without browser interface
- **WHEN** the context declares a container image, orchestrator target, rolling strategy, stateless workload, and event interface
- **THEN** the generated plan contains image/rollout/event checks and omits ZIP, PID, Windows, browser, database, and LLM assumptions

#### Scenario: Windows in-place stateful service
- **WHEN** the context declares a Windows VM adapter, in-place strategy, filesystem/database state, and HTTP/browser interfaces
- **THEN** the plan includes applicable PowerShell/runtime/state/browser checks without changing the core invariants

### Requirement: Progressive disclosure and valid Skill package
The Skill SHALL keep the core instructions concise, load one-level references conditionally, provide valid `agents/openai.yaml`, and include only reusable scripts/assets required for release work.

#### Scenario: Skill package validation
- **WHEN** the Skill validation tool checks the folder
- **THEN** frontmatter contains only `name` and `description`, metadata matches the Skill, and all referenced resources exist

### Requirement: Deterministic tooling remains evidence-neutral
Skill scripts MUST validate input, support reproducible dates/outputs, write to stdout by default, and MUST NOT report a generated checklist as passing release evidence.

#### Scenario: Same context and explicit date are reused
- **WHEN** the plan generator receives the same validated context and date twice
- **THEN** it emits byte-identical output
