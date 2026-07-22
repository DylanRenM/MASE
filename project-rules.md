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

### R04 分级 TDD

先写失败测试再实现。微循环运行相关 unit/contract；Capability 边界运行独立的 integration、评审和攻击面扫描；功能、测试与人工确认稳定后冻结最终候选，再对该候选运行一次全量测试与适用 E2E。失败修复或候选输入变化才重跑 final，不在 Build 中提前刷全量门禁。

### R05 硬门禁

已触发的 API 契约必须 100% 通过；只有产品有 UI 且本 change 修改 UI 时才触发 P0 E2E；Sandbox 恢复不一致时阻断。硬门禁不得删除或普通基线化。自动门禁的 passed 只能由 Gate Runner 产生，并随规范化输入、日志、制品或候选变化转为 stale/invalid；人工证据只能满足明确允许人工完成的 gate。门禁命令、输入与测试集合以 `.mase/gates.yaml` 为唯一执行定义；只有完整执行签名 fresh 时允许复用，跨 gate 覆盖必须显式声明。

Standard 的深度安全评审只由注册风险或显式项目 gate 触发。Strict 独立评审默认一轮；无异议即可确认，只有异议、候选输入变化或证据失效才追加评审。

### R06 根因分析

Bug 修改前必须形成可验证的根因假设，并先取得失败证据。

### R07 系统化修复

修复根因、补测试并扫描同类风险；不接受只遮蔽症状的临时补丁。

### R08 可回滚提交

按纵向工作包或 Capability 完成提交 Conventional Commit；不再按对话次数提交。

### R09 非破坏迁移

删除、回退、覆盖用户文件或框架迁移前必须先 dry-run 并备份。生成文件被修改、Schema 未知或内容无法验证时报告 conflict 并保留原文件，不静默覆盖。Brownfield 失败只有具备稳定签名、负责人、期限和处置 change 的非硬门禁记录才能进入基线。

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

`framework-manifest.yaml` 定义发布资源、生成目标和默认上下文排除目录。
