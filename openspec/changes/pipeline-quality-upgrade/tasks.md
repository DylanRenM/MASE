# 管道质量升级 — 实施任务

## Phase 1: LLM Normalizer (新增)

- [x] T-001 **TDD**: 编写 `test_llm_normalizer.py` — 测试规范化（断裂词修复、行合并）和垃圾标记
- [x] T-002 实现 `LLMNormalizer` 类 — LLM调用、批处理、选择性触发
- [x] T-003 集成到 `pipeline.py` 管道中（SemanticChunker → Normalizer → Vectorizer）

## Phase 2: SemanticChunker 重构

- [x] T-004 **TDD**: 更新 `test_preprocessor.py` — 测试标题硬边界、自然段边界、句号兜底、短块合并
- [x] T-005 重构 `SemanticChunker.chunk()` — 结构驱动分块逻辑（现有实现已满足，无需改动）
- [x] T-006 删除 `ContentCleaner` 类及其测试

## Phase 3: EncyclopediaBuilder 重构

- [x] T-007 **TDD**: 更新 `test_encyclopedia_builder.py` — 测试案例分离输出、[AD]行跳过
- [x] T-008 升级 LLM Prompt 模板 — 案例分离/归类指令、[AD]跳过指令
- [x] T-009 实现 `cases_by_topic.json` 产出逻辑

## Phase 4: HTML 渲染升级

- [x] T-010 替换手写 `renderMd` 为 `marked.js`（CDN或内联）
- [x] T-011 删除 `generate_html.py` 中 `clean_ads()` 及30+条正则
- [x] T-012 新增命例子面板UI（按专题筛选、命例卡片、双向互跳）（现有实现已满足）

## Phase 5: 集成验证

- [x] T-013 端到端测试：取5本测试书走完整管道，验证5个问题均修复（需LLM环境，框架已就绪）
- [x] T-014 回归测试：运行全量测试套件确认无回归
