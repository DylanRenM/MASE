## ADDED Requirements

### Requirement: Change 状态具有唯一事实来源
MASE MUST 以 change 的 `mase-state.yaml` 记录 Profile、stack、phase、risk 和 gate evidence，并拒绝从人工编写报告反向推断状态。

#### Scenario: 任务完成但阶段未更新
- **WHEN** 所有任务完成而 state 仍处于 build
- **THEN** `mase status` 报告状态不一致并返回非成功结果，而不是显示含糊的完成状态

### Requirement: 报告由证据自动生成
MASE MUST 从 state、Spec ID、测试标签和验证命令结果生成状态、追踪与验证摘要，不要求 Agent重复抄写通过数量。

#### Scenario: 验证命令完成
- **WHEN** 单元、集成、契约和 E2E 命令写入结构化 evidence
- **THEN** 状态输出包含各门禁结果、时间和证据路径

### Requirement: Master 仅作为归档快照
MASE MUST 在 release/archive 时生成只读系统快照，日常开发不得要求模型对 change 与 master 进行双写语义合并。

#### Scenario: Design 完成
- **WHEN** change 通过 Design 门禁
- **THEN** 系统更新 change 状态但不要求立即重写 `openspec/master/`

#### Scenario: Change 归档
- **WHEN** change 完成并归档
- **THEN** 系统生成可追溯到 change 和提交的 master 快照
