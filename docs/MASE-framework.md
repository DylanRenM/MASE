# MASE v2：风险自适应 AI 软件工程框架

> 现行规范 · 版本由 `framework-manifest.yaml` 定义

## 目标

MASE 用可验收需求、风险验证、契约、TDD 和 E2E 保证质量，同时让过程重量与实际风险匹配。它不要求每个项目机械执行同一套文档和测试频率。

## 三种 Profile

| Profile | 适用范围 | 默认产物 | 评审/测试节奏 |
|---|---|---|---|
| Lite | 本地工具、MVP、小变更 | change、Specs、tasks | diff-only；相关测试；最终 P0/API 门禁 |
| Standard | UI、文件、外部依赖、并发、持久化 | Lite + focused design + API contract | capability 评审/安扫；最终全量门禁 |
| Strict | 鉴权、支付、监管、不可逆迁移 | 完整可行性、架构、详细设计、契约 | 独立多轮评审与全量回归 |

Profile 的机器定义在 `profiles/*.yaml`，标准风险注册表在 `profiles/risks.yaml`。GatePlan 同时考虑基础 Profile、风险触发器、`product.has_ui` 与 `impact.ui_changed`；Capability 可局部升级，不能借 Profile 删除已触发的硬门禁。

## 流程

```text
需求/已有规格
   ↓ 差异分析与必要确认
风险分诊 → 选择 Profile / capability 升级
   ↓
风险驱动设计与 POC
   ↓
纵向工作包 TDD
   ├─ micro: related unit + contract
   ├─ capability: integration + review + risk scan
   └─ final: full applicable suite + P0 E2E
   ↓
可执行/人工结构化证据 → complete → archive snapshot
```

阶段仍可标为 draft/proposal/design/build/verify/retro/release，但它们是状态，不是强制暂停点。无新增用户决策时自动继续。

## 不变的质量底线

- 用户可见行为必须有确认的验收要求。
- UI 交互变化在开发前确认参考原型；无 UI 和内部重构不需要原型。
- 未知工具链、外部依赖和高风险边界先做可重跑 POC。
- API/公共协议契约测试必须通过。
- 产品有 UI 且 change 修改 UI 时，P0 E2E 必须 100%；Sandbox 必须恢复一致。
- Bug 先有失败证据和根因，再系统修复与补测。
- 迁移、覆盖和删除前备份。
- 自动 passed 必须来自 Gate Runner；输入、日志或制品变化会使证据失效。
- API/P0/凭据/数据安全硬门禁不得通过普通 Brownfield 基线绕过。

## 单一事实来源

| 事实 | 唯一来源 |
|---|---|
| 框架版本、发布边界 | `framework-manifest.yaml` |
| 工程规则 | `project-rules.md` |
| Profile 策略 | `profiles/*.yaml` |
| Change 状态/门禁证据 | `mase-state.yaml` |
| Brownfield 遗留失败债务 | `.mase/baseline.yaml` |
| 工作完成事实 | `tasks.md` |
| 验收行为 | `specs/*/spec.md` |

IDE 规则、验证摘要、追踪矩阵和 master 都是生成物。`openspec/master/` 仅在 release/archive 生成快照，不在 Design 阶段与 change 双写。

主 `stack` 是项目的执行/构建骨架，只允许 generic、python、swift；SwiftUI、Flutter、Dart、Kotlin、Flask 等辅助技术写入 `toolchains`。`mase status` 无参数时汇总全部非 archived change，并诊断依赖环、缺失依赖、显式互斥、影响路径冲突、损坏状态与过期基线。

## Agent 路由

- Agent 1：选 Profile、路由工作、校验状态和门禁。
- Agent 2：先读来源、批量澄清、确认原型、产出唯一验收行为。
- Agent 3：风险驱动设计，按边界运行 TDD。
- Agent 4：按 Profile 独立评审、验证和根因修复。

Lite 可由一个工作 Agent 连续执行；Standard/Strict 才需要更多独立交接。

## Token 路由

单个工作包默认只加载当前 Spec、相关接口/测试、diff 和最近交接摘要。历史、培训、归档、其他产品和未命中的 Skill reference 默认排除。详细排除列表见 manifest。

平台提供 usage 时记录 input/output/cache Token；否则只报告文件数和字符数代理，不能把估算称为 Token。

## 产物策略

- `tech-feasibility.md`：未知工具链/依赖或高风险才生成。
- `architecture.md`：Standard/Strict 的跨模块决策。
- `detailed-design.md`：Strict，或状态机/迁移/复杂数据模型触发。
- `contract.md`：API 必做；模块/函数风险触发。
- 验证报告：从 state、Spec ID、测试标签和命令结果生成。

## 框架边界

运行时只分发 rules、profiles、schemas、templates、agents、skills 和现行文档。`docs/superpowers`、history、training、framework 演示、生成站点、examples 和产品实例均为非规范内容，默认不进入 Agent 上下文。

采用 MASE 的真实产品是框架使用者，不是框架组成部分。产品必须使用独立项目根、`.mase.yaml`、OpenSpec 状态和 Git 仓库；MASE 仓库不得依赖产品源码或产品测试才能通过自身门禁。
