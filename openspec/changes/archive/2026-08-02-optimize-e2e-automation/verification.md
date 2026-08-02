# Verification summary — 2026-07-30

## Framework verification

- OpenSpec strict validation: passed.
- Repository boundary/governance/manifest/GatePlan/evidence/reporter/distribution focused suite: 76 passed.
- Canonical framework regression: 190 Python tests passed; 15 Node/Vitest tests passed.
- `python3 scripts/audit_repository_boundary.py`: clean.
- `framework_contract` red tests first reproduced the missing state field and acceptance of a sibling-source interface; Schema/model/template implementation now preserves the installed CLI contract and rejects that source-coupled interface.
- Training source and the editable V2.3 deck now teach the same repository boundary: product-owned adapters, installed CLI/versioned Schema consumption, `framework_contract`, and clean-room temporary adopter verification. Chinese-facing terminology is normalized to “六步开发主线”、“三种过程档位”和“可选发布附加流程”; Lite/Standard/Strict are retained only as first-definition CLI mappings.
- The deck front-loads six development principles and their human/AI/automation responsibilities. Agent 2 now owns acceptance-scenario and test-design traceability while executable cases remain separate from Specs; Agent 3 explicitly uses risk- and contract-driven design. Later former-concept slides now explain evidence freshness and Spec-to-Test-to-Gate traceability, and the completion slide is Chinese-first.
- Slide 4 uses an intentional six-card editable layout so every principle has its own number, title and explanation. GatePlan/Gate Runner are explained as 门禁计划/门禁运行器; `mase gate freeze` retains its executable spelling with a Chinese behavioral explanation. Slides 21, 30 and 31 use meaningful Chinese labels instead of numeric circles or unexplained seed/shrink/Web/Sandbox terms. Code review uses problem-driven re-review rather than mandatory rounds.

## Clean-room adopter contract verification

- Temporary-project tests validate `mase-test-manifest/v1`, safe relative selectors, unique IDs, P0 requirements and stable manifest digests.
- Generated temporary adopters verify exact Capability/path selection, unmapped-UI `conservative_all_tier` fallback and non-UI no-fallback behavior through framework APIs.
- GatePlan and Gate Runner tests verify `{selected_tests}` expansion, ordered selected-test signatures, manifest-driven invalidation and projects without a manifest retaining static gate behavior.
- Reporter tests exercise the public `mase-test-diagnostic/v1` contract, including retry/flaky, artifacts, environment classification and unknown fallback, without invoking a product repository.
- Repository-boundary tests reject named adopter work in the active framework change. Framework verification does not read, modify or execute any adjacent product project.

## Compatibility, metrics and rollback

- Projects without `.mase/tests.yaml` retain canonical static `tests`; gates without `test_tiers` retain their old command behavior.
- Dynamic evidence binds ordered test IDs, selectors and manifest digest; retry pass stays flaky and missing diagnostics fall back to unknown.
- Metrics report actual evidence for first-pass rate, flaky rate, duration, Capability journey coverage and classified failures. Manual regression time is unavailable unless both duration and source are supplied; no proxy is invented.
- Rollback restores the prior static gate command. The manifest, diagnostic JSON and fixture metadata are additive and do not migrate product data.

## Remaining manual gate

The explicit manual `code_review` gate remains pending. Candidate freeze and Gate Runner final regression must follow that review; direct framework regressions above are test evidence, not fabricated final-gate evidence.
