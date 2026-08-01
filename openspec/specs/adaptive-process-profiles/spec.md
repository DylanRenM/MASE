# adaptive-process-profiles Specification

## Purpose
TBD - created by archiving change adaptive-lightweight-mase. Update Purpose after archive.
## Requirements
### Requirement: 项目选择基础过程 Profile
MASE MUST 为每个 change 记录 Lite、Standard 或 Strict 基础 Profile，并给出可机器读取的必需产物、测试门禁和评审强度。

#### Scenario: 创建低风险本地工具
- **WHEN** 用户创建无鉴权、无不可逆远程写入的本地工具并选择 Lite
- **THEN** 系统只要求轻量变更说明、行为 Spec、工作包和相关测试，不强制完整设计文档全家桶

#### Scenario: 创建高风险系统
- **WHEN** 项目选择 Strict
- **THEN** 系统要求完整设计、API 契约、独立质量评审和全量门禁

### Requirement: Capability 风险只能提升门禁
MASE MUST 根据不可信输入、鉴权、密钥、并发、不可逆写入、迁移和监管风险将单个 capability 提升到更严格的策略，且不得降低已触发的硬门禁。

#### Scenario: Lite 项目包含文件解析
- **WHEN** Lite 项目的 capability 解析不可信归档或文档
- **THEN** 该 capability 至少启用安全评审、边界契约和恶意输入测试，而其他低风险 capability 仍保持 Lite

### Requirement: 测试执行按边界分级
MASE MUST 在历史行为变更的设计前运行影响分析，在微循环运行相关测试，在 capability 边界运行影响复扫、集成与评审，在最终门禁运行全量测试和适用 P0 E2E。影响分析适用于 Lite、Standard、Strict，L1 可使用紧凑产物，L2/L3 只能增加而不得降低 Profile 门禁。

#### Scenario: 修改一个历史纯函数
- **WHEN** 开发者修改一个历史纯函数且证据证明为 L1
- **THEN** 设计前仍完成紧凑影响分析，微循环不要求每次运行全部 E2E，但相关调用方测试和最终适用门禁必须满足

#### Scenario: Lite capability 发生 L3 契约变化
- **WHEN** Lite change 的一个 capability 修改公共契约并波及系统边界
- **THEN** 该 capability 获得 L3 影响门禁和必要的 Profile 风险升级，而框架不创建第四种 Profile

### Requirement: Profile 与 Change Risk 共同决定治理
MASE SHALL 让 Profile 表达产品或 Capability 的基础风险，让 Change Risk 表达本次修改的治理重量，并 SHALL 取二者、Impact Level 和硬触发要求的并集形成 GatePlan。

#### Scenario: Lite change 命中硬风险
- **WHEN** Lite Profile 的 change 命中不可逆迁移
- **THEN** 系统保持 Profile 记录可追溯，但按 L4 与 Strict 下限选择完整门禁
