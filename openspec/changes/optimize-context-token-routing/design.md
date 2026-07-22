## Context

MASE 2.2 已有风险 Profile、GatePlan、候选冻结、执行签名复用和证据保留上限，但 Token 路由仍是建议性规则。框架 manifest 的排除路径没有覆盖真实的 `openspec/changes/archive`、`openspec/changes/_archived` 和 `.mase/evidence`；Gate Runner 默认流式回显全部输出；metrics 只有调用者手工传 Token 时才记录真实用量。采用项目若缺少 `.mase/gates.yaml`，仍可能直接运行脚本而失去复用能力。

## Goals / Non-Goals

**Goals:**

- 让 Agent 在执行前获得确定、可审计、受软预算约束的 context plan。
- 默认把完整门禁输出留在脱敏日志，只把有限摘要送入 Agent 上下文。
- 自动消费平台通过环境或 usage JSON 提供的真实 Token，并保持代理指标语义准确。
- 让安全与独立评审由实际风险驱动，并在无异议时停止。
- 让采用项目明确知道 canonical gate definitions 是否已经启用。

**Non-Goals:**

- 不在首版实现跨供应商统一 tokenizer，也不把字符数换算成 Token。
- 不删除完整证据日志或降低鉴权、密钥、迁移等风险的硬门禁。
- 不自动推断任意源文件与测试文件的语义依赖图。
- 不实现远程 Token 账单或跨机器缓存。

## Decisions

### 1. 新增 `mase context plan`

命令以项目 manifest 的排除规则、change 当前 Specs/tasks/state 摘要、`impact.paths` 和调用者显式 `--read` 为输入，输出纳入文件、排除原因、文件数和字符数。预算按 Profile 提供默认软上限：Lite 8K、Standard 16K、Strict 24K input-token budget；没有 tokenizer/usage 时只执行文件数和字符数代理上限并标记 `proxy_only`。

选择“先计划、后读取”而不是让 CLI 拼接所有内容，避免 CLI 自身成为新的大上下文生成器，也允许不同 Agent 平台使用同一计划。

### 2. 排除规则优先于自动发现，显式读取需要审计

补充真实归档、evidence、测试报告、日志、数据、输出和依赖缓存目录。普通自动发现永不纳入这些路径；调用者显式请求被排除文件时，计划保留拒绝原因，只有 `--allow-excluded` 才纳入并标记 override。

### 3. Gate Runner 默认 concise，verbose 显式开启

完整输出始终写入现有脱敏 evidence log。默认 CLI 不逐行回显，而是在结束后输出状态、耗时、日志路径；失败时额外输出最后一个有限字符窗口。`--verbose` 保留原增量流式行为，供人工调试长任务使用。

相比截断持久化日志，这一设计不损失审计证据；相比始终流式输出，它能避免测试点、warnings 和长堆栈自动进入 Agent 上下文。

### 4. Token telemetry 使用“平台数据优先、代理值兜底”

`mase metrics` 继续接受显式参数，并新增 usage JSON 与标准 `MASE_INPUT_TOKENS`、`MASE_OUTPUT_TOKENS`、`MASE_CACHE_TOKENS` 环境读取。优先级为显式参数、usage JSON、环境变量；缺失时只报告字符数、文件数和可选工具输出字符数。

### 5. Standard 安全评审由风险注册表触发

Standard Profile 不再无条件把 `security_review` 加入 hard/capability gate 和普通 capability schedule。不可信输入、归档、不可逆写入等风险仍通过 `profiles/risks.yaml` 触发安全评审。Strict 继续保留安全和独立评审，但 review 模式改为单轮确认；只有明确异议、候选输入变化或证据 stale 才追加。

### 6. 采用诊断明确说明兼容模式能力缺失

`mase check` 和 `mase update --dry-run` 在 `.mase/gates.yaml` 缺失或为空时列出不可用能力：candidate freeze、exact reuse、covers 和 overlap diagnostics。提示保持非阻断，以避免旧项目升级即失败；Standard/Strict release 可以在项目策略中提升为阻断。

## Risks / Trade-offs

- **[Risk] concise 模式隐藏实时进度** → `--verbose` 保留流式模式，日志始终完整落盘。
- **[Risk] 默认排除误伤需要调查的日志** → 显式 override 可纳入，并在计划中留下审计标记。
- **[Risk] 字符预算对中英文不等价** → 明确标记 proxy，不声称为 Token；真实 usage 可用时以真实值为准。
- **[Risk] Standard 移除通用安全评审导致漏检** → 风险分诊测试覆盖每个攻击面触发器，未知风险仍可显式声明 gate。
- **[Risk] context 自动发现过宽** → 只从 change 影响路径和显式 reads 产生候选，不递归加载整个仓库。

## Migration Plan

1. 先补 context plan、concise runner、metrics 和 review routing 的失败测试。
2. 实现 CLI 与配置，更新 manifest/Profile/规则和文档。
3. 运行框架聚焦测试与全量回归。
4. 在 Pilot 通过非破坏 update 生成 `.mase/gates.yaml`，再人工填写真实命令、输入和覆盖关系。
5. 回滚时可恢复旧 Profile/manifest，并使用 `mase gate run --verbose` 保持原输出体验；已保存日志无需迁移。

## Open Questions

- 各 Agent 平台未来能否提供统一 usage JSON 路径，可在首版环境变量契约验证后再标准化。
