## ADDED Requirements

### Requirement: 发布认证接续合并验证
MASE SHALL 在 `merge_verified` 后才允许冻结候选，并 SHALL 只在显式 Release Overlay intent 存在时要求发布与观察时点 gate。

#### Scenario: 没有发布意图的合并验证
- **WHEN** change 已达到 `merge_verified` 但没有 Release Overlay
- **THEN** 系统不把发布、线上验证或观察 gate 作为当前阻塞项

#### Scenario: 发布候选认证
- **WHEN** 候选 fresh 且所有适用 release 时点 gate 对同一候选通过
- **THEN** 状态报告 `release_ready`，但在真实消费者验证前不报告 `live_verified`
