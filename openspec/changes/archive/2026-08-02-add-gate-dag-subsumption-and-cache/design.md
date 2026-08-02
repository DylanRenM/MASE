## Context

`GateDefinition.requires` 已存在但只对 release gate 执行，`covers` 可扇出 evidence，却主要比较输入和 selector。执行签名未显式包含依赖锁、工具链、fixture/config 和环境等级，无法完整证明跨 gate 覆盖与缓存等价。

## Goals / Non-Goals

**Goals:**

- 所有 gate 形成无环依赖图并按前序计划。
- `requires`、`covers`、缓存复用和候选绑定有独立语义。
- 只有完整等价条件满足时才产生 `subsumed`。

**Non-Goals:**

- 不根据名称、Jaccard 或历史同时通过自动生成 covers。
- 不消除开发聚焦测试与发布候选全量回归。
- 不修改具体采用项目 selector。

## Decisions

### 1. 加载时校验 DAG

对所有 `requires` 做 DFS/拓扑排序，拒绝自环、环路与未知节点。GatePlan 只在所有 required predecessors fresh 时将 gate 标记 runnable，下一动作指向最早未满足前序。

### 2. 覆盖是一次执行产生的派生证据

源 gate 通过后，若 `covers` 的所有条件满足，为目标 gate 写入 `result: subsumed`、`reused_from` 和同一 execution ID，而不是伪装成目标 gate 独立 passed。`subsumed` 可满足 gate，但审计输出必须可见来源。

### 3. 执行环境摘要显式建模

Gate 定义可声明 dependency locks、toolchain、fixture/config inputs 和 `environment: equivalent|strict`。运行器归一化为 `environment_digest`，与命令、输入、test ID set、candidate、scope、release digest 共同组成 cache key。

### 4. 覆盖要求超集与同对象

源选择器必须覆盖目标 Test ID/selector；源输入和环境必须相同或更严格；候选绑定目标要求同一 candidate；目标输入在源执行后未变化。缺一项即拒绝扇出并给出原因。

### 5. 重复率排除跨时点的合理再验证

只统计 required_at 相同、候选相同、输入/环境等价且选择器重复的执行。development 聚焦与 release 全量不计作冗余。

## Risks / Trade-offs

- [缓存键更严格导致命中率下降] → 正确性优先，并通过成本指标显示未命中原因。
- [现有 covers 缺少环境声明] → 兼容模式只允许同 gate 精确复用；跨 gate covers 给迁移诊断。
- [DAG 阻塞现有错误配置] → update dry-run 在启用前报告环路和缺失前序。

## Migration Plan

1. Schema/加载器接受环境摘要输入并校验 DAG。
2. 计划器通用化 requires。
3. evidence 增加 subsumed 和环境摘要，旧 passed 继续可读。
4. 更新 MASE 自身 gate 定义与定向测试。
5. 回滚时忽略新增摘要；原执行 evidence 保持可审计。

## Open Questions

- 无。
