## ADDED Requirements

### Requirement: Profile 与 Change Risk 共同决定治理
MASE SHALL 让 Profile 表达产品或 Capability 的基础风险，让 Change Risk 表达本次修改的治理重量，并 SHALL 取二者、Impact Level 和硬触发要求的并集形成 GatePlan。

#### Scenario: Lite change 命中硬风险
- **WHEN** Lite Profile 的 change 命中不可逆迁移
- **THEN** 系统保持 Profile 记录可追溯，但按 L4 与 Strict 下限选择完整门禁
