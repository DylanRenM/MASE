## ADDED Requirements

### Requirement: 形式化人工审查按 Change Risk 路由
L1/L2 SHALL NOT 要求形式化 manual evidence；L3 SHALL 选择一次独立综合审查；L4 SHALL 仅按命中的安全、数据恢复和发布批准风险选择对应人工 gate。

#### Scenario: L2 自动化修复
- **WHEN** Change Risk 为 L2 且未命中人工硬触发
- **THEN** GatePlan 不要求 code_review 或 independent_review 的形式化人工证据

#### Scenario: 实现者自查
- **WHEN** 实现 Agent 提交自己的 review 记录
- **THEN** 记录只能标记 self review，不能满足 independent manual gate
