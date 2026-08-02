## Why

MASE 已要求从 Spec 推导契约并在 TDD 中执行，但当前规范只要求边界测试，没有定义何时使用属性测试、如何描述生成数据域，也没有要求把最小反例沉淀为可重放证据。结果是 AI 容易生成少量固定样例，或反过来把 PBT 机械施加到所有接口，既漏掉大输入空间中的缺陷，也可能制造错误契约和不稳定测试。

## What Changes

- 新增风险驱动的属性测试路由：仅在复杂输入空间、解析/序列化、数值边界、状态机、不可信输入或兼容性变更等适用场景使用 PBT/模型测试。
- 扩展契约模板，为每条属性记录 Spec 来源、合法/非法数据域、边界、oracle、适用语义、隔离要求和测试追踪。
- 明确属性测试补充而不替代确定性样例与回归测试；幂等、round-trip 和后向兼容只有在 Spec 声明相应语义时才是必测属性。
- 要求属性测试失败保留可重放 seed、最小反例和 Property ID，并将重要反例固化为确定性回归测试。
- 提供工具无关的核心指导和按需加载的 Python/Hypothesis 参考，不向 MASE 运行时强制增加测试库依赖。
- 强化错误响应、分页、时区、并发和兼容性等条件属性，同时拒绝固定数量不变量、固定测试次数和全接口统一模板。

## Capabilities

### New Capabilities

- `risk-driven-property-testing`: 定义从 Spec 不变量到生成策略、属性/模型测试、最小反例和门禁证据的风险自适应工作方式。

### Modified Capabilities

无。

## Impact

- 影响 `project-rules.md`、`docs/MASE-framework.md`、`templates/contract.md`、开发/质量 Agent 和 TDD Skill。
- 新增属性测试按需参考及相应框架测试，更新发布清单以确保参考随 MASE 分发。
- PBT 继续由现有 `related_contract`/`api_contract` gate 执行，不新增全局硬门禁，不改变 Lite/Standard/Strict 的基础 Profile。
- 不强制 Hypothesis、Schemathesis 或其他语言专属依赖，不改变采用项目的产品 API。
