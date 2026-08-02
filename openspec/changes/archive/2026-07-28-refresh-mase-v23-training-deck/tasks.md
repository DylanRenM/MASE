## 1. Baseline and failing evidence

- [x] 1.1 Record V1 deck checksum, slide count, extracted obsolete claims, and current visual structure
- [x] 1.2 Add automated deck contract tests and run them against the missing V2.3 output to observe a relevant RED

## 2. Versioned training source

- [x] 2.1 Create the 37-slide structured content source aligned with MASE v2.3 canonical rules
- [x] 2.2 Cover Profile/risk routing, Agents, state flow, contracts/TDD/gates, governance, examples, workshop, and summary
- [x] 2.3 Encode legacy-claim exclusions, source version, page numbering, and per-slide content budgets

## 3. Editable PPTX generation

- [x] 3.1 Implement reusable 16:9 slide layouts and brand-safe typography/color helpers
- [x] 3.2 Generate editable text and vector shapes without external network assets
- [x] 3.3 Generate `MASE框架培训讲义V2.3.pptx` without modifying V1 files

## 4. Automated and visual verification

- [x] 4.1 Implement the PPTX verifier for version, topics, forbidden claims, numbering, bounds, and source alignment
- [x] 4.2 Run focused tests and verifier until all deck contracts pass
- [x] 4.3 Export the deck to PDF, render all pages as thumbnails/contact sheets, and visually inspect clipping, overlap, contrast, and density
- [x] 4.4 Correct any visual findings and repeat automated and rendered verification

## 5. Governance and completion

- [x] 5.1 Add `mase-state.yaml`, run OpenSpec strict validation, and record applicable Gate Runner evidence
- [x] 5.2 Complete the implementation and pre-freeze diff review while preserving unrelated user files; run the full MASE suite as the candidate-bound final gate

## 6. V1-structured revision after training review

- [x] 6.1 Add failing contracts for V1 page-slot continuity, shape geometry parity, per-page Measures logo, and Chinese-first plain-language headings
- [x] 6.2 Rewrite the 37-slide source as a V1-template content map with v2.3-correct, example-led wording
- [x] 6.3 Replace the free-form renderer with a checksum-guarded V1 template text updater while preserving editability
- [x] 6.4 Rebuild and automatically verify version, current topics, forbidden claims, page structure, geometry, bounds, and V1 integrity
- [x] 6.5 Export all pages, visually inspect the revised deck against V1, and correct clipping, density, or unclear wording
- [x] 6.6 Refresh OpenSpec and Gate Runner evidence, freeze the revised candidate, and run the candidate-bound full regression
