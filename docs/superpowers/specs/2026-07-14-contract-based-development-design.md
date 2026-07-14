# MASE 框架契约式开发（DbC）强化设计

> 创建日期：2026-07-14
> 状态：Draft
> 作者：Brainstorming Session

## 1. 背景与目标

### 1.1 当前痛点

MASE 框架目前缺少"契约"层作为独立防线，存在以下问题：

1. **框架 Spec 缺失契约概念**：`unified-dev-framework-design.md` 完全没有提及契约，只有 TDD + E2E 两道防线
2. **已有高质量文档未对齐**：`ai-spec-contract-tdd.html` 详细阐述了 Spec → 契约 → TDD 的四阶段模型，但与 MASE 的六阶段模型互不引用，形成了"各自为政"的局面
3. **"契约"术语多义混乱**：同一词汇在培训幻灯片（"外层契约"= TDD 外循环）、Playwright（"fixtures.json 契约"= 数据约定）、bug-fixer（"修契约"= 数据流约定）等不同语境下指代完全不同的概念，造成混淆

### 1.2 目标

1. **将契约式开发（Design by Contract）正式纳入 MASE 框架**，作为第三道质量防线
2. **统一"契约"术语**：在 MASE 中，"契约"只指 DbC 风格的三类断言（前置条件 / 后置条件 / 不变式）
3. **建立三元关系**：Spec 管"做什么" → Contract 管"正确性边界" → TDD 管"行为正确" + E2E 管"用户视角正确"
4. **强调 Spec 的基础位置**：spec 是设计的核心，契约是对 spec 的降维补充——从 Gherkin 场景推导约束，而非替代 spec

### 1.3 非目标

- 不替代 TDD（契约与 TDD 互补而非替代）
- 不覆盖类型系统范畴（类型检查由语言编译器和类型注解完成）
- 不要求所有项目都做全部三层（API 级必做，模块级推荐，函数级可选）

### 1.4 决策记录

| 决策项 | 选择 | 理由 |
|:---|:---|:---|
| 契约定义 | DbC 风格：前置/后置/不变式 | 经典方法论，与已有 ai-spec-contract-tdd.html 一致 |
| 契约粒度 | 三层混合（API 必做 + 模块推荐 + 函数可选） | 分层防御，不过度设计 |
| 插入位置 | Design L2 末尾，Gherkin spec 之后 | 契约推导是设计活动，不放编码阶段 |
| 产出物 | 独立 `contract.md`（与 spec.md 平级） | 单一职责，可独立评审和版本化 |
| 检查方式 | 双重检查：TDD 翻译到测试 + 代码运行时断言 | 测试验证契约正确性，断言防止回归 |
| Spec 与契约关系 | Spec 是核心和基础；Contract 是 Spec 的补充和约束层 | spec 定义了行为，contract 约束了边界 |

## 2. 架构总览

### 2.1 三元关系模型

```
                      ┌─────────────────────────┐
                      │     Spec（行为规格）        │
                      │ Gherkin: Given/When/Then  │
                      │    管"要做什么"             │
                      └───────────┬───────────────┘
                                  │ 输入（Gherkin → 契约）           E2E（用户视角验证）
                                  ▼                               ┌──────────────────┐
                      ┌─────────────────────────┐                  │ Playwright 全量  │
                      │   Contract（约束规格）    │ ← 本次新增       │   E2E 回归        │
                      │  前置/后置/不变式          │                 │  管"用户视角正确" │
                      │  管"正确性的边界"         │                 └──────────────────┘
                      └───────────┬───────────────┘                       ↑
                                  │ 驱动                                   │
                      ┌───────────┴───────────────┐                        │
                      ▼                           ▼                        │
          ┌──────────────────┐       ┌──────────────────┐                  │
          │   TDD（行为正确）  │       │ 运行时断言（守护）  │                  │
          │  单元+集成测试    │       │ require/ensure/   │                  │
          │  管"开发的节奏"   │       │ invariant_check   │ ─────────────────┘
          └──────────────────┘       └──────────────────┘   (E2E 回归中同步验证)
```

### 2.2 在六阶段中的位置

```
Proposal → Design L1 → Design L2 (Gherkin spec + tasks)
                              │
                              ▼
                    ┌──────────────────┐
                    │  Contract 推导    │  ← 本次新增（Design L2 末尾）
                    │  产出 contract.md │
                    └────────┬─────────┘
                             │
                             ▼
                    Build (TDD 消费契约 + 运行时断言)
                             │
                             ▼
                    Verify (E2E + 契约门禁检查)
                             │
                             ▼
                    Retro (契约违规模式分析)
```

### 2.3 八大工程原则修改

原则总数从 8 条增加到 9 条。新增**第 3 条"契约式约束"**，插入在"设计预研"和"TDD 驱动"之间，表明契约是从设计到编码的桥梁：

| # | 原则 | 核心要点 |
|---|------|---------|
| 1 | 需求澄清优先 | 需求不清晰不开工 |
| 2 | 设计预研，消除风险 | 技术预研 + POC 验证 |
| **3** | **契约式约束** | **从 Spec 推导 DbC 契约（前置/后置/不变式）。API 级硬性必做，模块级强推荐，函数级可选。TDD 翻译契约到测试，代码保留运行时断言。** |
| 4 | TDD 驱动 | 内外双循环：spec 驱动 + 测试驱动 |
| 5 | 验证与确认检查 | E2E 自动化回归 + 人工探索性测试 + 合规审查 |
| ... | ... | ... |

### 2.4 不修改的部分

- 第 1-2 条原则主体不变，第 4-9 条编号后移（原第 3 → 第 4，以此类推）
- 四 Agent 分工不变
- 六阶段名称和顺序不变
- 上次 E2E Playwright 强化设计不动

## 3. contract.md 模板与三层契约结构

### 3.1 文件定位

`contract.md` 是 Design 阶段的独立产出物，与 `spec.md`、`architecture.md` 平级，放在 `openspec/changes/{name}/specs/{capability}/contract.md`。

### 3.2 三层契约的强制执行级别

| 层级 | 必做/可选 | 触发条件 | 违反后果 |
|---|---|---|---|
| API 级 | **必做**（硬性） | 所有有 API 的项目 | Verify 门禁阻断 |
| 模块级 | 强推荐 | Capability 含业务规则时（如唯一性约束、状态迁移规则） | Verify 门禁告警 |
| 函数级 | 可选 | 高风险函数（数据处理、权限校验、金钱计算）或 bug-fixer 补写 | Retro 记录缺口 |

### 3.3 contract.md 模板

```markdown
# {Capability} 契约定义

> 从 spec.md 的 Gherkin 场景推导，定义本 Capability 的三层契约约束。
> 契约优先级：API 级 □ 模块级 □ 函数级 □（勾选适用层级）

## 一、API 级契约（硬性必做）

### 端点: POST /api/{resource}
- **前置条件**:
  - 请求体必须包含 {field1}，类型为 {type}，非空
  - {field2} 若存在，必须在 {min}-{max} 范围内
- **后置条件**:
  - 响应状态码 201
  - 响应体包含 id，类型为 integer，> 0
  - {resource} 已持久化到数据库
- **不变式**:
  - 同一 {unique_key} 不能创建两条记录

### 端点: GET /api/{resource}/{id}
- **前置条件**: id 必须是正整数
- **后置条件**:
  - 若记录存在：状态码 200，响应体匹配 {schema}
  - 若记录不存在：状态码 404，响应体包含 error_code
- **不变式**: 无

## 二、模块级契约（强推荐，有业务规则时必做）

### 模块: {ModuleName}
- **前置条件**:
  - <调用此模块公共方法前必须满足的条件>
- **后置条件**:
  - <调用后保证的状态>
- **不变式**:
  - <跨所有公共方法必须保持的规则>
  - 例：UserRepository 中同一 email 不重复

## 三、函数级契约（可选增强）

> 仅标注高风险或关键路径函数，不是所有函数都需要。

### 函数: {function_name}({params})
- **前置条件**: {param} 非空，{param} 在 {range} 内
- **后置条件**: 返回值类型为 {type}，{constraint}
- **违反后果**: {数据丢失 / 安全风险 / 逻辑错误}
```

### 3.4 契约推导规则

Agent 3 从 `spec.md` 的 Gherkin 场景推导契约时遵循以下映射规则：

| 从 Gherkin 推导 | 到契约类型 | 示例 |
|---|---|---|
| Scenario 的 Given | 前置条件 | `Given 用户已登录` → 前置条件：请求包含有效 token |
| Scenario 的 Then | 后置条件 | `Then 订单状态为"已创建"` → 后置条件：order.status == "created" |
| 跨 Scenario 的业务规则 | 不变式 | 多个 Scenario 中都提到"库存不能为负" → 不变式：inventory >= 0 |

## 4. 双重检查机制

### 4.1 TDD 翻译契约到测试

Agent 3 在 Build 阶段 TDD 微循环的 RED 步骤中，从 `contract.md` 读取契约，翻译为可执行测试。扩展后 TDD 微循环从 9 步变为 10 步：

```
Build 阶段 Scenario 微循环（修改后）：
 1. 复用检查
 2. 读 contract.md → 翻译契约到测试（契约 → TDD RED）
 3. 写行为测试（Spec → TDD RED）
 4. 写实现代码（含运行时断言）
 5. 跑测试（单元 + 集成 + 契约测试）
 6. E2E 测试
 7. 功能测试
 8. 代码评审（契约合规检查作为新检查项）
 9. 安全扫描
 10. 通过 → git commit
```

TDD 三层循环更新：

```
TDD 内层循环：RED(单元测试 + 契约翻译测试) → GREEN(实现 + 运行时断言) → REFACTOR
TDD 外层循环：功能实现 → E2E 测试编写 → E2E 测试通过
               ↑
               外层契约补充：require/ensure/invariant_check 运行时守护
```

### 4.2 运行时断言模式

契约断言保留在生产代码中，通过环境变量控制断言级别：

```python
# 函数级运行时断言示例
def create_user(email: str, name: str) -> User:
    # 前置条件（运行时断言）
    assert email and "@" in email, "require: email must be valid"
    assert name and len(name) <= 100, "require: name must be non-empty and <= 100 chars"

    user = _do_create(email, name)

    # 后置条件（运行时断言）
    assert user.id > 0, "ensure: user.id must be positive"
    assert user.email == email, "ensure: email must match input"

    return user

# 模块级不变式断言
class UserRepository:
    def _check_invariant(self) -> None:
        """确保 email 唯一性不变式"""
        emails = [u.email for u in self._users.values()]
        assert len(emails) == len(set(emails)), \
            "invariant: duplicate email detected in UserRepository"
```

### 4.3 环境分级断言策略

```python
# ASSERT_LEVEL = strict | relaxed | off
# strict: 断言失败 → 500 + 日志告警（Development/Staging）
# relaxed: 断言失败 → 日志告警 + 继续执行（Production 默认）
# off: 完全跳过（极端性能场景，可配合 python -O）
```

**默认策略**：

| 环境 | ASSERT_LEVEL | 行为 |
|---|---|---|
| Development | strict | 断言失败抛异常 |
| CI/E2E | strict | 断言失败终止流水线 |
| Production | relaxed | 断言失败只记录 WARNING 日志，不中断请求 |

### 4.4 性能影响分析

| 断言类型 | 单次耗时 | 典型频率 | 单请求总开销 |
|---|---|---|---|
| 简单类型检查（`assert id > 0`） | ~50ns | 每函数 1-3 次 | <1μs |
| 不变量检查（遍历集合） | ~1μs/100元素 | 每请求 1-2 次 | ~10μs |
| API 响应校验（JSON schema） | ~50μs | 每 API 1 次 | ~50μs |

典型 API 请求总耗时（含数据库查询）约 1-10ms，契约断言总开销 < 0.1ms，占比 < 1%。**性能影响几乎可忽略。** 且 Production 默认 `relaxed` 模式不中断请求，亦可用 `python -O` 在字节码层面完全移除断言。

### 4.5 TDD 翻译示例

contract.md 中的 API 级契约：

```markdown
### POST /api/users
- **前置**: email 必须包含 @，name 非空且 ≤100 字符
- **后置**: 状态码 201，响应 id > 0
- **不变式**: 同一 email 不重复
```

对应的契约测试（TDD 翻译产物）：

```python
# tests/test_user_api_contract.py
def test_create_user_requires_valid_email(client):
    """契约翻译：POST /api/users 前置条件 - email 必须有效"""
    resp = client.post("/api/users", json={"email": "invalid", "name": "Test"})
    assert resp.status_code == 422

def test_create_user_returns_id(client):
    """契约翻译：POST /api/users 后置条件 - id > 0"""
    resp = client.post("/api/users", json={"email": "a@b.com", "name": "Test"})
    assert resp.status_code == 201
    assert resp.json()["id"] > 0

def test_create_user_enforces_email_uniqueness(client):
    """契约翻译：不变式 - email 不重复"""
    client.post("/api/users", json={"email": "a@b.com", "name": "First"})
    resp = client.post("/api/users", json={"email": "a@b.com", "name": "Second"})
    assert resp.status_code == 409
```

## 5. 三阶段中契约的消费方式

### 5.1 Design 阶段 — 契约推导（新增子步骤）

```
Design L2 流程（修改后）
1. 技术预研 → POC（已有）
2. 架构设计 → architecture.md（已有）
3. 详细设计 → spec.md：Gherkin 行为规格（已有）
4. 契约推导 → contract.md（新增）
5. 任务分解 → tasks.md（已有）
```

### 5.2 Build 阶段 — TDD 微循环消费契约

详见 4.1 节 TDD 扩展为 10 步。

TDD skill（`test-driven-development/SKILL.md`）需在 RED 步骤指导中增加"读取 contract.md 并翻译契约到测试"的说明。

### 5.3 Verify 阶段 — 契约门禁

Verify 门禁 Checklist 新增契约维度：

```markdown
## Verify 门禁 Checklist

### E2E 门禁（has_ui: true 时）
- [ ] P0 场景 E2E 测试存在且 100% 通过
- [ ] E2E 测试报告已生成（含通过率、执行时间）
- [ ] 失败用例已修复或豁免（附理由）

### 契约门禁（新增）
- [ ] API 级契约测试 100% 通过（硬阻断）
- [ ] 模块级契约测试通过（若有）或记录缺口（门禁告警）
- [ ] 运行时断言在 CI/Staging 环境未触发 strict 违规

### 通用门禁
- [ ] 全部 BUG 关闭
- [ ] 代码评审通过
- [ ] 安全扫描无高危项
```

### 5.4 Retro 阶段 — 契约违规分析

复盘报告新增 `## 十、契约违规分析` 章节（接在 E2E 指标之后）：

```markdown
## 十、契约违规分析

| 违规类型 | 次数 | 阶段 | 根因 |
|---|---|---|---|
| 前置条件违反 | 3 | Build TDD | 边界值测试遗漏 |
| 后置条件违反 | 1 | Verify E2E | API 返回字段变更未更新契约 |
| 不变式违反 | 0 | - | - |

> 违规次数 > 0 时，需产出改进措施。
```

## 6. 术语统一

MASE 项目中"契约"一词只指 DbC 风格的三个断言。以下全局术语统一：

| 文件 | 旧术语 | 新术语 | 原因 |
|---|---|---|---|
| 培训幻灯片 `.frontend-slides/*.html`（6 个变体） | "外层契约" | "TDD 外循环" | 本质是 TDD 不是 DbC |
| [harness-maturity-model.md](harness-maturity-model.md) | "接口契约" | "接口协议同步" | 协议 ≠ 契约 |
| [webapp-testing SKILL.md](github-repo/measures-framework-package/skills/webapp-testing/SKILL.md) | "fixtures.json 契约" | "fixtures 约定" | 数据约定 ≠ DbC 契约 |
| [playwright-e2e-design.md](framework/playwright/2026-07-12-playwright-e2e-testing-design.md) | "fixtures.json 契约" | "fixtures 约定" | 同上 |

## 7. 受影响文件清单

### 7.1 需修改的框架文件

| 文件 | 修改内容 | 改动量 |
|---|---|---|
| [README.md](github-repo/README.md) | 新增第 3 条原则"契约式约束"，原第 3-8 条后移编号 | 小 |
| [unified-dev-framework-design.md](github-repo/docs/superpowers/specs/2026-07-03-unified-dev-framework-design.md) | ① Principles 新增第 3 条 ② Design L2 新增契约推导子步骤 ③ Build TDD 微循环 9→10 步 ④ Verify 门禁新增契约维度 ⑤ Retro 新增契约违规分析 | 中 |
| [test-driven-development SKILL.md](github-repo/measures-framework-package/skills/test-driven-development/SKILL.md) | TDD RED 步骤增加"读 contract.md → 翻译契约到测试"指导 | 小 |
| [test_api_contract.py](tests/test_api_contract.py) | 从字段名校验升级为 DbC 风格契约测试示例 | 中 |
| [harness-maturity-model.md](framework/harness-maturity-model.md) | "接口契约"术语改为"接口协议同步" | 小 |
| [webapp-testing SKILL.md](github-repo/measures-framework-package/skills/webapp-testing/SKILL.md) | "fixtures.json 契约"术语改为"fixtures 约定" | 小 |
| [bug-fixer SKILL.md](github-repo/measures-framework-package/skills/bug-fixer/SKILL.md) | 补充"补写函数级契约断言"作为修复步骤之一 | 小 |
| 培训幻灯片 `.frontend-slides/*.html`（6 个文件） | "外层契约"术语改为"TDD 外循环" | 小 |
| [playwright-e2e-design.md](framework/playwright/2026-07-12-playwright-e2e-testing-design.md) | "fixtures.json 契约"术语改为"fixtures 约定" | 小 |

### 7.2 需新增的文件

| 文件 | 内容 | 位置 |
|---|---|---|
| `contract.md`（模板） | 三层契约模板 | `github-repo/measures-framework-package/templates/` |
| `2026-07-14-contract-based-development-design.md` | 本设计文档 | `docs/superpowers/specs/` |

### 7.3 不修改的文件

- 四 Agent 分工定义不变
- 六阶段名称和顺序不变
- 上次 E2E Playwright 强化设计不动
- `ai-spec-contract-tdd.html` 源文件不动（作为参考文档保留）
- org-harness-framework 文件不动（与契约无直接关联）

### 7.4 改动影响评估

| 维度 | 评估 |
|---|---|
| 原则变更 | 新增 1 条，总数从 8 → 9 |
| 流程变更 | Design L2 新增契约推导子步骤，Build 微循环 9 → 10 步 |
| 门禁变更 | Verify 门禁新增契约维度（API 级硬阻断） |
| 技能修改 | TDD skill 修改指引，bug-fixer 补充修复步骤 |
| 术语统一 | 约 12 处替换（6 个培训文件 + 3 个规范文件） |
| 向后兼容 | 全部增量修改，不破坏现有流程。无 contract.md 的旧项目在门禁中标记为"待补充"而非阻断 |

## 8. Spec 与 Contract 的关系

- **Spec 是 Contract 的基础**：contract.md 中的每条契约均从 spec.md 的 Gherkin 场景推导而来，不能凭空编造
- **Contract 是 Spec 的补充**：Gherkin 场景描述"在什么条件下应该发生什么"，Contract 将其中的约束条件（前置/后置/不变式）显式化
- **优先级**：当 Contract 与 Spec 冲突时，以 Spec 为准（Spec 反映用户需求，Contract 是对 Spec 的解释）
- **为什么 Contract 不能替代 Spec**：Spec 描述完整的行为语义（包括异常流程、边界条件、交互顺序），Contract 只抽取其中的约束条件。好的 Spec 可以指导契约推导，但契约不能反向替换 Spec
