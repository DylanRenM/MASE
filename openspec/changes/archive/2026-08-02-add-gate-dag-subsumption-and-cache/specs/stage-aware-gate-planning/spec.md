## ADDED Requirements

### Requirement: GatePlan 遵循显式 DAG 前序
GatePlan SHALL 在阶段和 required_at 筛选后，对选中的 gate 及其传递前序做拓扑排序，并 SHALL 把必要前序包含在默认视图中。

#### Scenario: 可选 gate 是必需前序
- **WHEN** 一个当前必需 gate requires 一个未被风险直接选择的 gate
- **THEN** 默认计划仍包含该前序，并标记其被包含的依赖原因
