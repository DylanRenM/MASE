## ADDED Requirements

### Requirement: 冗余执行率只统计等价验证对象
MASE SHALL 将冗余定义为相同候选、相同输入、等价环境和相同业务时点下重复执行的测试节点，并 MUST 排除开发聚焦测试与发布候选全量认证之间的合理重复。

#### Scenario: 开发和发布分别运行同一测试
- **WHEN** 一个测试在 development 聚焦门禁和后续 frozen candidate 的 release 全量回归中各执行一次
- **THEN** 该行为不计入同候选冗余执行率
