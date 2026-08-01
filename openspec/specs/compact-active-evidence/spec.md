# compact-active-evidence Specification

## Purpose
TBD - created by archiving change optimize-mase-execution-efficiency. Update Purpose after archive.
## Requirements
### Requirement: 完整 evidence 外置且活动状态紧凑
MASE SHALL 将新生成的完整结构化 evidence 写入项目内 `.mase/evidence/<change>/`，并在 `mase-state.yaml` 中只保留判定当前 gate 状态、新鲜度和审计位置所需的有限摘要。

#### Scenario: 自动门禁成功
- **WHEN** Gate Runner 完成一次自动门禁
- **THEN** 完整命令、输入、测试、平台和结果保存在独立 sidecar，状态摘要引用 execution ID、digest、日志和 sidecar 路径

#### Scenario: Agent 读取活动状态
- **WHEN** Agent 请求 change 当前状态而没有请求 evidence 详情
- **THEN** 系统返回有限 gate 摘要，不内联历史命令、完整输入和测试清单

### Requirement: 旧式内嵌 evidence 保持兼容
MASE MUST 继续读取旧式完整内嵌 evidence，并且只有在 sidecar 写入、Schema 校验和摘要校验成功后才可压缩现有记录。

#### Scenario: 打开未迁移项目
- **WHEN** 状态包含旧式完整 evidence 且不存在 sidecar
- **THEN** 状态和新鲜度判定保持可用，不丢失或静默重写记录

#### Scenario: sidecar 写入失败
- **WHEN** 迁移无法原子写入或校验完整 evidence
- **THEN** 系统保留原内嵌记录并报告 conflict

### Requirement: Evidence 详情按需加载
MASE SHALL 提供按 execution ID 或 gate 获取 evidence 详情的读取路径，默认状态、GatePlan 和 Agent 交接不得自动展开 sidecar 内容。

#### Scenario: 调试失败门禁
- **WHEN** 人工明确请求某次失败 evidence
- **THEN** 系统加载该条 sidecar 和日志引用，而不是加载同一 change 的全部历史 evidence
