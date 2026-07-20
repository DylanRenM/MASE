# Runtime debugging escalation

Use only after ordinary tests, logs and static tracing cannot isolate a runtime-only defect.

1. Define one hypothesis and the minimum state needed to falsify it.
2. Add temporary, uniquely marked instrumentation without sensitive data.
3. Capture pre-fix evidence and reproduce once.
4. Apply the fix and capture comparable post-fix evidence.
5. Convert the evidence into a stable test.
6. Remove all temporary instrumentation and verify the diff is clean.

Do not start debug servers, expose ports or inject production instrumentation without explicit authority.
