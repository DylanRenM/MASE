# MASE — Measures AI Software Engineering

> 本项目是 MASE（Measures AI Software Engineering）话题的集中讨论与工作空间，于 2026-07-14 将散落在其他项目中的历史记录和产出物迁移至此。

## 项目概述

**MASE** 是麦哲思科技结合 VIBE 工程（Vibe-Driven AI Engineering）实践经验，沉淀并开源的一套 AI 软件工程统一方法论与工具集。它在 OpenSpec（规范层）和 Superpower/Skills（能力层）的基础上，补齐了流程编排、质量门禁、复盘闭环等关键拼图。

- **GitHub 仓库**：https://github.com/DylanRenM/MASE（v1.1）
- **核心架构**：四 Agent · 六阶段 · PDCA 闭环
- **开源博客**：[MASE：一套会自我进化的 AI 软件工程方法论](https://blog.csdn.net/dylanren/article/details/110038792)

### 架构层级

```
┌──────────────────────────────────────────┐
│ MASE（编排层）                             │
│ 四 Agent 协作 · 六阶段流转 · PDCA 进化     │
├──────────────────────────────────────────┤
│ OpenSpec 层（规范层）                      │
│ proposal / design / specs / tasks         │
├──────────────────────────────────────────┤
│ Superpower / Skills 层（能力层）           │
│ brainstorming / TDD / code-review / ...   │
└──────────────────────────────────────────┘
```

### 四 Agent 分工

| Agent | 角色 | 职责 |
|---|---|---|
| A1 | 计划与统管 | 接收需求 → 分解任务 → 调度 → 门禁把关 → 发布 |
| A2 | 需求 | 澄清需求 → 交互原型 → 操作流程 → 系统测试用例 |
| A3 | 开发 | 技术预研 + POC → 架构设计 → TDD 构建 |
| A4 | 质量 | 设计评审 → 代码评审+安全扫描 → BUG修复 → 复盘 |

### 六阶段

Proposal → Design → Build → Verify → Retro → Release

### 八大工程原则

1. 需求澄清确认（原型确认后才进入开发）
2. 设计预研，消除风险（技术预研 + POC 验证）
3. TDD 驱动（内外双循环）
4. 验证与确认检查（端到端验证 + 合规审查）
5. 根因分析（任何 Bug 必须找到根本原因）
6. 系统化解决（杜绝临时补丁）
7. 固定节奏提交（每 20 次对话一次提交）
8. 及时备份（删除/回退前必做备份）

---

## 目录结构

```
MASE/
├── README.md                           # 本文件
├── github-repo/                        # GitHub 仓库（v1.1，通过 ZIP 下载解压）
├── training/                           # 培训材料
│   ├── mase-framework/                 # MASE 框架培训（5个文件）
│   ├── ai4se/                          # AI4SE 培训体系（9个文件）
│   └── skills/                         # Skill 系列培训（9个文件）
├── framework/                          # 框架文档与演示
│   ├── process-framework.html          # 过程框架
│   ├── hmm-presentation.html           # HMM 演示
│   ├── harness-maturity-model.md       # HMM 模型文档
│   ├── risd-framework.html             # RISD 框架
│   ├── AInotSilver.html
│   ├── 需求工程标准-中文版.html
│   ├── org-harness-framework/          # 组织级 Harness 框架
│   │   ├── dod.md
│   │   ├── lcm.md
│   │   └── README.md
│   ├── spec-contract-tdd/              # Spec、契约与 TDD 融合之道
│   │   ├── ai-spec-contract-tdd.html
│   │   ├── _shared/fonts/              # 字体资源
│   │   └── assets/                     # 图片资源
│   └── playwright/                     # Playwright 测试规范
│       ├── playwright-standards.md     # 元素定位规范
│       └── 2026-07-12-playwright-e2e-testing-design.md  # 设计文档
├── scripts/                            # PPT 生成与分析脚本（9个文件）
├── tests/                              # 测试示例
│   └── test_api_contract.py            # API 接口契约测试
├── history/                            # 历史讨论记录
│   └── MASE_历史讨论汇总.md            # 完整历史汇总
└── .gitignore
```

---

## 培训材料索引

### MASE 框架培训（[training/mase-framework/](training/mase-framework/)）

| 文件 | 说明 |
|---|---|
| MASE框架培训讲义.pptx | 最新版（37页，16:9，深蓝+金色+青色） |
| MASE框架培训讲义V1.pptx | V1 版本 |
| MASE框架培训讲义V1.pdf | V1 PDF 版 |
| MASE框架培训讲义V01.pptx | AIM 版本 |
| MASE框架培训大纲.xlsx | 培训大纲（2天/半天） |

### AI4SE 培训体系（[training/ai4se/](training/ai4se/)）

| 文件 | 说明 |
|---|---|
| AI4SE培训课件-V1.pptx | AI4SE 课件 V1 |
| AI4SE培训课件-V0.pptx | AI4SE 课件 V0 |
| AI4SE培训课件-V1.pdf | AI4SE 课件 PDF |
| AI4SE培训大纲.xlsx | 半天 3 小时大纲 |
| AI4SE-思想与实践.html | HTML 版思想与实践 |
| AI软件工程培训讲义.pptx | AI 软件工程讲义 |
| AI编程思想完整分类归集.docx | 编程思想分类 |
| 培训大纲案例.xlsx | 大纲参考案例 |
| measures-training.html | HTML 培训材料 |

### Skill 系列培训（[training/skills/](training/skills/)）

| 文件 | 说明 |
|---|---|
| 白话Skill.html / .pptx | Skill 通俗讲解 |
| what-is-skill.html / -v2.html | Skill 概念介绍 |
| skill-vs-program.html | Skill 与程序对比 |
| skill-vs-prompt.html | Skill 与 Prompt 对比 |
| skill-experience.html | Skill 实践经验 |
| refactor-22-case.html / -full.html | 22 种代码坏味道重构 |

---

## 框架文档索引

| 文件 | 路径 | 说明 |
|---|---|---|
| process-framework.html | [framework/](framework/process-framework.html) | 过程框架演示 |
| hmm-presentation.html | [framework/](framework/hmm-presentation.html) | HMM 成熟度模型演示 |
| harness-maturity-model.md | [framework/](framework/harness-maturity-model.md) | HMM 模型文档 |
| risd-framework.html | [framework/](framework/risd-framework.html) | RISD 框架 |
| org-harness-framework/ | [framework/](framework/org-harness-framework/) | 组织级 Harness 框架（dod/lcm） |
| ai-spec-contract-tdd.html | [framework/spec-contract-tdd/](framework/spec-contract-tdd/ai-spec-contract-tdd.html) | AI 编程的三重奏：Spec、契约与 TDD 的融合之道 |
| playwright-standards.md | [framework/playwright/](framework/playwright/playwright-standards.md) | Playwright 元素定位规范 |
| playwright-e2e-testing-design.md | [framework/playwright/](framework/playwright/2026-07-12-playwright-e2e-testing-design.md) | Playwright E2E 测试设计文档 |

---

## 测试示例

| 文件 | 路径 | 说明 |
|---|---|---|
| test_api_contract.py | [tests/](tests/test_api_contract.py) | API 接口契约测试（字段命名一致性、响应结构验证） |

---

## 历史讨论

完整的 MASE 历史讨论汇总请参阅 [history/MASE_历史讨论汇总.md](history/MASE_历史讨论汇总.md)。

历史讨论来源：
- **日常办公项目**（2026-07-07 ~ 07-08）：MASE 框架培训讲义 PPT 生成与多轮格式调整
- **SOLO Agent 项目**（2026-07-08）：AI4SE 培训大纲生成与字体统一

---

## 待处理事项

- [x] ~~GitHub 仓库克隆~~：已通过 ZIP 下载解压到 `github-repo/` 目录（git clone 因网络超时失败，改用 curl + Python zipfile 方案成功）

---

## 迁移记录

- **迁移日期**：2026-07-14
- **迁移方式**：复制（保留原件）
- **迁移范围**：MASE 框架核心 + AI4SE 培训体系 + Skill 系列 + HMM + Spec/契约/TDD 融合文档 + Playwright 测试规范 + API 契约测试
- **原件位置**：日常办公、新讲义、org-harness-framework、pilot、numerology、新想法等项目
- **记忆迁移**：20260705（TDD）+ 20260707 + 20260708 + 20260713（Playwright）四期 session memory 已复制到本项目 memory 目录

## License

MIT © 2026 麦哲思科技 (Measures Technology)
