<!-- MASE:CORE:START source_hash=a0fb9d893812f96867488c85041827aa868d7e2f8209fc7791143b9f11259d6a -->
# MASE v2 核心工程规则

> 唯一人工维护规则源。IDE 适配文件由工具生成；详细规范按任务读取，禁止全量预加载。

## 过程 Profile

- `lite`：低风险本地工具、MVP、小范围变更。
- `standard`：UI、文件解析、外部依赖、并发或持久化项目。
- `strict`：鉴权、支付、医疗、金融、监管或不可逆迁移。
- Capability 遇到不可信输入、归档解析、并发、鉴权、密钥或迁移时只能升级门禁，不能降级。

Profile 的机器定义见 `profiles/*.yaml`，标准风险触发器见 `profiles/risks.yaml`；change 的唯一状态源是 `mase-state.yaml`。主 `stack` 只允许 generic/python/swift，其他技术写入 `toolchains`。

## 不可违反的规则

### R01 需求确认

影响用户行为时先确认可验收需求；有 UI 时原型确认后开发。纯重构、修 Bug 和无 UI 变更不强制制作原型。

### R02 风险先行

仅对外部依赖、未知工具链和高风险边界做技术预研与可重跑 POC；已验证事实引用证据，不重复调研。

### R03 契约边界

API/公共协议的输入、输出和行为语义必须有契约测试。模块和函数契约由业务不变量或高风险触发，不做无差别三层契约。

复杂输入空间、解析/序列化、数值边界、状态机、不可信输入、并发不变量或兼容性变更命中时，评估属性测试或模型测试；它们补充确定性样例与回归测试，不得替代 Spec 或凭空赋予接口幂等、Round-trip、默认值等语义。失败必须保留可重放的最小反例。

### R04 分级 TDD

先写失败测试再实现。微循环运行相关 unit/contract；Capability 边界运行独立的 integration、评审和攻击面扫描；功能、测试与人工确认稳定后冻结最终候选，再对该候选运行一次全量测试与适用 E2E。失败修复或候选输入变化才重跑 final，不在 Build 中提前刷全量门禁。

### R05 硬门禁

已触发的 API 契约必须 100% 通过；只有产品有 UI 且本 change 修改 UI 时才触发 P0 E2E；Sandbox 恢复不一致时阻断。硬门禁不得删除、跳过或普通基线化。自动门禁的 passed 只能由 Gate Runner 产生，并随规范化输入、日志、制品或候选变化转为 stale/invalid；人工证据只能满足 `.mase/gates.yaml` 明确声明 `mode: manual` 的 gate，并绑定输入、范围、候选和发布上下文。门禁阶段、命令和基础输入以 `.mase/gates.yaml` 为唯一执行定义，动态测试分层与选择器以 `.mase/tests.yaml` 为唯一清单；只有完整执行签名 fresh 时允许复用，跨 gate 覆盖必须显式声明。

浏览器测试必须分为 UI contract、P0 journey 与 P1 regression：只加载页面、检查元素/布局或 mock 自有 API 的测试不是 P0；P0 必须穿透真实 UI、应用路由和受控持久化，只在不可控外部依赖边界使用 fake。`.mase/tests.yaml` 是 Capability 到测试集合的唯一清单；影响映射不确定时扩大适用 P0 范围，不得返回空集合绕过门禁。重试后通过必须记录 flaky，不能冒充首次通过。

Standard 的深度安全评审只由注册风险或显式项目 gate 触发。Strict 独立评审默认一轮；无异议即可确认，只有异议、候选输入变化或证据失效才追加评审。

### R06 根因分析

Bug 修改前必须形成可验证的根因假设，并先取得失败证据。

### R07 系统化修复

修复根因、补测试并扫描同类风险；不接受只遮蔽症状的临时补丁。

### R08 可回滚提交

按纵向工作包或 Capability 完成提交 Conventional Commit；不再按对话次数提交。

### R09 非破坏迁移

删除、回退、覆盖用户文件或框架迁移前必须先 dry-run 并备份。生成文件被修改、Schema 未知或内容无法验证时报告 conflict 并保留原文件，不静默覆盖。Brownfield 失败只有具备稳定签名、负责人、期限和处置 change 的非硬门禁记录才能进入基线。

### R10 变更治理

影响用户可见行为、公共契约、过程语义或分发内容的变更必须先创建 OpenSpec change，并以 proposal、specs、design 和 tasks 形成可验证闭环后实施。纯内部修复仍须保留失败证据、测试和根因，但无需为不改变需求契约的机械整理虚构新能力。

### R11 发布完整性

计划打包、发布、部署、线上验证或恢复时启用可选 `Release Overlay`，但不新增 Profile。候选、制品、目标、线上与观察证据分别产生 `candidate_ready`、`artifact_ready`、`target_ready`、`live_verified`、`observed`，不得把制品就绪或进程/HTTP 存活报告为发布成功。发布必须绑定不可变制品身份与来源，停服/切流/发布前完成可前置预检，按真实消费者路径验证，并在清理旧版本或备份前保留可验证恢复路径和观察窗口。清单不是 passed evidence；release gate 必须属于当前 Overlay/GatePlan，遵守 intent、authority 和阶段前序，且只有 Gate Runner 或声明为 `mode: manual` 的人工证据可满足。

### R12 框架仓库边界

MASE 根目录只允许过程框架运行时、唯一规则源、现行文档、MASE 培训源/受保护课件、测试和治理元数据。采用 MASE 的产品、产品数据、通用培训、研究演示、历史备份和生成缓存必须位于独立同级目录，不得以“默认排除”代替物理分离。提交前运行 `python3 scripts/audit_repository_boundary.py`；未知顶层目录、嵌套产品/仓库或生成残留必须阻断。

### R13 影响链先行

修改、删除、重命名、替换或绕行历史运行时代码、公共契约、配置、Schema、消息或持久化行为时，设计/实现前必须完成影响链分析，实现后必须按实际 diff 复扫。纯注释、格式或非机器消费文案只有取得无行为变化的分类证据才可豁免；监控、审计或程序消费的日志不豁免。

内部实现只有在签名、业务语义、异常、副作用、幂等、并发、事务、缓存、持久化、超时和重试均不变时才可只追踪直接调用方；契约或语义变化必须追踪到系统边界，并检查序列化、代理/切面、反射、配置/SPI、消息、定时任务和异步回调等隐性通道。深度三层仍未到边界时停止自动递归并触发人工耦合处置，不能宣称分析完整。

影响等级独立于 Profile：L1 运行受影响调用方单元测试和新旧差异契约；L2 增加适用集成、AI 差异说明与人工评审；L3 增加架构评审、全链路冒烟、灰度停止条件和回滚验证。第一方调用方超过 10 个、系统边界达到 3 个、三层未收敛或隐性依赖不可控时，AI 不得继续实施；必须由人工选择版本隔离、特性开关、拆分或终止。`impact-analysis.yaml` 是影响事实源，三份可读说明由它生成并随基线、diff、规则、Spec、契约、测试或范围变化而过期。

## Token 上下文规则

每个工作包默认只读取：当前 Spec、相关接口、相关测试、当前 diff、最近交接摘要。历史设计、培训、其他产品、归档和未命中的 Skill reference 默认排除。真实 Token 与字符数代理指标必须明确区分。

读取前优先运行 `mase context plan`；被排除文件只有在明确覆盖时才能进入计划并记录原因。Gate Runner 默认只返回状态、耗时、有限失败摘要和完整日志路径；只有人工调试明确使用 `--verbose` 时才流式回显完整输出。

## 按需规范索引

| 场景 | 读取 |
|---|---|
| 流程与 Profile | `docs/MASE-framework.md`、`profiles/*.yaml` |
| 编码 | `docs/coding-standards.md` |
| 设计评审 | `docs/design-principles.md` |
| 初始化/结构 | `docs/project-structure-spec.md` |
| UI E2E | `skills/webapp-testing/SKILL.md` 及命中的平台 reference |
| Bug | `skills/bug-fixer/SKILL.md` 及命中的问题路径 |
| 打包、发布、部署、线上验证、故障恢复 | `skills/release-software/SKILL.md` 及 Release Overlay 命中的 adapter reference |

`framework-manifest.yaml` 定义发布资源、生成目标和默认上下文排除目录。
<!-- MASE:CORE:END -->

<!-- MASE:PROJECT-EXTENSIONS:START -->
<!-- 在此维护采用项目自己的附加规则；mase update 会原样保留本区块。 -->
<!-- MASE:PROJECT-EXTENSIONS:END -->
