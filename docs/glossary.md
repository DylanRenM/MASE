# MASE v2.4 术语表

| 术语 | 定义 |
|---|---|
| MASE 设计宗旨 | 让 Agentic Coding 高效交付正确、健壮、优化且易于维护的代码；以高效交付、需求正确、运行健壮、质量优化、整洁可维护五个结果验证 |
| 可手测等待收益 | `1 - T_new(dev_verified) / T_old(pre-hand-test)`；只表达早反馈等待改善，不把后续发布门禁冒充为已删除 |
| 观测中位数代理 | 样本少于 3 时用于方向性观察的低置信度数值；不得称为正式 p50/p90 |
| Profile（基础过程档位） | 产品或 Capability 的长期基础风险及机器可读过程策略 |
| Change Risk（变更风险） | 本次修改的治理重量 L1–L4；与基础过程档位、影响等级分别计算 |
| Lite | 低风险轻量流程；保留 API/P0 等适用硬底线 |
| Standard | UI、文件、依赖、并发、持久化等常规产品流程 |
| Strict | 鉴权、支付、监管、不可逆迁移等高风险流程 |
| Capability escalation | 单个能力因风险采用比项目基础 Profile 更严格的策略 |
| 影响链分析 | 从历史修改点向调用方、隐性依赖和系统边界追踪波及范围，并据此选择测试、评审与回滚约束 |
| L1 / L2 / L3 | 与 Profile 正交的影响等级：内部低影响、核心/不确定影响、契约/边界高影响 |
| `dev_verified`（开发已验证） | RED、实现与 development 聚焦门禁已完成；可本地手测，尚不代表可合并或发布 |
| `merge_verified`（合并已验证） | 适用契约、集成、构建和合并审查已完成；允许冻结候选 |
| `candidate_frozen`（候选已冻结） | 候选 ID 与输入摘要仍新鲜；输入变化即失效 |
| `release_ready`（发布已就绪） | 同一冻结候选的全量、安全、恢复与发布前门禁已通过；尚不代表线上行为已验证 |
| `required_at`（最晚要求时点） | gate 最晚必须在 development、merge、release 或 observe 哪一时点满足 |
| `subsumed`（被覆盖） | 更严格 gate 对同一候选、输入和等价环境完整覆盖目标测试后的可审计状态 |
| 隐性依赖通道 | 序列化、代理/切面、反射、配置/SPI、消息、定时任务、异步回调等无法只靠普通调用语句发现的关系 |
| 影响复扫 | 实现后将实际 diff 与设计前批准的修改点、调用方和边界重新比对；范围扩大会使证据过期 |
| 负向保证 | 不只证明新增行为完成，还通过变更边界、调用边差异、受保护测试和副作用预算证明旧根基未被未授权削弱 |
| 受保护测试 | 比较基线中已经存在、用于证明历史行为的测试；删除、跳过、弱化或实质修改需要明确审批 |
| 副作用预算 | 变更获准使用的文件、持久化、外部调用、消息等效果范围，以及明确禁止的效果 |
| 架构耦合告警 | 追踪三层仍未到系统边界或隐性关系不可控时产生的人工处置阻断 |
| Canonical source | 某类事实唯一允许人工维护的来源 |
| Generated adapter | 从核心规则生成的 IDE 入口文件，带 source hash |
| Evidence | 门禁命令、结果、时间和报告路径的结构化记录 |
| Context proxy | 文件数、字符数等上下文规模指标；不是实际 Token |
| P0 E2E | 核心用户价值端到端场景；业务旅程或影响关键闭环的交互变化时为 100% 硬门禁 |
| API contract | 公共接口的输入、输出和行为语义约束及测试 |
| Sandbox | E2E 前快照、执行中隔离、结束后恢复并验证的环境 |
| Archive snapshot | Release/archive 时从完成 change 生成的只读系统全貌 |
| 可选发布附加流程（Release Overlay） | 独立于基础过程档位的发布上下文；组合意图、权限、制品、目标、发布策略、状态、接口、恢复和观察 |
| Immutable artifact identity | 能唯一定位最终交付内容且不可漂移的 digest、签名坐标、版本/构建身份或等价证明 |
| `candidate_ready` | 开发候选已冻结且 final evidence fresh；尚未证明发布制品或目标 |
| `artifact_ready` | 精确制品的身份、来源、完整性和禁止内容 evidence fresh；不表示已经上线 |
| `target_ready` | 目标、配置、状态和恢复预检已满足，尚未证明真实线上行为 |
| `live_verified` | 目标提供精确制品且真实消费者/能力路径通过；观察窗口尚可未完成 |
| `observed` | `live_verified` 后声明的观察信号在窗口内满足停止条件 |
| `recovered` | 已执行恢复并以 fresh evidence 验证恢复后的身份、状态和消费者路径 |
| Release adapter | 由目标/运行时/接口条件选择的平台细节；不改变发布核心不变量 |
| `mase-state.yaml` | Change 的 Profile、stack、phase、risk、影响分析摘要/引用、可选发布附加流程、gates、evidence 唯一状态源 |
| `impact-analysis.yaml` | 影响修改点、调用方、隐性通道、边界、分级、测试、决策和回滚的结构化唯一事实源 |
| `.mase.yaml` | 项目级框架版本、基础 Profile 和技术栈元数据 |

历史文档中的“master 语义合并”属于 v1.3 术语；v2 只在归档时生成 snapshot。
