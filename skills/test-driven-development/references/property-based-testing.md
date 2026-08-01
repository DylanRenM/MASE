# Risk-driven property and model testing

Load this reference only after the affected contract is routed here. Property-based testing (PBT) samples and shrinks a broad input domain; it is not exhaustive proof, and it does not replace accepted business examples.

## 1. Confirm applicability

Prefer property or model testing when at least one condition holds:

- the valid or invalid input space is combinatorial;
- parsing, encoding, serialization or format conversion should preserve declared information;
- numerical precision, overflow or boundary behavior matters;
- collection, sorting, pagination, deduplication or aggregation has algebraic invariants;
- a state machine or operation sequence has modelable transitions;
- untrusted inputs need broad rejection and failure-atomicity coverage;
- concurrency has a declared final-state invariant;
- a versioning policy declares provider/consumer compatibility behavior.

Use deterministic examples alone when the domain is small and explicit. Never invent a fixed minimum number of properties.

## 2. Derive the property from the Spec

For each property record:

1. `Property ID` and source Spec/Scenario.
2. Valid domain, invalid domain and explicit boundaries.
3. Oracle: invariant, equality, set relation, reference model, Round-trip, or metamorphic relation.
4. State isolation and cleanup.
5. Test ID and existing contract/integration gate.

Equality such as `decode(encode(x)) == normalized(x)` is a valid property oracle. A ban on `expected == actual` confuses hard-coded examples with equality itself.

Candidate properties such as idempotence, Round-trip, backward compatibility, pagination completeness, timezone normalization and concurrent final-state consistency apply only when the Spec, versioning policy or public protocol declares the corresponding behavior.

## 3. Design generators

- Keep valid and invalid domains separate. For invalid-domain tests, keep unrelated fields valid so the assertion identifies the intended error contract.
- Include exact boundaries deliberately; fixed boundary values are useful and are not prohibited merely because they are fixed.
- Generate only data the contract permits. `None`, empty strings, arbitrary Unicode, NaN and infinity are not universal requirements.
- Do not sample production records, secrets or personal data.
- Bound recursive structures, list sizes and operation sequences according to the risk and gate budget, not a universal example count or deadline.
- For stateful I/O use transaction rollback, a per-example namespace, deterministic fakes at the unit boundary, or the MASE Sandbox.

## 4. Preserve failures

The existing Gate Runner log or artifact must retain:

- Property ID;
- tool and version;
- seed, generated example database entry, or equivalent replay parameters;
- the shrink/minimization result;
- the command needed to reproduce the failure.

Do not accept “the next random run passed” as a fix. Reproduce the minimized failure deterministically before implementation, and retain a material counterexample as a regression after the broader property is green. If the tool has no automatic shrinking, record a manual or tool-assisted reduction procedure.

## 5. Python with Hypothesis

Hypothesis is one optional Python implementation, not a MASE runtime dependency.

- Prefer domain strategies built from Schema and business constraints over unconstrained dictionaries.
- Hypothesis performs shrinking automatically; preserve its reproduction information rather than adding custom print-only failure handling.
- For state machines, consider `RuleBasedStateMachine` only when operation sequences are part of the accepted behavior.
- Configure `max_examples`, deadline, health checks and example database according to test cost and environment. There is no universal setting for all tests.
- For API properties, isolate every generated example. A fixed idempotency key shared across different generated payloads creates cross-example pollution; generate a fresh key per example and reuse it only within the calls whose idempotency is being tested.
- For 金额 and other exact decimal quantities, prefer an integer minor unit or `Decimal` strategy when required by the contract; unrestricted binary floats can create false precision failures. Exclude NaN and infinity unless explicitly supported.
- Ensure generated UUID and date/time objects are encoded into the actual wire representation before sending JSON.

## 6. Compatibility and stateful boundaries

- Request compatibility requires old request fixtures against the new provider.
- Response compatibility requires the actual old decoder/client contract against new responses; checking only that the new server ignores extra fields does not prove the old client survives.
- Missing fields receive defaults only when the version policy says so.
- CRUD does not automatically imply `Create -> Get -> Delete`; immutable, soft-delete, asynchronous and read-only resources have different models.
- All POST requests are not automatically idempotent. Test idempotency only when the contract declares an idempotency key or equivalent semantics.

## Rejected blanket rules

- “PBT must 替代样例测试.”
- “所有 POST or PUT must be repeated N times.”
- “Every interface must define at least three invariants.”
- “Every optional field must accept null.”
- “Every test must use the same example count and deadline.”
- “A 固定幂等键 may be reused across all generated examples.”
