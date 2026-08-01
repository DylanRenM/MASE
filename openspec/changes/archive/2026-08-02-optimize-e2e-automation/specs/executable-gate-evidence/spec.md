## MODIFIED Requirements

### Requirement: 可复现自动门禁证据
自动门禁的 passed 证据 MUST 由受控 Gate Runner 在命令成功后原子生成，至少记录 gate、证据类型、结果、时间、耗时、退出码、脱敏后的实际命令、平台、Git commit、工作区指纹、日志引用、实际测试集合摘要和选择原因。测试 adapter 提供诊断时，证据 MUST 同时绑定诊断摘要与制品；系统不得把仅含自由文本描述或未实际消费的测试选择当作新鲜自动证据。

#### Scenario: 自动测试成功后记录证据
- **WHEN** Gate Runner 执行配置的契约或 E2E 测试命令并以退出码零完成
- **THEN** 系统写入结构化 passed 证据并保存可定位日志、实际测试集合摘要、选择原因和代码状态指纹

#### Scenario: 命令或环境包含密钥
- **WHEN** 门禁命令、诊断或环境包含 API Key、Token、密码或签名凭据
- **THEN** 系统在日志、诊断和状态文件落盘前进行脱敏且不得泄露原值

#### Scenario: 重试后通过
- **WHEN** adapter 诊断显示首轮失败且最终通过
- **THEN** 自动证据保留 passed 的最终退出状态，同时记录 flaky 分类、attempts 和首轮失败，不将其汇总为首次通过

### Requirement: 证据新鲜度与制品完整性
系统 SHALL 根据 gate 输入路径、当前代码状态、实际测试集合与 manifest 摘要、日志存在性、诊断和制品摘要判断证据为 fresh、stale、missing 或 invalid。stale 证据 MUST 不再满足硬门禁，且重新执行后才能恢复 passed；声明了动态测试 tier 的证据缺少实际选择摘要时 MUST 判为 invalid。

#### Scenario: 相关实现变更使旧测试证据过期
- **WHEN** passed 证据生成后，属于该 gate 输入集合的实现、测试 manifest 或已选测试文件发生变化
- **THEN** 状态显示该证据 stale，并将 gate 恢复为待执行

#### Scenario: 发布制品被替换
- **WHEN** 状态记录的发布制品哈希与磁盘上的当前制品不一致
- **THEN** 制品门禁失败且报告预期与实际摘要

#### Scenario: 动态测试证据缺少选择摘要
- **WHEN** gate 声明动态 P0 tier 但历史 passed evidence 没有对应测试集合摘要
- **THEN** 系统将该证据判为 invalid，要求通过当前 Gate Runner 重跑
