# lite-change-workflow Specification

## Purpose
TBD - created by archiving change add-risk-adaptive-lite-change-workflow. Update Purpose after archive.
## Requirements
### Requirement: 低风险修复使用单文件源
`mase fix start <name>` SHALL 为 L1/L2 生成一个 `change.md`，其必需章节为原因、验收行为、影响范围、根因假设与 RED 证据、测试方法、回滚方式和 Tasks。

#### Scenario: 创建低风险 Bug 修复
- **WHEN** 用户运行 `mase fix start typo-layout`
- **THEN** 系统创建可校验的单文件 change，不要求空的 proposal/design/specs 文件全家桶

### Requirement: 风险升级无损提升完整结构
`mase fix promote <name> --to standard` SHALL 在公共契约、持久化、并发、核心计算等风险出现时，将单文件内容映射为完整 OpenSpec 工件并保留原文件和来源摘要。

#### Scenario: Lite 修复发现公共 API 变化
- **WHEN** 风险解析将 change 提升到 L3 且用户执行 promote
- **THEN** 系统原子生成 proposal、design、specs、tasks 和 mase-state，所有原章节均可追溯

#### Scenario: 目标文件已存在
- **WHEN** promote 发现将覆盖未知或人工修改的目标文件
- **THEN** 系统报告 conflict，不写入部分结果也不删除 change.md
