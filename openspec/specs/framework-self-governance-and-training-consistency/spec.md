# framework-self-governance-and-training-consistency Specification

## Purpose
TBD - created by archiving change close-mase-governance-and-safety-gaps. Update Purpose after archive.
## Requirements
### Requirement: User-visible changes require governed changes
The canonical MASE rules MUST require an OpenSpec change for changes affecting user-visible behavior or public contracts, and generated IDE adapters MUST consistently point to the regenerated project rule source.

#### Scenario: Adapters are regenerated
- **WHEN** canonical rules change
- **THEN** AGENTS, Claude, Copilot, and convention adapters share the expected source and body hashes

### Requirement: Project rule extensions survive framework update
`mase update` MUST distinguish generated MASE core rules from project-maintained extensions and MUST preserve extensions; ambiguous edits to generated or legacy undelimited rules MUST produce a backed-up conflict instead of silent overwrite.

#### Scenario: Project has a local rule extension
- **WHEN** framework core rules update in an adopted project
- **THEN** the core section updates and the local extension remains byte-for-byte present

#### Scenario: Legacy rules diverge ambiguously
- **WHEN** an adopted project's unmarked rule source differs from both installed and incoming canonical content
- **THEN** update reports conflict, writes no replacement, and retains a backup

### Requirement: Framework self-state is truthful
MASE's own `mase check`, `mase status`, and `openspec validate --all --strict` MUST pass on a clean working copy, and completed changes MUST have valid state or be archived consistently with repository policy.

#### Scenario: Governance validation runs
- **WHEN** the repository's governance commands are run after the repair
- **THEN** no completed change is falsely reported as gate-pending and no malformed delta change fails strict validation

### Requirement: Repository boundary is clean and reproducible
Strict boundary validation MUST exclude documented operating-system metadata consistently while rejecting unknown top-level content, nested products/repositories, build output, caches, and extracted historical material.

#### Scenario: Finder metadata exists
- **WHEN** `.DS_Store` exists but no prohibited framework content exists
- **THEN** the standard boundary command applies the documented metadata policy consistently

#### Scenario: Pytest runs in the repository
- **WHEN** tests execute with normal Python bytecode behavior
- **THEN** subsequent boundary validation is not made nondeterministic by generated cache files

### Requirement: Training source and deck match runtime vocabulary
The editable training source and generated PPTX MUST include the full release progression including `target_ready`, explain the compact teaching progression relative to all schema phases, and match the current framework version.

#### Scenario: Training deck verification runs
- **WHEN** the deck is rebuilt and verified from the editable YAML
- **THEN** required state vocabulary, version, editability, geometry, logo, and bounds checks all pass

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

### Requirement: 设计宗旨在框架表面一致
MASE 唯一规则源、README、现行框架/用户/设计文档、Agent 指引和当前培训课件 SHALL 对顶层设计宗旨保持语义一致，并 MUST NOT 把单纯生成更多代码、减少测试或跳过评审表述为框架目标。

#### Scenario: 同步核心规则后执行一致性检查
- **WHEN** 顶层设计宗旨被修改或重新表述
- **THEN** 自动验证确认核心文档、生成的 IDE adapter 和培训课件均包含一致的五个结果维度
