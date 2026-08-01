# change-portfolio-status Specification

## Purpose
TBD - created by archiving change strengthen-mase-evidence-governance. Update Purpose after archive.
## Requirements
### Requirement: 默认多 change 组合视图
`mase status` 在未指定 change 时 SHALL 汇总所有非 archived change，而不是因零个或多个 change 抛出异常。组合视图 MUST 展示 phase、任务进度、GatePlan 摘要、证据新鲜度、blocker、依赖、冲突和遗留基线债务，并支持等价 JSON 输出。

#### Scenario: 项目有多个活动 change
- **WHEN** 用户在包含多个活动 change 的项目根执行 `mase status`
- **THEN** 系统返回全部活动 change 的稳定排序汇总，并用退出码反映是否存在阻断项

#### Scenario: 项目没有活动 change
- **WHEN** 用户在没有活动 change 的合规项目执行状态命令
- **THEN** 系统返回空组合视图和清晰提示，不输出 traceback

### Requirement: Change 依赖与冲突
状态模型 SHALL 允许 change 声明依赖、互斥或重叠文件范围。Portfolio MUST 检测缺失依赖、依赖未完成、循环依赖以及并行 change 的潜在文件冲突。

#### Scenario: 实现依赖的基础 change 未完成
- **WHEN** change B 声明依赖 change A，且 A 尚未达到要求阶段
- **THEN** portfolio 将 B 标记为 blocked 并说明依赖条件

#### Scenario: 两个活动 change 修改相同高风险边界
- **WHEN** 两个无依赖关系的活动 change 声明重叠的鉴权或迁移文件范围
- **THEN** portfolio 报告潜在冲突并要求排序或显式接受并行策略

### Requirement: 阶段与完成语义一致
verify、retro 和 release SHALL 被视为进行中阶段；只有 complete 和 archived 是完成态。系统 MUST 区分任务完成、门禁完成、准备发布和最终完成，不得仅凭复选框或 phase 单字段宣称 change 完成。

#### Scenario: 任务完成但门禁待执行
- **WHEN** 所有 tasks 已勾选但仍有 pending 或 stale 硬门禁
- **THEN** 状态显示 `ready_for_gate` 或 blocked，而不是 complete

#### Scenario: 门禁全过但尚未完成发布动作
- **WHEN** tasks 和硬门禁均完成但 phase 仍为 release
- **THEN** 状态显示 `ready_to_complete` 并列出剩余发布/归档动作

### Requirement: 稳定诊断与退出码
所有 CLI 状态和检查命令 SHALL 捕获预期的配置、YAML、Schema、路径和选择错误，输出简洁诊断及稳定退出码。默认输出不得包含 Python traceback；调试模式可以显式请求堆栈。

#### Scenario: 状态 YAML 语法错误
- **WHEN** 某个 change 的状态文件存在 YAML 语法错误
- **THEN** CLI 返回配置错误退出码并显示文件、位置和建议，不影响其他 change 的诊断

#### Scenario: 指定不存在的 change
- **WHEN** 用户通过 `--change` 指定不存在或不安全的名称
- **THEN** CLI 返回可操作的 not-found 或 invalid-name 诊断且不读取 change 根目录外路径

### Requirement: 非破坏组合迁移
从旧项目元数据和状态迁移到新模型 SHALL 支持 dry-run、备份、冲突保留和幂等。迁移器 MUST 不得把无法验证的旧 passed 描述自动升级为新鲜可执行证据。

#### Scenario: 迁移旧复合 stack 和自由文本证据
- **WHEN** dry-run 遇到可识别的复合 stack 与旧式 evidence
- **THEN** 系统预览主 stack/toolchains 拆分，并将旧 evidence 标记为 legacy/stale 待重跑

#### Scenario: 重复运行迁移
- **WHEN** 已成功迁移的项目再次执行更新
- **THEN** 系统不产生新的文件差异或重复备份
