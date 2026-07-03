# 麦哲思AI软件开发统一流程 — 使用手册

> 适用于通过 Agent 协作的增量式软件开发流程

## 快速开始

一句话：**说需求，Agent 1 自动调度其他 Agent 走完全流程。**

```
用户: "我要做一个XXX功能"
     ↓
Agent 1 (统管): 分发 → Agent 2 做需求澄清 → Agent 3 做技术预研+开发 → Agent 4 做质量把关
```

---

## 六个阶段（PDCA 闭环）

| 阶段 | PDCA | 谁干 | 产出什么 | 你看什么 |
|------|:---:|------|---------|---------|
| 1. 需求 | P | Agent 2 | proposal + 原型 + 测试用例 | 原型能不能走通 |
| 2. 设计 | P | Agent 3 + 4 | tech-feasibility + architecture + specs | POC 跑通？架构合理？ |
| 3. 构建 | D | Agent 3 + 4 | 可运行的代码 + 自动化测试 | 代码评审报告 |
| 4. 验证 | C | Agent 4 | 全部 BUG 关闭 | 端到端测试通过 |
| 5. 复盘 | A | Agent 4 + 1 | 复盘报告 + 改进措施 | 经验是否沉淀？流程是否改进？ |
| 6. 发布 | — | Agent 1 | commit + 手册 + 归档 | git log |

---

## 阶段 1：需求（Proposal）

**触发**：你说"我要做XXX功能"

**流程**：
1. Agent 2 通过 `brainstorming` 逐问题澄清需求
2. Agent 2 用 `frontend-skill` 生成可交互 HTML 原型
3. Agent 2 编写 proposal.md（含操作流程 + 系统测试用例）

**你确认**：
- [ ] 看 HTML 原型 → 操作流程是否通顺？
- [ ] 看 proposal.md → Success Criteria 是否覆盖了你的期望？
- [ ] 看测试用例表 → 是否所有关键路径都有用例？

**典型对话**：
```
你: 我想做一个书籍合并去重的工具
Agent 2: 输入是电子书文件对吧？支持什么格式？
你: EPUB/TXT/PDF
Agent 2: 我生成一个原型你看看 → [HTML 原型]
你: 这里加一个进度条
...
你: 没问题，进入设计阶段
```

---

## 阶段 2：设计（Design）

### Layer 1：技术可行性研究（Agent 3 执行）

**流程**：
1. 识别技术难点，联网搜索成熟方案 + 最新技术
2. 评估外部依赖，每个都写 POC 验证脚本跑通
3. 提取可复用构件清单

**产出**：`tech-feasibility.md`，含 3 张汇总表 + POC 验证记录

**你确认**：
- [ ] 所有 POC 脚本跑通了？
- [ ] 每个技术难点都有可行方案？
- [ ] 可复用构件清单列出来了？

### Layer 2：架构设计（Agent 3 执行）

**产出**：
- `architecture.md` — 架构图 + 技术栈 + 模块边界
- `detailed-design.md` — 数据模型 + API + 管道设计
- `specs/{capability}/spec.md` — Gherkin 验收规格
- `tasks.md` — 开发任务清单（`project-planning-expert` 编排）

### 设计评审（Agent 4 执行）

- `code-quality-controller`：架构合规 + 需求一致性 + 文档一致性
- `frontend-design`（如涉及 UI）：视觉/交互/响应式/a11y 审查

**典型对话**：
```
你: 进入设计阶段
Agent 3: 先做技术预研。BGE 嵌入模型选哪个版本？
你: bge-large-zh-v1.5
Agent 3: POC 验证脚本跑通了。向量库 Qdrant 本地 Docker 部署验证 OK。
...
Agent 3: architecture.md 写好了，你确认下
你: 模块边界可以，继续
Agent 3: detailed-design.md 完成，进入 specs 编写
Agent 4: 设计评审通过：架构合规 ✅，需求一致性 ✅，文档一致性 ✅
```

---

## 阶段 3：构建（Build）

**TDD 微循环**：每个 Capability 的每个 Scenario，按以下步骤：

```
① 复用检查 → 对照可复用构件清单
② 写测试 → pytest（TDD 内层循环）
③ 写实现代码
④ 跑测试
⑤ 功能测试 → webapp-testing
⑥ 代码评审 → code-review（含 spec 合规 + 代码规约）
⑦ 安全扫描 → TRAE-security-review
⑧ 通过 → git commit
```

**Agent 3 写代码，Agent 4 是旁路质量防线。**

**典型对话**：
```
Agent 1: book-parser capability 开始构建
Agent 3: Scenario 1 -- 写测试 → 写实现 → 测试通过 ✅
Agent 4: 代码评审：spec 合规 ✅，代码规约：变量命名建议 snake_case ⚠️
Agent 3: 已修改
Agent 4: 评审通过 ✅
Agent 3: Scenario 2 -- ...
Agent 1: book-parser 全部 Scenario 完成 → 提交
```

---

## 阶段 4：验证（Verify）

全部 Capability 构建完成后，你做端到端测试，发现问题 → Agent 4 修复。

**BUG 修复微循环**：
```
发现 BUG → bug-fixer 修复 → 回归验证 → 测试缺口复盘
    → 横向扫描同类 BUG → 经验教训记录 → BUG 关闭
```

**典型对话**：
```
你: 上传 EPUB 文件报 500 错误
Agent 4: bug-fixer 启动 → 路径 A：崩溃错误
Agent 4: 根因是章节解析时空章节导致 NoneType → 已修复
Agent 4: 回溯：自动化测试为什么没发现？
          → epubs/ 里没有空章节的测试用例
          → 已补充 test_empty_chapter.py
Agent 4: 横向扫描：PDF/TXT 解析器也有同样风险 → 已加固
Agent 4: 经验记录：空章节边界条件 ✓
你: 继续 → 无新 BUG → 验证通过
```

---

## 阶段 5：复盘（Retrospective — PDCA 闭环）

验证通过后，Agent 4 做系统性复盘：

**产出**：`docs/lessons/YYYY-MM-DD-{project}-retro.md`

**复盘内容**：
```
① 收集材料 — 本轮所有 lessons / cases / 代码评审记录
② 模式分析 — 高发 BUG 模式 / 测试盲区 / 设计缺陷 / 流程短板
③ 产出报告 — 含改进措施
④ 执行改进 — 更新 Skill 规则 / 模板 / 代码规约 / 门禁 Checklist
```

**典型对话**：
```
Agent 4: 本轮复盘：
         - BUG 共 5 个，其中 3 个是空值边界遗漏
         - 测试盲区：epub/txt/pdf 解析器缺少空输入测试 → 已补充
         - 建议：code-review 第 7 组增加空值检查规约
你: 同意，更新规约
Agent 4: code-review SKILL.md 已更新 ✓
Agent 1: 复盘报告已存档 → 进入发布
```

---

## 阶段 6：发布（Release）

Agent 1 自动执行：
1. 最终合规审查（对照 spec + design 全量检查）
2. 生成使用手册（就是这份文档）
3. git commit（Conventional Commit + 变更摘要）
4. 归档 OpenSpec Change

**你只需要说"发布"即可。**

---

## 四个 Agent 速查

| Agent | 角色 | 一句话职责 |
|-------|------|-----------|
| Agent 1 | 计划与统管 | 接收需求 → 分解任务 → 调度 ABC → 门禁 → 发布 |
| Agent 2 | 需求 | 问清楚你要什么 → 原型确认 → 生成验收标准 |
| Agent 3 | 开发 | 预研 + 架构 + 编码 → 做了还要做对 |
| Agent 4 | 质量 | 设计评审 + 代码评审 + 安全扫描 + BUG 修复，专门挑刺 |

---

## 命令速查

| 你说的话 | 触发动作 |
|---------|---------|
| "我要做 XXX 功能" | 启动阶段 1：需求 |
| "创建新项目" | 按模板初始化目录结构 + openspec |
| "进入设计阶段" | 启动阶段 2：设计 |
| "开始构建" | 启动阶段 3：TDD 构建 |
| "端到端测试" | 启动阶段 4：验证 |
| "复盘总结" | 启动阶段 5：复盘（PDCA-ACT） |
| "发布" | 启动阶段 6：发布归档 |
| "发现 BUG：XXX" | Agent 4 bug-fixer 介入 |

---
## 项目结构速查

| 目录 | 放什么 | 谁维护 |
|------|--------|--------|
| `src/{pkg}/{capability}/models/` | 数据模型 | Agent 3 |
| `src/{pkg}/{capability}/services/` | 业务逻辑 | Agent 3 |
| `src/{pkg}/{capability}/routes/` | API 路由 | Agent 3 |
| `src/{pkg}/{capability}/schemas/` | 请求/响应 Schema | Agent 3 |
| `src/{pkg}/shared/` | 跨 capability 共享代码 | Agent 3 |
| `tests/unit/{capability}/` | 单元测试（镜像 src/） | Agent 3 |
| `tests/integration/` | 集成测试 | Agent 3 |
| `tests/fixtures/` | 测试数据 | Agent 3 |
| `docs/user-guide.md` | 使用手册 | Agent 1 |
| `docs/lessons/` | 经验教训 | Agent 4 |
| `docs/cases/bugs/` | BUG 案例 | Agent 4 |
| `docs/cases/patterns/` | 可复用模式 | Agent 3 |
| `docs/cases/pitfalls/` | 踩坑记录 | 任何 Agent |
| `openspec/changes/{name}/` | 当前变更的规范文档 | Agent 2+3 |

详细规范见：[项目目录结构规范](file:///Users/dylanren/Documents/trae_projects/merge-books/docs/superpowers/specs/2026-07-03-project-structure-spec.md)

初始化一行命令：
```bash
# 复制模板 + 按 STRUCTURE.md 创建目录
cp -r openspec/changes/_template/* openspec/changes/{your-project}/
bash openspec/changes/_template/init.sh  # 自动建目录
```

---

## 常见问题

**Q: 可以跳过某个阶段吗？**
A: 不建议。每个阶段有门禁检查，跳过会导致后续阶段无法进入。

**Q: 多个 Capability 可以并行吗？**
A: 可以。Design Layer 2 产出后，不同 Capability 可并行进入 Build。

**Q: 能在 Build 中途加需求吗？**
A: 建议回到阶段 1，补充 proposal → 通过后追加到 tasks.md。

**Q: 怎么知道当前在哪个阶段？**
A: 看 `openspec/changes/{name}/.openspec.yaml` 的 `status` 字段。

---

## 相关文档

- [框架设计文档](file:///Users/dylanren/Documents/trae_projects/merge-books/docs/superpowers/specs/2026-07-03-unified-dev-framework-design.md)
- [项目目录模板](file:///Users/dylanren/Documents/trae_projects/merge-books/openspec/changes/_template/)
