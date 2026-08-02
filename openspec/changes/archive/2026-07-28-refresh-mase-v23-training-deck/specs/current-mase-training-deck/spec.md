## ADDED Requirements

### Requirement: Current framework narrative
The training deck SHALL identify itself as MASE v2.3 and SHALL teach the current risk-adaptive framework from canonical runtime sources. It SHALL cover Profile selection, capability escalation, Spec-derived contracts, boundary-tiered TDD, Gate Runner evidence, candidate freeze, context routing, Brownfield/Sandbox governance, and risk-driven property testing.

#### Scenario: Learner receives the current framework overview
- **WHEN** the V2.3 deck is opened from its cover through the summary
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
The system SHALL preserve V1 files and SHALL generate an editable 16:9 `MASE框架培训讲义V2.3.pptx` from a versioned structured source and deterministic build script.

#### Scenario: Deck is rebuilt
- **WHEN** the build script runs twice with unchanged source and environment
- **THEN** both outputs have the same slide structure and extracted text, and the existing V1 files remain byte-identical

### Requirement: Presentation quality is verifiable
The deck SHALL contain exactly 37 slides, retain the V1 page-number convention, introduce no out-of-bounds shape beyond the inherited V1 geometry, enforce content-length budgets, and render successfully to PDF for visual review.

#### Scenario: Automatic deck validation
- **WHEN** the verifier examines the generated PPTX
- **THEN** it reports the correct version, page count, aspect ratio, page numbering, required topics, source alignment, and no new out-of-bounds shape beyond the V1 template

#### Scenario: Visual review
- **WHEN** the generated PPTX is exported to PDF and rendered as page thumbnails
- **THEN** the reviewer can inspect all slides for clipping, overlap, contrast, and excessive density before completion

### Requirement: V1 structural and visual continuity
The V2.3 deck SHALL preserve the V1 37-slide teaching skeleton and SHALL inherit the V1 slide shapes, geometry, typography, colors, section rhythm, and the Measures logo at the top-right of every slide. The sequence SHALL remain concepts, four Agents, six process states, project/tool matrix, individual tools, quick start, and closing; current v2.3 rules SHALL be taught inside those familiar slots.

#### Scenario: Existing learner opens the revised deck
- **WHEN** a learner familiar with V1 moves through the V2.3 deck
- **THEN** the learner recognizes the same chapter transitions and page patterns while seeing corrected v2.3 content

#### Scenario: Visual structure is compared automatically
- **WHEN** the verifier compares V1 and V2.3 page by page
- **THEN** every slide has the same shape types and geometry, including the Measures logo picture at its original position and size, while all V2.3 text remains editable

### Requirement: Plain-language teaching
The deck SHALL use Chinese-first headings and SHALL explain new terms through concrete triggers, actions, examples, or outcomes before relying on abbreviations. It SHALL avoid a sequence of standalone abstract English concept pages.

#### Scenario: A new learner reads the process section
- **WHEN** the learner encounters Profile, Capability escalation, candidate freeze, fresh/stale evidence, Brownfield, Sandbox, or property testing
- **THEN** the slide provides a short Chinese explanation and a practical example or decision rule in the same local section
