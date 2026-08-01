## Context

MASE 当前通过 Profile、risk trigger、`.mase/gates.yaml` 和 `mase-state.yaml` 推导并执行门禁，Gate Runner 已把静态 `tests` 集合摘要写入执行签名。采用项目仍需在 gate 脚本中硬编码浏览器测试文件；`impact.paths` 只能缩小输入摘要，不能选择真实测试集合。Playwright 的重试、fixture 版本和失败类型也不会进入证据，因此“通过”无法区分首次通过与重试后通过。

本 change 同时影响 GatePlan、证据 Schema、发布模板和 Web E2E Skill。必须兼容没有测试 manifest 的既有采用项目，并保护当前 MASE 工作区中的未提交修改；迁移只增加或增量修改框架资源，不清理历史文件。采用契约只通过生成的临时项目 fixture 验证，框架 change 不读取、修改或执行任何命名产品仓库。

## Goals / Non-Goals

**Goals:**

- 让 MASE 从 change 影响路径得到确定、可解释、可保守回退的测试集合。
- 把少量 P0 用户旅程与 UI contract/P1 回归明确分层。
- 让实际选择集合参与执行签名、证据新鲜度和状态输出。
- 让浏览器 adapter 以统一 JSON 输出重试与失败分类，降低人工分诊成本。
- 让新项目和更新后的采用项目获得 Schema、模板、文档、Skill 和验证测试。

**Non-Goals:**

- 不让 MASE 理解 pytest、Playwright 或 XCTest 的内部语法；selector 对核心运行时保持不透明。
- 不自动把全部历史浏览器用例重写成 Page Object 或视觉基线。
- 不把 AI 生成的测试候选直接升级为硬门禁。
- 不要求旧项目立即创建 manifest；缺失时继续使用 canonical gate 的静态 `tests`，并给出迁移诊断。

## Decisions

### 1. 使用 `.mase/tests.yaml` 作为唯一测试选择清单

清单使用 `mase-test-manifest/v1`，每个测试项声明稳定 ID、tier、runner、selectors、关联 capabilities、输入 paths 和可选 tags。tier 固定为 `unit`、`contract`、`integration`、`ui_contract`、`p0_journey`、`p1_regression`，避免采用项目创造含义冲突的 P0/P1。

选择器是传递给 adapter 的不透明参数；MASE 只负责校验安全相对路径、排序、去重、摘要和可解释原因。相比把测试文件继续塞进 `.mase/gates.yaml`，独立 manifest 能被多个 gate、Profile 和本地命令复用，也能单独验证覆盖与重复。

### 2. Gate definition 通过 `test_tiers` 和占位符消费选择结果

gate 可声明 `test_tiers`，命令中的独立参数 `{selected_tests}` 在执行前展开为选择器。Gate Runner 使用展开后的命令和实际测试 ID/selector 计算签名，并在 plan 中展示 `selected_tests`、`selection_reason` 与 `selection_fallback`。

若 gate 声明 `test_tiers` 却没有占位符，Schema/加载阶段拒绝配置，防止“显示已选测但实际执行全量或其他集合”。未声明 `test_tiers` 的旧 gate 保持原行为。

### 3. 选择以 Capability 路径为主，无法证明安全时扩大范围

选择流程先按显式 scope，再匹配 manifest item 的 capabilities/paths 与 change `impact.paths`。目录前缀和 glob 使用安全的项目相对路径。若 UI change 触发 P0 但没有精确命中，选择所有 `p0_journey` 并标记 `conservative_all_tier`；绝不返回空集合来满足硬门禁。非 UI change 仍由风险推导决定 P0 是否适用。

### 4. 诊断由 adapter 生成，Gate Runner 负责绑定和验证

Gate Runner 为每次自动执行提供唯一 `MASE_TEST_DIAGNOSTIC_PATH`。测试 adapter 可写 `mase-test-diagnostic/v1` JSON，包含 attempts、first_attempt_result、final_result、classification、failed_tests 和 artifact references。Gate Runner 校验并摘要写入 Evidence；失败且没有 adapter 输出时生成 `classification: unknown` 的最小诊断。

Playwright reporter 将 retry 后通过归类为 `flaky`。MASE 的 gate 结果仍以最终退出码决定，但 evidence/result summary 必须保留 `first_attempt_result: failed` 和 `classification: flaky`，状态与指标不得把它统计为首次通过。

### 5. E2E 只穿透自有系统，stub 停在不可控外部边界

P0 journey 使用真实 UI、真实应用路由、真实持久化 adapter 和隔离测试数据；只能在 LLM、SMTP、支付、第三方 SaaS 等不可控边界使用确定性 fake。mock 自有 API 的浏览器测试归为 `ui_contract`。这样在缩短执行时间的同时保留端到端缺陷探测能力。

### 6. 隔离身份由 fixture manifest 绑定

Web E2E adapter 必须在临时测试根启动服务，并生成包含 `schema_version`、`fixture_digest` 和 `test_root` 的 fixture manifest。硬门禁禁止 `reuseExistingServer`，状态型并行测试使用 per-worker 根；无法隔离时串行执行并明确记录，而不是冒险共享开发数据。

### 7. 自动生成仅产生候选

从 OpenSpec Scenario 生成的用例先进入 `candidate` 状态。只有当它具备稳定业务断言、确定性数据、非重复旅程和正确 tier，并通过一次评审后，才能写入 manifest。选择器修复、快照基线更新和 flaky 忽略不得自动批准。

### 8. 采用验证使用 clean-room 临时项目

MASE 只定义并验证公开 Schema、CLI、模板和 adapter 输出协议。动态选测、旧项目兼容、证据新鲜度和 reporter 合同均在测试创建的临时采用项目中验证；具体产品的 manifest、脚本、fixture、测试数据和 E2E 执行由产品仓库自行负责。这样框架发布不依赖相邻产品仓库的存在、状态或测试结果。

## Risks / Trade-offs

- [采用项目 manifest 不完整导致漏测] → UI/P0 无精确命中时全 tier 回退，manifest 校验报告未覆盖 impact path。
- [测试选择使证据复用错误] → 实际测试 ID、selector、manifest 摘要和展开命令全部进入执行签名。
- [通用 Gate Runner 无法理解 runner 重试] → 用版本化诊断 JSON 作为 adapter 契约，缺失时保守标记 unknown。
- [共享数据库下并行更快但不稳定] → per-worker 隔离优先；不具备隔离能力的 suite 明确串行。
- [P0 数量短期下降被误解为覆盖下降] → 同时报告 capability 旅程覆盖、contract 覆盖和 P1 计划回归，不使用单一用例数量衡量质量。
- [现有 MASE 工作区相关文件已修改] → 仅在当前内容上做小块增量 patch，验证 diff，不回退或重写用户修改。

## Migration Plan

1. 先发布 Schema、解析/选择模块和失败契约测试，保持旧 gate 行为。
2. 更新 gate Schema/模板、核心规则、Profile、Web E2E Skill、文档和分发清单。
3. 生成临时采用项目 fixture，使用 dry-run/plan 验证 manifest 精确选择、保守回退和旧静态 gate 兼容。
4. 在临时 fixture 中验证 `{selected_tests}` 展开、诊断 reporter 和 fixture 身份等公开协议，不接入任何真实产品仓库。
5. 运行 MASE 全量回归、分发完整性、clean-room 采用契约和仓库边界审计。
6. 回滚时恢复 gate 定义中的静态测试命令；保留 manifest 和诊断文件，它们不改变产品数据。

## Open Questions

- 后续是否把 selector manifest 扩展到跨仓库测试服务，留待独立 change；v1 只支持单项目根。
- flaky 是否最终升级为阻断由采用项目阈值决定；v1 默认最终退出码为零时 gate 通过但显式告警。
