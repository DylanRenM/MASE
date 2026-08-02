## Context

MASE 当前以 Spec 为验收事实源，通过 `contract.md` 抽取 API/公共协议的前置条件、后置条件和不变式，再由分级 TDD 翻译为测试。现有契约模板没有表达输入域、oracle、属性适用性和反例重放；TDD Skill 也只笼统要求边界值。与此同时，MASE 是 generic/python/swift 多栈框架，不能把 Hypothesis 语法或某个 PBT 库变成全局依赖。

本变更是规范、模板、Agent 路由和 Skill 参考的横切增强，不改变 Gate Runner 状态模型，也不改变采用项目的产品行为。

## Goals / Non-Goals

**Goals:**

- 让 AI 能从 Spec 中识别适合属性/模型测试的不变量，而不是只生成固定样例。
- 让 `contract.md` 可追踪地表达属性、输入域、边界、oracle、隔离和测试映射。
- 保留最小反例及重放信息，并把重要反例转成确定性回归测试。
- 保持 MASE 风险自适应、多语言和现有契约硬门禁模型。

**Non-Goals:**

- 不用 PBT 替代样例测试、端到端测试或形式化证明。
- 不要求每个接口、每条契约或每个项目使用 PBT。
- 不规定不变量数量、`max_examples`、deadline 或特定测试库。
- 不把 POST、CRUD、默认字段或兼容策略强行赋予 Spec 未声明的语义。
- 不新增全局 `pbt` gate 或 MASE 运行时依赖。

## Decisions

### 1. PBT 是契约测试的风险路由，而不是新测试层

命中以下任一特征时，Agent 才评估属性/模型测试：组合输入空间大、解析/序列化、数值边界、集合/分页、状态机、不可信输入、并发不变量或版本兼容。最终测试仍由现有 `related_contract`、`api_contract` 或风险触发的 integration gate 执行。

选择这一方式而不是新增 `pbt` 硬门禁，是因为测试技术不等于质量目标；全局门禁会让简单 API 和非 Python 项目承担无收益成本。

### 2. 确定性样例与属性测试并存

Spec 的典型业务场景、精确错误格式和历史回归反例继续使用确定性样例。属性测试覆盖输入空间中的普遍规律；模型/状态机测试覆盖操作序列。每个属性必须有可判定 oracle，允许使用等式、集合关系、模型对照、round-trip 或 metamorphic relation。

选择互补而不是“PBT 替代样例”，是因为生成测试不能稳定表达所有产品示例，且失败定位后的反例需要成为长期、确定性的回归资产。

### 3. 契约模板增加结构化属性计划

每个适用属性记录：Property ID、来源 Spec/Scenario、适用边界、合法域、非法域、显式边界、oracle、隔离/清理、对应测试。错误响应与成功响应使用相同级别的契约描述。

幂等、round-trip、后向兼容、分页完整性、时区一致性和并发一致性作为“候选性质”，只有 Spec 或公共协议声明相应语义时才能进入契约，避免 AI 从技术习惯反向发明产品需求。

### 4. 反例证据复用现有 Gate Runner

PBT 命令必须让失败日志包含 Property ID、测试工具/版本、seed 或等价重放参数以及 shrink 后的最小反例。Gate Runner 已保存命令、版本环境和完整日志，因此不修改 `mase-state` 或 gates schema。若工具无法自动 shrink，测试必须提供等价的最小化或精简步骤。

重要反例修复前先作为确定性失败测试重放，修复后保留为回归测试；随机 seed 不能成为唯一回归手段。

### 5. 核心规范工具无关，工具细节按需加载

核心规则只使用 property/model/generator/oracle/counterexample 等通用概念。TDD Skill 在命中 Python PBT 时按需读取 Hypothesis 参考；其他栈采用项目已有工具或补充相应 reference。参考文件通过现有 `skills/test-driven-development/references/*.md` 打包规则分发。

## Risks / Trade-offs

- [生成测试增加执行时间或产生 flaky] → 优先放在纯函数/隔离适配器，显式控制数据规模、deadline 和外部 I/O，按 Profile 放入相关 gate。
- [状态型 API 污染数据库] → contract 中必须声明隔离/清理；复用 MASE Sandbox、事务回滚或每例独立命名空间。
- [AI 编造看似合理的性质] → 所有 Property ID 必须引用 Spec/Scenario；未声明的幂等和兼容语义不得推断。
- [最小反例含敏感数据] → 生成器不得使用生产数据，Gate Runner 继续执行日志脱敏与留存策略。
- [模板变重] → 属性计划只在适用时填写；简单契约明确标记“不适用及理由”，不要求伪造属性。

## Migration Plan

1. 先增加规范契约测试，证明当前模板和 Skill 尚未包含属性路由与反例要求。
2. 更新核心规则、框架文档、契约模板、Agent/Skill 路由和 Python 参考。
3. 同步生成式 IDE 适配文件并运行相关测试与全量框架测试。
4. 新项目自动获得新模板；既有项目在常规 MASE update 中按非破坏迁移规则处理冲突，不自动覆盖人工修改的 contract。

回滚仅需撤销本 change 的规范、模板和参考文件；不涉及用户数据或 Schema 迁移。

## Open Questions

无。其他语言的具体 PBT 参考在真实项目命中需求后按需增加，避免本 change 未经验证地引入工具建议。
