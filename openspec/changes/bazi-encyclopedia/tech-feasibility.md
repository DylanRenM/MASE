# 技术可行性研究
> **状态**: 待补充 | 原设计见 `docs/superpowers/specs/2026-07-01-bazi-encyclopedia-design.md`

本项目的技术可行性分析分散在原设计文档（`openspec/changes/bazi-encyclopedia/design.md`）和 Superpower 详细设计文档中。

核心选型已确认：
- Embedding: bge-large-zh-v1.5 (768维)
- 向量库: Qdrant
- LLM: Qwen3-32B (本地 Ollama/vLLM)
- 前端: 单HTML + 原生JS/CSS
- 后端: Python (FastAPI)
- OCR: PaddleOCR

详细 POC 验证记录待补充。
