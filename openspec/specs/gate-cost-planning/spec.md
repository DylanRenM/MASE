# gate-cost-planning Specification

## Purpose
TBD - created by archiving change add-gate-cost-planning-and-metrics. Update Purpose after archive.
## Requirements
### Requirement: GatePlan 展示历史成本估计
MASE SHALL 从结构化 evidence 计算每个 gate 和 development、merge、release、observe 目标的历史 p50/p90 预计耗时，并 SHALL 显示样本数、未知状态和缓存/覆盖后的增量成本。

#### Scenario: L1 开发计划有足够样本
- **WHEN** 当前 L1 change 的 development gate 至少有三个等价历史样本
- **THEN** GatePlan 显示开发验证 p50/p90、逐 gate 明细和估计依据

#### Scenario: 没有历史样本
- **WHEN** 一个新 gate 没有可比 evidence
- **THEN** 预计耗时标记 unknown，而不是显示 0

### Requirement: 预算超限不得降低门禁
当阶段预计耗时超过配置预算时，MASE SHALL 报告重复 selector、缓存机会、风险等级和可延迟的后续门禁，但 MUST NOT 自动跳过硬门禁。

#### Scenario: L2 开发验证预计超过十五分钟
- **WHEN** L2 development p90 超过默认预算
- **THEN** 计划建议收窄 selector 或复核分级，所有适用硬 gate 仍保持选中

### Requirement: 效率指标语义明确
MASE SHALL 报告同候选等价冗余率、缓存命中率、失败定位时间、代码完成到 dev_verified 和候选冻结到 release_ready 的耗时，并 SHALL 对缺失事件返回 unknown。

#### Scenario: 开发聚焦与发布全量均执行
- **WHEN** 两次执行属于不同 required_at 或不同候选对象
- **THEN** 指标不把它们计为等价冗余
