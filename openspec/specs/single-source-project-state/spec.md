# single-source-project-state Specification

## Purpose
TBD - created by archiving change adaptive-lightweight-mase. Update Purpose after archive.
## Requirements
### Requirement: Change 状态具有唯一事实来源
MASE MUST 以 change 的 `mase-state.yaml` 记录 Profile、stack、phase、risk、impact-analysis applicability/summary/reference 和 gate evidence，并拒绝从人工编写报告或生成的影响范围、测试范围、回滚视图反向推断状态。完整影响图 MUST 保存在引用的规范化影响分析产物中，不得复制进状态文件。

#### Scenario: 任务完成但阶段未更新
- **WHEN** 所有任务完成而 state 仍处于 build
- **THEN** `mase status` 报告状态不一致并返回非成功结果，而不是显示含糊的完成状态

#### Scenario: 生成视图与规范产物不一致
- **WHEN** 人工编辑的影响范围说明与状态引用的影响产物摘要不一致
- **THEN** MASE 以结构化产物和摘要校验结果为准并要求重新生成视图

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

### Requirement: 唯一状态源使用 evidence 索引
`mase-state.yaml` SHALL 继续作为 Profile、phase、risk、gate 当前结果和 evidence 索引的唯一状态源，但完整历史 evidence MAY 存放在由状态摘要完整引用的项目内 sidecar，报告不得从日志正文反推状态。

#### Scenario: 完整 evidence 位于 sidecar
- **WHEN** 状态摘要引用经过 digest 绑定的 evidence sidecar
- **THEN** `mase status` 从摘要和被引用记录验证当前结果，仍不接受人工报告替代结构化证据

#### Scenario: sidecar 被修改或丢失
- **WHEN** 状态引用的 evidence 详情不存在或 digest 不匹配
- **THEN** 对应 gate 变为 missing 或 invalid，而不是继续显示 passed

### Requirement: 过程阶段与验证里程碑分开报告
`mase status` SHALL 同时报告人工维护的 OpenSpec phase、证据派生的 verification milestone 和独立的 release outcome，并 SHALL 给出每个后续里程碑的未满足原因。

#### Scenario: Build 阶段已可手测
- **WHEN** phase 为 build 且 development gate 全部 fresh passed
- **THEN** 状态可报告 `dev_verified`，而不会因 phase 尚未进入 verify 抹去开发验证结果
