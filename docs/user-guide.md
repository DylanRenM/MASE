# MASE v2 使用手册

## 安装

```bash
python3 -m pip install .
mase install --source .
mase --version
```

`mase install` 只复制 `framework-manifest.yaml` 声明的运行时，不复制历史、培训或产品实例。

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
| `mase status --change NAME` | 从 state+tasks 检查进度一致性 |
| `mase metrics FILE...` | 报告上下文代理指标 |
| `mase metrics ... --input-tokens N` | 记录平台提供的真实 Token |
| `mase update --dry-run` | 预览 v1.3→v2 迁移 |
| `mase install --dry-run` | 查看框架将分发的资源 |

## 开发方式

1. 对已有需求、原型和测试做差异分析；一次批量确认真正的冲突。
2. 记录 Profile、stack、风险和门禁到 change 的 `mase-state.yaml`。
3. 只生成 Profile/风险需要的设计产物。
4. 将工作拆成纵向任务，每项声明 `reads` 和 `verify`。
5. RED→GREEN→REFACTOR 只跑相关测试；Capability 和最终边界再扩大验证。
6. 从结构化 evidence 生成报告，归档时生成 master 快照。

## 状态不一致

如果任务全部完成但 state 仍是 build，`mase status` 会失败。修正唯一 state，而不是修改验证报告。相反，state 标为 complete 但仍有任务未完成也会失败。

## 非破坏更新

`mase update` 默认检测：版本、核心规则、IDE adapters、Sandbox 模板和 Gitignore。实际修改前写入 `.mase-backup/<timestamp>/`；用户修改过的 generated 文件报告 conflict，不静默覆盖。

## Token 节约

- 每个任务只读当前 Spec、相关接口/测试、diff 和交接摘要。
- Skill 先读短路由器，只加载命中的 reference。
- 默认排除 history、training、framework 演示、产品实例和归档。
- 没有平台 usage 时，字符数只能称为 context proxy。

## 兼容说明

- `mase init NAME -p package -c cap...` 继续按 Python 项目工作。
- v1.3 master 和历史文档不会自动删除；v2 停止开发期双写。
- 安装、更新和删除前始终可先使用 `--dry-run`。
