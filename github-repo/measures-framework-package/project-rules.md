# MASE 工程规则 — AI 可读版本

> 本文件为 MASE 框架九大工程原则的机器可读格式，供 AI IDE 自动加载。
> 人类可读版本见 README.md。

## 规则定义

### R01: 需求澄清确认
- **定位**: Proposal 阶段
- **规则**: 原型确认后才进入开发，不确认不设计
- **门禁**: proposal.md + HTML 原型 + 系统测试用例三件套齐全

### R02: 设计预研，消除风险
- **定位**: Design L1 阶段
- **规则**: 技术预研 + POC 验证，所有外部依赖必须跑通验证脚本
- **产出**: tech-feasibility.md（三张汇总表 + 可复用构件清单）

### R03: 契约式约束
- **定位**: Design L2 → Build 阶段
- **规则**: 从 Spec (Gherkin) 推导 DbC 契约（前置条件/后置条件/不变式）
  - **API 级**: 硬性必做 — 接口输入输出的形状约束 + 行为语义约束
  - **模块级**: 强推荐 — 核心业务规则的不变量（有业务规则时必做）
  - **函数级**: 可选 — 高风险函数的参数/返回值边界（或 bug-fixer 补写）
- **产出**: contract.md
- **消费**: TDD 翻译契约到测试（RED 步骤）；代码保留运行时断言 (require/ensure/invariant_check)
- **运行时断言级别**:
  - Development: strict（断言失败 → 500）
  - CI/E2E: strict
  - Production: relaxed（只告警不中断）

### R04: TDD 驱动
- **定位**: Build 阶段
- **规则**: 每个功能必须有自动化测试，先写测试再写代码
- **微循环（10 步）**:
  1. 复用检查
  2. 契约翻译 → 测试（contract.md → TDD RED）
  3. 写行为测试（Spec → TDD RED）
  4. 写实现代码（含运行时断言 require/ensure）
  5. 跑测试（单元 + 集成 + 契约测试）
  6. E2E 测试（has_ui: true 时）
  7. 功能测试（webapp-testing）
  8. 代码评审（code-review: spec 合规 + 契约合规 + 代码规约）
  9. 安全扫描（security-review）
  10. 通过 → git commit

### R05: 验证与确认检查
- **定位**: Verify 阶段
- **规则**: E2E 自动化回归（门禁）+ 人工探索性测试 + 合规审查
- **E2E 门禁**（has_ui: true 时）:
  - P0 场景 E2E 覆盖率 100%（硬阻断）
  - 失败 → bug-fixer 微循环 → 重跑
  - 连续 3 次失败 → 升级 Agent 1 决策
- **契约门禁**:
  - API 级契约测试 100% 通过（硬阻断）
  - 模块级契约测试通过或记录缺口
- **E2E 豁免条件**（需 Agent 1 批准）:
  - 纯样式调整（不改 DOM 结构）
  - 紧急热修复（事后补 E2E）
  - 实验性原型（proposal 标注 prototype: true）

### R06: 根因分析
- **定位**: Verify 阶段（bug-fixer）
- **规则**: 任何 BUG 修复必须先找到根本原因，不碰运气

### R07: 系统化解决
- **定位**: Verify 阶段（bug-fixer）
- **规则**: 杜绝临时补丁，只做系统性根治方案。修一个 BUG 防一类 BUG。

### R08: 固定节奏提交
- **定位**: Build 阶段
- **规则**: 每 20 次对话执行一次 Git 提交（Conventional Commit 格式）

### R09: 及时备份
- **定位**: 全局
- **规则**: 删除或回退代码前必须做备份

## 项目类型声明

项目必须在 `.openspec.yaml` 中声明类型：

```yaml
project_type:
  has_ui: true | false
  ui_platform: web | electron | mobile | null
```

- has_ui: true → 适用 E2E 门禁（R05）
- has_ui: false → 豁免 E2E 门禁

## E2E 验收场景优先级

- **P0**: 核心业务流程 — 必须 100% E2E 覆盖
- **P1**: 重要辅助功能 — 应当覆盖
- **P2**: 边缘场景 — 可人工探索

## 元素定位规范

E2E 测试中元素定位优先级（降级策略）：

1. `getByRole` — 语义化角色，最稳定
2. `getByLabel` — 表单标签关联
3. `getByPlaceholder` — 输入框占位符
4. `getByText` — 可见文本
5. `getByTestId` — 最后备选（仅当以上均不适用）

> 详见: skills/webapp-testing/playwright-standards.md

## 文件命名规范

```
openspec/changes/{change-id}/
├── proposal.md          # 需求提案 + E2E 验收场景
├── architecture.md      # 架构设计 + E2E 测试策略
├── contract.md          # 三层契约定义
├── specs/
│   └── {capability}/
│       └── spec.md      # Gherkin 行为规格
├── tasks.md             # 任务分解
├── cases/
│   └── bugs/
│       └── {date}-{bug-id}.md  # BUG 记录（含 found_by 字段）
└── lessons/
    └── {date}-retro.md  # 复盘报告（含 E2E 指标 + 契约分析）
```

## 术语表

| 术语 | 定义 | 勿与 |
|------|------|------|
| 契约 | DbC 风格前置/后置/不变式约束 | 接口协议、fixtures 格式约定 |
| TDD 外循环 | Spec → 测试 → 实现 → E2E（非 DbC 契约） | 契约 |
| fixtures 约定 | E2E 测试数据格式约定 | 契约 |
| 接口协议同步 | 前后端 API 协议格式同步 | 契约 |
