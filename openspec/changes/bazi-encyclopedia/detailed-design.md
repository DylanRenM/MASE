# 详细设计
> 详细设计见 `docs/superpowers/specs/2026-07-01-bazi-encyclopedia-design.md` 第 3-5 节

## 四阶段管道
1. 批量解析与统一分块 (300-500字/块, 50字重叠)
2. 全量向量化 + LLM分类 (流派/专题/内容类型)
3. 聚类去重 (DBSCAN + LLM精判: duplicate/complementary/conflicting/distinct)
4. 百科全书编排 (核心观点/各家论述/流派分歧/经典命例/参见)

## 数据模型
- SQLite: books, pipeline_logs
- Qdrant: bazi_knowledge (768维向量 + payload)
- JSON: encyclopedia.json + cases.json

## API 接口
- POST /api/books/import
- GET /api/books
- POST /api/books/{id}/merge
- GET /api/books/{id}/progress
- GET /api/encyclopedia
- GET /api/cases
