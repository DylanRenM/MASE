## Why

MASE 已定义按风险、按工作包和按证据新鲜度执行，但真实 change 仍会递归展开宽泛影响目录、把完整历史 evidence 嵌入活动状态，并在多个 capability gate 中重复运行相同测试。当前样本上下文达到 Standard 字符预算的 4.5 倍，前置测试节点重复率达到 53.3%，需要把既有节流原则变成可执行约束。

## What Changes

- 将上下文计划收敛到工作包或 Capability，目录默认只形成诊断而不递归灌入全部内容，并拒绝二进制、隐藏缓存和无理由超预算读取。
- 将活动状态中的完整自动 evidence 外置为结构化记录，`mase-state.yaml` 只保留足以判定状态和新鲜度的摘要引用，同时兼容读取旧式内嵌 evidence。
- 以测试节点包含率补充 Jaccard 重叠诊断，支持 Capability 测试清单和真实 selector，避免语义不同的 gate 运行同一整文件测试集。
- GatePlan 默认只展示必需 gate，并为人工 gate、阻塞前序和可选 `--all` 输出正确下一步。
- 合并人工评审材料包但保留影响、架构和代码三个独立决策，不降低 API、P0、最终回归、影响复扫或回滚底线。

## Capabilities

### New Capabilities

- `compact-active-evidence`: 活动状态使用紧凑 evidence 引用，完整审计记录保存在 `.mase/evidence`。

### Modified Capabilities

- `enforced-context-routing`: 上下文计划必须支持工作包/Capability 范围、目录安全展开和可执行预算约束。
- `stage-aware-gate-planning`: GatePlan 必须识别测试集包含关系、隐藏非必需 gate，并给出模式正确的下一步。
- `capability-scoped-gate-plan`: Capability gate 使用稳定测试 ID/selector，减少相同节点在同一边界重复执行。
- `single-source-project-state`: 唯一状态源保留当前事实与证据索引，不要求在活动文件中内嵌完整历史记录。

## Impact

- 代码：`mase_cli/context.py`、`mase_cli/evidence.py`、`mase_cli/state.py`、`mase_cli/gates.py`、`mase_cli/main.py`。
- Schema/模板：状态、evidence、gate 与测试清单 Schema 和模板。
- 配置：MASE 自身 `.mase/gates.yaml`、`.mase/tests.yaml` 与 Profile 声明。
- 文档/Agent：核心规则、用户指南和四 Agent 的最小上下文、评审包规则。
- 兼容性：旧式内嵌 evidence 继续可读；更新器以非破坏方式迁移，完整证据不得丢失。
