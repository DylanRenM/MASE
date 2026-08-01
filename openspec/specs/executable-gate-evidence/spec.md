# executable-gate-evidence Specification

## Purpose
TBD - created by archiving change strengthen-mase-evidence-governance. Update Purpose after archive.
## Requirements
### Requirement: 全项目结构与状态 Schema 校验
系统 SHALL 在执行项目检查时校验 `.mase.yaml` 以及所有非归档 change 的 `mase-state.yaml`，并使用随当前框架版本发布的 Schema 检查必需字段、枚举、条件约束和版本兼容性。单个文件损坏不得阻止其他 change 被检查，诊断 MUST 包含安全相对路径、错误位置和修复建议。

#### Scenario: 整体结构存在但状态文件损坏
- **WHEN** 项目目录结构完整但某个活动 change 的 YAML 无法解析
- **THEN** `mase check` 返回非零状态并报告该 change 的文件和行列位置，同时继续汇总其他 change

#### Scenario: Schema 不允许的复合技术栈
- **WHEN** 状态把多个工具链拼接为一个不受支持的主 stack
- **THEN** 系统拒绝将该状态视为合规，并建议迁移为主 stack 与 toolchains 列表

### Requirement: 风险驱动 GatePlan
系统 SHALL 根据项目 Profile、Capability 局部 Profile、标准风险触发器、产品属性和 change 影响面推导 GatePlan。状态声明 MUST 包含全部推导出的硬门禁；用户可以增加门禁但不得通过删除、降级或自由文本覆盖来绕过硬门禁。

#### Scenario: 不可信文件和鉴权触发局部严格门禁
- **WHEN** Standard 项目的某 Capability 同时涉及不可信文件、鉴权或租户数据边界
- **THEN** 系统将该 Capability 升级到相应最小 Profile，并要求安全评审、API 契约及适用攻击面测试

#### Scenario: 非 UI change 不误用产品 UI 属性
- **WHEN** 产品具有 UI 但本次 change 只修改发布签名且未改变 UI 行为
- **THEN** GatePlan 根据产品属性与 change 影响面分别决策，不因字段含义混淆而静默跳过或无条件重复 UI 门禁

### Requirement: 可复现自动门禁证据
自动门禁的 passed 证据 MUST 由受控 Gate Runner 在命令成功后原子生成，至少记录 gate、证据类型、结果、时间、耗时、退出码、脱敏命令、平台、Git commit、工作区指纹和日志引用。系统不得把仅含自由文本描述的记录当作新鲜自动证据。

#### Scenario: 自动测试成功后记录证据
- **WHEN** Gate Runner 执行配置的契约测试命令并以退出码零完成
- **THEN** 系统写入结构化 passed 证据并保存可定位的日志引用和代码状态指纹

#### Scenario: 命令或环境包含密钥
- **WHEN** 门禁命令或环境包含 API Key、Token、密码或签名凭据
- **THEN** 系统在日志和状态文件落盘前进行脱敏且不得泄露原值

### Requirement: 证据新鲜度与制品完整性
系统 SHALL 根据 gate 输入路径、当前代码状态、日志存在性和制品摘要判断证据为 fresh、stale、missing 或 invalid。stale 证据 MUST 不再满足硬门禁，且重新执行后才能恢复 passed。

#### Scenario: 相关实现变更使旧测试证据过期
- **WHEN** passed 证据生成后，属于该 gate 输入集合的实现或测试文件发生变化
- **THEN** 状态显示该证据 stale，并将 gate 恢复为待执行

#### Scenario: 发布制品被替换
- **WHEN** 状态记录的发布制品哈希与磁盘上的当前制品不一致
- **THEN** 制品门禁失败且报告预期与实际摘要

### Requirement: 结构化人工证据
无法自动化的原型确认、真机验收或风险接受 SHALL 使用 `kind: manual` 的结构化证据，记录确认来源、时间、验收对象和引用。人工证据 MUST 只满足明确允许人工完成的 gate。

#### Scenario: 用户确认参考原型
- **WHEN** UI change 的参考原型由用户确认
- **THEN** 系统记录独立于自动测试的人工证据，并能追溯到具体原型版本和确认时间

#### Scenario: 用人工文字冒充自动测试
- **WHEN** 自动契约门禁只有一条“测试已通过”的人工描述
- **THEN** 系统将该自动门禁判为缺少有效证据
