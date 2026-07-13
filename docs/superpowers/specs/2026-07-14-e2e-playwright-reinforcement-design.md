# MASE 框架 E2E Playwright 强化设计

> 创建日期：2026-07-14
> 状态：Draft
> 作者：Brainstorming Session

## 1. 背景与目标

### 1.1 当前痛点

MASE 框架的 Verify 阶段当前依赖"人工端到端测试 → 发现 BUG → bug-fixer 微循环"的流程。这种方式存在以下问题：

- **效率低**：每次代码变更后需人工点击所有页面验证功能未退化，耗时长
- **易遗漏**：人工回归测试覆盖不全，边缘场景容易漏测
- **不可重复**：无自动化回归基准，每次回归都是一次性劳动
- **幸福度低**：重复性手工测试消耗开发者精力，降低工作满意度

### 1.2 目标

1. **E2E 自动化回归**：将有 UI 项目的核心业务流程自动化验证，减少手工回归投入
2. **全链路追溯**：从 Proposal 阶段定义验收场景，到 Build 阶段实现 E2E 测试，到 Verify 阶段执行门禁
3. **BUG 拦截率提升**：E2E 自动化拦截 ≥80% 的 Verify 阶段 BUG
4. **开发效率与幸福度**：全量 E2E 回归 ≤10 分钟，比人工回归快 3-6 倍

### 1.3 非目标

- 不替代单元测试（TDD 内循环不变）
- 不追求 100% 场景覆盖，首期聚焦 P0 核心场景 100% 覆盖
- 不修改四 Agent 分工和六阶段名称/顺序
- 不修改 OpenSpec 的 capability spec 结构

### 1.4 决策记录

| 决策项 | 选择 | 理由 |
|:---|:---|:---|
| 约束级别 | 混合级（原则级描述 + 门禁级执行） | 既有原则高度又有执行力度 |
| 适用范围 | 有 UI 的项目（Web/桌面/移动） | Playwright 支持 Web + Electron + Mobile |
| E2E 产生时机 | Proposal 预定义 + Build 实现 + Verify 执行 | 全链路追溯，符合 MASE 理念 |
| Skill 落点 | 升级 webapp-testing skill | 避免 skill 膨胀，职责内聚 |
| 成功标准 | E2E 覆盖率门禁 + BUG 拦截率 | 可量化、可自动化采集 |

## 2. 架构总览与原则修改

### 2.1 E2E 在 MASE 架构中的定位

E2E 自动化测试是 MASE **Verify 阶段的核心门禁**，也是 **TDD 外循环**的执行手段。本次强化将 Verify 阶段从"人工端到端测试"升级为"自动化 E2E 测试 + 人工探索性测试"双轨制：

```
当前：  人工 E2E 测试 → 发现 BUG → bug-fixer 微循环
强化后：自动化 E2E 回归（门禁）→ 人工探索性测试 → bug-fixer 微循环
         ↑                                    ↑
         Playwright 全量回归             人工只做创造性探索
```

### 2.2 八大工程原则修改

修改**第 4 条**，从笼统的"端到端验证"升级为明确的 E2E 自动化要求：

| 原文 | 修改后 |
|---|---|
| 4. 验证与确认检查（端到端验证 + 合规审查） | 4. 验证与确认检查（E2E 自动化回归 + 人工探索性测试 + 合规审查） |

在原则下方增加 E2E 专项说明：

> **E2E 自动化测试要求**：凡有用户界面（Web/桌面/移动）的项目，在 Proposal 阶段定义 E2E 验收场景，Build 阶段同步编写 E2E 测试实现，Verify 阶段执行全量 E2E 回归作为门禁。核心场景 E2E 覆盖率 100% 方可通过 Verify。

### 2.3 不修改的部分

- 第 1-3、5-8 条原则不动
- 四 Agent 分工不动（Agent 2/3/4 的角色不变，只是产出物增加 E2E 相关内容）
- 六阶段名称和顺序不动（Proposal → Design → Build → Verify → Retro → Release）
- OpenSpec 规范层不动（不新增 capability 类型）

## 3. 六阶段流程调整

### 3.1 Proposal 阶段（Agent 2）— E2E 验收场景预定义

**新增产出物**：`e2e-scenarios.md`（嵌入 OpenSpec proposal 中）

Agent 2 在需求澄清阶段，除了定义系统测试用例外，同步定义 E2E 验收场景。每个场景包含：

```markdown
## E2E 验收场景

### 场景 1: <场景名称>
- 用户故事: 作为<角色>，我希望<操作>，以便<价值>
- 前置条件: <条件>
- 操作步骤:
  1. <步骤>
  2. <步骤>
- 预期结果: <可验证的断言>
- 优先级: P0（核心）/ P1（重要）/ P2（次要）
```

**场景优先级判定规则**：
- P0 场景 = 核心业务流程，**必须** 100% E2E 覆盖
- P1 场景 = 重要辅助功能，应当覆盖
- P2 场景 = 边缘场景，可人工探索

**UI 项目判定**：Agent 2 在 Proposal 阶段的 `.openspec.yaml` 中标注项目类型（`has_ui: true/false`）。有 UI 才需定义 E2E 场景。

### 3.2 Design 阶段（Agent 3）— E2E 测试策略

**architecture.md 新增章节**：`## E2E 测试策略`

内容包含：
- Page Object Model 结构设计（哪些页面、哪些组件）
- fixtures 数据准备方案（测试数据库隔离策略）
- 元素定位策略（遵循 playwright-standards.md）
- 测试环境配置（baseURL、webServer 启动方式）

### 3.3 Build 阶段（Agent 3）— E2E 测试同步编写

**TDD 外循环**：Agent 3 在实现功能后，同步编写对应的 E2E 测试。这是对现有 TDD skill（单元测试内循环）的补充。

```
TDD 内循环（现有）：  RED(单元测试) → GREEN(实现) → REFACTOR
TDD 外循环（新增）：  功能实现 → E2E 测试编写 → E2E 测试通过
```

**产出物**：
- `e2e/tests/*.spec.js` — E2E 测试用例
- `e2e/fixtures/seed.py` — 测试数据生成
- `e2e/helpers/pages.js` — Page Object 封装

**门禁**：Capability 的所有 P0 场景 E2E 测试通过，方可进入 Verify 阶段。

### 3.4 Verify 阶段（Agent 4）— E2E 全量回归门禁

**修改后流程**：

```
1. 执行全量 E2E 回归（Playwright）
   ├── P0 场景全部通过 → 继续
   └── P0 场景有失败 → bug-fixer 微循环（修复后重跑）
        └── 门禁：P0 场景 100% 通过

2. 人工探索性测试（仅创造性探索，不重复 E2E 已覆盖的）
   ├── 发现 BUG → bug-fixer 微循环
   └── 横向扫描同类 BUG

3. 测试缺口复盘
   └── E2E 未拦截的 BUG → 补充 E2E 用例

4. 门禁：全部 BUG 关闭 + P0 E2E 100% 通过
```

**新增产出物**：E2E 测试报告（含通过率、执行时间、失败用例 trace 路径）

### 3.5 Retro 阶段（Agent 4）— E2E 指标分析

复盘报告新增 `## E2E 测试指标` 章节，详见第 6 节。

### 3.6 不变的阶段

- **Release 阶段**：不调整，E2E 测试在 Verify 已完成
- **OpenSpec 的 proposal/specs/tasks 结构**：不新增文件类型，E2E 场景嵌入 proposal.md，E2E 策略嵌入 architecture.md

## 4. webapp-testing Skill 升级

### 4.1 升级定位

从"调试工具"升级为"调试 + E2E 测试"双重职责：

| 维度 | 当前 | 升级后 |
|---|---|---|
| 定位 | Toolkit for testing local web apps | Toolkit for E2E testing & debugging of web apps |
| 能力 | 浏览器操作 + 截图 + DOM 检查 | + E2E 测试编写规范 + 全量回归执行 + 报告生成 |
| 触发时机 | 开发者按需调试 | Build 阶段编写 E2E + Verify 阶段执行回归 + 按需调试 |

### 4.2 SKILL.md 新增章节

保留现有调试内容不动，新增三个章节：

**新增章节 1：`## E2E Test Authoring`**

内容：
- 元素定位规范（直接引用 playwright-standards.md，不重复）
- Page Object Model 编写规范（每页一个 class，测试用例不裸写选择器）
- fixtures 数据准备规范（seed.py 生成 fixtures.json，测试只读）
- 场景优先级标注（P0/P1/P2 对应 test.describe 中的 tag）

**新增章节 2：`## E2E Regression Execution`**

内容：
- 全量回归命令：`npx playwright test`
- 按优先级执行：`npx playwright test --grep @P0`
- 报告查看：`npx playwright show-report`
- trace 回放：`npx playwright show-trace <trace-path>`
- 失败排查流程：截图 + DOM + trace 三件套

**新增章节 3：`## MASE Integration`**

内容：
- Build 阶段：每实现一个 P0 场景功能，同步编写对应 E2E 测试
- Verify 阶段：执行 `--grep @P0` 必须 100% 通过
- Retro 阶段：从 report 中提取覆盖率、执行时间指标

### 4.3 现有内容调整

**Decision Tree 调整**：在现有决策树前增加一个入口判断：

```
User task → MASE 阶段?
    ├─ Build（写 E2E 测试）→ 读 E2E Test Authoring 章节
    ├─ Verify（执行回归）→ 读 E2E Regression Execution 章节
    └─ 调试（原有场景）→ 进入现有 Decision Tree
```

**Best Practices 补充**：在现有最佳实践后增加 E2E 专属条目：
- E2E 测试不修改 fixtures 数据（只读操作）
- 禁止 `sleep()`，用 `waitForResponse` 等待 API
- 每个 spec 文件 `beforeAll` 重新跑 `seed.py`
- `trace: 'on-first-retry'` 必须开启

### 4.4 不变的部分

- 现有的 `with_server.py` helper 脚本不动
- 现有的 Reconnaissance-Then-Action 模式不动
- 现有的 Common Pitfall 不动
- Reference Files 不动

## 5. 门禁规则与豁免机制

### 5.1 UI 项目判定标准

Agent 2 在 Proposal 阶段的 `.openspec.yaml` 中声明项目类型：

```yaml
# .openspec.yaml
project_type:
  has_ui: true          # Web/桌面/移动 UI
  ui_platform: web      # web | electron | mobile | null
```

**判定规则**：
- `has_ui: true` → 适用 E2E 门禁
- `has_ui: false` → 豁免 E2E 门禁（CLI、API、库等项目）
- 未声明 → Agent 1 在 Proposal 审核时要求 Agent 2 补充声明

### 5.2 Verify 阶段 E2E 门禁判定

```
Verify 阶段开始
    │
    ▼
项目 has_ui?
├── No → 跳过 E2E 门禁，进入人工探索性测试
│
└── Yes → 执行 E2E 全量回归（--grep @P0）
    │
    ▼
    P0 场景全部通过?
    ├── Yes → 门禁通过，进入人工探索性测试
    │
    └── No → bug-fixer 微循环
        │
        ▼
        修复后重跑 P0 E2E
        ├── 通过 → 门禁通过
        └── 同一 P0 场景连续 3 次修复后仍失败 → 升级到 Agent 1 决策
            （回退 Build 阶段 或 降级 P0→P1 需用户确认）
```

### 5.3 门禁失败处置

| 情况 | 处置 |
|---|---|
| E2E 测试不存在（Build 阶段未写） | **硬阻断**：回退 Build 阶段，要求 Agent 3 补写 |
| P0 场景 E2E 失败 | bug-fixer 微循环修复，重跑 |
| 同一 P0 场景连续 3 次修复仍失败 | 升级 Agent 1：评估是设计缺陷（回退 Design）还是需求变更（回退 Proposal） |
| E2E 执行超时（>10 分钟） | 不阻断，但 Retro 阶段标记"性能待优化" |

### 5.4 豁免机制

**可豁免 E2E 的特殊情况**（需 Agent 1 批准并记录）：

| 场景 | 豁免条件 | 替代措施 |
|---|---|---|
| 纯样式调整（CSS/颜色/间距） | 不改 DOM 结构 | 人工视觉验证 + 截图对比 |
| 紧急热修复 | 线上故障，Agent 1 判定需立即发布 | 事后补 E2E（Retro 阶段跟踪） |
| 实验性原型 | Proposal 标注 `prototype: true` | 不进正式 Release |

**不可豁免的情况**：
- 涉及用户交互流程变更（登录、表单提交、导航等）
- 涉及 API 契约变更
- 涉及数据持久化逻辑

### 5.5 门禁 Checklist

写入 Verify 阶段门禁 checklist（Agent 4 执行）：

```markdown
## Verify 门禁 Checklist

### E2E 门禁（has_ui: true 时必填）
- [ ] P0 场景 E2E 测试存在且 100% 通过
- [ ] E2E 测试报告已生成（含通过率、执行时间）
- [ ] 失败用例已修复或豁免（附理由）

### 通用门禁
- [ ] 全部 BUG 关闭
- [ ] 代码评审通过
- [ ] 安全扫描无高危项
```

## 6. 成功指标与度量机制

### 6.1 E2E 覆盖率门禁

**定义**：P0 场景 E2E 覆盖数 / P0 场景总数

**度量方式**：
- 分子：`e2e/tests/` 中标记 `@P0` 且通过的测试数
- 分母：`proposal.md` 中 `e2e-scenarios.md` 定义的 P0 场景数

**自动化采集**：Playwright 报告 + proposal 场景清单对比

```bash
# 执行 P0 场景并输出 JSON 报告
npx playwright test --grep @P0 --reporter=json > e2e-report.json
```

Agent 4 从 `e2e-report.json` 提取通过数，与 proposal 中的 P0 场景数比对，计算覆盖率。

**门禁阈值**：P0 覆盖率 = 100%（硬门禁）

### 6.2 BUG 拦截率

**定义**：E2E 拦截的 BUG 数 / Verify 阶段总 BUG 数

**度量方式**：
- 分子：Verify 阶段由 E2E 测试发现的 BUG 数（BUG 记录中标注 `found_by: e2e`）
- 分母：Verify 阶段发现的总 BUG 数（E2E + 人工探索 + 代码评审 + 安全扫描）

**采集方式**：BUG 记录模板新增字段

```markdown
<!-- docs/cases/bugs/_TEMPLATE.md 新增字段 -->
found_by: e2e | exploratory | code-review | security-scan
```

**目标阈值**：≥ 80%（软目标，Retro 阶段分析，不阻断 Release）

**未达标处置**：Retro 阶段需产出根因分析：
- 是 E2E 场景定义缺失（Proposal 阶段问题）→ 补充场景定义流程
- 是 E2E 测试实现缺失（Build 阶段问题）→ 补充测试实现
- 是 E2E 无法覆盖的场景（如视觉问题）→ 标记为人工探索专属

### 6.3 辅助指标（Retro 阶段记录，不作门禁）

| 指标 | 度量方式 | 目标 |
|---|---|---|
| 回归执行时间 | `e2e-report.json` 中的 duration | ≤ 10 分钟 |
| 人工回归节约 | 估算人工回归时间 - E2E 执行时间 | 正值 |
| E2E 维护成本 | 本轮新增/修改 E2E 测试代码行数 | 持续观察 |

### 6.4 指标存储

指标写入复盘报告 `docs/lessons/YYYY-MM-DD-{project}-retro.md`：

```markdown
## E2E 测试指标

| 指标 | 本轮值 | 目标 | 达标 |
|---|---|---|---|
| P0 覆盖率 | 100% | 100% | ✅ |
| BUG 拦截率 | 85% | ≥80% | ✅ |
| 回归执行时间 | 6.5 分钟 | ≤10 分钟 | ✅ |
| 人工回归节约 | ~40 分钟 | 正值 | ✅ |
```

### 6.5 指标趋势追踪

跨轮次趋势写入 `project_memory.md`，供 Agent 1 在 Proposal 阶段评估历史 E2E 健康度：

```
## E2E 健康趋势
- 2026-07 轮次: P0 覆盖 100%, 拦截率 85%, 执行 6.5min
- 2026-08 轮次: P0 覆盖 100%, 拦截率 72% (↓), 执行 8min
  → 拦截率下降，Retro 标记需补充 E2E 场景
```

## 7. 受影响文件清单

### 7.1 需修改的框架文件（github-repo）

| 文件 | 修改内容 | 改动量 |
|---|---|---|
| `github-repo/README.md` | 八大原则第 4 条修改 + E2E 专项说明 | 小 |
| `github-repo/docs/superpowers/specs/2026-07-03-unified-dev-framework-design.md` | Verify 阶段流程修改（3.4 节）+ Build 阶段补充 E2E（3.3 节）+ Retro 指标（3.5 节） | 中 |
| `github-repo/measures-framework-package/skills/webapp-testing/SKILL.md` | 新增 3 个章节 + 决策树调整 | 中 |
| `github-repo/measures-framework-package/templates/proposal.md` | 新增 E2E 验收场景章节 + has_ui 声明 | 小 |
| `github-repo/measures-framework-package/templates/.openspec.yaml` | 新增 project_type 字段 | 小 |
| `github-repo/measures-framework-package/templates/architecture.md` | 新增 E2E 测试策略章节 | 小 |
| `github-repo/measures-framework-package/templates/docs/cases/bugs/_TEMPLATE.md` | 新增 found_by 字段 | 小 |
| `github-repo/measures-framework-package/templates/docs/lessons/_RETRO_TEMPLATE.md` | 新增 E2E 测试指标章节 | 小 |

### 7.2 需新增的文件

| 文件 | 内容 | 位置 |
|---|---|---|
| `2026-07-14-e2e-playwright-reinforcement-design.md` | 本设计文档 | `docs/superpowers/specs/` |
| `playwright-standards.md` | 迁移现有规范到框架包 | `measures-framework-package/skills/webapp-testing/`（作为 skill 的参考文件） |

### 7.3 不修改的文件

- 四 Agent 分工定义不变
- 六阶段名称和顺序不变
- `test-driven-development/SKILL.md` 不动（E2E 是外循环，独立于 TDD 内循环）
- OpenSpec 的 capability spec 结构不变
- 现有 `with_server.py` 等 helper 脚本不动

### 7.4 改动影响评估

- **框架核心**：8 个文件修改 + 2 个文件新增，改动集中在模板和文档，不涉及代码逻辑
- **向后兼容**：现有项目无 `has_ui` 声明时，Agent 1 在 Proposal 审核时要求补充，不会阻断现有流程
- **风险**：模板修改影响新建项目，已有项目需手动适配（不强制）
