# risk-scoped-e2e-automation Specification

## Purpose
TBD - created by archiving change optimize-e2e-automation. Update Purpose after archive.
## Requirements
### Requirement: 浏览器测试分层
MASE SHALL 定义 `ui_contract`、`p0_journey` 和 `p1_regression` 的互斥职责。P0 journey MUST 验证通过真实用户界面、应用路由和受控持久化边界完成的关键业务闭环；只验证页面可加载、元素存在、布局或 mock 自有 API 的测试 MUST 不得作为 P0 journey。

#### Scenario: 自有 API 被浏览器路由 mock
- **WHEN** 浏览器测试 mock 产品自身生成接口并验证 Tab 和按钮状态
- **THEN** 系统将其登记为 UI contract 而不是 P0 journey

#### Scenario: 关键生成与下载闭环
- **WHEN** 测试通过真实 UI 上传隔离 fixture、调用真实应用 API、等待确定性外部 fake 并下载结果
- **THEN** 系统允许其登记为对应 Capability 的 P0 journey

### Requirement: 受版本控制的测试 Manifest
采用项目 SHALL 使用符合 `mase-test-manifest/v1` 的 `.mase/tests.yaml` 声明稳定测试 ID、tier、runner、selectors、capabilities 和相关路径。MASE MUST 校验路径安全、ID 唯一、tier 合法且 P0 journey 具有 Capability 和用户闭环说明。

#### Scenario: Manifest 包含逃逸路径
- **WHEN** selector 或相关路径使用绝对路径或 `..` 逃逸项目根
- **THEN** MASE 拒绝清单并报告安全相对路径诊断

#### Scenario: P0 缺少 Capability
- **WHEN** 一个 P0 journey 没有关联 Capability 或验收场景
- **THEN** MASE 拒绝将其用于硬门禁并给出补充字段建议

### Requirement: 风险与影响驱动选测
MASE SHALL 根据 gate tier、change `impact.paths`、Capability paths 和显式 scope 产生排序稳定的测试选择。UI change 已触发 P0 但无法精确证明映射时 MUST 选择全部 P0 journey 并标记保守回退，不能以空集合满足门禁。

#### Scenario: 单一 Capability UI 变更
- **WHEN** change 只修改测试用例生成页面且 manifest 存在对应路径映射
- **THEN** P0 gate 选择该 Capability 的旅程并展示命中路径和测试 ID

#### Scenario: 未覆盖 UI 路径
- **WHEN** UI change 的影响路径没有命中任何 manifest item
- **THEN** P0 gate 选择所有 P0 journey，输出 `conservative_all_tier` 诊断并要求补映射

### Requirement: 确定性且隔离的 P0 执行
Web P0 hard gate MUST 在隔离测试根中启动非复用服务，并绑定 fixture `schema_version`、`fixture_digest` 和测试根。状态型并发用例 MUST 使用 per-worker 数据根；不能隔离时 MUST 串行且不得访问开发数据库或开发服务。

#### Scenario: 本地已有开发服务
- **WHEN** P0 hard gate 启动且开发端口已有服务
- **THEN** adapter 使用隔离端口和测试根启动新服务，而不是复用开发实例

#### Scenario: Fixture Schema 已变化
- **WHEN** fixture 数据库存在但其 Schema 或 fixture 摘要与当前声明不一致
- **THEN** setup 重建隔离 fixture，不使用旧数据继续测试

### Requirement: 标准失败诊断与 flaky 可见性
自动浏览器 adapter SHALL 输出 `mase-test-diagnostic/v1` 诊断，分类限定为 `product`、`test`、`environment`、`test-data`、`flaky` 或 `unknown`，并记录首轮结果、最终结果、attempts、失败测试和制品引用。重试后通过 MUST 标记 flaky，不得统计为首次通过。

#### Scenario: 首轮失败重试通过
- **WHEN** runner 报告同一测试首轮失败且重试通过
- **THEN** gate 可按项目策略最终通过，但证据记录 `classification: flaky` 和失败的首轮结果

#### Scenario: 命令失败但没有 adapter 诊断
- **WHEN** 自动 gate 非零退出且没有产生有效诊断 JSON
- **THEN** Gate Runner 生成 unknown 最小诊断并保留日志路径，不猜测产品根因

### Requirement: 自动测试候选受控晋级
从 OpenSpec Scenario 或模型生成的测试 SHALL 先作为候选，只有具备业务可观测断言、确定性 fixture、非重复覆盖、正确 tier 且经评审后才能写入硬门禁 manifest。系统 MUST 不得自动批准选择器修复、忽略 flaky 或视觉基线变更。

#### Scenario: 生成页面存在性测试
- **WHEN** 自动生成候选只断言标题或按钮存在且已有 UI contract 覆盖
- **THEN** 系统标记重复或低层级候选，不加入 P0 manifest

### Requirement: E2E 自动化质量指标
MASE SHALL 报告 P0 首轮通过率、flaky 率、P0 时长、Capability 旅程覆盖、失败自动分类率和人工回归时长；指标 MUST 区分真实计数与代理值，不能仅以 E2E 用例数量衡量质量。

#### Scenario: 团队减少 P0 数量并增加契约覆盖
- **WHEN** 浅层页面测试下沉且关键 Capability 旅程和契约保持覆盖
- **THEN** 指标展示分层后的覆盖与人工时长变化，而不是把用例数减少报告为质量下降

### Requirement: 框架与采用项目保持仓库独立
MASE SHALL 使用测试期间生成的临时采用项目验证公开 CLI、Schema、模板和 adapter 契约。MASE 的运行时、活动 change 和验证 MUST NOT 依赖、修改或执行任何命名产品仓库及其产品测试；具体产品的 manifest、质量脚本、fixture 和 E2E 由采用项目自行维护。

采用项目 MAY 在 change state 中声明 `framework_contract`，其接口必须是 `installed-cli-and-versioned-schemas` 并绑定语义版本；MASE 状态输出 SHALL 保留该契约，MUST NOT 接受相邻源码仓库作为接口类型。

#### Scenario: 验证动态 P0 选测
- **WHEN** 框架回归验证精确路径命中、未映射 UI 回退和非 UI 不触发语义
- **THEN** 测试在临时目录生成最小采用项目并仅通过公开接口断言结果

#### Scenario: 相邻产品仓库不存在
- **WHEN** MASE 在干净克隆或 wheel 安装环境运行框架回归
- **THEN** 所有框架测试和发布完整性验证仍可完成，不要求任何产品源码、数据或测试存在
