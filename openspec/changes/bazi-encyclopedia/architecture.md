# 架构设计
> 详细架构见 `docs/superpowers/specs/2026-07-01-bazi-encyclopedia-design.md` 第 2 节

## 系统架构
```
books/ → [Parser] → blocks → [Vectorizer+Classifier] → Qdrant
                                                        ↓
                                            [Dedup Pipeline]
                                              DBSCAN → LLM
                                                        ↓
                                            [Encyclopedia Builder]
                                                        ↓
                                        encyclopedia.json + cases.json
                                                        ↓
                                                  Web UI (index.html)
```

## 组件模块
- book-parser: 电子书解析与分块
- content-vectorizer: 向量化与分类
- dedup-pipeline: 聚类去重
- encyclopedia-builder: 百科编排
- web-ui: 双面板 Web 界面
