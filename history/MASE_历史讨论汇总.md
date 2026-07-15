# MASE 历史讨论汇总

> 本文档汇总了在多个项目中散落的 MASE（Measures AI Software Engineering）相关讨论记录，于 2026-07-14 迁移至本项目。

---

## 一、MASE 框架概述

**MASE（Measures AI Software Engineering）** 是麦哲思科技结合 VIBE 工程（Vibe-Driven AI Engineering）实践经验，沉淀并开源的一套 AI 软件工程统一方法论与工具集。

- **GitHub 仓库**：https://github.com/DylanRenM/MASE（v1.1，2026-07-04 发布）
- **核心架构**：四 Agent · 六阶段 · PDCA 闭环
- **定位**：在 OpenSpec（规范层）和 Superpower/Skills（能力层）之上的编排层

### 四 Agent 分工

| Agent | 角色 | 职责 |
|---|---|---|
| A1 | 计划与统管 | 接收需求 → 分解任务 → 调度 → 门禁把关 → 发布 |
| A2 | 需求 | 澄清需求 → 交互原型 → 操作流程 → 系统测试用例 |
| A3 | 开发 | 技术预研 + POC → 架构设计 → TDD 构建 |
| A4 | 质量 | 设计评审 → 代码评审+安全扫描 → BUG修复 → 复盘 |

### 六阶段

Proposal → Design → Build → Verify → Retro → Release，层层递进，PDCA 闭环。

### 八大工程原则

1. 需求澄清确认（原型确认后才进入开发）
2. 设计预研，消除风险（技术预研 + POC 验证）
3. TDD 驱动（内外双循环：spec 驱动 + 测试驱动）
4. 验证与确认检查（端到端验证 + 合规审查）
5. 根因分析（任何 Bug 必须找到根本原因）
6. 系统化解决（杜绝临时补丁，修一个 Bug 防一类 Bug）
7. 固定节奏提交（每 20 次对话一次提交）
8. 及时备份（删除/回退前必做备份）

---

## 二、讨论来源项目

历史讨论散落在以下多个项目中：

| 来源项目 | 项目路径 | 讨论日期 | Session ID | 主题 |
|---|---|---|---|---|
| numerology | `trae_projects/numerology/` | 2026-07-05 | 6a48c814... | TDD 驱动实现功能 |
| 日常办公 | `trae_projects/日常办公/` | 2026-07-07 ~ 2026-07-08 | 6a387be0... | MASE PPT 生成 + AI4SE PPT 处理 |
| SOLO Agent（AI4SE 大纲） | TRAE SOLO ModularData | 2026-07-08 | 6a4d8c91... | AI4SE 培训大纲生成 |
| pilot | `trae_projects/pilot/` | 2026-07-13 | 6a53728c... | Playwright E2E 测试执行 |
| TRAE Work | Documents/新想法/ | 2026-07-14 | - | Spec、契约与 TDD 融合之道 |

---

## 三、讨论时间线与内容

### 阶段一：AI4SE 培训 PPT 处理（2026-07-07）

**来源**：日常办公项目，Session 6a387be0...

| 时间 | 意图 | 关键产出 |
|---|---|---|
| 18:26 | 将 HTML 文件转换为 PPTX 格式 | 生成 37 页 PPTX，发现 PPTX 无法完全还原 HTML 高级 CSS 样式 |
| 20:25 | 修复排版混乱问题 | 使用 Playwright 无头浏览器截图方案，37 页 PPT 保留原设计但文字不可编辑（3.4MB） |
| 20:47 | 生成可编辑文本版本 | 递归树形遍历 + Flex/Grid 容器处理 + 文本高度估算，输出 87KB 可编辑 PPT |
| 21:32 | 方案对比与选择建议 | 截图版（布局完美但不可编辑，2.8MB）vs 文本框版（可编辑但布局混乱，0.7MB） |

**关键经验**：
- PPTX 格式无法完全还原 HTML 中的高级 CSS 样式（flexbox 等）
- 截图方式能完美保留原 HTML 排版但文字不可编辑
- 可编辑版本需实现递归树形遍历、Flex/Grid 容器识别、文本高度估算
- HTML 转 PPTX 比直接重新生成效率低，flexbox 与绝对定位差异巨大

---

### 阶段二：MASE 框架培训讲义生成（2026-07-08）

**来源**：日常办公项目，Session 6a387be0...

| 时间 | 意图 | 关键产出 |
|---|---|---|
| 05:50 | 重新生成 MASE 框架培训讲义 PPTX | 37 页 16:9 宽屏，深蓝背景+金色标题+青色强调色，包含核心理念/Agent层/阶段层/设计哲学/项目与工具/Skills详解/快速上手等章节 |
| 06:07 | 修复 4 个问题 | 添加麦哲思 logo（37页）、修复第3页溢出、调整第5页顺序、解决第17页重叠 |
| 06:22 | 修复 6 个格式问题 | 绿色文字改色（#3A7878→#7DCECE）、间距调整、删除重复行、文本框扩展、垂直居中、排版优化 |
| 06:27 | 修复第34页和末页 | 底部面板高度调整（0.8"→1.4"）、删除"谢谢"上方∞符号 |
| 06:37 | 缩小标题与解释间距 | 调整 space_before/line_spacing/step_height 参数 |
| 06:49 | 精细调整第5页间距 | 标题行高 1.2→1.0，step_height 0.55"→0.7" |
| 06:53 | 全局统一条目间距 | 全局降低标题行高至 1.0，解释文字 line_spacing 1.2 + space_before 1pt |
| 07:03 | 总结 PPT 编写经验教训 | 8 条核心经验记录到 project_memory.md |

**PPT 编写 8 条核心经验**：
1. **文本间距控制**：需同时调整 line_spacing 和 step_height
2. **文字溢出色块**：panel 高度要预留足够空间，用程序验证 bottom < 7.0"
3. **文字折行**：文本框宽度不够时增加宽度，函数参数化支持自定义 width
4. **分隔线重叠**：增大 item_height 可解决
5. **HTML 转 PPTX**：flexbox 与绝对定位差异巨大，直接重新生成比转换更高效
6. **颜色对比度**：深色背景上用亮色系（#7DCECE 替代 #3A7878）
7. **Logo 添加**：深色背景用无色 Logo，浅色用有色 Logo
8. **可验证性**：每次修改后用 python 脚本验证 shape 属性

**配色方案**：深蓝背景 + 金色标题 + 青色（#7DCECE）强调

---

### 阶段三：AI4SE 培训大纲生成（2026-07-08）

**来源**：SOLO Agent 项目，Session 6a4d8c91...

| 时间 | 意图 | 关键产出 |
|---|---|---|
| 07:35 | 为 MASE 框架培训讲义 V1 生成培训大纲 | 2 天 875 分钟，32 个主题，6 列结构（时间/大类/小类/主题/时间/重点），含 SUM 公式汇总 |
| 07:38 | 压缩为半天 3 小时 | 32 条精简为 11 条，4 个 Agent 合并为 1 条，6 个阶段合并为 3 条，875 分钟→180 分钟 |
| 07:57 | 为 AI4SE 培训课件 V2 生成大纲 | 半天 3 小时，4 大模块（开场导入/需求与设计/编码/AI编程思想与总结），覆盖 74 页 PPT |
| 08:12 | 补充遗漏模块 | 补充测试与质量保障（自动化测试/五维度分类/测试护城河三层防线/质量度量/知识沉淀）+ 过程体系（OSSP→PDP→Harness/HMM五级成熟度/LLM赋能CMMI） |
| 08:16 | 修复 WPS 打开问题 | 文件大小变化因 recalc 计算公式值导致 |
| 08:22 | 确认 6 大模块覆盖 | 认知重塑/工程哲学/需求与设计/编码/测试与质量保障/过程体系 |
| 18:34 | 统一字体字号 | 全部统一为微软雅黑，修改 136 处文本 |
| 18:42 | 调整页面字号 | 统一所有标题字号为 22pt Bold |

**AI4SE 培训 6 大模块**：
1. 认知重塑
2. 工程哲学
3. 需求与设计
4. 编码
5. 测试与质量保障
6. 过程体系

**关键概念**：
- 五维度分类
- 测试护城河三层防线
- HMM 五级成熟度
- OSSP→PDP→Harness 三级架构

---

### 阶段四：TDD 驱动实现（2026-07-05）

**来源**：numerology 项目，Session 6a48c814...

| 时间 | 意图 | 关键产出 |
|---|---|---|
| 08:55 | 方案A的规范审核与确认 | 规范已完成自我审查并保存，无 TBD/TODO，设计与现有代码结构一致 |
| 09:55 | 使用 TDD 驱动实现功能 | 创建 C测算V2Panel.test.tsx 测试文件，实现 6 个测试用例，所有 42 个测试通过 |

**新流程路径**：idle → calibrating → feedback → question → analyzing → result；跳过校验路径：idle → question(跳过校验) → analyzing → result

**核心经验**：
- 规范审核先于实现，确保设计清晰无歧义
- TDD 驱动：先写测试用例，再实现功能
- 测试覆盖所有流程路径（正常路径 + 跳过路径）

---

### 阶段五：Playwright E2E 测试体系（2026-07-13）

**来源**：pilot 项目，Session 6a53728c...

| 时间 | 意图 | 关键产出 |
|---|---|---|
| 06:01 | 运行所有功能的 E2E 测试 | 60 通过，2 预存失败，6 跳过；覆盖用户登录/COSMIC度量/NESMA度量/知识库/设置等模块 |
| - | 补充交互测试 | 新增按钮交互测试（Tab切换、radio切换、清除按钮），总测试达 109 通过，1 预存失败 |

**测试体系设计要点**：
- 元素定位优先级：getByRole → getByLabel → getByPlaceholder → getByText → getByTestId
- 禁止使用 CSS class/id 选择器和 XPath
- 双轨制：Playwright 原生 runner（回归测试）+ Python debug.py（TRAE 调试）
- 独立测试数据库 `pilot_test.db`，数据隔离
- fixtures 体系：seed.py 生成 fixtures.json，测试只读操作

---

### 阶段六：Spec、契约与 TDD 融合之道（2026-07-14）

**来源**：TRAE Work，Documents/新想法/

**产出物**：[ai-spec-contract-tdd.html](framework/spec-contract-tdd/ai-spec-contract-tdd.html)

**核心内容**：AI 编程的三重奏 — Spec（规范）、契约（Contract）与 TDD（测试驱动开发）的融合方法论

---

## 四、产出物清单

### MASE 框架培训材料

| 文件 | 路径 | 说明 |
|---|---|---|
| MASE框架培训讲义.pptx | `training/mase-framework/` | 最新版（37页，16:9，深蓝+金色+青色） |
| MASE框架培训讲义V1.pptx | `training/mase-framework/` | V1 版本 |
| MASE框架培训讲义V1.pdf | `training/mase-framework/` | V1 PDF 版 |
| MASE框架培训讲义V01.pptx | `training/mase-framework/` | AIM 版本 |
| MASE框架培训大纲.xlsx | `training/mase-framework/` | 培训大纲（2天/半天） |

### AI4SE 培训材料

| 文件 | 路径 | 说明 |
|---|---|---|
| AI4SE培训课件-V1.pptx | `training/ai4se/` | AI4SE 课件 V1 |
| AI4SE培训课件-V0.pptx | `training/ai4se/` | AI4SE 课件 V0 |
| AI4SE培训课件-V1.pdf | `training/ai4se/` | AI4SE 课件 PDF |
| AI4SE培训大纲.xlsx | `training/ai4se/` | 半天 3 小时大纲 |
| AI4SE-思想与实践.html | `training/ai4se/` | HTML 版思想与实践 |
| AI软件工程培训讲义.pptx | `training/ai4se/` | AI 软件工程讲义 |
| AI编程思想完整分类归集.docx | `training/ai4se/` | 编程思想分类 |
| 培训大纲案例.xlsx | `training/ai4se/` | 大纲参考案例 |
| measures-training.html | `training/ai4se/` | HTML 培训材料 |

### Skill 系列培训

| 文件 | 路径 | 说明 |
|---|---|---|
| 白话Skill.html / .pptx | `training/skills/` | Skill 通俗讲解 |
| what-is-skill.html / -v2.html | `training/skills/` | Skill 概念介绍 |
| skill-vs-program.html | `training/skills/` | Skill 与程序对比 |
| skill-vs-prompt.html | `training/skills/` | Skill 与 Prompt 对比 |
| skill-experience.html | `training/skills/` | Skill 实践经验 |
| refactor-22-case.html / -full.html | `training/skills/` | 22 种代码坏味道重构 |

### 框架文档

| 文件 | 路径 | 说明 |
|---|---|---|
| process-framework.html | `framework/` | 过程框架演示 |
| hmm-presentation.html | `framework/` | HMM 成熟度模型演示 |
| harness-maturity-model.md | `framework/` | HMM 模型文档 |
| risd-framework.html | `framework/` | RISD 框架 |
| org-harness-framework/ | `framework/` | 组织级 Harness 框架（dod/lcm） |
| ai-spec-contract-tdd.html | `framework/spec-contract-tdd/` | AI 编程的三重奏：Spec、契约与 TDD 的融合之道 |
| playwright-standards.md | `framework/playwright/` | Playwright 元素定位规范（优先级：getByRole→getByLabel→getByPlaceholder→getByText→getByTestId） |
| 2026-07-12-playwright-e2e-testing-design.md | `framework/playwright/` | Playwright E2E 测试设计文档（13 章，含数据流、定位策略、Page Object、TDD 调试工具） |

### 测试示例

| 文件 | 路径 | 说明 |
|---|---|---|
| test_api_contract.py | `tests/` | API 接口契约测试（字段命名一致性、响应结构验证） |

### 脚本工具

| 文件 | 路径 | 说明 |
|---|---|---|
| verify_mase_ppt.py | `scripts/` | MASE PPT 验证脚本 |
| analyze_pptx.py | `scripts/` | PPTX 分析工具 |
| extract_slides.py | `scripts/` | 幻灯片提取 |
| html_to_pptx.py | `scripts/` | HTML 转 PPTX |
| pptx_to_pdf.py | `scripts/` | PPTX 转 PDF |
| slide_layouts.json | `scripts/` | 布局配置 |

---

## 五、迁移记录

- **迁移日期**：2026-07-14
- **迁移方式**：复制（保留原件）
- **迁移范围**：MASE 框架核心 + AI4SE 培训体系 + Skill 系列 + HMM + Spec/契约/TDD 融合文档 + Playwright 测试规范 + API 契约测试
- **记忆迁移**：20260705（TDD）+ 20260707 + 20260708 + 20260713（Playwright）四期 session memory 已复制到本项目 memory 目录
- **GitHub 仓库**：https://github.com/DylanRenM/MASE（v1.1，已通过 ZIP 下载解压到 github-repo/ 目录）
- **原件位置**：日常办公、新讲义、org-harness-framework、pilot、numerology、新想法等项目
