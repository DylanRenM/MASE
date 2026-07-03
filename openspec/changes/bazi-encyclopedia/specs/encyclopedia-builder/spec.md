## ADDED Requirements

### Requirement: Generate encyclopedia entries by genre-topic matrix
The system SHALL organize all remaining knowledge blocks into a two-level hierarchy of [流派] → [专题], producing one encyclopedia entry per combination.

#### Scenario: Generate entry for旺衰派-婚姻
- **WHEN** the knowledge pool contains retained blocks tagged 旺衰派+婚姻
- **THEN** system generates a structured entry with sections: 核心观点, 各家论述, 流派分歧, 经典命例, 参见

### Requirement: Fuse complementary content
The system SHALL use the local Qwen LLM to fuse complementary blocks into a coherent "核心观点" section, synthesizing different angles into a unified exposition.

#### Scenario: Fuse multi-source content
- **WHEN** three blocks from different books provide complementary perspectives on the same topic
- **THEN** LLM synthesizes them into a single coherent exposition with source attributions

### Requirement: Preserve conflicting viewpoints
When conflicting blocks exist for a topic, the system SHALL preserve all viewpoints in a "流派分歧" section with source attribution for each position.

#### Scenario: Preserve流派 disagreements
- **WHEN** 旺衰派 and格局派 have opposing views on用神判断
- **THEN** both views are presented in the流派分歧 section with book and author citations

### Requirement: Build case study database
The system SHALL extract all case_study blocks into a separate case database, indexed by topic tags, genre tags, and八字 features for multi-dimensional filtering.

#### Scenario: Filter cases by topic
- **WHEN** user filters cases by topic "婚姻"
- **THEN** all命例 tagged with 婚姻 are displayed

#### Scenario: Filter cases by八字 features
- **WHEN** user searches for cases with specific八字 characteristics (e.g., 官杀混杂)
- **THEN** system returns matching命例

### Requirement: Cross-reference between entries
The system SHALL generate "参见" links between related entries across genres and topics based on content co-occurrence.

#### Scenario: Cross-reference generation
- **WHEN** an entry for调候-婚姻 is generated
- **THEN** the参见 section links to related entries like 格局派-婚姻 and 旺衰派-婚姻

### Requirement: Output to JSON format
The system SHALL output the encyclopedia and case database as structured JSON files for the web UI to consume.

#### Scenario: Encyclopedia JSON structure
- **WHEN** all entries are generated
- **THEN** output is a single encyclopedia.json with nested structure: {流派: {专题: {entry_content}}}
