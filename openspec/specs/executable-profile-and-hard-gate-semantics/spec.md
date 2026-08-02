# executable-profile-and-hard-gate-semantics Specification

## Purpose
TBD - created by archiving change close-mase-governance-and-safety-gaps. Update Purpose after archive.
## Requirements
### Requirement: Profiles compile into executable GatePlans
The system MUST compile base and capability Profile requirements for artifacts, gates, reviews, test schedules, and final verification into one GatePlan and MUST use that plan for check, status, and execution decisions.

#### Scenario: Standard capability reaches final verification
- **WHEN** a Standard change has related, integration, review, and final schedule requirements
- **THEN** completion remains blocked until each applicable requirement has fresh evidence or a valid required artifact

### Requirement: Risk escalation uses one registry
Top-level and capability risks MUST resolve through the same risk registry, apply each trigger's `minimum_profile`, and reject unknown risk identifiers with a diagnostic.

#### Scenario: Capability infrastructure change requires Strict
- **WHEN** a Lite capability declares `infrastructure_change` and the registry sets its minimum Profile to Strict
- **THEN** the effective capability and change Profile are at least Strict

#### Scenario: Risk identifier is misspelled
- **WHEN** a state file declares an identifier not present in the risk registry
- **THEN** validation fails and identifies the unknown trigger

### Requirement: Hard gates cannot be bypassed
A required hard gate MUST accept only fresh evidence from an allowed source for its complete signature and MUST NOT be satisfied by `skipped`, `passed_with_baseline`, a raw gate label, or an ordinary baseline record.

#### Scenario: API contract is skipped
- **WHEN** `api_contract` is required and state labels it `skipped`
- **THEN** consistency and lifecycle completion fail

#### Scenario: Security hard gate is offered for baseline
- **WHEN** a triggered security hard gate fails
- **THEN** baseline creation rejects it regardless of a static allow-list omission

### Requirement: Terminal lifecycle states are internally consistent
A change MUST NOT be complete or otherwise terminal while any GatePlan requirement is pending, stale, invalid, or absent.

#### Scenario: Complete phase has a pending gate
- **WHEN** phase is terminal but a required gate lacks satisfying evidence
- **THEN** status reports inconsistency and does not treat the change as complete

### Requirement: 旧 UI 布尔字段保守迁移
对于只声明 `ui_changed: true` 的旧状态，MASE MUST 在没有更精细分类前保守按 journey 处理，并 SHALL 提供迁移诊断而不静默降低 P0。

#### Scenario: 旧 change 仍可读取
- **WHEN** 2.3 状态包含 has_ui true 和 ui_changed true
- **THEN** 2.4 GatePlan 保持 P0 适用，并提示补充 ui_change_kind
