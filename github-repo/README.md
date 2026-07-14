# MASE — Measures AI Software Engineering

> 不止于 Spec，不止于 Skill — 一套会自我进化的 AI 软件工程方法论

**MASE** 是麦哲思科技结合自身在 VIBE 工程（Vibe-Driven AI Engineering）领域的一线实践经验，沉淀并开源的一套 AI 软件工程统一方法论与工具集。它在 OpenSpec（规范层）和 Superpower/Skills（能力层）的基础上，补齐了流程编排、质量门禁、复盘闭环等关键拼图。

```
┌──────────────────────────────────────────┐
│              MASE（编排层）                  │
│   四 Agent 协作 · 六阶段流转 · PDCA 进化     │
├──────────────────────────────────────────┤
│  OpenSpec 层（规范层）                       │
│   proposal / design / specs / tasks       │
├──────────────────────────────────────────┤
│  Superpower / Skills 层（能力层）            │
│   brainstorming / TDD / code-review / ... │
└──────────────────────────────────────────┘
```

## 核心架构

**四 Agent** — 专业分工，各司其职：

| Agent | 角色 | 职责 |
|:-----:|------|------|
| A1 | 计划与统管 | 接收需求 → 分解任务 → 调度 → 门禁把关 → 发布 |
| A2 | 需求 | 澄清需求 → 交互原型 → 操作流程 → 系统测试用例 |
| A3 | 开发 | 技术预研 + POC → 架构设计 → TDD 构建 |
| A4 | 质量 | 设计评审 → 代码评审+安全扫描 → E2E 自动化回归+契约门禁 → BUG修复 → 复盘 |

**六阶段** — Proposal → Design → Build → Verify → Retro → Release，层层递进，PDCA 闭环。

## 九大工程原则

按研发生命周期排序，贯穿始终：

| # | 原则 | 核心含义 |
|:-:|------|------|
| 1 | 需求澄清确认 | 原型确认后才进入开发 |
| 2 | 设计预研，消除风险 | 技术预研 + POC 验证 |
| **3** | **契约式约束** | **从 Spec 推导 DbC 契约（前置/后置/不变式）。API 级硬性必做，模块级强推荐，函数级可选。TDD 翻译契约到测试，代码保留运行时断言。** |
| 4 | TDD 驱动 | 内外双循环：spec 驱动 + 测试驱动 |
| 5 | 验证与确认检查 | E2E 自动化回归 + 人工探索性测试 + 合规审查 |
| 6 | 根因分析 | 任何 Bug 必须找到根本原因 |
| 7 | 系统化解决 | 杜绝临时补丁，修一个 Bug 防一类 Bug |
| 8 | 固定节奏提交 | 每 20 次对话一次提交 |
| 9 | 及时备份 | 删除/回退前必做备份 |

> **E2E 自动化测试要求**：凡有用户界面（Web/桌面/移动）的项目，在 Proposal 阶段定义 E2E 验收场景，Build 阶段同步编写 E2E 测试实现，Verify 阶段执行全量 E2E 回归作为门禁。核心场景 E2E 覆盖率 100% 方可通过 Verify。

## 与已有框架的关系

| 维度 | OpenSpec | Superpower/Skills | **MASE** |
|------|:---:|:---:|:---:|
| 定位 | 规范层 | 能力层 | **编排层** |
| 解决什么 | 规范怎么写 | 具体任务怎么做 | **整个过程怎么跑** |
| 有质量门禁？ | 无 | 无 | **有** |
| 有复盘闭环？ | 无 | 无 | **有（PDCA）** |
| 能自我进化？ | 不能 | 不能 | **能** |

## 快速开始

```bash
# 1. 安装（部署 Skills 到 AI IDE）
cd measures-framework-package
./install.sh

# 2. 创建新项目
# 触发 brainstorming → 框架自动运转

# 3. 复盘总结
# 触发 Retro 阶段 — 四层蒸馏复盘
```

## 目录结构

```
measures-framework-package/
├── training/          # 培训讲义（HTML 幻灯片）
├── docs/              # 设计文档、项目结构规范、用户手册
├── skills/            # Skill 定义文件
├── templates/         # 全套模板体系
└── install.sh         # 一键部署脚本

docs/
├── superpowers/       # 统一开发框架设计文档
└── mase-framework-introduction-blog.md   # 详细介绍博文
```

## License

MIT © 2026 麦哲思科技 (Measures Technology)
