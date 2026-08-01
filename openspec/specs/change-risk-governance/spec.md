# change-risk-governance Specification

## Purpose
TBD - created by archiving change add-risk-adaptive-lite-change-workflow. Update Purpose after archive.
## Requirements
### Requirement: Change Risk 独立于 Profile 与影响等级
MASE SHALL 为每个 change 记录 L1–L4 Change Risk 及固定风险维度，并 SHALL 分别呈现 Profile、Change Risk 与历史代码 Impact Level。

#### Scenario: Standard 项目的纯展示改动
- **WHEN** 基础 Profile 为 Standard，但本次变更仅为可逆的 presentation UI 修改且稳定回归存在
- **THEN** Change Risk 可为 L1，同时 Profile 仍保持 Standard

#### Scenario: 同时存在影响链等级
- **WHEN** change_risk.level 为 L3 且 impact_analysis.level 为 L2
- **THEN** 状态输出分别标记变更风险 L3 和影响等级 L2，不合并或覆盖二者

### Requirement: 硬风险定义不可降级下限
MASE MUST 将认证、授权、密钥、额度、数据迁移或不可逆写入至少提升为 L4，并 MUST 将公共 API、核心算法、跨模块业务语义、并发或持久状态机至少提升为 L3；迁移与并发/持久状态组合仍为 L4。

#### Scenario: 用户低报认证改动
- **WHEN** 状态声明 L1 但 authentication 维度为 true
- **THEN** GatePlan 使用 L4 并报告硬下限升级原因

### Requirement: UI 改动按行为类别路由
MASE SHALL 区分 presentation、interaction 和 journey；只有 journey 或影响关键业务闭环的 interaction MUST 触发 P0 E2E。

#### Scenario: 颜色和间距变化
- **WHEN** UI 类型为 presentation
- **THEN** 系统选择聚焦 UI contract 或视觉断言，而不选择 P0 journey

#### Scenario: 登录提交链路变化
- **WHEN** UI 类型为 journey
- **THEN** 系统强制选择适用 P0 E2E
