# stack-aware-cli Specification

## Purpose
TBD - created by archiving change adaptive-lightweight-mase. Update Purpose after archive.
## Requirements
### Requirement: 初始化支持多技术栈
`mase init` MUST 支持 generic、python 和 swift stack，并只生成该 stack 与 Profile 需要的目录和文件。

#### Scenario: 初始化 Swift Lite 项目
- **WHEN** 用户执行 `mase init demo --stack swift --profile lite`
- **THEN** 项目包含 Swift 适用结构和 MASE 状态，不包含 Python 专属 models/routes/pyproject 模板

#### Scenario: 保持旧 Python 参数兼容
- **WHEN** 用户使用 v1.3 的 `-p` 与 `-c` 参数初始化 Python 项目
- **THEN** CLI 仍能创建等价 Python 项目并给出迁移提示

### Requirement: 合规检查消费 Profile 和 stack
`mase check` MUST 只检查当前 Profile 与 stack 声明的规则，并支持人类可读和 JSON 输出。

#### Scenario: 检查 Swift 项目
- **WHEN** state 声明 stack 为 swift
- **THEN** 检查器不要求 pyproject.toml、Makefile 或 Python models/services 目录

### Requirement: CLI 提供诊断状态和度量
CLI MUST 提供 doctor、status 和 metrics 命令，用于环境预检、状态一致性和 Token/上下文代理指标。

#### Scenario: 环境缺少可选工具
- **WHEN** doctor 发现缺少完整 Xcode 但 SwiftPM 与 Command Line Tools 可用
- **THEN** 结果说明可继续的构建模式，而不是把完整 Xcode 作为无条件阻断

### Requirement: 更新操作非破坏且可预览
`mase update` MUST 支持 dry-run、备份、generated 文件识别和冲突报告。

#### Scenario: 用户修改过 IDE 规则文件
- **WHEN** 更新器发现目标文件与记录的 source hash 不一致
- **THEN** 更新器先备份并报告冲突，不静默覆盖用户内容
