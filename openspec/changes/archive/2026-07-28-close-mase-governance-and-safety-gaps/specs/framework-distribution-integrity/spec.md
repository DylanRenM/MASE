## ADDED Requirements

### Requirement: Wheel runtime resources match the manifest
The normalized runtime resource set in `framework-manifest.yaml` MUST be included in built wheels without duplicate declarations, including every file in the release Skill.

#### Scenario: Clean wheel is inspected
- **WHEN** a wheel is built from a clean temporary copy and its contents are compared with the manifest
- **THEN** no required runtime resource is missing and duplicate manifest entries are rejected

### Requirement: Package versions remain synchronized
Python and JavaScript package metadata and lock metadata MUST report the same framework release version.

#### Scenario: Metadata validation runs
- **WHEN** package metadata is checked in CI
- **THEN** `pyproject.toml`, `package.json`, and `package-lock.json` versions agree

### Requirement: Release Skill is portable and discoverable
The release Skill MUST contain valid skill metadata, invoke its bundled planning script through a location-independent framework command or resolved Skill path, and select explicit Windows, macOS, Linux/Unix, or generic adapters according to the target.

#### Scenario: Skill is used from a product root
- **WHEN** an agent plans a release while its current directory is not the Skill directory
- **THEN** the documented command resolves and produces a plan without assuming a repository-relative `scripts/` path

#### Scenario: Linux target is selected
- **WHEN** target metadata indicates Linux or Unix
- **THEN** adapter selection includes the Linux/Unix guidance rather than only a generic or Windows branch

### Requirement: Documentation links resolve
Every in-repository relative link from distributed Skills and framework documentation MUST resolve to a shipped resource or use a correct repository-relative path.

#### Scenario: Skill link audit runs
- **WHEN** distributed Skill Markdown links are checked
- **THEN** no referenced framework document is missing from the resolved location
