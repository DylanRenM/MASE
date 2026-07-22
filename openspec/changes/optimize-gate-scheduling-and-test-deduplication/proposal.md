## Why

Pilot 的 Strict 变更实战表明，MASE 的质量底线是必要的，但当前 CLI 没有把测试阶段、Capability 作用域和证据新鲜度连成可执行计划，导致全量回归过早执行、相同测试集合被多个 gate 重复运行、输入目录稍有变化便需要人工判断是否重跑。与此同时，现有 `assess_evidence()` 并未接入 `mase status/check`，规范声称的 stale 行为与实际状态判断不一致。

## What Changes

- 将自动证据的新鲜度计算接入 change 状态：每个 gate 只由最新适用的 fresh 证据满足，输入变化、日志缺失和制品变化分别产生 stale、missing、invalid。
- 新增项目级 `.mase/gates.yaml` 门禁定义，固定每个 gate 的阶段、命令、输入、制品、测试集合和显式覆盖关系，避免 Agent 每次临时选择过宽路径。
- 新增 `mase gate plan`，按 micro、capability、final 阶段展示应执行、可复用、已延后和阻断的门禁，并诊断测试集合重叠和相同命令重复。
- 新增最终候选冻结：`mase gate freeze --change NAME` 在前置任务/门禁满足后生成候选摘要；final gate 绑定候选摘要，候选输入变化后自动解冻并使 final 证据 stale。
- Gate Runner 在命令、输入摘要、测试集合和候选摘要完全相同时复用 fresh 执行结果；只有门禁定义显式声明 `covers` 时，同一次执行才可满足多个语义 gate。
- 真正读取 `risk.capabilities`，生成 Capability 级 Profile、路径和 gate 计划；局部风险升级不再无条件把整个 change 的开发阶段测试升级为 Strict，但 change 级最终硬门禁仍由合并后的风险决定。
- 对 gate 命令输出提供实时转发，同时继续将脱敏完整日志写入证据目录。
- 压缩重复证据：状态保留每个 gate 最近的有效、失败和必要审计记录，历史日志仍可追溯但不让 `mase-state.yaml` 无限增长。
- 更新 Profile、Schema、模板、用户指南和行为测试；不删除 API 契约、安全、P0、全量回归或独立评审质量底线。

## Capabilities

### New Capabilities

- `stage-aware-gate-planning`: 固定门禁定义、micro/capability/final 调度、最终候选冻结和重复测试诊断。
- `evidence-freshness-and-reuse`: 状态新鲜度、候选绑定、等价执行复用、显式 gate 覆盖和证据压缩。
- `capability-scoped-gate-plan`: 从 Capability 风险与影响路径推导局部门禁，同时保留 change 级最终质量底线。

### Modified Capabilities

- 无（当前仓库尚未建立归档后的 `openspec/specs/` 基线）。

## Impact

- CLI：扩展 `mase gate` 子命令，修改 `mase status/check` 的有效证据判断和输出。
- 核心模型：`mase_cli/evidence.py`、`state.py`、`risk.py`、`profiles.py`，新增门禁定义/计划与候选模型。
- Schema/模板：新增 `.mase/gates.yaml` Schema 和默认模板，扩展 `mase-state.yaml` 的 Capability 与 candidate 字段。
- 安装/迁移：manifest 分发新 Schema/模板；现有项目没有 gates 文件时保持兼容并给出可操作诊断，不静默伪造定义。
- 测试/文档：增加 stale 状态接线、测试集合重叠、缓存复用、final 阶段、候选失效、Capability 局部升级和实时输出测试。
