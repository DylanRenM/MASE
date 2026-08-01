## ADDED Requirements

### Requirement: 设计宗旨在框架表面一致
MASE 唯一规则源、README、现行框架/用户/设计文档、Agent 指引和当前培训课件 SHALL 对顶层设计宗旨保持语义一致，并 MUST NOT 把单纯生成更多代码、减少测试或跳过评审表述为框架目标。

#### Scenario: 同步核心规则后执行一致性检查
- **WHEN** 顶层设计宗旨被修改或重新表述
- **THEN** 自动验证确认核心文档、生成的 IDE adapter 和培训课件均包含一致的五个结果维度
