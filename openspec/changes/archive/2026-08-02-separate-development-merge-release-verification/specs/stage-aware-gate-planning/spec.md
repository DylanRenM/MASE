## ADDED Requirements

### Requirement: Gate 声明最晚要求时点
每个 canonical gate SHALL 支持 `required_at: development|merge|release|observe`，GatePlan SHALL 只把不晚于当前目标时点的适用 gate 作为阻塞项。

#### Scenario: 请求开发验证计划
- **WHEN** 调用者为一个 change 请求 development 目标 GatePlan
- **THEN** 计划不要求生产构建、候选冻结、全量回归或发布审计 gate

#### Scenario: 旧 gate 配置
- **WHEN** gate 只有旧 `stage` 而没有 `required_at`
- **THEN** 系统使用记录在兼容规则中的确定性映射，并报告可迁移诊断

### Requirement: 候选绑定门禁不得提前
候选绑定 gate MUST 只在 release 或 observe 时点执行，Schema 或加载器 MUST 拒绝将其声明为 development 或 merge。

#### Scenario: 非法提前全量回归
- **WHEN** `full_regression` 同时声明 `candidate_bound: true` 和 `required_at: development`
- **THEN** MASE 在执行前拒绝该 gate 定义
