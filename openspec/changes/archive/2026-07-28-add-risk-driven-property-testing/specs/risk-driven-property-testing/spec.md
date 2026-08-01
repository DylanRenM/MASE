## ADDED Requirements

### Requirement: Risk-routed property testing
MASE SHALL route property-based or model-based testing when an affected contract has a large combinatorial input space, parsing or serialization behavior, numerical boundaries, collection/pagination semantics, a state machine, untrusted input, concurrency invariants, or compatibility changes. MASE SHALL NOT require property testing for every interface or introduce a global property-testing hard gate.

#### Scenario: Complex input domain is routed to property testing
- **WHEN** a contract contains parsing behavior with many valid, invalid, and boundary inputs
- **THEN** the development guidance requires evaluation of generators and invariant, metamorphic, round-trip, or model-based properties under the existing related contract gate

#### Scenario: Simple contract remains lightweight
- **WHEN** a contract has a small explicit input set and no applicable property-testing trigger
- **THEN** deterministic examples satisfy the test-design route without a fabricated property suite

### Requirement: Examples and properties remain complementary
MASE SHALL retain deterministic examples for canonical business scenarios, exact error contracts, and regression cases. Property tests SHALL supplement rather than replace those examples, and equality SHALL remain a valid oracle when required by the property.

#### Scenario: Known regression remains deterministic
- **WHEN** a generated test finds a minimal counterexample that represents a material defect
- **THEN** the fix retains that counterexample as a deterministic regression test in addition to any broader property

#### Scenario: Equality is the correct oracle
- **WHEN** a round-trip or reference-model property requires expected and actual values to be equal
- **THEN** the guidance permits an equality assertion instead of rejecting it as an example-only pattern

### Requirement: Property plans are traceable to the contract
The contract template SHALL let an applicable property record a stable Property ID, source Spec or Scenario, valid and invalid domains, explicit boundaries, oracle, isolation or cleanup requirement, and mapped test ID. Error responses SHALL be treated as contract behavior with the same traceability as successful responses.

#### Scenario: Property is derived from an accepted behavior
- **WHEN** an Agent defines a property test for an API contract
- **THEN** the property plan references the accepted Spec or Scenario and defines the data domains and oracle before implementation

#### Scenario: Stateful property protects the sandbox
- **WHEN** generated examples create or mutate persistent resources
- **THEN** the property plan specifies transaction rollback, per-example isolation, cleanup, or the applicable MASE Sandbox boundary

### Requirement: Contract semantics are not invented
MASE SHALL require idempotence, round-trip, backward compatibility, pagination completeness, timezone consistency, or concurrency consistency only when the accepted Spec, versioning policy, or public protocol declares the relevant semantic. It SHALL NOT infer that every POST is idempotent, every CRUD resource is deletable, or every missing field receives a default.

#### Scenario: POST has no declared idempotency contract
- **WHEN** an interface uses POST and neither the Spec nor protocol declares idempotency behavior
- **THEN** the Agent does not generate an idempotency property merely because the method is POST

#### Scenario: Compatibility behavior is declared
- **WHEN** a version change declares support for an old request and an old client decoder
- **THEN** the contract tests both the new server's request handling and the old consumer's response compatibility according to that policy

### Requirement: Counterexamples are reproducible evidence
Property-test failures SHALL preserve the Property ID, tool and version, seed or equivalent replay parameters, and the minimized counterexample in the existing gate log or artifact. A passing random rerun SHALL NOT by itself close the defect.

#### Scenario: Shrinking finds a minimal failure
- **WHEN** a property-testing tool shrinks a failing generated input
- **THEN** the gate evidence contains enough information to replay the minimized failure without relying on chance

#### Scenario: Tool has no automatic shrinking
- **WHEN** the selected stack's tool cannot shrink failures automatically
- **THEN** the test workflow records an equivalent minimization or reduction procedure before accepting the fix

### Requirement: Property guidance remains stack-neutral
MASE SHALL keep normative property-testing guidance independent of a specific library and SHALL load stack-specific examples only when the affected project uses that stack. The MASE runtime SHALL NOT gain a mandatory product PBT dependency.

#### Scenario: Python project selects Hypothesis
- **WHEN** a Python work package is routed to property testing and Hypothesis is available or selected
- **THEN** the Agent may load the Python/Hypothesis reference while the core contract remains tool-independent

#### Scenario: Non-Python project uses another tool
- **WHEN** a generic or Swift project is routed to property testing
- **THEN** the Agent follows the same domain, oracle, isolation, and counterexample contract without requiring Hypothesis
