# token-efficient-context-routing Specification

## Purpose
TBD - created by archiving change adaptive-lightweight-mase. Update Purpose after archive.
## Requirements
### Requirement: IDE 规则由单一规则源生成
MASE MUST 从一个核心规则源生成各 IDE 适配文件，并在生成文件中记录源哈希和生成标记。

#### Scenario: 核心规则更新
- **WHEN** `project-rules.md` 发生变化并运行规则同步
- **THEN** AGENTS、CLAUDE、CONVENTIONS 和 Copilot 文件得到一致内容与相同 source hash

### Requirement: 任务声明最小读取上下文
MASE MUST 允许工作包声明 `reads`，并指导 Agent 默认只读取当前 Spec、相关接口/测试和 diff。

#### Scenario: 实现单个 capability
- **WHEN** 工作包只涉及一个 capability
- **THEN** Agent 不默认加载其他 capability 的详细设计、历史 change 或培训材料

### Requirement: Skill 按风险加载参考路径
MASE MUST 将长 Skill 的分诊入口与详细参考分离，只有命中的风险或问题类型才能触发对应参考加载。

#### Scenario: 普通低风险代码评审
- **WHEN** Lite 项目请求评审小范围 diff 且无高风险攻击面
- **THEN** 系统使用短版 diff review，不加载多轮审查和所有语言 Bug 模式

### Requirement: Token 度量区分真实值和代理值
MASE MUST 接受平台提供的 input/output/cache Token，并在缺失时只报告文件数、字符数等代理指标，不得把估算冒充真实 Token。

#### Scenario: 平台未提供 usage
- **WHEN** metrics 没有真实 Token 输入
- **THEN** 输出明确标记为 context proxy，并显示被读取文件与字符数
