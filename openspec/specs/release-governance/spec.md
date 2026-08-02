# release-governance Specification

## Purpose
TBD - created by archiving change add-release-governance-and-skill. Update Purpose after archive.
## Requirements
### Requirement: Optional Release Overlay
MASE SHALL accept an optional platform-neutral Release Overlay without changing the validity or gate plan of changes that do not declare release intent.

#### Scenario: Legacy change without release intent
- **WHEN** a valid existing `mase-state.yaml` has no `release` object
- **THEN** MASE validates and plans the change using its existing Profile, risks, and gates

#### Scenario: Change declares a production deployment
- **WHEN** a state declares release intent, artifact, target, rollout, state impact, interfaces, and recovery metadata
- **THEN** MASE validates the overlay and exposes its release outcome separately from the development phase

### Requirement: Release outcome distinguishes readiness levels
MASE MUST distinguish candidate readiness, artifact readiness, target readiness, live verification, observation, and recovery outcomes so a built package cannot be reported as a verified production release.

#### Scenario: Artifact has passed local checks only
- **WHEN** artifact gates pass but target/live/observation gates have no fresh evidence
- **THEN** release status reports `artifact_ready` and does not report `live_verified` or `observed`

#### Scenario: Live release has completed observation
- **WHEN** all required artifact, preflight, live, and observation gates have fresh passing evidence
- **THEN** release status reports `observed`

### Requirement: Release gates are evidence-bound
MASE SHALL support `release_artifact`, `release_preflight`, `release_live`, and `release_observe` gate stages and SHALL preserve the existing rule that only Gate Runner or explicitly allowed manual evidence can satisfy them.

#### Scenario: Artifact identity changes
- **WHEN** a gate's configured release artifact changes after passing evidence was recorded
- **THEN** the evidence becomes stale and cannot satisfy the release gate

#### Scenario: Checklist is generated
- **WHEN** `mase release plan` generates a complete runbook
- **THEN** all derived release gates remain pending until evidence is recorded

### Requirement: Release risk adapts independently of Profile
MASE SHALL add release-specific risk triggers for cross-platform deployment, runtime configuration change, stateful upgrade, public exposure, multi-service release, and infrastructure change, while preserving Profile escalation semantics.

#### Scenario: Ordinary stateless publication
- **WHEN** a Standard change declares a package publication without high-risk release triggers
- **THEN** MASE adds applicable release gates without escalating the whole change to Strict

#### Scenario: Infrastructure change is bundled into a release
- **WHEN** a release declares an infrastructure-change trigger
- **THEN** MASE escalates to the configured minimum Profile and requires independent recovery/security evidence

### Requirement: Release CLI is read-only
MASE SHALL provide release planning and status commands that validate and report release contracts without performing production mutations.

#### Scenario: Generate JSON release plan
- **WHEN** a user runs the release planner for a valid cross-platform context with JSON output
- **THEN** the CLI returns invariant groups, pending gates, hard stops, and selected adapters without modifying the target or state

#### Scenario: Invalid contradictory context
- **WHEN** a release context declares a canary rollout without observation signals or a stateful migration without recovery strategy
- **THEN** the CLI exits non-zero with actionable validation errors

### Requirement: 发布认证接续合并验证
MASE SHALL 在 `merge_verified` 后才允许冻结候选，并 SHALL 只在显式 Release Overlay intent 存在时要求发布与观察时点 gate。

#### Scenario: 没有发布意图的合并验证
- **WHEN** change 已达到 `merge_verified` 但没有 Release Overlay
- **THEN** 系统不把发布、线上验证或观察 gate 作为当前阻塞项

#### Scenario: 发布候选认证
- **WHEN** 候选 fresh 且所有适用 release 时点 gate 对同一候选通过
- **THEN** 状态报告 `release_ready`，但在真实消费者验证前不报告 `live_verified`
