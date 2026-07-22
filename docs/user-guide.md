# MASE v2 使用手册

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
| `mase gate run GATE --change NAME -- COMMAND...` | 执行门禁并原子记录可复现证据 |
| `mase gate run ... --verbose -- COMMAND...` | 人工调试时流式显示完整门禁输出 |
| `mase gate plan --change NAME [--json]` | 查看 runnable/reusable/deferred/stale 门禁和重复测试诊断 |
| `mase gate freeze --change NAME` | 在前置门禁完成后冻结最终候选 |
| `mase gate manual GATE --change NAME ...` | 记录允许人工完成的结构化证据 |
| `mase metrics FILE...` | 报告上下文代理指标 |
| `mase metrics ... --input-tokens N` | 记录平台提供的真实 Token |
| `mase metrics ... --usage-file usage.json` | 读取平台导出的 input/output/cache Token |
| `mase context plan --change NAME --read PATH --json` | 生成不包含文件正文的上下文计划 |
| `mase update --dry-run` | 预览 v1.3→v2 迁移 |
| `mase install --dry-run` | 查看框架将分发的资源 |

## 开发方式

1. 对已有需求、原型和测试做差异分析；一次批量确认真正的冲突。
2. 记录 Profile、主 stack、toolchains、风险、产品属性与本次影响面到 `mase-state.yaml`，由此推导 GatePlan。
3. 只生成 Profile/风险需要的设计产物。
4. 将工作拆成纵向任务，每项声明 `reads` 和 `verify`。
5. RED→GREEN→REFACTOR 只跑相关测试；Capability 边界运行互不重复的 integration/security/P0。
6. 先完成轻量人工确认，再用 `mase gate freeze` 固定最终候选；只对该候选运行 final 全量门禁。
7. 用 Gate Runner 生成自动 evidence；仅受影响输入、日志、制品或候选变化后重新执行 stale 门禁。完整签名未变时 Runner 复用 evidence，归档时生成 master 快照。

## 门禁定义与去重

`.mase/gates.yaml` 为 gate 的 stage、command、inputs、artifacts、tests、covers 和 candidate 绑定的唯一执行源。初始化/迁移生成的空模板仍保持 legacy ad-hoc 兼容，填入首个 gate 后才启用 canonical 执行。`inputs` 和 Capability `paths` 可使用项目根内 glob；摘要按实际命中文件计算。`related_tests` 与 `integration_tests` 必须选择不同边界；相同 selector/command 会由 `mase gate plan` 告警。不同 gate 不因命令偶然相同而自动互认，只有 `covers` 显式声明且来源输入、制品和候选绑定覆盖目标时才共享一次执行。

Gate Runner 默认 concise：完整脱敏输出写入 `.mase/evidence`，终端只显示结果、耗时、日志路径和有限失败末尾。人工调试长任务需要实时进度时使用 `--verbose`；两种模式产生相同的证据语义。

`mase gate plan` 同时输出生效 Profile 的 micro/capability/final 调度和每个 gate 的 `next_action`。final 的任务、缺失定义和未通过的 non-final 前置条件会先显示，只有这些条件满足后才建议 freeze。

final gate 不应在 Build 中用于“看看是否全绿”。先运行 micro/capability，处理人工意见并冻结候选；候选后生产代码、测试、规格或门禁定义发生变化时解冻，再修复受影响门禁。失败驱动的重跑属于必要验证，成功候选未变化时的重复全量测试才应被消除。

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
