## ADDED Requirements

### Requirement: 验证里程碑由新鲜证据派生
MASE SHALL 独立派生 `working`、`dev_verified`、可选 `user_confirmed`、`merge_verified`、`candidate_frozen`、`release_ready`、`live_verified` 和 `observed`，并 MUST NOT 接受原始状态标签替代门禁证据。

#### Scenario: 聚焦测试完成后可手测
- **WHEN** development 时点的所有适用 gate 均为 fresh passed，但 merge/release gate 尚未执行
- **THEN** 状态报告 `dev_verified`，并明确允许本地手测但尚不可合并或发布

#### Scenario: 候选输入变化
- **WHEN** 已冻结候选的任一绑定输入发生变化
- **THEN** `candidate_frozen` 失效，后续 release_ready 也不得成立

### Requirement: 用户确认是可选里程碑
MASE SHALL 仅在项目显式声明适用的人工确认 gate 时派生 `user_confirmed`，并 SHALL 允许不需要手工确认的 change 从 `dev_verified` 进入 `merge_verified`。

#### Scenario: 自动化变更不需要手测
- **WHEN** change 未选择用户确认 gate 且 merge gate 全部通过
- **THEN** 系统报告 `merge_verified`，不会因缺少形式化手测证据阻塞
