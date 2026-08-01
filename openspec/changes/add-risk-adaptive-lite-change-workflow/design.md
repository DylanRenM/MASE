## Context

Profile 当前既升级过程产物又决定门禁，影响链另有 L1–L3；同时 `impact.ui_changed` 是布尔值。需要新增本次变更治理重量，但不能与影响链等级混名或削弱既有硬门禁。

## Goals / Non-Goals

**Goals:**

- Profile、Change Risk、Impact Level 三者职责清晰并可组合。
- 小改动使用单文件 change，发现风险后无损提升。
- UI 展示变化不再无条件触发 P0。
- 人工证据只在确有独立判断时产生。

**Non-Goals:**

- 不自动声称理解所有业务语义；不确定时升级而非降级。
- 不移除影响链 L1–L3。
- 不改变采用项目的业务代码或 gate 脚本。

## Decisions

### 1. Change Risk 使用独立字段与命名

状态新增 `change_risk.level: L1..L4` 和固定 dimensions；影响分析继续使用 `impact_analysis.level: L1..L3`。CLI 始终输出“变更风险/影响等级”全名，避免口头 L1 混淆。

### 2. 风险解析采用下限合并

显式 level、Profile 基础下限、风险维度和注册 trigger 分别计算，最终取最大值。认证/授权/密钥/额度、不可逆迁移为 L4；公共契约/核心计算/跨系统/并发/持久状态机至少 L3。用户可以上调，不能下调硬下限。

### 3. UI 分类替代布尔触发

新增 `ui_change_kind: none|presentation|interaction|journey`。presentation 选择 UI contract；interaction 默认 UI contract，只有被标记为关键闭环时选择 P0；journey 总是选择 P0。旧 `ui_changed: true` 在迁移前保守映射为 journey。

### 4. Lite change 是一个可验证源文件

`mase fix start` 生成 `change.md`，包含原因、验收行为、影响范围、根因假设与 RED、测试、回滚和 Tasks。状态中记录 schema `bugfix-lite/v1`。`promote` 解析这些章节并原子生成 proposal/design/specs/tasks/state；源文件保留为 provenance，若目标冲突则不写入。

### 5. 人工审查按独立判断路由

L1/L2 不选择 manual gate；L3 选择一个 `independent_review` 综合判断；L4 根据命中的安全、恢复和发布维度选择相应 manual gate。相同 actor 与实现者时只能记为 self review，不能满足 independent gate。

## Risks / Trade-offs

- [风险字段被低报] → 硬触发器重新计算下限，未知/冲突维度保守升级并给诊断。
- [旧 ui_changed 语义不明确] → 保守映射为 journey，update 只建议人工细分，不静默降级。
- [promote 丢失信息] → 先 dry-run、校验完整章节、原子创建且保留 change.md provenance。

## Migration Plan

1. Schema 接受新字段并兼容旧布尔 UI。
2. 风险解析器输出新级别和路由原因。
3. 增加 Lite 命令和无损提升测试。
4. 更新 Profile、规则、模板和 Agent 指引。
5. 回滚时完整 change 仍可用；Lite 源文件始终保留。

## Open Questions

- 无；成本预算由后续 change 处理。
