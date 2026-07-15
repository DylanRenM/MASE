## ADDED Requirements

### Requirement: Dual-panel layout
The system SHALL provide a single-page HTML interface with two collapsible panels: a book management panel on the left and an encyclopedia browser panel on the right.

#### Scenario: Default layout
- **WHEN** user opens the application
- **THEN** both panels are visible in a responsive two-column layout

### Requirement: Book management panel
The left panel SHALL display a list of all imported books with status indicators (✅merged / ⏳pending / 🔄processing / ❌failed) and action buttons for each book.

#### Scenario: Add a new book
- **WHEN** user clicks "[+ 添加书籍]"
- **THEN** a file picker opens supporting EPUB, PDF, and TXT formats for single or batch import

#### Scenario: Start merging a pending book
- **WHEN** user clicks "[开始合并]" on a pending book
- **THEN** the merge pipeline starts with real-time stage progress displayed

#### Scenario: Re-merge a completed book
- **WHEN** user clicks "[重新合并]" on a merged book
- **THEN** the book is re-processed through the full pipeline

### Requirement: Encyclopedia browser panel
The right panel SHALL display a collapsible tree view of the encyclopedia structure on the left side and rendered content on the right side.

#### Scenario: Browse by genre and topic
- **WHEN** user clicks a流派 node in the tree
- **THEN** sub-topic nodes expand; clicking a topic displays the corresponding entry content

#### Scenario: Search the encyclopedia
- **WHEN** user types in the search box above the tree
- **THEN** matching entries are filtered in real-time

#### Scenario: Case database view
- **WHEN** user navigates to the命例数据库 section
- **THEN** cases are displayed with multi-dimensional filter controls (topic, genre, 八字 features)

### Requirement: Real-time merge progress display
When a book is being merged, the system SHALL show the current pipeline stage and progress percentage in the book management panel.

#### Scenario: Progress during merge
- **WHEN** a book is in stage 2 (向量化+分类) at 45% completion
- **THEN** the book card shows 🔄 合并中 with "向量化+分类 45%" label

### Requirement: Zero-dependency deployment
The web UI SHALL be a single HTML file with embedded CSS and JavaScript, requiring no build step or external CDN dependencies.

#### Scenario: Open in browser
- **WHEN** user opens index.html in any modern browser
- **THEN** the full interface renders correctly without internet access
