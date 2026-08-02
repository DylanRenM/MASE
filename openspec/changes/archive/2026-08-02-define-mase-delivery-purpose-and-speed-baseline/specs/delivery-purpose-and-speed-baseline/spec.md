## ADDED Requirements

### Requirement: 顶层设计宗旨统一框架取舍
MASE SHALL 以“让 Agentic Coding 高效交付正确、健壮、优化且易于维护的代码，确保正确满足需求、软件可靠运行，并持续消除坏味道”作为顶层设计宗旨，并 SHALL 将其映射到高效交付、需求正确、运行健壮、质量优化和整洁可维护五个可验证结果维度。

#### Scenario: 评审一项流程优化
- **WHEN** 一项建议能缩短等待，但会削弱契约、可靠性或可维护性
- **THEN** MASE 拒绝以该建议冒充高效交付，并保留适用的质量要求

### Requirement: 速度收益可复算且分阶段
MASE SHALL 分别计算代码完成到 `dev_verified`、候选冻结到 `release_ready` 和质量调整后交付效率，并 MUST 用等价环境下的结构化 evidence 显示样本数、p50/p90 或 `unknown`。

#### Scenario: 估算优化后可手测速度
- **WHEN** 已知优化前手测前门禁耗时和 2.4 development 时点门禁耗时
- **THEN** 系统或文档按 `1 - T_new(dev_verified) / T_old(pre-hand-test)` 给出收益，并同时报告未被删除的后续发布认证

#### Scenario: 历史样本不足
- **WHEN** 一个 gate 的等价历史样本少于 3 个
- **THEN** MASE 将 percentile 标记为 `unknown`，不使用 0 或单次观测冒充 p50/p90

### Requirement: 提速估算不降低质量
MASE MUST NOT 将延迟到 release 执行的硬门禁计为被消除的总成本，并 SHALL 将可手测等待、发布认证、缓存/冗余、返工和逸出缺陷分开报告。

#### Scenario: 全量回归从开发时点移到发布时点
- **WHEN** 同一套候选绑定全量回归仍在发布前执行
- **THEN** MASE 可将早期等待缩短计入可手测收益，但不将该全量回归从发布总成本中删除

### Requirement: 优化与坏味道处置必须可验证
MASE SHALL 要求性能、资源、安全或算法优化具有可测目标和前后对比，并 SHALL 在消除重复、过度耦合、过大单元、隐式契约或过期代码时保护已有行为。

#### Scenario: 重构以消除坏味道
- **WHEN** Agent 通过拆分过大函数或去除重复实现改善可维护性
- **THEN** 它在修改前锁定受保护行为和影响边界，在修改后运行相关回归并复扫实际影响
