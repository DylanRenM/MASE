## ADDED Requirements

### Requirement: Generate embedding vectors for all blocks
The system SHALL generate 768-dimensional embedding vectors for all text blocks using the bge-large-zh-v1.5 model running locally.

#### Scenario: Batch vectorization
- **WHEN** a book is parsed into N text blocks
- **THEN** each block receives a 768-dim vector computed by the local embedding model

### Requirement: Store vectors in Qdrant with metadata
The system SHALL store vectors in a local Qdrant collection with payload containing book_id, genre_tags, topic_tags, content_type, chapter, and block_text.

#### Scenario: Vector with metadata stored
- **WHEN** a block is vectorized
- **THEN** the vector and its full metadata payload are persisted in the bazi_knowledge Qdrant collection

### Requirement: LLM-based content classification
The system SHALL classify each text block using the local Qwen LLM, assigning multi-label genre tags (旺衰派/格局派/盲派/神煞/调候/病药/阴阳/综合), multi-label topic tags (婚姻/健康/寿命/六亲/财运/事业/学业/性格/用神/大运/流年/基础理论), and content type (theory/case_study/mixed).

#### Scenario: Classify theory content
- **WHEN** a block discusses八字 theoretical concepts
- **THEN** LLM assigns genre tag(s), topic tag(s), and content_type "theory"

#### Scenario: Classify case study content
- **WHEN** a block describes a specific命例 with birth date and analysis
- **THEN** LLM assigns relevant tags and content_type "case_study" with person description

#### Scenario: Multi-tag assignment
- **WHEN** a block discusses婚姻 topic from both旺衰派 and调候 perspectives
- **THEN** LLM assigns both genre tags and the relevant topic tag

### Requirement: Batch processing with progress tracking
The system SHALL process classification in batches and report real-time progress through the pipeline log.

#### Scenario: Progress during classification
- **WHEN** 50000 blocks need classification
- **THEN** system reports progress percentage and estimated time remaining through the pipeline log
