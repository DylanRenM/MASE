## Context

MASE v2 把 Profile、change 状态和质量证据集中到了 `.mase.yaml` 与 `mase-state.yaml`，但检查链路仍是宽松读取：项目检查只验证少量目录存在，状态读取没有执行 JSON Schema，gate 和风险触发器是自由字符串，evidence 主要是人工填写的描述。磨耳朵的实战样本中已经同时存在合法单栈、Schema 未定义的复合栈、损坏 YAML、全任务完成但仍停在 verify、以及无法自动判断是否过期的通过证据。

Pilot 是典型 Brownfield：已经有部分 MASE v1.3 结构、十余个并行 OpenSpec change、较大历史测试集和已知失败。若直接套用“最终全量测试必须全绿”，团队只能在永久阻塞和虚假豁免之间选择，因此需要可审计的遗留基线。

## Goals / Non-Goals

**Goals:**

- 让 `mase check` 能判断项目、所有活动 change、Profile、风险、门禁和证据是否真实一致。
- 让自动门禁的 passed 状态来自可复现执行，并能识别代码、配置或制品变化造成的证据过期。
- 为遗留项目提供不降低硬门禁的渐进式质量基线。
- 提供可机器消费也适合人阅读的多 change portfolio 状态与友好诊断。
- 非破坏迁移现有 v2 项目和 v1.3 项目。

**Non-Goals:**

- 不把 MASE 变成 CI 托管平台或通用工作流编排器。
- 不自动修改产品业务代码或替团队决定风险豁免。
- 不要求所有门禁都能自动化；原型确认、真机验收等允许结构化人工证据。
- 不在本变更中迁移 Pilot；Pilot 采用由独立 change 执行。

## Decisions

### 1. Schema 校验成为所有状态命令的共同入口

引入统一的 `ProjectMetadata`、`ChangeState` 和 `EvidenceRecord` 解析层，使用发布包内的 JSON Schema 校验后再构造领域对象。`check`、`status`、迁移和报告不得各自宽松解析 YAML。采用标准 JSON Schema 校验库，避免继续维护不完整的手写 required-field 检查。

备选方案是保持 PyYAML 加手写判断；其依赖更少，但无法可靠处理枚举、条件字段和兼容演进，已经被实战反证。

### 2. 主技术栈与工具链分离

`.mase.yaml` 和 change state 保留一个受支持的主 `stack`（generic/python/swift），新增 `toolchains` 字符串列表描述 flutter、dart、kotlin、gradle 等平台。旧的复合 stack 由迁移器按已知标记拆分；无法确定主栈时只报告冲突，不猜测覆盖。

### 3. Profile、风险和 gate 形成可推导 GatePlan

增加标准风险触发器注册表，触发器声明最小 Profile、必需 gate 和适用影响面。GatePlan 由项目 Profile、Capability 局部升级、change 影响面和风险触发器合并产生；状态文件可以增加 gate，但不能删除推导出的硬门禁。未知风险触发器作为警告保留，安全相关未知项在 Strict change 中阻断。

产品属性与 change 影响面拆为 `product.has_ui` 和 `impact.ui_changed`，P0 E2E 是否触发由二者、Profile 和风险共同决定，不再由含义模糊的单一 `project_type.has_ui` 控制。

### 4. 自动证据由 Gate Runner 原子记录

新增等价于 `mase gate run <gate> -- <command>` 的执行入口。Runner 在子进程完成后原子写入结果，至少保存：gate、kind、result、时间、耗时、退出码、规范化命令、平台、Git commit、工作区指纹、日志路径和相关制品摘要。命令与环境变量在落盘前执行密钥脱敏。

人工证据使用 `kind: manual`，要求确认人/来源、时间、验收对象和引用路径；人工记录不能冒充自动测试。

证据是否新鲜由 gate 的输入路径集合、当前 commit 和工作区指纹判断。提交变化但未触及 gate 输入时允许复用；输入变化、日志缺失或制品摘要不一致时状态转为 stale，而不是继续显示 passed。

### 5. Brownfield 基线只吸收既有、可定位的非硬门禁失败

基线存放于 `.mase/baseline.yaml`，按测试命令、稳定测试 ID/失败签名记录首次观测、负责人、原因、到期日和处置 change。验证时比较当前失败集合：基线内未恶化的失败标记为 known；任何新增失败、签名变化或数量增长均阻断。

API contract、安全扫描、凭据泄露、数据破坏和 P0 E2E 等硬门禁不得被普通基线豁免。确需豁免时必须使用单独的有期限风险接受记录，并在 portfolio 中醒目标示。

### 6. Portfolio 是默认状态视图

不指定 change 时，`mase status` 返回所有非 archived change 的表格/JSON，展示 phase、任务、GatePlan、passed/pending/stale/failed、blocker、依赖和冲突。指定 change 时保留详细视图。零 change、多 change、文件缺失、YAML 损坏和 Schema 错误均返回稳定退出码与可操作消息，不输出 traceback。

终态仅为 complete/archived；verify/retro/release 是进行中阶段。全任务完成但仍有 pending gate 时显示 `ready_for_gate`，全门禁通过但未完成发布时显示 `ready_to_complete`。

### 7. 迁移保持预览、备份、冲突保留和幂等

`mase update --dry-run` 展示 metadata、状态、stack/toolchains、证据和适配文件迁移计划。实际更新前写入 `.mase-backup/<timestamp>/`；不合法或无法确定的内容保留原文件并报告 conflict。重复运行不得产生额外变化。

## Risks / Trade-offs

- [结构化证据增加状态文件复杂度] → 提供 Gate Runner 和生成式摘要，正常用户不手写自动证据。
- [工作区指纹计算影响大仓库性能] → 只哈希 GatePlan 声明的输入路径，并缓存文件元数据。
- [Brownfield 基线被当成永久豁免] → 强制负责人、到期日、处置 change，portfolio 展示债务年龄且硬门禁不可普通基线化。
- [标准风险注册表无法覆盖所有领域] → 允许扩展触发器，但未知项必须显式分类，不能静默忽略。
- [增加 JSON Schema 运行依赖] → 固定兼容版本并把离线安装包/锁定依赖纳入发布测试。
- [旧项目迁移出现大量 stale 证据] → 首次迁移只转换可证明字段，其余标记 pending/stale，不伪造 passed。

## Migration Plan

1. 先实现新 Schema、兼容读取器和诊断模型，不改变现有文件。
2. 增加 GatePlan、evidence runner、portfolio status 与 Brownfield 对比测试。
3. 发布迁移 dry-run，对 MASE 自身和磨耳朵运行并修复所有诊断。
4. 备份后迁移磨耳朵的复合 stack、损坏状态和旧 evidence；对自动证据重新执行门禁。
5. 更新框架版本、模板、规则、用户指南和安装包。
6. 保留一个版本的旧状态只读兼容；回滚时恢复 `.mase-backup` 并使用旧 CLI。

## Open Questions

- Gate 输入路径由 Profile 默认、change 显式声明还是测试收集器自动发现，首版采用哪种组合最稳定？
- 人工验收确认人的身份在纯本地仓库中使用用户名、Git identity 还是签名文件表达？
- 风险接受记录是否独立成 `risk-acceptance.yaml`，还是作为 state 的结构化子对象？
