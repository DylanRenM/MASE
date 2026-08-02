## ADDED Requirements

### Requirement: 课件前置呈现设计宗旨
MASE 2.4 可编辑课件 SHALL 在六项原则和六步开发主线之前明确说明“高效交付、需求正确、运行健壮、质量优化、整洁可维护”的顶层宗旨，并 SHALL 在课程总结中回收这五个结果维度。

#### Scenario: 学员开始学习 MASE
- **WHEN** 学员从开场进入框架全景和原则章节
- **THEN** 学员先理解 MASE 要交付的工程结果，再学习 Agent、流程和门禁

### Requirement: 课件说明可校准速度模型
课件 SHALL 在现有效率治理或度量章节展示可手测等待收益公式、MASE 本仓当前约 71% 的示例及其样本边界，并 MUST NOT 将该示例表述为所有项目的通用承诺。

#### Scenario: 学员评估自己项目的收益
- **WHEN** 学员阅读速度估算内容
- **THEN** 课件要求使用该项目自身的 development/merge/release evidence 重算，而不是直接套用 71%
