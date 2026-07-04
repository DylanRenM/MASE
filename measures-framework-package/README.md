# 麦哲思AI软件开发统一流程

> MASE (Measures AI Software Engineering) — v1.0

## 概述

本框架是一套完整的 AI 辅助软件开发方法论与工具集，核心架构为"**四 Agent · 六阶段 · PDCA 闭环**"，专为 Trae IDE 环境设计。

- **四 Agent**：计划与统管 (A1) + 需求 (A2) + 开发 (A3) + 质量 (A4)
- **六阶段**：Proposal → Design → Build → Verify → Retro → Release
- **PDCA 闭环**：每一次开发都在自我进化

## 安装方式

### 方式一：自动安装（macOS / Linux）

```bash
chmod +x install.sh
./install.sh
```

安装脚本会自动完成：
1. 将模板文件部署到 `~/.measures-framework/templates/`
2. 将 Skills 部署到 `~/.trae-cn/skills/`（Trae IDE 技能目录）
3. 将文档和培训讲义复制到 `~/.measures-framework/`

### 方式二：手动安装

```bash
# 1. 部署项目模板
cp -r templates/ ~/.measures-framework/templates/

# 2. 部署 Skills（Trae IDE）
cp -r skills/* ~/.trae-cn/skills/

# 3. 复制文档
cp -r docs/ ~/.measures-framework/docs/
cp -r training/ ~/.measures-framework/training/
```

## 快速开始

1. 安装完成后，在 Trae IDE 中打开或创建项目
2. 将模板复制到项目中：

```bash
cp -r ~/.measures-framework/templates/* openspec/changes/_template/
```

3. 创建项目目录结构（参考 `templates/STRUCTURE.md`）
4. 对 AI 说："创建新项目 {项目名}"，框架将自动按照六阶段流程运转

## 包含内容

| 目录 | 内容 |
|------|------|
| `templates/` | 项目初始化模板（proposal/design/specs/tasks + cases/lessons 模板） |
| `skills/` | 9 个 AI Skills 定义（bug-fixer/code-review/brainstorming/TDD 等） |
| `docs/` | 框架设计文档 + 项目结构规范 + 使用手册 |
| `training/` | 35 页 Vellum 风格培训讲义（HTML，可直接浏览器打开） |

## 八大工程规则

1. **设计方案先行** — 修改代码前必做设计
2. **需求澄清确认** — 原型确认后才进入开发
3. **根因分析** — 任何改错必找到根本原因
4. **系统化解决** — 杜绝临时补丁
5. **TDD 驱动** — 每个功能自动化测试
6. **提交节奏** — 每 20 次对话做提交
7. **备份机制** — 删除/回退必做备份
8. **合规检查** — 代码评审对照 spec + design

## 版本

v1.0 — 2026-07-03

## 许可

Measures (麦哲思) 版权所有

## CLI 工具

框架附带 `mase` 命令行工具：

```bash
# 安装
pip install -e .

# 初始化新项目
mase init my-project -p my_app -c auth payment

# 合规检查
mase check
```

详细用法见 `mase --help`。
