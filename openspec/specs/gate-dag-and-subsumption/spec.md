# gate-dag-and-subsumption Specification

## Purpose
TBD - created by archiving change add-gate-dag-subsumption-and-cache. Update Purpose after archive.
## Requirements
### Requirement: 所有 gate 的 requires 构成有向无环图
MASE SHALL 对全部 gate 的 `requires` 做存在性、自依赖和环路校验，并 SHALL 按拓扑前序生成可执行计划。

#### Scenario: 普通合并 gate 缺少前序
- **WHEN** integration_tests requires api_contract 且 api_contract 尚无 fresh evidence
- **THEN** integration_tests 为 deferred，下一动作指向 api_contract

#### Scenario: Gate 依赖成环
- **WHEN** A requires B 且 B 直接或间接 requires A
- **THEN** 加载器在执行任何命令前拒绝配置并报告完整环路

### Requirement: 被覆盖状态保留来源
当一个 gate 的执行被另一 gate 完整覆盖时，MASE SHALL 将其记录为 `subsumed` 并绑定来源 execution、候选和环境摘要；状态判断可接受 subsumed，但审计不得把它显示为独立执行 passed。

#### Scenario: 全量回归覆盖相同候选的聚焦集合
- **WHEN** full_regression 的测试集合与输入满足显式 covers，且候选与环境等价
- **THEN** 被覆盖 gate 显示 subsumed 和来源，而不重复执行
