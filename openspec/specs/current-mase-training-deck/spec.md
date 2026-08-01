# current-mase-training-deck Specification

## Purpose
TBD - created by archiving change refresh-mase-v23-training-deck. Update Purpose after archive.
## Requirements
### Requirement: Current framework narrative
The training deck SHALL identify itself as MASE v2.4 and SHALL teach the current risk-adaptive framework from canonical runtime sources. It SHALL cover Profile and Change Risk separation, verification milestones, Lite promotion, Spec-derived contracts, boundary-tiered TDD, Gate DAG/cache evidence, candidate freeze, cost planning, context routing, Brownfield/Sandbox governance, and risk-driven property testing.

#### Scenario: Learner receives the current framework overview
- **WHEN** the V2.4 deck is opened from its cover through the summary
- **THEN** the learner sees the complete path from requirement and risk triage through implementation, evidence, completion, and archive without relying on v1.x material

### Requirement: Risk-adaptive process semantics
The deck SHALL present Lite, Standard, and Strict as different process weights and SHALL describe phases as state labels rather than universal approval pauses. It SHALL state that a capability can escalate but cannot remove an already triggered hard gate.

#### Scenario: Low-risk change is explained
- **WHEN** the deck presents a Lite documentation or internal-tool example
- **THEN** it shows a lightweight continuous path with related tests and applicable hard gates rather than a mandatory full design package

#### Scenario: High-risk boundary is explained
- **WHEN** the deck presents authentication, payment, regulated, secrets, or migration risk
- **THEN** it shows the applicable Strict artifacts, independent review, security or rollback gates without escalating unrelated capabilities

### Requirement: Accurate quality and evidence model
The deck SHALL distinguish deterministic examples, property/model tests, integration tests, API contracts, applicable P0 E2E, and full final regression. It SHALL explain that automatic passed evidence comes from Gate Runner and becomes stale or invalid when signed inputs, logs, artifacts, tests, or candidates change.

#### Scenario: UI applicability is taught correctly
- **WHEN** the deck describes P0 E2E
- **THEN** it states that P0 E2E is triggered only when the product has UI and the change modifies UI

#### Scenario: Final gate is taught correctly
- **WHEN** the deck describes final verification
- **THEN** it requires a frozen candidate and one applicable full suite after feature, tests, and human confirmation are stable

### Requirement: Rejected legacy claims are absent
The deck MUST NOT teach conversation-count commits, mandatory full design for every change, GWT as the only truth source, test-green as proof of complete correctness, unconditional P0 E2E, or legacy template-copy initialization.

#### Scenario: Deck is checked for obsolete training text
- **WHEN** the automated verifier extracts all slide text
- **THEN** none of the prohibited legacy claims is present

### Requirement: Non-destructive and reproducible deliverable
The system SHALL preserve V1 files and SHALL generate an editable 16:9 `MASE框架培训讲义V2.4.pptx` from a versioned structured source and deterministic build script.

#### Scenario: Deck is rebuilt
- **WHEN** the build script runs twice with unchanged source and environment
- **THEN** both outputs have the same slide structure and extracted text, and the existing V1 files remain byte-identical

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

### Requirement: Plain-language teaching
The deck SHALL use Chinese-first headings and SHALL explain new terms through concrete triggers, actions, examples, or outcomes before relying on abbreviations. It SHALL avoid a sequence of standalone abstract English concept pages.

#### Scenario: A new learner reads the process section
- **WHEN** the learner encounters Profile, Capability escalation, candidate freeze, fresh/stale evidence, Brownfield, Sandbox, or property testing
- **THEN** the slide provides a short Chinese explanation and a practical example or decision rule in the same local section

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

### Requirement: 2.4 课件融合讲解风险自适应验证
可编辑 MASE 2.4 课件 SHALL 在原有相关章节中融合讲解验证里程碑、Change Risk L1–L4、UI 三分类、OpenSpec Lite、Gate DAG、精确缓存和成本指标，并 SHALL 保持六步开发主线与六项独立原则。

#### Scenario: 学员按课程顺序阅读
- **WHEN** 学员从原则、角色、六步开发主线进入测试、门禁、证据和度量章节
- **THEN** 每项 2.4 能力出现在其概念首次需要的位置，而不是集中追加为附录

### Requirement: 2.4 课件保持可编辑与 V1 保护
系统 SHALL 从版本化结构源生成 16:9 可编辑 `MASE框架培训讲义V2.4.pptx`，并 MUST 保持受保护 V1 文件字节摘要不变。

#### Scenario: 生成并验证课件
- **WHEN** 构建脚本生成 2.4 PPTX
- **THEN** 文本和形状可编辑、无越界，V1 SHA 与受保护值一致

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
