# 麦哲思AI软件开发统一流程 (MASE (Measures AI Software Engineering)) 设计文档

> 状态: 已确认 | 日期: 2026-07-14 | 版本: v1.1

## 1. 概述

将 OpenSpec、Superpower 及现有 Skills 整合为一个统一的开发框架，采用「一拖三」Agent 架构，实现小步快跑、增量开发、并行开发的工程目标。

### 核心原则

1. 设计先行，方向确认再实现
2. TDD 内外双循环（spec 驱动测试，测试驱动代码）
3. 系统性解决问题，不做临时补丁
4. 需求澄清优先，原型确认优先
5. 根因分析，不盲目修改
6. 经验沉淀，每次都要学一次

---

## 2. Agent 架构

```
                      用户
                       │
                       ▼
┌──────────────────────────────────────────────┐
│        Agent 1: 计划与统管 (Orchestrator)       │
│    接收需求 → 分解 → 调度 → 门禁 → Release       │
│    工具: project-planning-expert, git-commit    │
└──────┬────────────┬────────────┬──────────────┘
       │            │            │
       ▼            ▼            ▼
┌──────────┐ ┌────────────┐ ┌──────────────┐
│ Agent 2  │ │  Agent 3   │ │   Agent 4    │
│  需求     │ │   开发      │ │    质量       │
├──────────┤ ├────────────┤ ├──────────────┤
│Proposal  │ │Design L1   │ │设计评审       │
│ +        │ │ 技术预研    │ │ code-quality │
│ HTML原型  │ │ + POC      │ │ frontend     │
│ +        │ │            │ │ -design      │
│ 操作流程  │ │Design L2   │ │              │
│ +        │ │ 架构+详细   │ │Build质量把关  │
│ 测试用例  │ │ 设计+specs │ │ code-review  │
│          │ │ +contract  │ │ security-    │
│          │ │            │ │ review       │
│          │ │Build       │ │              │
│          │ │ TDD微循环  │ │Verify        │
│          │ │ (10步)     │ │ bug-fixer    │
└──────────┘ └────────────┘ └──────────────┘
```

### Agent 职责

| Agent | 职责 | 使用的 Skills/Subagents |
|-------|------|------------------------|
| Agent 1 (计划与统管) | 接收需求、任务分解调度、门禁管理、Release | `project-planning-expert`, `git-commit` |
| Agent 2 (需求) | 需求探索澄清、生成交互原型、编写操作流程、定义测试用例 | `brainstorming`, `frontend-skill` |
| Agent 3 (开发) | 技术预研+POC、架构设计、契约推导、Specs 编写、TDD 构建 | `test-driven-development`, `webapp-testing` |
| Agent 4 (质量) | 设计评审、代码评审+合规检查、安全扫描、端到端验证+Bug修复 | `code-quality-controller`, `frontend-design`, `code-review`, `security-review`, `bug-fixer` |

---

## 3. 阶段流程

### 3.1 阶段1: 需求 (Proposal) — Agent 2 执行

**目标**: 确认「要什么」，产出可验证的验收标准。

| 产出物 | 形式 | 说明 |
|--------|------|------|
| Proposal 文档 | `openspec/changes/{name}/proposal.md` | Why / What Changes / Capabilities / Impact / Out of Scope / Stakeholders / Success Criteria |
| 界面原型 | 可交互 HTML 文件 | `frontend-skill` 生成，覆盖核心操作流程 |
| 操作流程 | proposal.md 内嵌章节 | Markdown 编号步骤列表 |
| 系统测试用例 | proposal.md 内嵌表格 | 用例ID / 前置条件 / 操作步骤 / 预期结果 |

**工具**: `brainstorming`（需求澄清）、`frontend-skill`（原型生成）

**门禁** (Agent 1 执行):
- [ ] 人工确认 Proposal 文档
- [ ] Checklist 逐项检查（所有 Success Criteria 有对应测试用例、原型覆盖全部操作流程）
- [ ] 原型走查演示

---

### 3.2 阶段2: 设计 (Design) — Agent 3 执行

**目标**: 确认「怎么做」，消除技术风险，产出完整设计规格。

#### Layer 1: 技术可行性研究

| 产出物 | 内容 |
|--------|------|
| `tech-feasibility.md` | ① 三张汇总表（技术难点方案 / 非功能性需求 / 外部依赖评估）|
| | ② 高风险项详细调研（成熟方案 + 最新技术 + 接口规范 → 推荐方案 + 遗留风险）|
| | ③ 可复用构件清单 |
| | ④ 全量 POC 验证脚本（所有外部依赖在本环境跑通）|

**工具**: `WebSearch`（联网调研）、`RunCommand`（POC 验证）

**门禁**: Checklist + 人工确认 + POC 结果演示

#### Layer 2: 架构设计

| 产出物 | 内容 |
|--------|------|
| `architecture.md` | 系统架构图、技术栈决策表、组件/模块边界、接口协议、部署拓扑 |
| `detailed-design.md` | 管道流程设计、数据模型（ER图/表结构）、API 接口定义、关键算法/策略 |
| `contract.md` | 三层契约（API级/模块级/函数级）— 前置/后置/不变式 |
| `specs/{capability}/spec.md` | Gherkin 风格验收规格（ADDED/MODIFIED/REMOVED Requirements + Scenario）|
| `tasks.md` | `project-planning-expert` 编排的开发任务清单 |

**节奏**: 分层审批（architecture → detailed-design → specs+contract），capability 可并行

**设计评审** (Agent 4 执行):
- [ ] `code-quality-controller`: 架构合规性（SOLID/GRASP）、需求一致性、技术可行性一致性、文档一致性
- [ ] `frontend-design`: 视觉设计原则、交互设计原则、响应式策略、无障碍性、前端性能策略

**门禁**: Checklist + 人工确认 + 设计走查

---

### 3.3 阶段3: 构建 (Build) — Agent 3 执行

**目标**: TDD 微循环，逐个 Capability、逐个 Scenario 增量构建。

每个 Scenario 微循环（10步）:
1. **复用检查** — 对照 Layer 1 产出的可复用构件清单
2. **契约翻译 → 测试** — contract.md → TDD RED
3. **写行为测试** — Spec → TDD RED（pytest 单元测试 + 集成测试）
4. **写实现代码** — 含运行时断言 require/ensure/invariant_check
5. **跑测试** — 单元测试 + 集成测试 + 契约测试
6. **E2E 测试** — has_ui: true 时，webapp-testing
7. **功能测试** — `webapp-testing`（如有 UI）
8. **代码评审** — `code-review`（含 spec 合规检查 + 契约合规 + 代码规约检查）
9. **安全扫描** — `security-review`
10. **通过 → git commit**

**工具**: `test-driven-development`、`webapp-testing`、`code-review`、`security-review`

**Capability 门禁**: 该 Capability 所有 Scenario 测试通过 + 代码评审通过

---

### 3.4 阶段4: 验证 (Verify) — Agent 4 执行

**目标**: 端到端验证，发现并修复所有 Bug，补充测试缺口。

```
人工端到端测试 → 发现 BUG → bug-fixer 微循环:

  修复（A/B双修 + 系统性方案）
  → 回归验证
  → 测试缺口复盘（为什么自动化测试没发现？补充用例）
  → 横向扫描同类 BUG
  → 经验教训记录（结构化 YAML 格式）
  → BUG 关闭
  → 循环至无新 BUG
```

**工具**: `bug-fixer`（含合并的 TRAE-debugger 运行时调试能力）

**门禁**: 全部 BUG 关闭

---

### 3.5 阶段5: 复盘 (Retrospective) — Agent 4 + Agent 1 协同

**目标**: PDCA 闭环的 A（Act）环节。系统总结本轮开发经验，提炼模式，改进流程。

```
全部 BUG 关闭
    │
    ▼
┌──────────────────────────────────────────────────┐
│ 复盘分析                                           │
│                                                  │
│ 1. 收集材料                                        │
│    ├── docs/lessons/ 中本轮所有经验教训               │
│    ├── docs/cases/bugs/ 中本轮所有 BUG 案例          │
│    └── 代码评审记录中的反复出现的问题                   │
│                                                  │
│ 2. 模式分析                                        │
│    ├── 高发 BUG 模式：哪些类型的 BUG 反复出现？          │
│    ├── 测试盲区：哪些场景的测试覆盖始终不够？             │
│    ├── 设计缺陷：哪些架构决策导致了多个 BUG？            │
│    └── 流程短板：哪个阶段门禁没有挡住问题？              │
│                                                  │
│ 3. 产出复盘报告                                     │
│    └── docs/lessons/YYYY-MM-DD-{project}-retro.md   │
│                                                  │
│ 4. 改进措施（如需要）                                │
│    ├── 更新 Skill 规则                              │
│    ├── 更新模板                                    │
│    ├── 补充代码规约                                 │
│    └── 调整门禁 Checklist                           │
└──────────────────────────────────────────────────┘
```

**产出**: `docs/lessons/YYYY-MM-DD-{project}-retro.md`（复盘报告）

**门禁**: 复盘报告确认 + 改进措施执行完毕

---

### 3.6 阶段6: 发布 (Release) — Agent 1 执行

1. **最终合规审查** — 对照全部 spec + design 全量检查
2. **自动编写使用手册** — `docs/user-guide.md`
3. **git commit** — `git-commit` Skill, Conventional Commit + 变更摘要
4. **归档 OpenSpec Change**

**工具**: `code-review`（合规检查）、`git-commit`

---

## 4. Skills 与阶段映射汇总

| Skill / Subagent | Proposal | Design | Build | Verify | Release |
|-------|:---:|:---:|:---:|:---:|:---:|
| `brainstorming` | ✅ | | | | |
| `frontend-skill` | ✅ | | | | |
| `project-planning-expert` | | ✅ | | | |
| `code-quality-controller` | | ✅ | | | |
| `frontend-design` | | ✅ | | | |
| `test-driven-development` | | | ✅ | | |
| `webapp-testing` | | | ✅ | | |
| `code-review` | | | ✅ | | ✅ |
| `security-review` | | | ✅ | | |
| `bug-fixer` | | | | ✅ | |
| `git-commit` | | | | | ✅ |

---

## 5. 需变更的 Skills

| Skill | 变更内容 | 状态 |
|-------|---------|------|
| `bug-fixer` | + 原则 8「测试反哺原则」; 合并 TRAE-debugger 运行时调试能力（作为路径 A/B 增强模式） | ✅ 已完成 (v3) |
| `code-review` | + spec 合规检查项 + 代码规约检查项 | ✅ 已完成 (v2) |
| `TRAE-debugger` | 合入 bug-fixer 后删除 | ✅ 已合入 |

---

## 6. 目录结构

> 详见 [项目目录结构规范](project-structure-spec.md)

### 6.1 规范文档层 (openspec/)

```
openspec/
  changes/
    {change-name}/
      .openspec.yaml
      proposal.md            # Agent 2 产出
      tech-feasibility.md     # Agent 3 Layer 1 产出
      architecture.md         # Agent 3 Layer 2 产出
      detailed-design.md      # Agent 3 Layer 2 产出
      contract.md             # Agent 3 Layer 2 产出（契约推导）
      tasks.md                # Agent 3 Layer 2 产出 (project-planning-expert)
      specs/
        {capability}/
          spec.md             # Agent 3 Layer 2 产出
```

### 6.2 产品代码层 (src/)

```
src/
  {package_name}/
    {capability}/              # 与 specs/{capability}/ 一一对应
      models/                  # 数据模型
      services/                # 业务逻辑
      routes/                  # API 路由（可选）
      schemas/                 # 请求/响应 Schema（可选）
    shared/                    # 跨 capability 共享
      config/                  # 全局配置
      database/                # 数据库连接
      utils/                   # 通用工具
```

### 6.3 测试代码层 (tests/) — 镜像 src/

```
tests/
  unit/
    {capability}/
      models/                  # 镜像 src/{capability}/models/
      services/                # 镜像 src/{capability}/services/
      routes/                  # 镜像 src/{capability}/routes/
    shared/                    # 镜像 src/shared/
  integration/                 # 集成测试
  e2e/                         # E2E 测试（Playwright）
  fixtures/{capability}/       # 测试数据，镜像 src/
  conftest.py                  # pytest 共享 fixtures
```

### 6.4 文档层 (docs/)

```
docs/
  user-guide.md                # Agent 1 Release 产出
  lessons/                     # 经验教训（bug-fixer 原则7输出）
    YYYY-MM-DD-{topic}.md
  cases/                       # 典型案例
    bugs/                      # BUG 案例
    patterns/                  # 设计模式
    pitfalls/                  # 踩坑记录
  superpowers/
    specs/
      YYYY-MM-DD-{topic}-design.md
```

### 6.5 脚本与配置 (scripts/ config/)

```
scripts/                       # 工具脚本（非产品代码）
  run.py                       # 项目入口
  migrate.py                   # 一次性脚本
config/                        # 配置文件
  logging.yaml
pyproject.toml
Makefile
.env.example
.gitignore
README.md
```

---

## 7. 自审清单

- [x] 无 TBD/TODO 占位符
- [x] 6 阶段逻辑自洽，阶段间输入输出明确
- [x] Agent 职责边界清晰，无交叉和遗漏
- [x] 每个阶段明确了使用的 Skill/Subagent
- [x] 门禁机制完整（每阶段 Checklist + 人工确认 + 走查）
- [x] TDD 内外双循环明确定义（10步微循环）
- [x] Skills 变更计划已全部执行
- [x] 文档引用路径已统一为相对路径
