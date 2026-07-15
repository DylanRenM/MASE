## ADDED Requirements

### Requirement: Support multiple ebook formats
The system SHALL parse EPUB, PDF (text-based), TXT, and scanned PDF/image files to extract text content.

#### Scenario: Parse EPUB book
- **WHEN** user imports an EPUB file
- **THEN** system extracts all text content with chapter hierarchy preserved

#### Scenario: Parse text-based PDF
- **WHEN** user imports a text-based PDF
- **THEN** system extracts text content with page and section boundaries preserved

#### Scenario: Parse plain text file
- **WHEN** user imports a TXT file with UTF-8 or GBK encoding
- **THEN** system auto-detects encoding and extracts text content

#### Scenario: Parse scanned PDF via OCR
- **WHEN** user imports a scanned PDF or image-based file
- **THEN** system runs PaddleOCR to extract text with post-processing error correction

### Requirement: Intelligent text chunking
The system SHALL split parsed text into blocks of 300-500 characters, preserving semantic boundaries at paragraph and sentence level.

#### Scenario: Chunk by paragraph boundaries
- **WHEN** text contains natural paragraph breaks within 300-500 character windows
- **THEN** system splits at paragraph boundaries without cutting sentences

#### Scenario: Overlap between adjacent blocks
- **WHEN** two adjacent blocks are created
- **THEN** system adds a 50-character overlap window to prevent semantic boundary loss

### Requirement: Track source metadata per block
Each text block SHALL carry metadata including source book title, author, original chapter path, and a unique block ID.

#### Scenario: Block metadata preservation
- **WHEN** a text block is created from a book
- **THEN** the block contains source_book, author, chapter_path, and block_id fields

### Requirement: Incremental book addition
The system SHALL allow adding new books at any time without reprocessing already-merged books.

#### Scenario: Add a new book to existing library
- **WHEN** user adds a new book after some books have already been merged
- **THEN** only the new book goes through the full pipeline without affecting previously merged content
