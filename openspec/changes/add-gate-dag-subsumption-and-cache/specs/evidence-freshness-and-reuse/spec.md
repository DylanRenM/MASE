## ADDED Requirements

### Requirement: 缓存键绑定完整验证环境
自动 evidence 的缓存键 MUST 包含 gate 命令、规范化 Test ID/selector 集、源码与测试输入摘要、依赖锁摘要、工具链版本、fixture/config 摘要、候选 ID、scope 和适用 release context。

#### Scenario: 依赖锁变化
- **WHEN** 源码与测试未变但 dependency lock digest 变化
- **THEN** 旧 evidence 不得命中缓存或覆盖新执行

#### Scenario: 完全相同执行对象
- **WHEN** 所有缓存键分量相同且 evidence fresh
- **THEN** Gate Runner 复用已有 execution 并报告 cache hit

### Requirement: 跨 gate 覆盖要求等价或更严格
源 gate 只有在测试集合与输入为目标超集、候选相同、工具链和依赖相同、fixture/config 等价且环境相同或更严格时 SHALL 产生 subsumed evidence。

#### Scenario: Fixture 不等价
- **WHEN** 源 gate 使用 mock fixture 而目标要求受控真实持久化
- **THEN** 覆盖被拒绝，目标 gate 保持待执行
