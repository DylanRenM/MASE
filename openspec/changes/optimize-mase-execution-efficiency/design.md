## Context

MASE 已有上下文预算、证据新鲜度、Capability GatePlan 和 `covers`，但当前实现仍以 change 级 `impact.paths` 递归展开上下文，自动 evidence 全量嵌入状态，测试重叠只用 Jaccard 判断。真实 L3 change 因此产生 45 文件/285098 字符的上下文计划、91% evidence 状态占比，以及 53.3% 前置测试节点重复执行。

## Goals / Non-Goals

**Goals:**

- 让工作包 `reads` 和 Capability path 成为上下文计划的可执行范围。
- 保持所有 evidence 可审计，同时让活动状态只携带有限摘要。
- 在不错误合并语义 gate 的前提下识别测试包含关系并减少重复节点。
- 让默认 GatePlan 只输出当前必需动作，并正确处理 manual gate。
- 保持旧项目、旧状态和 ad-hoc gate 可读取、可迁移。

**Non-Goals:**

- 不取消最终候选全量回归、适用 API/P0、影响复扫或 L3 人工决策。
- 不用测试重叠自动推断两个 gate 语义等价。
- 不删除历史 evidence，也不把真实 Token 与字符代理混为一谈。
- 不修改任何采用项目或 Pilot 项目。

## Decisions

### 1. 上下文计划采用“基础事实 + 显式工作包读取”

新增可选 `--task` 和 `--capability`。指定工作包时只加载项目规则、该任务引用的 Spec、任务声明的 `reads` 和显式 `--read`；未指定时保持兼容的 change 级计划，但目录影响项只报告为 `broad_scope` 诊断，不递归读取。选择该方案而不是继续依赖软预算，因为报告超限但继续展开无法阻止 Token 浪费。

任务 `reads` 从 `tasks.md` 的结构化行 `reads: path, path` 解析，Capability 从状态中的精确 paths 解析。二进制、隐藏文件和默认排除项不计入可读上下文。预算超限返回 `over_budget`，CLI 默认退出非零；`--allow-over-budget` 必须显式使用并记录原因。

### 2. 完整 evidence 使用 sidecar，状态保留摘要

自动/人工 evidence 写入 `.mase/evidence/<change>/<execution-id>.json`，状态中的记录保留 gate、result、时间、scope、digest、执行 ID、日志路径、sidecar 路径和重用来源。状态加载器同时接受旧完整记录和新摘要；新鲜度判定需要细节时读取 sidecar。选择 sidecar 而不是单一大型 registry，避免每次追加重写全库并让单条证据可独立保留/清理。

迁移是渐进式的：已有内嵌记录不主动删除；当 update 或下一次 evidence 写入时，可先写 sidecar，再把可验证记录压缩。失败时保留原状态。

### 3. 测试重叠以 Test ID/node selector 为单位

重叠诊断同时计算 Jaccard 与双向包含率。任一测试集被另一集合包含 80% 以上就告警，即使大集合很大。诊断只建议拆分 selector 或声明显式 `covers`，不自动复用。

MASE 自身测试清单登记稳定 ID、tier、Capability 和 pytest node selector。差异契约、全链路冒烟、回滚验证改用精确 marker/node selector；不能证明覆盖的测试不通过 `covers` 复用。最终候选仍运行一次完整回归。

### 4. GatePlan 默认聚焦 required gates

计划构建仍计算所有定义，但默认序列化只包含 required gate 及其必要前序；`--all` 才展示未触发 gate。阻塞链根据前序 gate 的 `mode` 生成 `mase evidence add` 或 `mase gate run`。计划额外显示重叠诊断、预算诊断和下一最小动作。

### 5. 人工评审共享 subject packet，不共享结论

影响、架构、代码 gate 可以引用同一个 review packet/reference，但必须分别记录 reviewer、subject digest 和结论。架构决策仍在实现前，代码结论仍在实现后，不能用一次自我批准跨越时点。

## Risks / Trade-offs

- [旧 evidence 缺少 sidecar] → 加载器继续支持内嵌完整记录，只有成功写入并校验 sidecar 后才压缩。
- [目录不再递归导致漏读] → 计划报告宽泛路径及建议的 `--task`/`--read`，用户可显式覆盖并留下原因。
- [精确 selector 维护成本] → `.mase/tests.yaml` 成为唯一清单，测试文件移动时由完整性测试阻断。
- [错误声明 covers 掩盖语义差异] → 保留输入、制品、候选和测试包含校验，不由相似度自动生成 covers。
- [默认隐藏可选 gate 影响排障] → `--all` 和 JSON `optional_instances` 保留完整可见性。

## Migration Plan

1. 先增加 Schema、双读 evidence 与上下文新参数，不改变现有状态。
2. 增加测试覆盖，再启用 sidecar 写入和紧凑摘要。
3. 填充 MASE 自身测试清单并收窄 gate selector。
4. 更新规则、文档、模板和 update dry-run。
5. 对当前 change 运行定向测试、全量回归和非破坏迁移验证。

回滚时恢复旧式完整 evidence 写入和 change 级上下文兼容路径；sidecar 是附加数据，回滚不删除。

## Open Questions

- 暂不自动压缩所有历史 change；先验证新写入和显式 update 的迁移行为。
