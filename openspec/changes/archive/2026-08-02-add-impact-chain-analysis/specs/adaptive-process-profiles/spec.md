## MODIFIED Requirements

### Requirement: 测试执行按边界分级
MASE MUST 在历史行为变更的设计前运行影响分析，在微循环运行相关测试，在 capability 边界运行影响复扫、集成与评审，在最终门禁运行全量测试和适用 P0 E2E。影响分析适用于 Lite、Standard、Strict，L1 可使用紧凑产物，L2/L3 只能增加而不得降低 Profile 门禁。

#### Scenario: 修改一个历史纯函数
- **WHEN** 开发者修改一个历史纯函数且证据证明为 L1
- **THEN** 设计前仍完成紧凑影响分析，微循环不要求每次运行全部 E2E，但相关调用方测试和最终适用门禁必须满足

#### Scenario: Lite capability 发生 L3 契约变化
- **WHEN** Lite change 的一个 capability 修改公共契约并波及系统边界
- **THEN** 该 capability 获得 L3 影响门禁和必要的 Profile 风险升级，而框架不创建第四种 Profile
