## MODIFIED Requirements

### Requirement: Change 状态具有唯一事实来源
MASE MUST 以 change 的 `mase-state.yaml` 记录 Profile、stack、phase、risk、impact-analysis applicability/summary/reference 和 gate evidence，并拒绝从人工编写报告或生成的影响范围、测试范围、回滚视图反向推断状态。完整影响图 MUST 保存在引用的规范化影响分析产物中，不得复制进状态文件。

#### Scenario: 任务完成但阶段未更新
- **WHEN** 所有任务完成而 state 仍处于 build
- **THEN** `mase status` 报告状态不一致并返回非成功结果，而不是显示含糊的完成状态

#### Scenario: 生成视图与规范产物不一致
- **WHEN** 人工编辑的影响范围说明与状态引用的影响产物摘要不一致
- **THEN** MASE 以结构化产物和摘要校验结果为准并要求重新生成视图
