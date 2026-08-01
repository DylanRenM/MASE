# Artifact and state

## Artifact integrity

- Build from an explicit source/candidate, not an accidentally dirty workspace.
- Assign one immutable identity; never select a release by “latest”, timestamp guessing, or a reused unversioned directory.
- Verify the outer and nested payloads actually delivered. Commit metadata alone does not prove compiled bundles, generated resources, configuration, or user-visible content are current.
- Record provenance, file/content manifest, integrity proof, build inputs, and applicable signature/attestation.
- Scan forbidden content. Exclude secrets, private keys, production data, logs, backups, local environments, caches, and unrelated state unless the contract explicitly defines a protected migration package.
- Separate installation, upgrade, hotfix, package publication, and state-transfer artifacts. Never overwrite target state with development state by accident.

## Configuration and capabilities

Treat required configuration changes as a migration. Validate names, presence, syntax, precedence, target/runtime compatibility, and non-secret routing files before impact. Report secret presence or identity, never secret values.

Inventory external capabilities by behavior, not vendor name: protocol, authentication, model/tool support, quotas, network reachability, and expected response. Verify each capability through its real consumer path.

## Stateful change

Classify filesystem, database, object, queue, cache, registry, device, and external-service state independently. Define ownership and compatibility for each.

- Create a consistent backup/snapshot appropriate to the state engine.
- Preserve relative identity so same-named files or resources cannot overwrite one another.
- Validate backup completeness and restore usability; “copy command succeeded” is not evidence.
- Prefer expand/contract or forward-compatible migrations. Define rollback versus roll-forward before impact.
- Back up the target before restore or overwrite. Preserve the failed target and logs for diagnosis.
- Delay destructive cleanup until observation and recovery evidence are complete.
