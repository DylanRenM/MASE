## Context

MASE v2 已有 Profile、风险触发器、Gate Runner 和证据哈希，但执行链路仍是“规范化了一半”：Profile 的 `test_schedule` 没有 CLI 消费者；`mase gate run` 的 command/inputs 每次由调用者临时传入；`assess_evidence()` 只有单元测试直接调用，`mase status` 仍只看 `gates.<name>=passed`；`risk.capabilities` 被 Schema 接收但风险推导只读取 change 顶层 triggers。Pilot 实战因此在约 187 秒的全量回归成功后又运行两次，并让 related/integration 两个 gate 执行同一脚本。

框架必须同时避免两种相反风险：不能因“提效”复用语义不同的测试结果，也不能因目录级输入过宽而让不相关修改使所有门禁失效。现有项目已使用 ad-hoc `mase gate run ... -- COMMAND`，升级必须兼容该入口且不得伪造旧项目定义。

## Goals / Non-Goals

**Goals:**

- 让状态、生命周期和归档判断真正消费证据 fresh/stale/missing/invalid。
- 把 Profile 中的阶段节奏变成可执行 GatePlan，final gate 只针对冻结的候选版本运行。
- 为 gate 提供项目内唯一的命令、输入、测试选择器和覆盖关系定义。
- 在完全等价且仍 fresh 时复用执行；诊断重复测试集合而不擅自合并语义 gate。
- 生成 Capability 局部计划，缩小 capability 阶段的输入和测试范围，同时保留最终风险底线。
- 保持旧项目可读、旧 `gate run` 可执行和无破坏迁移。

**Non-Goals:**

- 不实现分布式 CI 缓存、远程制品存储或跨机器可信签名。
- 不根据 Python import 图自动证明所有测试影响关系；首版以显式定义和保守默认值为准。
- 不删除 Strict 的 full regression、security、API、P0 或 independent review。
- 不自动推断一个 gate 可以覆盖另一个；覆盖必须在项目定义中显式声明。

## Decisions

### 1. `.mase/gates.yaml` 是门禁执行定义的唯一项目源

新增 `mase-gates/v1`：每个 gate 定义 `stage`、`command`、`inputs`、`artifacts`、`tests`、`covers`、`candidate_bound`，可选 `capabilities`。命令使用字符串数组避免 shell 二次解析；输入必须为项目根内相对路径。

`mase gate run GATE --change NAME` 优先使用定义。保留 `-- COMMAND` 兼容模式，但 plan 将其标为 ad-hoc、不可跨 gate 复用；若定义和命令同时提供且不一致则拒绝，避免证据与配置漂移。

相比继续把命令写在脚本/对话里，定义文件可让 CLI 在执行前比较测试集合、阶段和输入。相比把定义塞进每个 change state，项目级文件避免十多个 change 复制同一测试命令；change 仍可用 scope/capability 选择定义。

### 2. GatePlan 输出 gate instance，而不是只有 gate 名称

新增内部 `GateInstance`：`gate`、`scope`、`stage`、`definition`、`effective_status`、`reason`。change 级 scope 为 `change`；Capability scope 为 capability ID。状态兼容地保留 `required_gates` 名称，同时增加 `gate_instances` 输出供新客户端使用。

Capability 输入为 gate 定义 inputs 与 capability paths 的保守交集/并集规则：定义显式声明 capability inputs 时使用该集合，否则使用 capability paths 加相关测试选择器。最终 change gate 始终基于冻结候选的完整定义输入。

### 3. 状态从最新证据派生，不再相信手写 passed

对每个 gate instance 按状态文件顺序选择最新证据：最新失败覆盖旧通过；最新通过调用 `assess_evidence()`。没有结构化证据时，手写 `passed` 对自动 gate 只作为 legacy/stale，不满足硬门禁。人工 gate 仍按允许列表判断。

`mase status/check` 返回 effective gate 状态并用它计算 lifecycle。为兼容迁移，旧 change 首次显示 stale/待重跑而不是损坏；`mase update --dry-run` 提示生成 gates 定义和重跑计划。

### 4. 候选冻结是 final gate 的时间边界

`mase gate freeze --change NAME` 要求 tasks 完成、所有非-final 必需 gate fresh、无 blocker，并根据所有 final 定义 inputs、Specs、tasks、gate 定义文件生成 candidate digest。candidate 保存于 state，含 id、时间、input digest 和 inputs。

final gate 在项目存在 gates 定义时必须绑定当前 candidate；执行前重新计算摘要。任何候选输入变化使 candidate stale，final gate 不执行，提示重新完成受影响前置 gate 并 freeze。旧项目无定义时保持当前行为并打印兼容警告。

选择显式 freeze 而不是“看到第一次 full regression 就自动冻结”，因为只有用户/Agent 知道功能、测试和人工评审是否已稳定。freeze 不保证一生只跑一次；失败修复或候选后修改仍应产生新 candidate 和新全量回归。

### 5. 复用签名严格等价，跨 gate 需要显式 covers

执行签名由规范化 command、环境无密钥摘要、input digest、test-set digest、candidate ID 和平台组成。同一 gate instance 找到 fresh 同签名证据时直接 cache hit，不启动子进程。

不同 gate 即使签名相同也默认不复用，而是在 plan 中报告重复；只有来源定义的 `covers` 包含目标 gate，成功执行才为被覆盖 gate 写入引用同一 execution ID/log 的派生证据。这样 related/integration 的配置错误会暴露，而不会被“聪明缓存”掩盖。

### 6. 测试重叠先做声明式诊断

首版把 `tests` 当稳定选择器集合，计算 exact duplicate 和 Jaccard overlap。exact duplicate 且无 covers 为 warning；高重叠阈值默认 0.8。Python adapter 后续可选择运行 `pytest --collect-only` 增强精度，但不作为 v1 Schema 必需行为。

### 7. Runner 同时流式输出和写脱敏日志

子进程使用逐行读取，将原始输出立即写到调用终端，将脱敏输出写入临时日志；结束后原子移动到 evidence 目录并写 state。若进程异常终止，保留失败日志但不写 passed。命令与环境继续脱敏。

### 8. 证据状态压缩而非删除审计日志

每个 gate instance 在 state 中保留最新 fresh/pass、最新 failure 和最近一次被替代记录，默认最多三条；被移出 state 的日志不自动删除，由 archive/retention 工具管理。`execution_id`、`reused_from` 和 `candidate_id` 保持追踪链。

## Risks / Trade-offs

- **[Risk] 错误 inputs 定义导致不该复用的证据仍 fresh** → final 默认保守包含所有 change impact paths、测试定义和规格；plan 对空 inputs 和目录过宽同时告警。
- **[Risk] Freeze 增加一个操作步骤** → `mase gate plan` 在条件满足时给出唯一下一命令；Strict 才默认强制，Lite/Standard 可由项目策略选择。
- **[Risk] 旧项目突然出现大量 stale** → 无 gates 定义时先兼容告警；迁移 dry-run 生成建议，不自动改业务项目。
- **[Risk] 测试 selector 不能精确代表 pytest 收集结果** → 首版只对 exact/high overlap 做诊断，不据此自动跳过 gate。
- **[Risk] Capability 与 change gate 输出更复杂** → 旧 JSON 字段保留，新 `gate_instances` 为增量字段。
- **[Trade-off] 状态只保留三条证据** → 完整日志仍在 `.mase/evidence`，archive 快照记录引用。

## Migration Plan

1. 先增加模型、Schema、纯函数和失败测试，不改变现有 CLI 默认行为。
2. 接入 status 新鲜度和 effective gates，提供 legacy/stale 兼容诊断。
3. 增加 gates loader、plan 与 overlap diagnostics，再增加 freeze/candidate。
4. 为 Gate Runner 增加定义解析、cache hit、covers、流式日志和压缩。
5. 接入 Capability 计划并更新 Profile/风险测试。
6. 更新模板、manifest、用户指南和迁移 dry-run；在 MASE 自身与 Pilot gates 定义样例上验证。
7. 回滚时旧 CLI 忽略新增 gates/candidate 字段；备份后可移除 `.mase/gates.yaml` 回到 ad-hoc 模式。

## Open Questions

- 首版不对 shell 环境做全量摘要，只允许定义显式声明影响测试的非密钥环境变量；跨机器复用仍限制在同一 platform signature。
