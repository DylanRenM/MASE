## ADDED Requirements

### Requirement: User-visible changes require governed changes
The canonical MASE rules MUST require an OpenSpec change for changes affecting user-visible behavior or public contracts, and generated IDE adapters MUST consistently point to the regenerated project rule source.

#### Scenario: Adapters are regenerated
- **WHEN** canonical rules change
- **THEN** AGENTS, Claude, Copilot, and convention adapters share the expected source and body hashes

### Requirement: Project rule extensions survive framework update
`mase update` MUST distinguish generated MASE core rules from project-maintained extensions and MUST preserve extensions; ambiguous edits to generated or legacy undelimited rules MUST produce a backed-up conflict instead of silent overwrite.

#### Scenario: Project has a local rule extension
- **WHEN** framework core rules update in an adopted project
- **THEN** the core section updates and the local extension remains byte-for-byte present

#### Scenario: Legacy rules diverge ambiguously
- **WHEN** an adopted project's unmarked rule source differs from both installed and incoming canonical content
- **THEN** update reports conflict, writes no replacement, and retains a backup

### Requirement: Framework self-state is truthful
MASE's own `mase check`, `mase status`, and `openspec validate --all --strict` MUST pass on a clean working copy, and completed changes MUST have valid state or be archived consistently with repository policy.

#### Scenario: Governance validation runs
- **WHEN** the repository's governance commands are run after the repair
- **THEN** no completed change is falsely reported as gate-pending and no malformed delta change fails strict validation

### Requirement: Repository boundary is clean and reproducible
Strict boundary validation MUST exclude documented operating-system metadata consistently while rejecting unknown top-level content, nested products/repositories, build output, caches, and extracted historical material.

#### Scenario: Finder metadata exists
- **WHEN** `.DS_Store` exists but no prohibited framework content exists
- **THEN** the standard boundary command applies the documented metadata policy consistently

#### Scenario: Pytest runs in the repository
- **WHEN** tests execute with normal Python bytecode behavior
- **THEN** subsequent boundary validation is not made nondeterministic by generated cache files

### Requirement: Training source and deck match runtime vocabulary
The editable training source and generated PPTX MUST include the full release progression including `target_ready`, explain the compact teaching progression relative to all schema phases, and match the current framework version.

#### Scenario: Training deck verification runs
- **WHEN** the deck is rebuilt and verified from the editable YAML
- **THEN** required state vocabulary, version, editability, geometry, logo, and bounds checks all pass
