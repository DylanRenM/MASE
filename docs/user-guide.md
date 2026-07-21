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
| `mase gate manual GATE --change NAME ...` | 记录允许人工完成的结构化证据 |
| `mase metrics FILE...` | 报告上下文代理指标 |
| `mase metrics ... --input-tokens N` | 记录平台提供的真实 Token |
| `mase update --dry-run` | 预览 v1.3→v2 迁移 |
| `mase install --dry-run` | 查看框架将分发的资源 |

## 开发方式

1. 对已有需求、原型和测试做差异分析；一次批量确认真正的冲突。
2. 记录 Profile、主 stack、toolchains、风险、产品属性与本次影响面到 `mase-state.yaml`，由此推导 GatePlan。
3. 只生成 Profile/风险需要的设计产物。
4. 将工作拆成纵向任务，每项声明 `reads` 和 `verify`。
5. RED→GREEN→REFACTOR 只跑相关测试；Capability 和最终边界再扩大验证。
6. 用 Gate Runner 生成自动 evidence；输入、日志或制品变化后重新执行 stale 门禁。归档时生成 master 快照。

## 状态不一致

如果任务全部完成但 state 仍是 build，`mase status` 会失败。verify/retro/release 都不是完成态：门禁未完成时显示 `ready_for_gate`，门禁完成后显示 `ready_to_complete`；只有 complete/archived 是终态。

## Brownfield 基线

`.mase/baseline.yaml` 只登记采用 MASE 前已存在且稳定复现的非硬门禁失败。每条债务必须有失败签名、负责人、到期日和处置 change。当前失败与有效基线完全一致时结果是 `passed_with_baseline`，新增、恶化或过期仍然阻断；API 契约、适用 P0 E2E、凭据与数据安全门禁不能通过普通基线豁免。

## 非破坏更新

`mase update --dry-run` 会预览 metadata、复合 stack→主 stack/toolchains、change state、旧 evidence、baseline、规则适配器、Sandbox 与 Gitignore。实际修改前写入 `.mase-backup/<timestamp>/`；无法验证的旧 passed evidence 降为 stale，损坏/未知 Schema 和用户修改文件报告 conflict，不静默覆盖。重复执行不得继续产生迁移变化。

## Token 节约

- 每个任务只读当前 Spec、相关接口/测试、diff 和交接摘要。
- Skill 先读短路由器，只加载命中的 reference。
- 默认排除 history、training、framework 演示、产品实例和归档。
- 没有平台 usage 时，字符数只能称为 context proxy。

## 兼容说明

- `mase init NAME -p package -c cap...` 继续按 Python 项目工作。
- v1.3 master 和历史文档不会自动删除；v2 停止开发期双写。
- 安装、更新和删除前始终可先使用 `--dry-run`。
