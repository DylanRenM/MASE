# MASE v2 术语表

| 术语 | 定义 |
|---|---|
| Profile | 一组机器可读的产物、门禁、测试节奏和评审策略 |
| Lite | 低风险轻量流程；保留 API/P0 等适用硬底线 |
| Standard | UI、文件、依赖、并发、持久化等常规产品流程 |
| Strict | 鉴权、支付、监管、不可逆迁移等高风险流程 |
| Capability escalation | 单个能力因风险采用比项目基础 Profile 更严格的策略 |
| Canonical source | 某类事实唯一允许人工维护的来源 |
| Generated adapter | 从核心规则生成的 IDE 入口文件，带 source hash |
| Evidence | 门禁命令、结果、时间和报告路径的结构化记录 |
| Context proxy | 文件数、字符数等上下文规模指标；不是实际 Token |
| P0 E2E | 核心用户价值端到端场景；有 UI 时 100% 硬门禁 |
| API contract | 公共接口的输入、输出和行为语义约束及测试 |
| Sandbox | E2E 前快照、执行中隔离、结束后恢复并验证的环境 |
| Archive snapshot | Release/archive 时从完成 change 生成的只读系统全貌 |
| `mase-state.yaml` | Change 的 Profile、stack、phase、risk、gates、evidence 唯一状态源 |
| `.mase.yaml` | 项目级框架版本、基础 Profile 和技术栈元数据 |

历史文档中的“master 语义合并”属于 v1.3 术语；v2 只在归档时生成 snapshot。
