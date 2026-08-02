## Context

Gate evidence 已包含 duration、execution signature 和 reused_from，但 GatePlan 不聚合历史耗时，也没有阶段预算或冗余/缓存指标。本 change 依赖前三个 change 提供 required_at、Change Risk 和精确缓存语义，并负责 2.4 一致交付。

## Goals / Non-Goals

**Goals:**

- 从结构化 evidence 计算可解释的 p50/p90 成本。
- 把预算用于诊断和调度，不用于绕过门禁。
- 统一升级并验证 MASE 2.4.0 与培训内容。

**Non-Goals:**

- 不上传遥测或引入外部统计服务。
- 不用字符数冒充 token，也不预测业务运行耗时。
- 不承诺样本不足时的精确 ETA。

## Decisions

### 1. 成本历史来自本项目 evidence sidecar

按 gate、scope、Change Risk 和 required_at 读取最近成功/失败 duration，默认最多 50 个 fresh 可解析样本；少于 3 个样本只显示 observed range，不宣称 percentile。统计不读取日志正文。

### 2. GatePlan 聚合阶段成本

对尚需执行的 gate 计算串行保守和可并行关键路径两种值；CLI 简洁视图显示 p50/p90 关键路径，JSON 保留 gate 明细、样本数和算法。缓存命中或 subsumed gate 预计增量成本为 0。

### 3. 预算是诊断阈值

默认 L1 development 5 分钟、L2 development 15 分钟、L3 merge 30 分钟；L4 由项目显式配置。超限仅生成 `budget_exceeded` 诊断和可执行建议，硬 gate 保持 selected。

### 4. 指标使用明确事件边界

从 evidence/state 时间戳计算 dev_verified latency、candidate-to-release latency、cache hit rate、equivalent redundant execution rate 和 failed-to-diagnostic latency。缺失事件返回 unknown，不补造 0。

### 5. 2.4 课件从 2.3 融合升级

保留受保护 V1；生成新的 v2.4 YAML/PPTX。新增内容插入原则、六步开发主线、风险、测试、门禁、证据和度量相关章节，不追加脱节附录。脚本与验证器参数化当前版本。

## Risks / Trade-offs

- [历史样本受机器性能影响] → 记录平台/工具链分组并展示样本数，不跨不等价环境聚合。
- [预计耗时被理解为 SLA] → CLI 标为历史估计并提供 p50/p90，不作为通过标准。
- [版本引用遗漏] → 分发完整性测试扫描 canonical version 与当前课件文件名。

## Migration Plan

1. 增加成本模型和 JSON 字段，旧 evidence 可读取。
2. CLI 增加简洁成本摘要与 metrics 输出。
3. 更新规则、文档、模板、版本和分发清单。
4. 生成并验证可编辑 2.4 PPTX，保留 V1 字节摘要。
5. 完整回归、wheel 与仓库边界通过后交付。

## Open Questions

- 无。
