## ADDED Requirements

### Requirement: Capability 使用稳定测试选择器
Capability gate SHALL 从 `.mase/tests.yaml` 选择稳定 Test ID 和最小可执行 selector，并 SHALL 在 evidence 中记录实际选择，避免以整个测试文件代替不同语义门禁的范围。

#### Scenario: 修改影响治理 Capability
- **WHEN** 影响路径只命中影响治理实现
- **THEN** 差异契约、冒烟和回滚 gate 分别获得与其语义匹配的 node selector，而不是共同运行完整影响测试文件

### Requirement: 同一边界避免重复测试节点
GatePlan SHALL 报告同一 Capability 边界中一个测试节点被多个 automatic gate 重复选择的次数，并 SHALL 推荐显式覆盖或 selector 分离；最终候选全量回归不计入可删除的边界重复。

#### Scenario: 前置门禁重复节点超过阈值
- **WHEN** capability 阶段多个 gate 的规范化 selector 重复比例超过配置阈值
- **THEN** 计划输出重复节点数量、涉及 gate 和收窄建议
