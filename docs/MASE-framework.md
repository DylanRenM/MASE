# MASE v2：风险自适应 AI 软件工程框架

> 现行规范 · 版本由 `framework-manifest.yaml` 定义

## 目标

MASE 用可验收需求、风险验证、契约、TDD 和 E2E 保证质量，同时让过程重量与实际风险匹配。它不要求每个项目机械执行同一套文档和测试频率。

## 三种 Profile

| Profile | 适用范围 | 默认产物 | 评审/测试节奏 |
|---|---|---|---|
| Lite | 本地工具、MVP、小变更 | change、Specs、tasks | diff-only；相关测试；最终 P0/API 门禁 |
| Standard | UI、文件、外部依赖、并发、持久化 | Lite + focused design + API contract | capability 评审；风险命中时安扫；最终全量门禁 |
| Strict | 鉴权、支付、监管、不可逆迁移 | 完整可行性、架构、详细设计、契约 | 一轮独立评审；有异议/变化时追加；全量回归 |

Profile 的机器定义在 `profiles/*.yaml`，标准风险注册表在 `profiles/risks.yaml`。GatePlan 同时考虑基础 Profile、风险触发器、`product.has_ui` 与 `impact.ui_changed`；Capability 可局部升级，不能借 Profile 删除已触发的硬门禁。

## 流程

```text
需求/已有规格
   ↓ 差异分析与必要确认
风险分诊 → 选择 Profile / capability 升级
   ↓
历史变更分类 → 计划影响链分析 / 豁免证据
   ↓ 超限时人工架构决策
风险驱动设计与 POC
   ↓
纵向工作包 TDD
   ├─ micro: related unit + contract
   ├─ capability: actual-diff impact reconcile + integration + review + risk scan
   └─ final: freeze candidate → one full applicable suite + selected P0 journeys
   ↓
可执行/人工结构化证据 → complete → archive snapshot
```

阶段仍可标为 draft/proposal/design/build/verify/retro/release，但它们是状态，不是强制暂停点。无新增用户决策时自动继续。

## Release Overlay

发布是独立于 Lite/Standard/Strict 的可选覆盖层，不是第四种 Profile。只有 change 声明计划、打包、发布、部署、线上验证或恢复意图时，才在 `mase-state.yaml` 增加 `release`，并组合描述制品、目标、发布策略、状态/配置、消费者接口、外部能力、恢复和观察；旧 change 不受影响。跨平台部署、运行配置、状态升级、公网暴露、多服务和基础设施变更继续通过风险注册表决定是否升级 Profile。

发布结果按证据严格递进：`planned → candidate_ready → artifact_ready → target_ready → live_verified → observed`；恢复完成并重新验证后使用 `recovered`。`artifact_ready` 只说明不可变制品的身份、来源、完整性与禁止内容通过，不能表述为已经上线；`live_verified` 需要目标正在提供准确版本并通过真实消费者/能力路径，仍不等于观察窗口已经完成。

发布门禁分为 `release_artifact`、`release_preflight`、`release_live`、`release_observe`。制品或候选输入变化会让绑定证据 stale；计划清单保持 pending，只有 Gate Runner 或在 `.mase/gates.yaml` 声明为 `mode: manual` 的人工 evidence 能通过门禁。Gate Runner 还会检查 Overlay intent、authority、阶段前序和同一 release digest。`mase release plan` 和 `mase release status` 只做校验与报告，不执行构建、上传、停服、切流、发布、基础设施变更或回滚。

所有发布场景遵循八个通用不变量：权限/范围明确、不可变制品身份与来源、最终交付内容等价、状态/配置/密钥兼容、影响前完成可前置检查、受控爆炸半径与停止条件、真实消费者线上证据、观察期内恢复能力。具体 VM、容器/编排、Serverless、Registry、桌面/移动端、App Store 或 Windows/PowerShell 细节由 `release-software` Skill 按目标加载；项目自己的 CI、Helm、Terraform、PowerShell 等仍是执行适配器，MASE 不提供万能生产部署器。

## 不变的质量底线

- 用户可见行为必须有确认的验收要求。
- UI 交互变化在开发前确认参考原型；无 UI 和内部重构不需要原型。
- 未知工具链、外部依赖和高风险边界先做可重跑 POC。
- API/公共协议契约测试必须通过。
- 契约具有复杂输入空间、解析/序列化、数值边界、状态机、不可信输入、并发不变量或兼容性变更时，评估属性测试或模型测试。它们补充而不替代确定性业务样例和回归测试。
- 属性必须从 Spec、版本策略或公共协议推导；幂等、Round-trip、后向兼容、分页、时区和并发等性质只有在相应语义被声明时才成立，不能由测试技术反向发明需求。
- 属性测试失败必须在既有 gate 日志或制品中保留 Property ID、工具/版本、seed 或等价重放参数及最小反例；重要反例应固化为确定性回归测试。
- 产品有 UI 且 change 修改 UI 时，P0 E2E 必须 100%；Sandbox 必须恢复一致。
- 浏览器测试分层为 UI contract、P0 journey 和 P1 regression。页面加载、元素/布局检查或 mock 自有 API 的测试下沉到 UI contract；P0 必须完成真实 UI→应用路由→受控持久化的关键用户闭环，只在 LLM、邮件、支付等不可控外部边界使用确定性 fake。
- `.mase/tests.yaml` 把稳定测试 ID、tier、Capability、selector 和产品路径绑定。GatePlan 按 `impact.paths` 选测；UI change 无法精确映射时执行全部 P0 journey 并报告治理诊断，不能用空集合通过硬门禁。
- Web hard gate 使用隔离测试根、版本化 fixture 摘要和非复用服务；retry 后通过保留 flaky 诊断，不统计为首次通过。
- Bug 先有失败证据和根因，再系统修复与补测。
- 历史行为变更在设计前分析显性调用方和隐性依赖，实现后按实际 diff 复扫；超过 10 个第一方调用方、达到 3 个系统边界或三层仍未收敛时由人工架构决策。
- L1/L2/L3 是影响等级而非第四种 Profile；未知调用频率、未验证隐性通道或低置信度不得判为 L1。
- 迁移、覆盖和删除前备份。
- 自动 passed 必须来自 Gate Runner；输入、日志或制品变化会使证据失效。
- final gate 必须绑定已冻结候选；相同执行只有完整签名 fresh 时复用。
- API/P0/凭据/数据安全硬门禁不得通过普通 Brownfield 基线绕过。

## 单一事实来源

| 事实 | 唯一来源 |
|---|---|
| 框架版本、发布边界 | `framework-manifest.yaml` |
| 工程规则 | `project-rules.md` |
| Profile 策略 | `profiles/*.yaml` |
| Change 状态/门禁证据 | `mase-state.yaml` |
| 采用项目绑定的框架版本与公开接口 | `mase-state.yaml` 的可选 `framework_contract` |
| 发布意图、制品、目标、观察与恢复上下文 | `mase-state.yaml` 的可选 Release Overlay |
| 门禁阶段、命令和基础输入 | `.mase/gates.yaml` |
| 测试分层、Capability 映射和选择器 | `.mase/tests.yaml` |
| Brownfield 遗留失败债务 | `.mase/baseline.yaml` |
| 工作完成事实 | `tasks.md` |
| 验收行为 | `specs/*/spec.md` |
| 影响调用图、分级、测试与回滚事实 | change 的 `impact-analysis.yaml`；三份 Markdown 为生成视图 |

IDE 规则、验证摘要、追踪矩阵和 master 都是生成物。`openspec/master/` 仅在 release/archive 生成快照，不在 Design 阶段与 change 双写。

主 `stack` 是项目的执行/构建骨架，只允许 generic、python、swift；SwiftUI、Flutter、Dart、Kotlin、Flask 等辅助技术写入 `toolchains`。`mase status` 无参数时汇总全部非 archived change，并诊断依赖环、缺失依赖、显式互斥、影响路径冲突、损坏状态与过期基线。

## Agent 路由

- Agent 1：选 Profile、路由工作、校验状态和门禁。
- Agent 2：先读来源、批量澄清、确认原型、确认允许的业务语义差异并产出唯一验收行为。
- Agent 3：执行计划影响扫描与实际 diff 复扫，风险驱动设计并按边界运行 TDD。
- Agent 4：独立检查影响链、测试范围和剩余风险，再按 Profile 评审、验证和根因修复。
- `release-software`：规划/校验发布，按目标选择 adapter，并守住权限、不可变制品、线上证据、观察与恢复边界。

Lite 可由一个工作 Agent 连续执行；Standard/Strict 才需要更多独立交接。

## Token 路由

单个工作包默认只加载当前 Spec、相关接口/测试、diff 和最近交接摘要。历史、培训、归档、其他产品和未命中的 Skill reference 默认排除。详细排除列表见 manifest。

平台提供 usage 时记录 input/output/cache Token；否则只报告文件数和字符数代理，不能把估算称为 Token。

`mase context plan` 在实际读取前给出纳入/排除原因和 Profile 软预算。完整测试输出写入脱敏 evidence 日志；Agent 默认只接收状态、耗时、有限失败摘要和日志路径，人工需要实时进度时显式使用 `mase gate run --verbose`。

## 产物策略

- `tech-feasibility.md`：未知工具链/依赖或高风险才生成。
- `architecture.md`：Standard/Strict 的跨模块决策。
- `detailed-design.md`：Strict，或状态机/迁移/复杂数据模型触发。
- `contract.md`：API 必做；模块/函数风险触发；适用的属性测试记录数据域、边界、oracle、隔离和测试追踪。
- 验证报告：从 state、Spec ID、测试标签和命令结果生成。
- E2E 指标：P0 首轮通过率、flaky 率、时长、Capability 旅程覆盖、失败分类率和人工回归时长；真实测量与代理值必须分开。

## 框架边界

运行时只分发 rules、profiles、schemas、templates、agents、skills 和现行文档。MASE 培训材料保留在独立 `training/mase-framework/`，默认不进入 Agent 上下文；通用培训、研究演示、历史备份、生成站点和产品实例不属于 MASE 仓库，必须物理迁出，不能只靠上下文排除隐藏。

采用 MASE 的真实产品是框架使用者，不是框架组成部分。产品必须使用独立项目根、`.mase.yaml`、OpenSpec 状态和 Git 仓库；可在 change state 中以 `framework_contract: {name: MASE, version: x.y.z, interface: installed-cli-and-versioned-schemas}` 显式绑定公开接口。MASE 仓库不得依赖产品源码或产品测试才能通过自身门禁，采用项目也不得把相邻 MASE 源码目录作为产品运行时。

仓库顶层文件和目录采用显式 allowlist，`python3 scripts/audit_repository_boundary.py` 同时检查未知根、非现行 docs/training、嵌套仓库和 `node_modules`、build 等重型生成残留；Finder `.DS_Store` 与 gitignored Python bytecode 按统一元数据策略忽略。根目录 `pytest` 只收集 `tests/`，使默认验证始终等于 MASE 框架测试；提交前仍应清理本地缓存。
