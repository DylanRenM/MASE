# Attack surfaces

- Untrusted input: validation order, canonicalization, size/depth limits and parser failure atomicity.
- AuthN/AuthZ: identity binding, object-level authorization, confused deputy and default-deny behavior.
- Secrets/crypto: secret origin, storage, logs, algorithm/mode and key lifecycle.
- Files/archives: traversal, symlink, decompression bombs, type confusion, permissions and cleanup.
- Execution: shell/SQL/template/deserialization injection and unsafe plugin loading.
- Sensitive data: logs, errors, telemetry, caches, exports and backup scope.
- Irreversible writes: authorization, idempotency, transaction boundary, confirmation and rollback.
