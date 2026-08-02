---
name: security-review
description: Risk-routed security review of a specified diff or capability, reporting only concrete and reachable vulnerabilities.
---

# Security review router

## Attack-surface triage

Deep review is required when scope handles untrusted input, authentication/authorization, secrets, cryptography, file/archive parsing, network boundaries, command/code execution, sensitive logging or irreversible writes.

For a low-risk internal diff, perform a short triage and stop if no attack surface changed. Load `references/attack-surfaces.md` only for matched surfaces.

## Procedure

1. Establish scope and author intent from affected Spec and diff.
2. Identify trust boundaries, attacker-controlled values and privileged effects.
3. Trace an end-to-end exploit or concrete confidentiality/integrity/availability failure.
4. Check existing framework/language mitigations before reporting.
5. Require an exact location, severity, confidence and remediation test.

## Exclusions

Do not report generic hardening, unavailable attack paths, dependency CVEs without the dependency/version, test-only fixtures with no production path, or issues outside the requested scope.

## Output

Return a concise findings table ordered by severity. A clean review states examined surfaces and remaining assumptions; it does not invent low-confidence warnings.
