# MASE v2 使用手册

## 设计宗旨

MASE 的宗旨是：**让 Agentic Coding 高效交付正确、健壮、优化且易于维护的代码，确保正确满足需求、软件可靠运行，并持续消除坏味道**。使用时应用 **高效交付、需求正确、运行健壮、质量优化、整洁可维护** 五个结果检查流程取舍，不用少测、跳过评审或生成更多代码冒充高效。

## 估算优化收益

1. 用优化前数据计算代码完成到可手测的 `T_old(pre-hand-test)`。
2. 用 2.4 development 门禁关键路径计算 `T_new(dev_verified)`。
3. 计算 `1 - T_new / T_old`，再分开报告 candidate→release_ready、返工率、逸出缺陷和缓存/冗余率。
4. 每个 gate 至少 3 个等价样本才报 p50/p90；否则标记 `unknown`。

MASE 本仓当前 54 条记录的观测中位数串行代理为 58.4s 降到 17.2s，方向性收益约 71%；由于 5 个 gate 样本不足，这是低置信度示例而非承诺。可用 `python3 scripts/estimate_mase_speed_gain.py --json` 复算 MASE 本仓数据，采用项目需对自己的 evidence 执行同等统计。

## 安装

```bash
python3 -m pip install .
mase install --source .
mase --version
```

`mase install` 只复制 `framework-manifest.yaml` 声明的运行时，不复制历史、培训或产品实例。

离线环境先在联网机器执行 `python3 -m pip download -r requirements-offline.txt -d wheels`，再复制仓库与 wheels，使用 `python3 -m pip install --no-index --find-links wheels .`。`requirements-offline.txt` 同时覆盖构建与运行依赖，纯运行依赖固定列在 `requirements-runtime.txt`。

## 创建项目

```bash
# 低风险通用项目
mase init demo --stack generic --profile lite

# Python 常规项目；-p/-c 与 v1.3 兼容
mase init api --stack python --profile standard -p api_pkg -c auth catalog

# 无完整 Xcode 也可先使用 SwiftPM/Command Line Tools
mase doctor --stack swift
mase init reader --stack swift --profile standard
```

Profile 选择：本地 MVP 用 Lite；UI/文件/并发用 Standard；鉴权/支付/监管/不可逆迁移用 Strict。高风险 capability 会局部升级。

## 常用命令

| 命令 | 用途 |
|---|---|
| `mase doctor --stack swift` | 非修改式环境预检 |
| `mase check --json` | 按当前 Profile/stack 检查结构 |
| `mase status [--json]` | 汇总所有活动 change、依赖、冲突与基线债务 |
| `mase status --change NAME` | 从 state+tasks 检查单个 change 一致性 |
| `mase fix start NAME` | 为 L1/L2 修复创建仅含 `change.md` 的 bugfix-lite 工作流 |
| `mase fix promote NAME --to standard` | 风险升级时无损生成完整 OpenSpec 工件并保留来源 |
| `mase gate run GATE --change NAME -- COMMAND...` | 执行门禁并原子记录可复现证据 |
| `mase gate run ... --verbose -- COMMAND...` | 人工调试时流式显示完整门禁输出 |
| `mase gate plan --change NAME --target development|merge|release|observe [--all] [--json]` | 按可手测、可合并、可发布或观察目标查看必需门禁；`--all` 审计未触发定义和重复测试诊断 |
| `mase gate freeze --change NAME` | 在 development/merge 前置门禁完成后冻结最终候选 |
| `mase gate manual GATE --change NAME ...` | 记录允许人工完成的结构化证据 |
| `mase impact classify KIND [--machine-consumed]` | 判定历史变更是否必须执行影响分析 |
| `mase impact scan --input adapter-result.yaml` | 校验语言/工具链扫描适配器输出 |
| `mase impact validate --change NAME` | 校验影响产物、分级、阈值和状态摘要绑定 |
| `mase impact status --change NAME [--json]` | 查看调用方/边界数量、等级、决策和复扫状态 |
| `mase impact reconcile --change NAME --actual-path PATH --actual-diff-digest DIGEST` | 用实际差异复扫计划范围 |
| `mase impact render --change NAME` | 从唯一结构化产物生成影响、测试和回滚三份视图 |
| `mase release plan --context release-context.yaml [--date DATE] [--json]` | 校验 Release Overlay 并生成只读、pending 发布计划 |
| `mase release status --change NAME [--json]` | 报告 `artifact_ready`、`live_verified`、`observed` 等发布证据状态 |
| `mase metrics FILE...` | 报告上下文代理指标 |
| `mase metrics ... --input-tokens N` | 记录平台提供的真实 Token |
| `mase metrics ... --usage-file usage.json` | 读取平台导出的 input/output/cache Token |
| `mase context plan --change NAME --task ID --json` | 按工作包 reads 生成不包含文件正文的上下文计划 |
| `mase context plan --change NAME --capability NAME --json` | 按精确 Capability paths 规划上下文 |
| `mase evidence show --change NAME --execution ID --json` | 按需读取一条完整 evidence sidecar |
| `mase update --dry-run` | 预览 v1.3→v2 迁移 |

`phase` 表示 OpenSpec 工作进度；`verification_milestone` 由新鲜门禁证据派生。`dev_verified` 只表示可启动本地服务和交付手测，不代表已完成生产构建、候选冻结、全量回归或发布审计；`merge_verified` 后才允许冻结候选，发布与观察门禁只在相应目标下执行。

Profile 是产品/Capability 的基础风险；`change_risk.level` 是本次修改的 L1–L4 治理重量；`impact_analysis.level` 是历史代码波及验证深度 L1–L3，三者不可互相替代。UI 使用 `ui_change_kind: presentation|interaction|journey`，纯展示不触发 P0，关键交互和 journey 才触发。

`.mase/gates.yaml` 中，`requires` 表示执行前序，`covers` 表示测试集合覆盖，`candidate_bound` 表示绑定冻结候选；缓存由完整执行签名自动判断。覆盖复用显示为 `subsumed` 并保留来源 execution，不会冒充目标 gate 独立运行。依赖锁、工具链、fixture/config、候选或环境变化都会使精确缓存失效。
| `mase install --dry-run` | 查看框架将分发的资源 |
| `python3 scripts/audit_repository_boundary.py` | 阻断产品、旧资料和生成缓存混入 MASE 框架仓库 |

## 开发方式

1. 对已有需求、原型和测试做差异分析；一次批量确认真正的冲突。
2. 记录 Profile、主 stack、toolchains、风险、产品属性与本次影响面到 `mase-state.yaml`，由此推导 GatePlan；需要显式审计框架版本时，增加 `framework_contract` 并使用 `installed-cli-and-versioned-schemas` 接口，不引用相邻源码仓库。
3. 修改历史行为时先建立 `impact-analysis.yaml`，扫描显性调用方与隐性依赖；纯注释、格式或非机器消费文案也必须留下豁免分类证据。
4. 超过 10 个第一方调用方、达到 3 个系统边界、三层仍未收敛或隐性依赖不可控时，等待人工选择版本隔离、特性开关、拆分或终止。
5. 只生成 Profile/风险需要的设计产物。
6. 将工作拆成纵向任务，每项声明 `reads` 和 `verify`。
7. RED→GREEN→REFACTOR 只跑相关测试；Capability 边界先按实际 diff 复扫影响范围，再运行互不重复的 integration/security/P0。
8. 先完成轻量人工确认，再用 `mase gate freeze` 固定最终候选；只对该候选运行 final 全量门禁。
9. 用 Gate Runner 生成自动 evidence；完整记录写入 `.mase/evidence`，活动状态只保留摘要索引。仅受影响输入、日志、制品或候选变化后重新执行 stale 门禁，完整签名未变时复用 evidence，归档时生成 master 快照。

## 影响链分析

`impact-analysis.yaml` 是唯一事实源，记录对比基线、批准的文件/符号、受保护不变量、调用方、调用边差异、隐性通道、系统边界、L1/L2/L3、受保护测试、副作用预算、变更声明、决策和回滚。`mase impact render` 生成《影响范围说明书》《测试范围确认单》《回滚方案》，不要手工维护三套事实。

只有签名、业务语义、异常、副作用、幂等、并发、事务、缓存、持久化、超时和重试都不变时，内部实现才能只追踪直接调用方。契约或语义变化递归到系统边界；达到三层仍未到边界时产生架构耦合告警，不能把深度上限当成“分析完成”。没有频率证据或仍有未验证隐性通道时至少按 L2。

新旧差异契约应优先使用历史测试或受控样本。生产来源必须授权、脱敏和最小化；两版运行要隔离副作用并规范化时间、随机数等非确定性输出。未在 Spec 中确认的差异按疑似误伤处理。

修改前已经存在的测试应登记为受保护测试；当前 change 新增的测试不能单独证明没有回归。删除、跳过、弱化断言或实质修改受保护测试时必须记录理由和人工审批。支持扫描的适配器比较修改前后的调用边；不支持时标记未验证而不是填空表示“无变化”。L2/L3 声明文件读写、持久化、外部调用和消息预算，并用可用的静态/Sandbox/运行轨迹核对。`mase impact status` 会重新摘要实际路径，复扫后的文件再次变化会立即显示 stale。

工作包在 `tasks.md` 的任务下声明 `reads: path, path`。默认 change 计划不会递归展开 `docs`、`agents` 等宽泛目录；超预算计划返回非成功，人工覆盖需同时使用 `--allow-over-budget --budget-reason REASON`。字符数和文件数仍是上下文代理，不是真实 Token。

## 门禁定义与去重

`.mase/gates.yaml` 为 gate 的 stage、command、inputs、artifacts、tests、covers 和 candidate 绑定的唯一执行源。`analysis` 阶段用于设计前影响门禁；`impact_reconcile` 位于 capability 阶段并在候选冻结前完成。初始化/迁移生成的空模板仍保持 legacy ad-hoc 兼容，填入首个 gate 后才启用 canonical 执行。`inputs` 和 Capability `paths` 可使用项目根内 glob；摘要按实际命中文件计算。`related_tests` 与 `integration_tests` 必须选择不同边界；相同 selector/command 会由 `mase gate plan` 告警。不同 gate 不因命令偶然相同而自动互认，只有 `covers` 显式声明且来源输入、制品和候选绑定覆盖目标时才共享一次执行。

Gate Runner 默认 concise：完整脱敏输出写入 `.mase/evidence`，终端只显示结果、耗时、日志路径和有限失败末尾。人工调试长任务需要实时进度时使用 `--verbose`；两种模式产生相同的证据语义。

`mase gate plan` 同时输出生效 Profile 的 micro/capability/final 调度和每个 gate 的 `next_action`。final 的任务、缺失定义和未通过的 non-final 前置条件会先显示，只有这些条件满足后才建议 freeze。

final gate 不应在 Build 中用于“看看是否全绿”。先运行 micro/capability，处理人工意见并冻结候选；候选后生产代码、测试、规格或门禁定义发生变化时解冻，再修复受影响门禁。失败驱动的重跑属于必要验证，成功候选未变化时的重复全量测试才应被消除。

## 发布软件

计划打包、发布、部署、线上验证或恢复时，从 `templates/release-context.yaml` 建立平台中立的 Release Overlay，并使用 `release-software` Skill。发布覆盖层不取代 Profile：它组合 `intent`、`authority`、不可变制品身份/来源、目标、rollout、状态迁移、接口、外部能力、恢复和观察，风险触发器仍可把 Standard 升级为 Strict。

先运行 `mase release plan --context release-context.yaml` 检查矛盾与生成 pending runbook；read-only 权限下不得构建、上传、停服、切流、发布、修改基础设施或恢复。实际命令仍由项目的 `.mase/gates.yaml` 和 CI/CD/平台脚本定义；release gate 必须显式声明 `mode`、`effect`、`required_authority` 和 `requires`，MASE CLI 不充当生产部署器。

状态只能按 fresh evidence 递进：`planned → candidate_ready → artifact_ready → target_ready → live_verified → observed`。最终包的 commit 或 manifest 正确并不能单独证明交付内容正确；`artifact_ready` 不能宣称上线。运行进程、容器 Ready 或 HTTP 200 也不能单独证明真实能力；`live_verified` 必须核对线上制品身份并通过声明的消费者路径。观察期完成前保留上一版、备份和恢复控制，恢复后重新验证才报告 `recovered`。

通用顺序是：尽量在影响前完成制品、运行时、配置、密钥、状态、staging 与恢复预检；再按受控 blast radius 发布；然后验证身份、接口、外部能力和真实 P0 路径；最后完成观察并清理。Windows/PowerShell、Linux、容器编排、Serverless、Registry、桌面/移动端和 App Store 只是按需 adapter，不进入通用默认清单。新增管理端口、共享主机重启或远程控制服务属于独立基础设施 change，不随应用发布静默扩权。

## 状态不一致

如果任务全部完成但 state 仍是 build，`mase status` 会失败。verify/retro/release 都不是完成态：门禁未完成时显示 `ready_for_gate`，门禁完成后显示 `ready_to_complete`；只有 complete/archived 是终态。

## Brownfield 基线

`.mase/baseline.yaml` 只登记采用 MASE 前已存在且稳定复现的非硬门禁失败。每条债务必须有失败签名、负责人、到期日和处置 change。当前失败与有效基线完全一致时结果是 `passed_with_baseline`，新增、恶化或过期仍然阻断；API 契约、适用 P0 E2E、凭据与数据安全门禁不能通过普通基线豁免。

## 非破坏更新

`mase update --dry-run` 会预览 metadata、复合 stack→主 stack/toolchains、change state、旧 evidence、baseline、规则适配器、Sandbox 与 Gitignore。实际修改前写入 `.mase-backup/<timestamp>/`；无法验证的旧 passed evidence 降为 stale，损坏/未知 Schema 和用户修改文件报告 conflict，不静默覆盖。重复执行不得继续产生迁移变化。

## Token 节约

- 读取前运行 `mase context plan --change NAME --read RELATED_PATH --json`，按计划而不是全仓扫描加载文件。
- 每个任务只读当前 Spec、相关接口/测试、diff 和交接摘要。
- Skill 先读短路由器，只加载命中的 reference。
- 默认排除 history、training、framework 演示、产品实例、OpenSpec 归档、`.mase/evidence`、日志、报告和数据目录。
- 平台可通过显式参数、usage JSON 或 `MASE_INPUT_TOKENS`/`MASE_OUTPUT_TOKENS`/`MASE_CACHE_TOKENS` 提供真实用量；没有 usage 时，字符数只能称为 context proxy。
- Standard 仅在风险命中时做深度安全评审；Strict 独立评审无异议时一轮结束。

## 兼容说明

- `mase init NAME -p package -c cap...` 继续按 Python 项目工作。
- v1.3 master 和历史文档不会自动删除；v2 停止开发期双写。
- 安装、更新和删除前始终可先使用 `--dry-run`。

## 框架仓库维护

MASE 仓库只保存过程框架及其现行文档、测试和 MASE 培训材料。采用项目必须放在同级独立根目录；通用培训、研究演示、历史备份和产品数据也不放入 MASE。根目录 `pytest` 只运行 `tests/`，提交前再运行 repository boundary audit，确保未知顶层目录、非现行资料、嵌套仓库与生成缓存没有回流。
