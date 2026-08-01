## ADDED Requirements

### Requirement: 工作包和 Capability 限定上下文
MASE SHALL 允许上下文计划指定工作包或 Capability，并 SHALL 将默认读取限定为项目规则、命中的当前 Spec、该工作包声明的 `reads`、相关测试/接口和显式读取项。

#### Scenario: 计划单个工作包
- **WHEN** change 包含多个能力且调用者指定一个带 `reads` 的任务
- **THEN** 计划不自动纳入其他任务、其他能力或整个 change 的宽泛影响目录

#### Scenario: 计划单个 Capability
- **WHEN** 调用者指定具有精确 paths 的 Capability
- **THEN** 计划只展开该 Capability 路径并报告使用的范围来源

### Requirement: 宽泛目录和不可读文件不自动展开
MASE MUST 不得把宽泛目录、二进制、隐藏缓存或默认排除路径自动作为 Agent 文本上下文；目录范围 SHALL 产生可操作诊断并要求更精确的工作包或显式读取。

#### Scenario: impact 声明整个 docs 目录
- **WHEN** change 级影响路径包含 `docs`
- **THEN** 默认计划报告 broad-scope 诊断而不递归读取全部文档

#### Scenario: 目录包含隐藏二进制文件
- **WHEN**候选目录包含 `.DS_Store` 或无法识别为文本的文件
- **THEN** 该文件被排除且字符预算不包含其解码替代文本

### Requirement: 上下文预算具有执行效果
MASE SHALL 在计划超过 Profile 文件数或字符预算时返回非成功执行结果，除非调用者使用显式超预算覆盖并提供可审计原因。

#### Scenario: Standard 计划超过字符预算
- **WHEN** 计划超过 Standard 的 `max_characters`
- **THEN** CLI 标记 budget-blocked 并推荐收窄任务、Capability 或读取路径

#### Scenario: 人工批准超预算读取
- **WHEN** 调用者显式允许超预算并提供原因
- **THEN** 计划保留 over-budget 状态、覆盖原因和代理指标，不把代理值报告为真实 Token
