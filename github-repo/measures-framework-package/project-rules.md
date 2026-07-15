# MASE 工程规则

> AI IDE 常驻加载。详细规范见按需文档。

## R01: 需求澄清确认
- **定位**: Proposal
- **规则**: 原型确认后才进入开发，不确认不设计

## R02: 设计预研，消除风险
- **定位**: Design L1
- **规则**: 技术预研 + POC 验证，所有外部依赖必须跑通验证脚本
- **产出**: tech-feasibility.md

## R03: 契约式约束
- **定位**: Design L2 → Build
- **规则**: Spec（Gherkin）→ 三层 DbC 契约
  - **API 级**: 硬性必做（输入输出形状 + 行为语义）
  - **模块级**: 强推荐（核心业务规则不变量）
  - **函数级**: 可选（高风险函数边界 / bug-fixer 补写）
- **产出**: contract.md
- **消费**: TDD 翻译契约到测试 → 代码保留运行时断言 (require/ensure)
- **运行时级别**: Dev/CI: strict → Production: relaxed（详见 [编码规范](docs/coding-standards.md#4-错误处理)）

## R04: TDD 驱动
- **定位**: Build
- **规则**: 先写测试再写代码，E2E 同步编写
- **微循环**: 复用检查 → 契约翻译测试 → 行为测试 → 实现 → 单测+集成+契约 → E2E → 功能测试 → 代码评审 → 安全扫描 → git commit
- > 完整 10 步定义: [Agent 3 SKILL.md](agents/agent-3-development/SKILL.md#build-tdd-微循环10-步)

## R05: 验证与确认检查
- **定位**: Verify
- **规则**: E2E 自动化回归 + 契约测试 + 合规审查
- **硬阻断**: P0 E2E 100% + API 契约测试 100%
- **豁免**: 需 Agent 1 批准（详见 [Agent 1 DoD](agents/agent-1-orchestrator/SKILL.md)）

## R06: 根因分析
- **定位**: Verify（bug-fixer）
- **规则**: 任何 BUG 修复必须先找到根本原因

## R07: 系统化解决
- **定位**: Verify（bug-fixer）
- **规则**: 杜绝临时补丁，修一个 BUG 防一类 BUG

## R08: 固定节奏提交
- **定位**: Build
- **规则**: 每 20 次对话或每 Capability 完成时 git commit（Conventional Commit）

## R09: 及时备份
- **定位**: 全局
- **规则**: 删除或回退代码前必须做备份

---

## 项目类型

`openspec/changes/{name}/mase-state.yaml` 声明 `project_type.has_ui` → 决定是否适用 E2E 门禁（R05）。

---

## 规范文档索引

> 以下按需加载，不常驻内存。

| 规范 | 文档 | 场景 |
|------|------|------|
| 编码规范 | [coding-standards.md](docs/coding-standards.md) | 编码时 |
| 设计原则 | [design-principles.md](docs/design-principles.md) | 设计/评审时 |
| 项目结构 | [project-structure-spec.md](docs/project-structure-spec.md) | 初始化时 |
| 术语表 | [glossary.md](docs/glossary.md) | 术语混淆时 |
| E2E 定位规范 | [webapp-testing](skills/webapp-testing/SKILL.md) | E2E 编写时 |
