## MODIFIED Requirements

### Requirement: Presentation quality is verifiable
The deck SHALL contain exactly 66 slides, use dynamic page numbering, introduce no out-of-bounds shape, enforce content-length budgets, and render successfully to PDF for visual review. The 66 pages SHALL form a substantive concept-mechanism-case-exercise course rather than duplicated or mechanically split text.

#### Scenario: Automatic deck validation
- **WHEN** the verifier examines the generated PPTX
- **THEN** it reports the correct version, 66-page count, aspect ratio, page numbering, required chapter topics, source alignment, editable text count and no out-of-bounds shape

#### Scenario: Visual review
- **WHEN** the generated PPTX is exported to PDF and rendered as page thumbnails
- **THEN** the reviewer can inspect all 66 slides for clipping, overlap, contrast, excessive density and chapter continuity before completion

### Requirement: V1 structural and visual continuity
The V2.3 full deck SHALL preserve the V1 file byte-for-byte and SHALL reuse its shapes, typography, colors, section rhythm, and Measures logo as approved layout sources. Existing baseline pages MAY be reordered or supplemented to form the 66-page course; every new page SHALL identify a source layout and keep edited content editable.

#### Scenario: Existing learner opens the expanded deck
- **WHEN** a learner familiar with V1 moves through the 66-page V2.3 deck
- **THEN** the learner recognizes the same visual language while receiving additional mechanisms, examples and exercises

#### Scenario: Visual structure is compared automatically
- **WHEN** the verifier examines a baseline-derived or cloned page
- **THEN** it confirms the approved source layout, Measures logo, editable text and canvas bounds without requiring every output slide to occupy the original 37-page position

## ADDED Requirements

### Requirement: 66 页完整培训结构
课件 SHALL 以八章 66 页覆盖课程导入与六原则、框架全景与角色、档位风险门禁、六步开发主线、影响链、测试与证据、BUG/评审/发布、案例演练与速查。

#### Scenario: 学员完成完整课程
- **WHEN** 学员从封面阅读到总结
- **THEN** 每章至少包含机制解释或案例，并能完成从需求到候选、发布和观察的贯穿练习

### Requirement: 深讲内容融入对应章节
新增机制、案例和演练页 SHALL 与其概览或流程锚点交错编排，MUST NOT 以“先完整播放 37 页概览、再集中追加深讲页”的方式形成后置附录。

#### Scenario: 学员进入风险与门禁章节
- **WHEN** 课件介绍过程档位、能力局部升级和门禁计划
- **THEN** 决策树、三档对比、门禁生成、门禁状态、上下文预算和证据索引在进入六步主线前连续形成一个完整章节

#### Scenario: 学员沿六步主线学习
- **WHEN** 课件从需求、设计推进到构建和验证
- **THEN** Proposal 退出条件、风险案例、研究停止、契约、测试设计、影响链、TDD、候选冻结和证据机制分别出现在对应步骤附近

#### Scenario: 学员完成课程
- **WHEN** 课件讲到提交发布、恢复和分组演练
- **THEN** 发布恢复紧跟提交发布，演练位于课程总结之前，不存在“概览完成后进入机制与案例”的中途结课页

### Requirement: 效率治理进入培训
课件 SHALL 解释工作包上下文、证据摘要、Capability 精确选测、测试重复诊断和最终候选全量回归之间的边界，且不得把减少重复执行描述为降低质量门禁。

#### Scenario: 学员比较微循环和最终验证
- **WHEN** 课件展示同一 change 的测试时间线
- **THEN** 学员看到相关测试在微循环运行、能力门禁在范围稳定后运行、全量回归只绑定最终冻结候选
