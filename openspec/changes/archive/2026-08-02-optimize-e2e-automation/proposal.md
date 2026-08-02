## Why

MASE 能按风险触发 P0 E2E 并记录门禁证据，但尚未定义浏览器测试分层、Capability 到测试集合的机器映射、确定性执行和失败诊断契约，采用项目仍需人工选择用例并判断失败来源。需要把这些能力纳入框架发布资源，使 E2E 成为少量、可复现、可按影响选取的用户旅程，而不是不断膨胀的页面检查集合。

## What Changes

- 定义 unit、contract、integration、UI contract、P0 journey 和 P1 regression 的职责；只有跨受控系统边界的关键用户闭环可标记 P0 journey。
- 发布 Capability-to-Test manifest Schema、模板和选择器，把 change `impact.paths` 与 capability paths 映射到相关测试；选择不确定时保守扩大范围。
- 为采用项目发布可选 `framework_contract` 状态契约，绑定已安装 CLI 与版本化 Schema，明确禁止以相邻源码仓库作为运行接口。
- 扩展 Gate Runner，使 canonical gate 可消费选择结果，并把选择摘要、测试集合摘要、首轮/重试状态和诊断制品绑定到证据。
- 增加标准失败分类：product、test、environment、test-data、flaky、unknown；重试后通过保留 flaky 状态，不等同首次通过。
- 强化 Web E2E Skill：硬门禁隔离测试根、Schema/fixture 摘要、禁止开发服务复用、系统内 API 与外部不确定依赖的 stub 边界、语义定位和无固定等待。
- 按 Profile 定义执行节奏：变更相关 UI contract/P0 用于开发和候选验证，完整 P1、多浏览器或长耗时场景进入计划回归，不把所有浏览器检查变成每次硬门禁。
- 增加 OpenSpec 验收场景生成自动化测试候选的质量过滤规则与指标定义。
- 更新核心规则、Profile、风险配置、文档、Skill、manifest、Schema、模板和培训源，并提供迁移兼容路径。

## Capabilities

### New Capabilities

- `risk-scoped-e2e-automation`: 定义浏览器测试分层、Capability 测试 manifest、按影响选测、确定性执行、失败诊断、候选生成和质量指标。

### Modified Capabilities

- `capability-scoped-gate-plan`: GatePlan 必须将 capability path 和测试 manifest 解析为可解释的测试选择，并在不确定时采用保守回退。
- `executable-gate-evidence`: 自动证据必须绑定实际测试集合、选择原因、诊断制品和首轮/重试结果，避免 flaky 被记为普通通过。

## Impact

- 运行时：`mase_cli/` GatePlan、manifest 读取、测试选择和证据模型。
- 契约：新增测试 manifest Schema，扩展 gates/state Schema、`framework_contract` 与模板，保持旧项目无 manifest/contract 时的保守兼容。
- 过程资产：`project-rules.md`、`profiles/`、`docs/MASE-framework.md`、`skills/webapp-testing/`、agent/quality Skill、培训源。
- 分发：`framework-manifest.yaml`、wheel/resource 完整性测试和 adopter 更新路径。
- 验证：新增 selector、manifest、证据诊断、Profile 和分发契约测试；现有 gate 名称和 `mase gate run` CLI 保持兼容。
