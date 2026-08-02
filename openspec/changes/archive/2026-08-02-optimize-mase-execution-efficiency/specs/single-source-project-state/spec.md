## ADDED Requirements

### Requirement: 唯一状态源使用 evidence 索引
`mase-state.yaml` SHALL 继续作为 Profile、phase、risk、gate 当前结果和 evidence 索引的唯一状态源，但完整历史 evidence MAY 存放在由状态摘要完整引用的项目内 sidecar，报告不得从日志正文反推状态。

#### Scenario: 完整 evidence 位于 sidecar
- **WHEN** 状态摘要引用经过 digest 绑定的 evidence sidecar
- **THEN** `mase status` 从摘要和被引用记录验证当前结果，仍不接受人工报告替代结构化证据

#### Scenario: sidecar 被修改或丢失
- **WHEN** 状态引用的 evidence 详情不存在或 digest 不匹配
- **THEN** 对应 gate 变为 missing 或 invalid，而不是继续显示 passed
