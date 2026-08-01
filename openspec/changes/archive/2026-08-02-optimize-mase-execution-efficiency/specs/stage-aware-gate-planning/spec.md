## ADDED Requirements

### Requirement: 测试包含关系诊断
MASE SHALL 对 gate 的稳定 Test ID 或规范化 selector 同时计算 Jaccard 和双向包含率，并 SHALL 在任一集合被另一集合高比例包含且没有显式覆盖关系时报告重复风险。

#### Scenario: 冒烟集合完全包含于契约集合
- **WHEN** `full_chain_smoke` 的全部 selector 都存在于更大的 `api_contract` 集合且未声明 covers
- **THEN** GatePlan 报告 100% 小集合包含率并要求拆分语义 selector 或证明覆盖

#### Scenario: 两个 gate 仅少量交集
- **WHEN** gate 只共享基础 fixture 或少量测试
- **THEN** 系统不因低包含率自动宣称重复或等价

### Requirement: 默认计划只展示必需门禁
`mase gate plan` SHALL 默认展示当前 GatePlan 必需 gate、必要前序和阻塞项；未触发的项目 gate SHALL 仅在显式完整视图中展示。

#### Scenario: Standard change 未触发安全风险
- **WHEN** 项目定义 security 和 independent gate 但当前 change 不要求它们
- **THEN** 默认计划不把这些 gate 显示为 runnable 或 manual

#### Scenario: 请求完整计划
- **WHEN** 调用者使用 `--all`
- **THEN** 输出包含未触发 gate，并明确标记 optional/not-selected

### Requirement: 下一步命令匹配 gate 模式
GatePlan SHALL 根据前序 gate 的 automatic/manual 模式生成可执行的下一步命令。

#### Scenario: Final 被人工架构评审阻塞
- **WHEN** 候选冻结前缺少 manual architecture review
- **THEN** 下一步为 `mase gate manual` 而不是尝试自动运行该 gate
