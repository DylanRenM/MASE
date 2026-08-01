## Context

当前状态同时存在 OpenSpec `phase`、gate `stage`、候选对象和 Release Overlay outcome，但状态报告只给出 `active/ready_for_gate/ready_to_complete`，且 `required_gates` 没有业务时点。结果是 GatePlan 容易把最终认证与开发完成混在一起。

## Goals / Non-Goals

**Goals:**

- 用证据派生开发、合并、候选和发布里程碑。
- 让昂贵门禁在其业务时点才成为阻塞项。
- 保持 phase、候选和 Release Overlay 的既有职责及旧配置兼容。

**Non-Goals:**

- 本 change 不引入 L1–L4 Change Risk。
- 不改变具体测试 selector 或缓存算法。
- 不把用户手测变成所有 change 的强制门禁。

## Decisions

### 1. 里程碑是派生状态，不替换 phase

`phase` 继续表达文档/实现进度；新增 `verification` 报告根据 fresh evidence 计算 `development`、`merge`、`candidate`、`release`、`live`、`observe`。选择派生值而非人工持久化枚举，避免状态与 evidence 漂移。

### 2. `required_at` 与 `stage` 正交

`stage` 保留物理执行边界和兼容语义；`required_at` 表示最晚必须满足的里程碑。旧定义按 `analysis/micro → development`、`capability → merge`、`final → release`、`release_observe → observe` 映射。显式值优先，但不得把候选绑定门禁放到 development/merge。

### 3. `user_confirmed` 是可选人工 gate，不在线性状态中硬编码

项目需要手测时声明 `user_confirmation` manual gate，默认 `required_at: merge`；否则状态可从 `dev_verified` 直接进入 `merge_verified`。这避免所有自动化 change 被人为阻塞。

### 4. 冻结前置改为 merge 里程碑

候选冻结要求任务完成、analysis/development/merge 门禁 fresh 且无 blocker；release/observe 门禁不参与冻结前置。`candidate_frozen` 表示候选摘要 fresh，`release_ready` 表示适用的 release 时点门禁 fresh。

## Risks / Trade-offs

- [旧项目未声明 required_at] → 使用确定性默认映射并在 update dry-run 中建议显式迁移。
- [同一 gate 被错误延迟] → 硬触发规则可覆盖 required_at，Schema 与运行时拒绝非法候选绑定组合。
- [用户误把 dev_verified 当完成] → CLI 同时显示目标、未满足后续里程碑和明确说明“仅可手测”。

## Migration Plan

1. Schema 和加载器先支持可选 `required_at`。
2. 增加里程碑派生与目标化 GatePlan，保持旧 CLI 默认行为可读。
3. 更新模板、MASE 自身 gate 配置和文档。
4. 回滚时忽略新字段；旧 `stage` 仍能恢复原计划。

## Open Questions

- 无；Change Risk 到时点的矩阵由后续 change 接入。
