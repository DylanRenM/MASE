## ADDED Requirements

### Requirement: 完整课件与当前运行时一致
MASE SHALL 从当前规则、Profile、Schema 和已归档 Specs 验证 66 页培训课件的关键说法，并 SHALL 阻止旧门禁名称、旧提交节奏、固定 37 页或采用项目专属规则进入当前课件。

#### Scenario: 执行培训一致性验证
- **WHEN** 运行框架全量回归
- **THEN** 验证器检查当前六项原则、六步主线、影响链、上下文预算、证据索引、测试分层和发布附加流程均存在且无禁用旧说法

### Requirement: 培训资产不进入默认 Agent 上下文
扩展后的 YAML、PPTX、PDF 或预览图 SHALL 继续位于培训资产边界并默认从开发 Agent 上下文排除，除非当前任务明确修改或评审培训材料。

#### Scenario: 普通代码工作包规划上下文
- **WHEN** change 不涉及培训内容
- **THEN** 66 页课件和其生成产物不进入默认上下文计划或 Token 代理统计
