## Why

MASE 已支持 `covers` 和执行签名复用，但 gate 前序仅在发布门禁中生效，覆盖证据也没有完整表达工具链、依赖锁、fixture 与环境等价性。需要把 gate 计划升级为可验证 DAG，确保只消除同一候选、相同输入和等价环境下的真实冗余。

## What Changes

- 将 `requires` 作为所有 gate 的通用 DAG 前序，校验未知依赖、自依赖与环路，并按拓扑顺序计划和执行。
- 保留 `covers` 表达测试覆盖关系，新增明确的 `subsumed` 计划/证据状态，不把名称相似或低成本聚焦测试自动视为被覆盖。
- 扩展执行签名和缓存键，纳入测试 ID 集、源码/测试摘要、依赖锁、工具链、fixture/配置、候选、命令与环境等级。
- 只有覆盖 gate 的测试集合、输入、候选和环境均为超集或等价，且被覆盖测试此后未变化，才允许复用。
- 将“重复执行为 0”定义为同候选、同输入、等价环境下的冗余为 0；开发聚焦与发布全量分别验证不同对象，不算冗余。

## Capabilities

### New Capabilities

- `gate-dag-and-subsumption`: 通用 gate 依赖图、拓扑计划和可审计覆盖状态。

### Modified Capabilities

- `stage-aware-gate-planning`: 按 DAG 前序而非隐式阶段顺序生成下一动作。
- `evidence-freshness-and-reuse`: 缓存与跨 gate 覆盖绑定完整执行环境和候选等价条件。
- `capability-scoped-gate-plan`: 重复率只统计同一验证对象的冗余执行。

## Impact

- 运行时：`mase_cli/gates.py`、`mase_cli/evidence.py`、`mase_cli/state.py`。
- Schema/配置：gate、evidence Schema 和 `.mase/gates.yaml`。
- 测试：DAG 环路、拓扑计划、覆盖拒绝、精确缓存命中与失效。
- 不包含任何 Pilot gate 拆分或路径映射。
