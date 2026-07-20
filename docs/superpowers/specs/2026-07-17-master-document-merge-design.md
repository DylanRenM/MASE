---
normative: false
status: superseded
superseded_by: openspec/changes/adaptive-lightweight-mase/design.md#d2状态与证据分离报告全部派生
---

# MASE Master 文档合并机制设计

> 创建日期：2026-07-17
> 状态：已被 MASE v2“归档时快照”替代
> 作者：Dylan Ren
> 基于：2026-07-03 MASE 统一开发框架设计

## 1. 背景与动机

### 1.1 当前状态

MASE 框架继承 OpenSpec 的 changeset 模式，所有规范文档按 change 独立存放：

```
openspec/changes/{change-name}/
  ├── proposal.md
  ├── architecture.md
  ├── detailed-design.md
  ├── contract.md
  ├── specs/{capability}/spec.md
  └── ...
```

当前 Release 阶段有一项操作：

> 最终合规审查 — 对照**全部** spec.md + 项目的设计文档全量检查

这暗示了框架需要"全量文档"的视角，但 MASE 目前没有定义这个"全量文档"以什么形式存在、如何维护、何时更新。

### 1.2 当前模式的具体问题

| # | 问题 | 场景 | 后果 |
|:---|:---|:---|:---|
| 1 | **无产品需求全景** | 想了解"这个产品有哪些功能需求" | 需遍历所有 change 目录手动汇总 |
| 2 | **跨 change 冲突隐蔽** | Change #3 修改了 login 的 spec，Change #7 也修改了同一部分 | Release 时才暴露，修复成本极高 |
| 3 | **Verify/Release token 浪费** | 每次合规审查需遍历所有 change 文件 | 10 个 change × 5 类文档 × 各 200 行 = 频繁大量读取 + Agent 推理拼接 |
| 4 | **无权威来源** | "模块 A 的当前架构是什么？" | 架构散落在 3 个 change 中，哪个是"当前有效版本"无明确答案 |
| 5 | **Spec 演化不可追溯** | "登录功能的验收标准从 v1 到 v3 发生了什么变化？" | 只能逐版本对比 change 目录 |
| 6 | **新 change 缺少冲突检查基础** | 启动一个新 change 时，Agent 2 无法判断是否与已有需求冲突 | 跳过检查（无数据源），埋下隐患 |

### 1.3 同类问题的影响范围

所有 per-change 产出的文档均受影响：

| 文档 | 影响 | 严重程度 |
|:---|:---|:---|
| proposal.md → master PRD | 无法回答"产品有哪些功能" | 中 |
| specs/{capability}/spec.md | 无法回答"系统有哪些验收标准"，P0 场景清单不可得 | 高 |
| architecture.md | 无法回答"当前系统架构是什么"，两个 change 可能以不同结构描述同一模块 | **极高** |
| detailed-design.md | 数据模型/API 定义各自为政，可能定义了同一张表的不同字段 | **极高** |
| contract.md | 同一 API 的契约在多个 change 中版本不一致，无权威答案 | 高 |

### 1.4 目标

1. 新增 `openspec/master/` 目录，存放合并后的当前系统全貌文档
2. 定义**两个合并节点**（Proposal 确认后、Design L2 门禁通过后）和机械/语义两种合并策略
3. 将冲突检测从 Release 前移到合并节点，降低修复成本
4. 大幅降低 Verify/Release 阶段的 token 消耗
5. 不修改 Agent 分工、不改变六阶段主流程

---

## 2. 架构总览

### 2.1 目录结构变更

```
openspec/
├── master/                          # ← 新增：当前系统全貌（权威来源）
│   ├── prd.md                       #   产品需求文档（从各 change 的 proposal.md 合并）
│   ├── architecture.md              #   当前系统架构（从各 change 的 architecture.md 合并）
│   ├── detailed-design.md           #   当前详细设计（从各 change 的 detailed-design.md 合并）
│   ├── contract.md                  #   当前契约定义（从各 change 的 contract.md 合并）
│   └── specs/
│       └── {capability}/
│           └── spec.md             #   当前验收规格（从各 change 的同名 spec 合并）
│
├── changes/                         # 不变，每个 change 独立维护
│   └── {change-name}/
│       ├── mase-state.yaml
│       ├── proposal.md
│       ├── tech-feasibility.md
│       ├── architecture.md
│       ├── detailed-design.md
│       ├── contract.md
│       ├── tasks.md
│       └── specs/
│           └── {capability}/
│               └── spec.md
```

### 2.2 两种合并策略

由于文档性质不同，合并策略分为两类：

| 文档类型 | 合并策略 | 原因 |
|:---|:---|:---|
| **spec.md** | **机械合并** | 使用 ADDED/MODIFIED/REMOVED 标记，变更可程序化识别和应用 |
| **proposal.md / architecture.md / detailed-design.md / contract.md** | **语义合并**（Agent 辅助） | 叙述性文档，无标准化变更标记，需要语义理解和结构重建 |

### 2.3 合并节点与触发条件

```
六阶段流程                              合并操作
─────────────────────────────────────────────────────────
Proposal (Agent 2)
  │
  ├─ 原型走查 + Checklist 确认通过
  │        │
  │        ▼
  │   ┌─────────────────────────┐
  │   │  合并节点 #1             │  ← proposal.md → master/prd.md
  │   │  Agent 2 执行            │     (语义合并)
  │   └─────────────────────────┘
  │
Design L2 (Agent 3)
  │
  ├─ Agent 4 设计评审通过
  │        │
  │        ▼
  │   ┌─────────────────────────┐
  │   │  合并节点 #2             │  ← spec.md → master/specs/
  │   │  Agent 3 执行            │     (机械合并)
  │   │  + Agent 1 门禁检查      │  ← architecture.md → master/architecture.md
  │   │                         │  ← detailed-design.md → master/detailed-design.md
  │   │                         │  ← contract.md → master/contract.md
  │   └─────────────────────────┘  │     (语义合并)
  │                                │
Build (Agent 3)                     ← 不在此阶段合并。Build 是对 spec 的消费，
  │                                    微小的措辞调整在 change 内部管理
Verify (Agent 4)                  ← 直接读取 master/ 做全量合规审查
  │
Retro (Agent 4+1)
  │
Release (Agent 1)                 ← 对照 master/ 做最终全量检查
                                      (不需要再遍历 changes/)
```

### 2.4 为什么不在 Build 阶段合并

Build 阶段的 10 步微循环中可能对 spec 有小幅调整（如 Scenario 措辞修正、补充遗漏的 When 条件）。每次微调都触发合并会过于频繁，且处于"编码中"状态的 spec 不宜作为 master 的权威来源。

规则：**只有当 Design L2 门禁通过（设计评审已完成），design 阶段的产出才被视为"稳定"并合并到 master。** Build 阶段的修改留在 change 目录内部，不做 master 同步。

---

## 3. 机械合并：spec.md

### 3.1 变更标记约定

变更 spec 使用 Gherkin 语义 + 标准化标记头：

```gherkin
## ADDED Requirements — 本次新增
### Requirement: 用户可通过邮箱找回密码
  As a 已注册用户
  I want to 通过注册邮箱接收重置链接
  So that 忘记密码时能恢复访问

  Scenario: 发送密码重置邮件
    Given 用户在登录页点击"忘记密码"
    When 输入已注册的邮箱地址
    Then 系统发送密码重置邮件
    And 页面显示"重置链接已发送"提示

---

## MODIFIED Requirements — 本次修改
### Requirement: 用户登录（修改）
  As a 已注册用户
  I want to 使用邮箱+密码或手机号+验证码登录    ← 原为"邮箱+密码"
  So that 有多种登录方式可选

  Scenario: 手机验证码登录（新增）
    Given 用户已注册并绑定手机号
    When 选择"手机验证码登录"标签页
    And 输入手机号并点击"获取验证码"
    Then 收到 6 位验证码短信
    And 输入验证码后成功登录

---

## REMOVED Requirements — 本次删除
### Requirement: 第三方账号登录
  **移除理由**: 安全评审发现 OAuth 实现存在 CSRF 漏洞，且当前用户基数小、优先级低。
```

### 3.2 合并算法

```
输入：master/specs/{capability}/spec.md（当前） + change/specs/{capability}/spec.md（增量）
输出：更新后的 master/specs/{capability}/spec.md

伪代码：
merge_spec(master_spec, change_spec):
    ADDED_requirements = parse_section(change_spec, "## ADDED Requirements")
    MODIFIED_requirements = parse_section(change_spec, "## MODIFIED Requirements")
    REMOVED_requirements = parse_section(change_spec, "## REMOVED Requirements")

    result = master_spec

    for each req in ADDED_requirements:
        if req.title already exists in result:
            → CONFLICT（冲突：新增需求重复）
        else:
            result = append(result, req)

    for each req in MODIFIED_requirements:
        if req.title NOT exists in result:
            → CONFLICT（冲突：修改不存在的需求）
        else:
            result = replace(result, req.title, req)

    for each req in REMOVED_requirements:
        if req.title NOT exists in result:
            → WARNING（警告：删除不存在的需求，可能已被前序 change 移除）
            // 不阻断，只记录
        else:
            result = remove(result, req.title)

    return result
```

### 3.3 冲突处理

| 冲突类型 | 检测条件 | 处理方式 |
|:---|:---|:---|
| 新增重复 | ADDED 的需求名在 master 中已存在 | **阻断合并** → Agent 3 确认是真正的重复需求还是命名冲突；若真正重复，标记为已覆盖并从 ADDED 移除 |
| 修改不存在 | MODIFIED 的需求名在 master 中不存在 | **阻断合并** → 可能 master 中该需求已被前序 change 删除，Agent 3 确认是否需要恢复或变更语义 |
| 删除不存在 | REMOVED 的需求名在 master 中不存在 | **警告** → 不阻断，可能已被前序 change 移除，记录 warning log |

### 3.4 初始状态（首个 change）

当 `master/specs/{capability}/spec.md` 不存在时（首个 change），合并简化为直接拷贝 ADDED 部分：

```
merge_spec(null, change_spec):
    = parse_section(change_spec, "## ADDED Requirements")
    // MODIFIED/REMOVED 在首个 change 中不应存在，若有则报错
```

---

## 4. 语义合并：设计文档与 PRD

### 4.1 为什么不能用机械合并

architecture.md、detailed-design.md、contract.md、proposal.md 是叙述性文档，没有标准化的"增/删/改"标记格式。两个 change 可能以完全不同的文档结构描述同一个系统：

- Change #3 的 architecture.md 按"前端/后端/数据库"三层组织
- Change #7 的 architecture.md 按"用户模块/订单模块/支付模块"领域组织
- 两者可能描述了同一组件（如"用户认证"）但放在不同位置、用不同表述

### 4.2 合并流程

```
┌──────────────────────────────────────────────────┐
│  语义合并流程（Agent 3 执行）                       │
│                                                  │
│  输入:                                            │
│    - master/{doc}.md（当前 master）                │
│    - changes/{name}/{doc}.md（本次 change 产出）   │
│                                                  │
│  步骤:                                            │
│                                                  │
│  1. 差异识别                                      │
│     Agent 3 读取两份文档，识别本次 change 引入的    │
│     新增内容、修改内容、删除内容                     │
│                                                  │
│  2. 冲突检测                                      │
│     检查本次修改是否与 master 中已有内容冲突          │
│     - 结构冲突: 相同概念在不同位置有不同描述          │
│     - 语义冲突: 同一组件的数量/参数/状态不一致        │
│                                                  │
│  3. 合并执行                                      │
│     - 无冲突: 将变更应用到 master                   │
│     - 有冲突: 阻断合并, 输出冲突报告, 等待人工决策    │
│                                                  │
│  4. 结构重建                                      │
│     合并后重新整理文档结构（目录、章节编号、交叉引用）  │
│     保持 master 文档作为"单一权威来源"的可读性       │
│                                                  │
│  输出: 更新后的 master/{doc}.md                    │
│                                                  │
│  Token 消耗: ~1500-3000 行（两份文档 + 推理 + 输出） │
└──────────────────────────────────────────────────┘
```

### 4.3 各文档的语义合并要点

| 文档 | 合并要点 | 冲突高发区 |
|:---|:---|:---|
| **prd.md** | 提取 proposal 中的 Capabilities、Success Criteria、Out of Scope，按产品域组织 | 两个 change 定义了重叠的 Capability |
| **architecture.md** | 系统架构图组件更新 + 技术栈决策表追加 + 模块边界调整 | 同一组件的架构描述不一致 |
| **detailed-design.md** | 数据模型字段增删改 + API 定义更新 + 算法/策略变更 | 同一数据表的字段在多个 change 中独立定义 |
| **contract.md** | 新增 API 契约追加 + 已有 API 契约更新 + 废弃 API 标记 | 同一 API 的 require/ensure 不一致 |

### 4.4 Design L2 合并结构

Design L2 门禁通过后，四类文档合并为一次原子操作执行：

```
Agent 3:
  ┌─────────────────────────────┐
  │ 1. merge_spec (机械)         │  → master/specs/*/spec.md
  │ 2. merge_contract (语义)     │  → master/contract.md
  │ 3. merge_architecture (语义) │  → master/architecture.md
  │ 4. merge_detailed_design(语义)│ → master/detailed-design.md
  └─────────────────────────────┘

Agent 1 门禁:
  ☑ 四项合并均无阻断性冲突
  ☑ master/ 下所有文件语法有效（无残留的占位符/模板标记）
  ☑ spec.md 的 MODIFIED/REMOVED 引用全部在 master 中找到对应需求
```

---

## 5. Token 经济学证明

### 5.1 假设模型

- 项目共 10 个 change
- 每个 change 修改 2 个 capability 的 spec
- 每个 spec.md 约 200 行
- 每类设计文档约 300 行
- 合并后 master/specs/*/spec.md 随项目成长，平均 800 行
- 合并后 master 设计文档平均 600 行

### 5.2 方案对比

| 操作 | 不合并（当前） | 合并（本方案） |
|:---|:---|:---|
| **Proposal 确认后** | 无 | 语义合并 proposal → prd.md: ~800 行/次 × 10 次 = ~8000 行 |
| **Design L2 后** | 无 | 机械合并 spec: ~1100 行/次 × 10 次 = ~11000 行 |
| | | 语义合并 3 类设计文档: ~1800 行/次 × 10 次 = ~18000 行 |
| | | **合并总投入** ≈ **37000 行** |
| **Verify 阶段** | 遍历 10 个 change × 4 类文档 × 2 capability = 80 次文件读取 + 在脑内拼接 ≈ 16000 行 + 大量推理 token × N 次调试循环 | 读取 master/ 下 5 份文档 ≈ 2600 行 × N 次 |
| **Release 阶段** | 同上 + 全量 spec 合规 ≈ 16000 行 | 读取 master/ ≈ 2600 行 |
| **启动新 change** | 无冲突检查（无数据源） | 读取 master/prd.md + master/specs ≈ 1400 行 → 可做冲突检查 |

### 5.3 盈亏分析

- **一次性合并投入**：~37000 行
- **每次 Verify/Release 节省**：~13400 行
- **回本点**：合并投入 / 每次节省 ≈ 37000 / 13400 ≈ **3 次 Verify 循环后开始盈利**

更重要的是，**版本间全量遍历在"不合并"方案中每轮 Verify 都发生**，而合并只在每个 change 执行一次。项目 change 数越多，合并方案的 token ROI 越高。

### 5.4 边际收益

| 项目 change 数 | 合并总投入 | 每轮 Verify 节省 | 回本所需 Verify 轮次 |
|:---|:---|:---|:---|
| 5 | ~18500 行 | ~7000 行 | 3 轮 |
| 10 | ~37000 行 | ~13400 行 | 3 轮 |
| 20 | ~74000 行 | ~26800 行 | 3 轮 |
| 50 | ~185000 行 | ~67000 行 | 3 轮 |

回报线性增长，回本点稳定在 3 轮 Verify。

---

## 6. 对现有阶段的影响

### 6.1 Proposal 阶段

| 变更项 | 内容 |
|:---|:---|
| **新增动作** | Proposal 门禁通过后，Agent 2 执行 `proposal.md` → `master/prd.md` 语义合并 |
| **变更说明** | Agent 2 在 Proposal 阶段的职责从"产出 proposal.md"扩展为"产出 proposal.md + 合并到 master PRD" |
| **Agent 1 门禁** | 新增：master/prd.md 更新无冲突 |
| **token 影响** | 每次 Proposal 约 +800 行读取 + +400 行输出 |

### 6.2 Design L2 阶段

| 变更项 | 内容 |
|:---|:---|
| **新增动作** | Design L2 门禁通过后，Agent 3 执行四类文档的合并：spec（机械）+ contract/architecture/detailed-design（语义） |
| **变更说明** | Agent 3 产出物新增"合并完成确认"。合并是 Design L2 的最后一步，合并完成才标记 phase = build |
| **Agent 1 门禁** | 新增：master/ 下所有文件无冲突、无模板残留 |
| **token 影响** | 每次 Design L2 约 +2900 行（spec 1100 + 三类设计文档 1800） |

### 6.3 Verify 阶段

| 变更项 | 内容 |
|:---|:---|
| **变更动作** | E2E 回归 + 人工探索中的"对照 spec 检查"从遍历 changes/ 改为读取 master/ |
| **收益** | token 降低约 80%，且不再需要 Agent 在脑内拼接多个 spec 文件 |

### 6.4 Release 阶段

| 变更项 | 内容 |
|:---|:---|
| **变更动作** | "最终合规审查 — 对照全部 spec.md" 改为读取 `master/` 下的文件 |
| **变更动作** | "归档 OpenSpec Change" 之后新增 `master/` 的历史版本快照（git commit 同时保存 master/ 的状态） |
| **收益** | 合规审查 token 降低约 80%，且 master/ 状态与 git commit 绑定，支持"任意版本的 spec 全貌"回看 |

---

## 7. 边界情况与规则

### 7.1 首个 change（master/ 为空）

- 合并 = 直接拷贝 proposal/design 文档到 master/
- 跳过冲突检测（master 为空，无冲突）

### 7.2 Bug Fix Change（纯修复，不产生新功能）

- Bug Fix 通常不变更 spec 或设计文档
- 合并操作自动跳过（检测到 change 的 specs/ 和设计文档无实质变更）

### 7.3 紧急热修复

- 热修复可能跳过 Proposal，直接 Design + Build
- 规则：跳过 Proposal → 跳过合并节点 #1。Design L2 后如果发现对 master 有变更，走正常合并流程

### 7.4 Change 被废弃

- 如果 change 在中间阶段被废弃（如 Design L2 评审不通过、Agent 1 决策回退）
- `mase-state.yaml` 中标记 `phase: abandoned`
- 该 change 的合并不再执行。如果已合并到 master 的部分需要回滚，人工决策

### 7.5 多 change 并行

- 两个 change 同时开发（如 Change #7 和 #8 都进入 Design L2）
- 先完成 Design L2 的先合并。后完成的在合并时检测到冲突 → 阻断、输出冲突报告、人工决策
- 不引入锁机制（保持简单），冲突发生时 Agent 3 会同两方的变化内容再做一次语义对齐

---

## 8. 受影响文件清单

### 8.1 需新增

| 文件 | 说明 |
|:---|:---|
| 本设计文档 | `docs/superpowers/specs/2026-07-17-master-document-merge-design.md` |
| spec 合并规范 | `docs/superpowers/specs/2026-07-17-spec-merge-specification.md`（可选，定义 ADDED/MODIFIED/REMOVED 的格式规范） |

### 8.2 需修改

| 文件 | 变更内容 |
|:---|:---|
| `docs/MASE-framework.md` | 第 6.1 节目录结构新增 `master/`；第 3.1-3.2 阶段流程新增合并节点；第 3.4-3.6 Verify/Release 变更为读取 master/ |
| `docs/project-structure-spec.md` | 新增 `openspec/master/` 目录说明；master 文档只读规则 |
| `docs/glossary.md` | 新增术语：master PRD、master spec、语义合并、机械合并 |
| `docs/coding-standards.md` | 新增 spec 变更标记规范（ADDED/MODIFIED/REMOVED 格式） |
| `openspec/changes/_template/` | `specs/{capability}/spec.md` 模板中预置 ADDED/MODIFIED/REMOVED 标记头和注释 |
| 各 Agent SKILL.md | Agent 2 新增"合并到 master PRD"职责；Agent 3 新增"合并 spec 和设计文档"职责；Agent 1 新增合并门禁检查项 |
| `project-rules.md` | 不新增原则。此为流程优化，不属于原则级变更 |

### 8.3 不修改

- 四 Agent 分工、六阶段主流程顺序——不变
- Agent 的执行 Skills 方案——不变
- 测试目录结构 `tests/`——不变

---

## 9. 迁移方案（已有项目）

对于已启动但未完成的项目：

1. **已有完成的 change**：以最近一次 Release 的 git commit 为基准，将该 commit 中 changes/ 目录下的所有 spec 和设计文档反向生成 `openspec/master/`。
2. **正在进行的 change**：change 自己正常推进。完成 Design L2 后走正常合并流程，此时 master/ 已存在（由第 1 步生成），正常做差异合并。
3. **mase update**：CLI 命令需要支持对已有项目补建 `openspec/master/` 目录结构的迁移操作。

---

## 10. 自审清单

- [x] 合并节点设计不修改六阶段主流程顺序
- [x] Agent 职责变更最小化（Agent 2 + 合并 PRD，Agent 3 + 合并设计文档）
- [x] 冲突检测机制明确（阻断/警告两级 + 人工决策路径）
- [x] Token 模型有盈亏分析，回报量化
- [x] 边界情况覆盖（首个 change、Bug Fix、热修复、废弃 change、多 change 并行）
- [x] 迁移方案涉及已有项目
- [x] master/ 为只读，仅合并操作可写
- [x] 无 TBD/TODO 占位符
- [x] 文档间交叉引用一致（MASE-framework.md ↔ project-structure-spec.md ↔ glossary.md）
