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
MASE MUST 在微循环运行相关测试，在 capability 边界运行集成评审，在最终门禁运行全量测试和 P0 E2E。

#### Scenario: 修改一个纯函数
- **WHEN** 开发者只修改一个纯函数
- **THEN** 微循环不要求每次运行全部 E2E，但最终门禁仍必须满足适用的 P0 和 API 契约要求
