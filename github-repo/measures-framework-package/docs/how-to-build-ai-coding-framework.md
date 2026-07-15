# 如何搭建自己的 AI Coding 过程框架

> 基于 MASE (麦哲思AI软件开发统一流程) 的设计实践总结。

---

## 为什么需要过程框架

AI Coding 工具（Trae、Cursor、Windsurf）降低了编码门槛，但带来了新问题：

- **风格飘忽**: LLM 每次采样不同，同一功能的代码风格来回跳
- **步骤跳跃**: 跳过设计直接写代码，跳过测试直接上线
- **质量黑洞**: 没有评审门禁，BUG 累积到不可收拾
- **知识流失**: 这次踩的坑下次还会踩，经验无法沉淀

过程框架解决的核心问题：**把人的工程纪律转化为 AI 的硬约束。**

---

## 框架八层架构

```
┌─────────────────────────────────────────┐
│ 1. 原则 (Principles)        常驻内存     │
│    ─────────────────                    │
│ 2. 规则 (Rules)             按需加载     │
│    ─────────────────                    │
│ 3. 职责 (Agents)            角色分工     │
│    ─────────────────                    │
│ 4. 阶段 (Phases)            流程串联     │
│    ─────────────────                    │
│ 5. 技能 (Skills)            动作拆解     │
│    ─────────────────                    │
│ 6. 质控 (Quality Control)   门禁检查     │
│    ─────────────────                    │
│ 7. 输出 (Outputs)           文档模板     │
│    ─────────────────                    │
│ 8. 工具 (Tools)             外部依赖     │
└─────────────────────────────────────────┘
```

---

## 第 1 层：原则 — 系统常驻，全程遵守

### 设计要点

原则是框架的"宪法"。AI IDE 会将原则文件注入**每一次对话**的上下文，因此必须满足：

1. **量少**: 常驻内存消耗 token，每条原则都要精简到极限
2. **不冗余**: 原则只写"是什么"，不写"怎么做"。细节放在规则层
3. **编号索引**: 用 R01-R09 编号，Agent 可精确引用 "违反 R03"

### MASE 实践

9 条原则，70 行，AI 每次对话都加载：

```
R01 需求澄清确认   → 原型确认后才进入开发
R02 设计预研       → POC 验证所有外部依赖
R03 契约式约束     → Spec → 三层 DbC 契约
R04 TDD 驱动       → 先写测试再写代码，10 步微循环
R05 验证与确认     → P0 E2E 100% + 契约测试 100%
R06 根因分析       → BUG 修复先找根本原因
R07 系统化解决     → 杜绝临时补丁
R08 固定节奏提交   → 每 20 次对话 / 每 Capability 提交
R09 及时备份       → 删除/回退前备份
```

### 关键决策

- 原则放 `project-rules.md`，同时部署到 `.trae/rules/`、`.cursor/rules/` 等 IDE 标准目录，确保各 IDE 都能自动加载
- 原则文件中不含操作细节，只保留"硬阻断"级别的约束和一个指向详细规范的索引表

---

## 第 2 层：规则 — 按需加载，场景触发

### 设计要点

原则说"要做什么"，规则说"怎么做"。规则文件独立存放，Agent 在特定场景下按需加载，避免常驻消耗 token。

### MASE 实践

| 规则文件 | 加载场景 | 内容 |
|---------|---------|------|
| `coding-standards.md` | Agent 3 编码时 | 9 章跨语言通用规范（命名/硬编码/函数/错误/日志/导入/注释/DRY） |
| `design-principles.md` | Design L2 / 设计评审时 | 23 条原则平铺（SOLID 5 + GRASP 9 + KISS/DRY/YAGNI + 分层 5） |
| `project-structure-spec.md` | 项目初始化时 | 目录结构规范（镜像原则 / Capability 对齐） |
| `glossary.md` | 术语混淆时 | 契约/TDD外循环/fixtures 等核心术语定义 |

### 关键决策

- 原则文件末尾放一个"规范文档索引"表，Agent 知道什么时候加载哪个文件
- 编码规范分两层：跨语言通用（框架提供）+ 语言特定（Agent 3 在 Design L2 技术栈确定后生成）
- 设计原则把 SOLID 5 条 + GRASP 9 条全部穷举平铺，不分层级，每条标注 MASE 评审重点

---

## 第 3 层：职责 — 划分 Agent，各司其职

### 设计要点

单 Agent 做全流程的问题是**角色混淆**：写代码时思考需求，评审时又为自己写的代码辩护。多 Agent 架构的核心是**让写代码的人不评审自己的代码**。

### MASE 实践 — 一拖三架构

```
Agent 1 (统管)
  ├── 调度 Agent 2/3/4
  ├── 管理六阶段门禁
  └── 执行 Release
      │
      ├── Agent 2 (需求)     brainstorming + 原型 + proposal
      ├── Agent 3 (开发)     Design L1/L2 + TDD Build
      └── Agent 4 (质量)     评审 + 扫描 + E2E + BUG修复 + 复盘
```

### 每个 Agent 的定义模板

每个 Agent 一个 `SKILL.md`，按统一模板定义：

```markdown
---
name: agent-X-xxx
description: 一句话定位
---

## 角色定位
| 身份 | 核心职责 | 使用 Skills | 上游 | 下游 |

## 激活条件
明确 4-5 个触发场景

## 执行流程
ASCII 流程图 + 步骤说明

## 产出物
| 产出物 | 阶段 | 位置 |

## 关键原则
3-5 条行为准则
```

### 关键决策

- Agent 和 Skill 是不同概念：Agent 是角色（持续存在），Skill 是可复用能力（被调用）
- Agent 1 不需要独立执行阶段，它的职责是调度和门禁
- Agent 3 承担最重的职责（Design L1/L2 + Build），因为设计和编码是同一个人格做出的决策更连贯

---

## 第 4 层：阶段 — 划分工作流程，门禁串联

### 设计要点

阶段定义"什么时候做什么"。每个阶段有明确的**准入条件、执行动作、产出物、完成标准（DoD）**。

### MASE 实践 — 六阶段 PDCA

```
Proposal  →  Design  →  Build  →  Verify  →  Retro  →  Release
(Plan)       (Plan)     (Do)      (Check)    (Act)      (Deliver)
```

| 阶段 | 谁执行 | 核心动作 | 门禁 |
|------|-------|---------|------|
| Proposal | Agent 2 | brainstorming + 原型 + proposal.md | 原型走查 + Checklist |
| Design L1 | Agent 3 | 技术预研 + POC | 所有外部依赖跑通 |
| Design L2 | Agent 3 | 架构设计 + Spec + 契约 + coding-standards | Agent 4 设计评审 |
| Build | Agent 3 (+4旁路) | 10 步 TDD 微循环 | 每个 Scenario 通过 |
| Verify | Agent 4 | E2E 回归 + Bug修复 + 合规审查 | P0 E2E 100% + BUG清零 |
| Retro | Agent 4 + 1 | 复盘 + 改进措施 | 改进措施执行完毕 |
| Release | Agent 1 | git commit + 文档归档 | 最终合规审查 |

### 关键决策

- 阶段状态写入 `mase-state.yaml`（一个 `phase` 字段），Agent 1 和 `mase check` 都读它来追踪进度
- Design 拆成 L1（技术预研）和 L2（架构设计），因为架构决策依赖预研结论
- Build 阶段 Agent 4 旁路并行执行评审和扫描，不阻塞 Agent 3

---

## 第 5 层：技能 — 定义每个动作的执行步骤

### 设计要点

技能 (Skill) 是 Agent 的"工具箱"。每个 Skill 定义了一个完整的执行流程。Agent 调用 Skill 而不是自己发明流程，确保每次执行的一致性。

### MASE 实践 — 12 个 Skills × 6 阶段矩阵

| 阶段 | 必做 Skills | 可选 |
|------|-----------|------|
| Proposal | brainstorming, frontend-skill | — |
| Design | code-quality-controller, frontend-design | — |
| Build | test-driven-development, webapp-testing | — |
| Build(旁路) | code-review, security-review | — |
| Verify | bug-fixer, code-review, security-review | flowchart-review 🔧 |
| Retro | — | — |
| Release | git-commit | — |

### 每个 Skill 的定义模板

```markdown
---
name: skill-name
description: 一句话描述
---

## 定位（属于哪个阶段、哪个 Agent 调用）
## 执行流程（步骤 1 → 步骤 2 → ...）
## 输入 / 输出
## 审查清单 / 检查维度
## 错误处理 / 门禁升级
```

### 关键决策

- Skill 分"必做"和"可选"两级。必做的在流程中刚性调用；可选的在描述中标注 🔧
- 评审类 Skill（code-review, security-review）设计为**分组多代理并行**架构，避免单次审查遗漏
- `flowchart-review` 作为可选工具，提供逻辑流一致性视角，但不强制

---

## 第 6 层：质控 — DoD、门禁、Checklist

### 设计要点

质控层定义"怎样算做完"。没有质控层，阶段变成一个无约束的概念。质控必须是**可检查的**，不能是模糊描述。

### MASE 实践

#### DoD 统一定义在 Agent 1

6 个阶段的完成标准全部写在 Agent 1 的 `门禁职责` 章节，每阶段一个可勾选的 checklist。其他文档只引用不重复定义。

#### Proposal 门禁示例

```
☑ 人工确认 Proposal 文档（Why/What/Capabilities/Scope）
☑ 每个 Success Criteria 有对应的测试用例
☑ 交互原型覆盖全部操作流程
☑ E2E 验收场景含 P0/P1/P2 分级
☑ 操作流程完整可执行
☑ 原型走查演示通过
☑ mase-state.yaml phase 更新为 proposal
```

#### 三级质量检查

| 级别 | 含义 | 示例 |
|------|------|------|
| 硬阻断 | 不通过则禁止进入下一阶段 | P0 E2E 失败、API 契约测试失败 |
| 软提醒 | 不通过不阻断，但需记录 | 代码规约建议、模块级契约缺口 |
| 豁免 | Agent 1 特批 | 纯样式调整免 E2E、紧急热修复 |

### 关键决策

- DoD 只有一个权威来源（Agent 1），避免多处定义不一致
- 门禁异常有升级路径（连续3次失败 → Agent 1 决策回退或豁免）
- `mase check` CLI 命令提供独立于 Agent 的客观合规检查

---

## 第 7 层：输出 — 文档模板与目录结构

### 设计要点

每个阶段的产出物必须有**固定位置、固定格式、固定模板**。AI 不能自由发挥文档结构——结构越自由，下游 Agent 解析越困难。

### MASE 实践

```
openspec/changes/{change-name}/
├── proposal.md              # Agent 2 产出（含 E2E 验收场景）
├── mase-state.yaml          # Agent 2 写入，全程更新
├── tech-feasibility.md      # Agent 3 Design L1 产出
├── architecture.md          # Agent 3 Design L2 产出
├── detailed-design.md       # Agent 3 Design L2 产出
├── contract.md              # Agent 3 Design L2 产出（三层契约）
├── coding-standards.md      # Agent 3 Design L2 产出（语言特定规范）
├── tasks.md                 # Agent 3 Design L2 产出
├── specs/
│   └── {capability}/
│       └── spec.md          # Agent 3 Design L2 产出（Gherkin）
├── cases/bugs/              # Agent 4 Verify 产出（BUG 记录）
└── lessons/                 # Agent 4 Retro 产出（复盘报告）
```

### 模板策略

- `mase init` 生成项目骨架时放入模板文件
- 模板使用占位符（`{name}`、`{capability}`），Agent 填充具体内容
- E2E 测试模板（Playwright conftest + P0 测试）自动生成到 `tests/e2e/`

### 关键决策

- `mase-state.yaml` 是唯一的状态机——Agent 2 写入初始值，后续 Agent 更新 `phase` 字段
- contract.md 放在 change 根级而非 specs/ 内，因为它是跨 capability 的契约定义
- 所有文档路径与 `mase check` 的检查逻辑严格对应

---

## 第 8 层：工具 — 外部依赖与运行环境

### 设计要点

框架需要 CLI 工具支持，不能纯靠文档和规则。CLI 负责：初始化项目、合规检查、状态追踪——这些事情 Agent 不应该自己做（不可靠），必须有确定性工具。

### MASE 实践

| 工具 | 用途 | 类型 |
|------|------|------|
| `mase init` | 项目初始化（目录 + 模板 + IDE 规则部署） | CLI |
| `mase check` | 合规检查（目录/阶段/内容 三层检查） | CLI |
| `mase_cli/contract.py` | DbC 运行时断言库（require/ensure/invariant_check） | Python 库 |
| `install.sh` | 框架安装（部署到 `~/.measures-framework/`） | Shell 脚本 |
| Playwright + Pytest | E2E 测试执行 | 外部依赖 |
| PyYAML | mase-state.yaml 解析 | Python 依赖 |

### CLI 设计原则

- `mase init -p <package> -c <capability1> <capability2>` — 必须参数化，不能交互式
- `mase check` — 输出格式化（pass/fail 计数 + 进度条 + 下一步提示）
- 所有 CLI 操作幂等——重复运行不出错

### 关键决策

- `install.sh` 在 `mase init` 之前运行，将框架组件部署到用户目录
- `mase init` 从 `~/.measures-framework/` 读取模板，部署到项目
- PyPI 包入口 (`pyproject.toml` 中 `[project.scripts]`) 使 `mase` 命令在 pip install 后全局可用

---

## 搭建你自己的框架：执行路线图

### 第 1 步：定义原则（第 1 层）

1. 列出你的团队最常违反的工程纪律（不会超过 10 条）
2. 每条用一句话描述，编号
3. 创建 `project-rules.md`，确认能被 IDE 自动加载

### 第 2 步：划分 Agent 和阶段（第 3、4 层）

1. 画一张泳道图：谁在什么时候做什么
2. 确保"写代码的人不评审自己的代码"
3. 定义每个阶段的准入条件、产出物、完成标准

### 第 3 步：定义 Skills（第 5 层）

1. 列出所有"重复性动作"（评审、测试、提交、BUG修复...）
2. 每个 Skill 写一个执行流程（步骤 1 → 步骤 2 → ...）
3. 按阶段分类，标注必做/可选

### 第 4 步：建立质控（第 6 层）

1. 每个阶段写 3-7 条可勾选的 DoD checklist
2. 明确硬阻断 / 软提醒 / 豁免三级
3. 有 CLI 命令做独立合规检查

### 第 5 步：固化输出（第 7 层）

1. 画一张项目目录结构图
2. 每个产出物定义模板文件
3. 初始化命令自动生成骨架和模板

### 第 6 步：补充规则和工具（第 2、8 层）

1. 编码规范、设计原则放入独立文件，按需加载
2. 建 CLI 工具：`init`、`check`
3. 写 `install.sh` 一键部署

### 第 7 步：验证一致性

1. 逐层检查：原则→规则→Agent→阶段→Skill→质控→输出，每层的引用是否对齐
2. 用 CLI 做端到端测试：`init` → `check` → 预期输出是否符合设计
3. 用真实项目跑一轮，记录所有卡点，迭代修正

---

## 经验教训

1. **先把原则写下来再开始设计**，否则每轮讨论都在原地打转
2. **常驻 vs 按需的分层**是 token 优化的核心——原则文件每多一行，每次对话都多一份成本
3. **不要害怕重命名**。`design.md` → `MASE-framework.md`、`.openspec.yaml` → `mase-state.yaml`——正确的名字大幅降低理解成本
4. **DoD 必须单一来源**。如果 DoD 散落在多个文件里，迭代时必然出现不一致
5. **CLI 是框架的"硬着陆"**。Agent 可能忘记某条规则，但 `mase check` 不会
6. **PPT/培训材料要随框架同步更新**。不一致的培训材料比没有材料更糟糕
