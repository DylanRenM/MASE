## Why

MASE 当前把开发验证、合并验证和最终候选认证集中在同一组“必需门禁”中，导致代码刚完成时就可能触发构建、全量回归和发布审计。需要在不降低硬门禁的前提下，把“可手测、可合并、可发布”拆成可由证据推导的独立里程碑。

## What Changes

- 新增 `dev_verified`、可选 `user_confirmed`、`merge_verified`、`candidate_frozen`、`release_ready` 验证里程碑，并与现有 `phase`、Release Overlay 结果分离。
- 为 gate 增加 `required_at: development|merge|release|observe`；兼容现有 `stage`，由 `stage` 描述执行边界、`required_at` 描述最晚必须满足的业务时点。
- 允许开发验证完成后启动本地服务并交付手测，不要求生产构建、候选冻结、全量回归或发布证据。
- 候选只在合并门禁、任务和阻塞项满足后冻结；发布门禁只在存在发布意图时进入计划。
- GatePlan 按目标里程碑输出当前必需门禁和下一动作，旧配置按确定性映射兼容。

## Capabilities

### New Capabilities

- `verification-milestones`: 以新鲜证据派生开发、合并、候选与发布验证里程碑。

### Modified Capabilities

- `stage-aware-gate-planning`: gate 定义增加业务要求时点，并按目标里程碑延迟昂贵验证。
- `single-source-project-state`: 状态报告同时呈现过程 phase 与派生验证里程碑，不接受手写状态冒充证据。
- `release-governance`: 候选冻结和发布就绪接续合并验证，但发布结果继续由 Release Overlay 独立推导。

## Impact

- 运行时：`mase_cli/gates.py`、`mase_cli/state.py`、`mase_cli/main.py`、`mase_cli/release.py`。
- Schema/配置：`schemas/mase-gates.schema.json`、`schemas/mase-state.schema.json`、`.mase/gates.yaml`、模板。
- 文档/测试：核心规则、用户指南、阶段门禁与候选冻结测试。
- 不涉及任何采用 MASE 的产品项目或 Pilot 配置。
