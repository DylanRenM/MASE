## ADDED Requirements

### Requirement: Capability impact gates are independently derived
The system SHALL derive impact-analysis gates from each Capability's historical-change applicability, impact level, affected paths, uncertainty, and threshold decision without forcing unrelated capabilities to use the same analysis or verification scope. Impact level MUST NOT create a fourth Profile and MUST NOT remove existing Profile/risk gates.

#### Scenario: One capability has an L3 contract change
- **WHEN** a Standard change contains an L3 API capability and an unrelated L1 utility capability
- **THEN** architecture review and full-chain smoke apply to the API capability while the utility retains its L1 impact gates and the change-level final risk floor remains intact

### Requirement: Unmapped affected paths are conservative
When an affected caller or boundary cannot be mapped to a declared Capability, the GatePlan MUST use change-level scope and emit a governance diagnostic rather than omitting impact gates.

#### Scenario: Caller has no Capability mapping
- **WHEN** reconciliation discovers an affected path outside every declared Capability
- **THEN** the plan selects conservative change-level verification and reports the missing mapping
