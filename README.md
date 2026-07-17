# 麦哲思AI软件开发统一流程

> MASE (Measures AI Software Engineering) — v1.3

## 概述

本框架是一套完整的 AI 辅助软件开发方法论与工具集，核心架构为"**四 Agent · 九原则 · 六阶段 · PDCA 闭环**"。

- **四 Agent**：计划与统管 (A1) + 需求 (A2) + 开发 (A3) + 质量 (A4)
- **九大工程原则**：需求澄清 → 设计预研 → 契约式约束 → TDD 驱动 → E2E 验证 → 根因分析 → 系统化解决 → 固定节奏提交 → 及时备份
- **六阶段**：Proposal → Design → Build → Verify → Retro → Release
- **PDCA 闭环**：每一次开发都在自我进化

---

## ⚠️ 安装顺序（必读）

```
第 1 步：  ./install.sh          → 部署框架组件到 ~/.measures-framework/
第 2 步：  pip install -e .       → 安装 mase 命令行工具
第 3 步：  mase init ...          → 创建新项目
```

**必须先运行 `install.sh`，再执行 `pip install`。** 颠倒顺序会导致 `mase init` 生成的 `mase check` 缺少工程规则文件（98% → 100% 的区别）。

---

## 第 1 步：安装框架

```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动完成：

| 操作 | 目标位置 |
|------|---------|
| 部署项目模板 | `~/.measures-framework/templates/` |
| 部署 Agent 定义（4个） | AI IDE skills 目录（自动检测） |
| 部署 Skills（11个） | AI IDE skills 目录（自动检测） |
| 部署工程规则 | `~/.measures-framework/project-rules.md` |
| 部署文档 + 使用手册 | `~/.measures-framework/docs/` |
| 部署培训讲义 | `~/.measures-framework/training/` |
| 部署文档索引页 | `~/.measures-framework/index.html` |

支持的 AI IDE：Trae / Cursor / Windsurf（自动检测 skills 目录）。

---

## 第 2 步：安装 CLI

```bash
pip install -e . --break-system-packages
```

> macOS 用户需要加 `--break-system-packages`（PEP 668）。Linux 用户如果遇到同样错误也加此参数。建议使用虚拟环境：
> ```bash
> python3 -m venv .venv && source .venv/bin/activate && pip install -e .
> ```

验证安装：

```bash
mase --help
```

---

## 第 3 步：创建项目

```bash
mase init my-project -p my_app -c auth payment

cd my-project

# （可选）安装项目开发依赖
pip install -e .

# 合规检查
mase check
```

预期输出：`MASE 合规检查 — ✓ 通过  41/41  100%`

然后对 AI 说：**"创建新项目 my-project"** — 六阶段自动运转。

---

## 包含内容

| 目录 | 内容 |
|------|------|
| `agents/` | 4 个 Agent 定义（计划与统管 / 需求 / 开发 / 质量，含阶段流程 + 门禁规则） |
| `templates/` | 项目初始化模板（proposal/design/specs/tasks/contract + cases/lessons 模板） |
| `skills/` | 11 个 AI Skills 定义（全 MASE 六阶段覆盖） |
| `project-rules.md` | 九大工程原则 + E2E 门禁 + 契约约束（AI 可读格式） |
| `docs/` | 框架设计文档 + 项目结构规范 + 使用手册 |
| `training/` | 35 页 Vellum 风格培训讲义（HTML，可直接浏览器打开） |
| `index.html` | 框架文档索引入口页 |

---

## 九大工程原则

1. **需求澄清确认** — 原型确认后才进入开发
2. **设计预研，消除风险** — 技术预研 + POC 验证
3. **契约式约束** — 从 Spec 推导 DbC 契约（前置/后置/不变式），TDD 翻译到测试 + 运行时断言
4. **TDD 驱动** — 内外双循环：spec 驱动 + 测试驱动，含 E2E 环境隔离
5. **验证与确认检查** — E2E 自动化回归 + 环境自动恢复 + 人工探索 + 合规审查
6. **根因分析** — 任何改错必找到根本原因
7. **系统化解决** — 杜绝临时补丁
8. **固定节奏提交** — 每 20 次对话做提交
9. **及时备份** — 删除/回退必做备份

---

## 命令速查

```bash
mase init <name> -p <pkg> -c <caps...>   # 创建项目
mase check                                 # 合规检查（含阶段状态追踪）
mase update                                # 同步框架最新版本到已有项目
mase update --dry-run                      # 预览更新变更（不实际修改）
mase update --check                        # 仅检查可更新组件
mase --help                                # 完整帮助
```

---

## 相关文档

- [框架设计文档](docs/MASE-framework.md)
- [使用手册](docs/user-guide.md)
- [项目目录结构规范](docs/project-structure-spec.md)
- [培训讲义（浏览器打开）](training/measures-training.html)

---

## 版本

v1.3 — 2026-07-17

## 许可

Measures (麦哲思) 版权所有
