# Platform adapters

Load only the sections selected by the release context. These adapters refine the invariant kernel; they never replace it.

## Container / orchestrator

Resolve image tags to digests; inspect manifest/platform compatibility and runtime user; scan layers and configuration; verify pull credentials, scheduling, probes, disruption budgets, resource limits, rollout state, service/endpoints, events, and logs. Test the declared consumer interface, not only pod readiness.

## VM / service manager

Check runtime and service-manager compatibility, paths/permissions, disk, ports, working directory, environment source, logs, startup/restart behavior, staging, atomic switch feasibility, and prior-version retention. Avoid relying on interactive-shell environment state.

## Serverless

Verify package/image identity, runtime, architecture, environment, permissions, triggers/routes, concurrency, timeout, cold-start behavior, aliases/versions, and rollback routing. Exercise the real trigger and downstream capabilities.

## Package registry

Validate package metadata, immutable version, signature/provenance, dependency constraints, forbidden files, install/resolve behavior, and consumer smoke tests from the target registry.

## Distributed client / app store

Verify signed/notarized build identity, entitlements/permissions, store metadata, review state, staged cohort, upgrade from supported versions, clean install, protocol compatibility, telemetry, crash signals, and mitigation/kill-switch strategy.

## Interface adapters

- HTTP/API: verify route, TLS, status, headers, schema/body, cache/proxy behavior, and authentication.
- Browser/UI: use the production build and real entry point; test clean state and supported upgrade state; confirm visible behavior and static resources rather than trusting cached assets.
- Events/queues: publish and consume uniquely identifiable probes; verify schema/version, ordering/deduplication contract, retry/dead-letter behavior, lag, and side effect.
- CLI/package: install or invoke from a clean target environment and verify exit codes, output contract, and side effects.

## Windows / PowerShell (conditional)

Check PowerShell/version and encoding behavior, reserved automatic variables such as `$PID`, execution policy, service/session boundaries, path quoting, process ownership, and stderr semantics. Do not assume `winget` exists. Avoid current-working-directory-dependent configuration loading. Distinguish file and directory cleanup and make both idempotent.

## Linux / Unix (conditional)

Check architecture/libc/runtime, user/group and file modes, service manager/container runtime, signals and graceful shutdown, filesystem mount semantics, environment/config source, limits, ports, logs, and atomic symlink/directory switch behavior.

## macOS / Unix (conditional)

Check architecture and universal-binary requirements, signing/notarization and quarantine attributes, launchd/service boundaries, sandbox entitlements, paths and file modes, keychain/config sources, signals, logs, and atomic bundle/directory replacement.

## Generic platform (conditional)

When the target platform is absent or unknown, keep commands platform-neutral, identify the runtime and filesystem/process constraints explicitly, and stop before mutation until a concrete compatible adapter is selected.
