## Why

当前管道输出的百科内容存在5个质量问题：广告残留、段落语义错误、案例未归类、语义分块不合理、Markdown渲染错误。根因是正则/规则驱动的方式面对上百本不同来源电子书时覆盖面不足，需要升级为LLM驱动的预处理与渲染。

## What Changes

- **删除** `ContentCleaner` 正则清洗层
- **新增** `LLMNormalizer` — 用千问LLM做文本规范化和垃圾标记
- **重构** `SemanticChunker` — 从字符数驱动改为结构驱动分块
- **重构** `EncyclopediaBuilder` — LLM Prompt加入案例分离/归类指令、跳过[AD]标记行
- **重构** HTML渲染 — 手写`renderMd`替换为`marked.js`，删除`clean_ads()`

详见 `docs/superpowers/specs/2026-07-03-pipeline-quality-upgrade-design.md`

## Capabilities

### New Capabilities
- `llm-normalizer`: LLM驱动的文本规范化和去广告标注

### Modified Capabilities
- `book-parser`: 重构SemanticChunker（结构驱动分块）、删除ContentCleaner
- `encyclopedia-builder`: LLM Prompt增强（案例分离+归类+跳过广告）
- `web-ui`: Markdown渲染升级为marked.js、删除clean_ads()
