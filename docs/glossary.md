# MASE 术语表

> **加载策略**: 按需加载。术语混淆时注入上下文。
> 本表定义 MASE 框架中的关键术语，避免概念混淆。

## 核心术语

| 术语 | 定义 | 容易混淆为 |
|------|------|-----------|
| 契约 (Contract) | DbC 风格前置条件/后置条件/不变式约束 | 接口协议、fixtures 格式约定 |
| TDD 外循环 | Spec → 测试 → 实现 → E2E 验证（行为驱动，非 DbC 契约） | 契约 (Contract) |
| fixtures 约定 | E2E 测试数据格式约定（Playwright test fixtures） | 契约 (Contract) |
| 接口协议同步 | 前后端 API 协议格式同步（OpenAPI/GraphQL schema） | 契约 (Contract) |

## 阶段术语

| 术语 | 定义 |
|------|------|
| Proposal | 需求澄清 + 原型确认阶段（Agent 2） |
| Design L1 | 技术预研 + POC 验证阶段（Agent 3） |
| Design L2 | 架构设计 + Spec + 契约推导阶段（Agent 3） |
| Build | TDD 微循环构建阶段（Agent 3 + Agent 4 旁路） |
| Verify | 端到端验证 + Bug 修复阶段（Agent 4） |
| Retro | 复盘分析 + 知识沉淀阶段（Agent 4 + Agent 1） |
| Release | 发布 + 合规审查阶段（Agent 1） |

## 门禁术语

| 术语 | 定义 |
|------|------|
| 门禁 (Gate) | 阶段间的质量检查点，不通过不推进 |
| DoD (Definition of Done) | 阶段完成的验收标准清单，统一定义在 Agent 1 |
| 硬阻断 | 不通过则禁止进入下一阶段（如 P0 E2E 失败） |
| 软提醒 | 不通过不阻断但需记录（如模块级契约缺口） |

## 文档术语

| 文件 | 定义 |
|------|------|
| `mase-state.yaml` | 项目状态机配置（phase/project_type/capabilities） |
| `.mase.yaml` | 项目根目录 MASE 标识文件 |
| `proposal.md` | 需求提案（含 E2E 验收场景） |
| `contract.md` | 三层契约定义（API/模块/函数级） |
| `spec.md` | Gherkin 行为规格 |
| `tech-feasibility.md` | 技术可行性报告（含可复用构件清单） |

## Agent 术语

| 术语 | 定义 |
|------|------|
| Agent 1 | 计划与统管 — 调度 + 门禁 + Release |
| Agent 2 | 需求 — brainstorming + 原型 + proposal |
| Agent 3 | 开发 — Design L1/L2 + TDD Build |
| Agent 4 | 质量 — 评审 + 扫描 + E2E + Bug修复 + 复盘 |
