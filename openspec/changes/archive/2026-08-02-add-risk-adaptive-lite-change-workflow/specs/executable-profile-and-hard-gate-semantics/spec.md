## ADDED Requirements

### Requirement: 旧 UI 布尔字段保守迁移
对于只声明 `ui_changed: true` 的旧状态，MASE MUST 在没有更精细分类前保守按 journey 处理，并 SHALL 提供迁移诊断而不静默降低 P0。

#### Scenario: 旧 change 仍可读取
- **WHEN** 2.3 状态包含 has_ui true 和 ui_changed true
- **THEN** 2.4 GatePlan 保持 P0 适用，并提示补充 ui_change_kind
