## ADDED Requirements

### Requirement: Sandbox mutations remain within allowed roots
Snapshot, backup, restore, deletion, and verification MUST canonicalize paths and MUST reject absolute inputs, traversal, symlink escape, and any resolved target outside configured allowed roots before filesystem mutation.

#### Scenario: Traversal points outside the project
- **WHEN** a configured mutable path contains `..` and resolves outside an allowed root
- **THEN** Sandbox fails before reading, copying, deleting, or restoring the target

#### Scenario: Symlink escapes an allowed root
- **WHEN** a path lexically inside the project resolves through a symlink to an outside location
- **THEN** Sandbox rejects the operation and leaves the outside location unchanged

### Requirement: Never-backup exclusions are enforced
Sandbox MUST apply `never_backup` patterns to every snapshot candidate and MUST NOT copy excluded secrets, caches, or forbidden content into backup storage.

#### Scenario: Excluded file is under a mutable directory
- **WHEN** a file matches `never_backup` beneath a configured mutable directory
- **THEN** the snapshot manifest and backup do not contain that file

### Requirement: Backups preserve relative identity and nested structure
Sandbox MUST identify backup entries by normalized root-relative paths, avoid same-basename collisions, and restore and verify nested files and directories exactly according to the snapshot manifest.

#### Scenario: Two files share a basename
- **WHEN** different nested directories contain files with the same basename
- **THEN** backup and restore preserve both files with their original content

### Requirement: Sandbox configuration has a truthful schema
The distributed Sandbox configuration template MUST reference a shipped schema that validates allowed roots, mutable paths, backup exclusions, and platform-neutral path semantics.

#### Scenario: Template schema is resolved
- **WHEN** a consumer validates the distributed Sandbox template
- **THEN** the referenced schema exists in the framework distribution and validation succeeds
