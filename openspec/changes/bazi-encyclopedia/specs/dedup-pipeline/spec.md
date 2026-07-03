## ADDED Requirements

### Requirement: Vector clustering within genre-topic groups
The system SHALL perform DBSCAN clustering on vectors within each [流派×专题] group, grouping blocks with cosine similarity >= 0.85 into knowledge clusters.

#### Scenario: Cluster similar content
- **WHEN** multiple books contain similar explanations of "旺衰派婚姻论断"
- **THEN** system groups those blocks into the same knowledge cluster

#### Scenario: Identify unique content as outliers
- **WHEN** a block has no similar counterparts (cosine similarity < 0.85 with all others)
- **THEN** DBSCAN marks it as noise/outlier, and the block is preserved as unique content

### Requirement: LLM fine-grained duplicate judgment
The system SHALL send each cluster with >= 2 blocks to the local Qwen LLM for fine-grained classification into four categories: duplicate, complementary, conflicting, or distinct.

#### Scenario: Detect duplicate content
- **WHEN** two blocks express the exact same knowledge point with different wording
- **THEN** LLM returns verdict "duplicate" with action "keep_one" and identifies the best version

#### Scenario: Detect complementary content
- **WHEN** two blocks address the same knowledge point from different angles
- **THEN** LLM returns verdict "complementary" with action "merge"

#### Scenario: Detect conflicting viewpoints
- **WHEN** two blocks express opposing views on the same topic (e.g., 旺衰派 vs 格局派 on 用神 selection)
- **THEN** LLM returns verdict "conflicting" with action "keep_all_with_note"

#### Scenario: Detect falsely clustered distinct content
- **WHEN** two blocks are clustered as similar but actually discuss different knowledge points
- **THEN** LLM returns verdict "distinct" with action "keep_all"

### Requirement: Dedup result processing
After LLM judgment, the system SHALL: keep the best version for duplicates, mark all complementary blocks for fusion, preserve conflicting blocks with divergence notes, and split distinct blocks into separate entries.

#### Scenario: Process duplicate cluster
- **WHEN** a cluster is judged as duplicate with a best version identified
- **THEN** only the best version is retained in the knowledge pool, others are discarded with source attribution recorded

#### Scenario: Process complementary cluster
- **WHEN** a cluster is judged as complementary
- **THEN** all blocks are retained and marked with a "merge_required" flag for the encyclopedia builder
