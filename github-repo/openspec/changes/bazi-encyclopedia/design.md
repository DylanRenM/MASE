> **注**: 本 design.md 保留旧结构，详细设计已按新规范拆分为以下文档：
> - [tech-feasibility.md](./tech-feasibility.md) — 技术可行性研究
> - [architecture.md](./architecture.md) — 架构设计
> - [detailed-design.md](./detailed-design.md) — 详细设计
> - 完整设计见 `docs/superpowers/specs/2026-07-01-bazi-encyclopedia-design.md`

## Context

用户拥有上百本八字命理电子书（EPUB/PDF/TXT/扫描件），期望将它们融合为一本按 [流派×专题] 二维结构组织的百科全书。本系统是一个本地运行的 Python 应用，全部模型本地部署以控制成本。

详见 `docs/superpowers/specs/2026-07-01-bazi-encyclopedia-design.md` 完整设计文档。

## Goals / Non-Goals

**Goals:**
- 支持 EPUB/PDF/TXT 电子书批量解析与智能分块
- 本地 Embedding 向量化 + Qdrant 语义索引
- 本地千问 LLM 做流派/专题分类
- DBSCAN 聚类粗筛 + LLM 精判两轮去重
- 按 [流派×专题] 编排百科全书条目
- 独立命例数据库，按专题分类，支持多维检索
- 双面板 Web 界面：书籍管理 + 百科浏览

**Non-Goals:**
- 不提供在线 SaaS 服务
- 不支持多用户
- 不自动下载书籍
- 不保证 100% 去重准确率（支持人工审校）

## Decisions

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 去重策略 | 纯向量 vs 纯LLM vs 混合 | 混合（向量粗筛+LLM精判） | 纯向量误判率高，纯LLM成本高；混合兼顾准确率和效率 |
| 聚类算法 | K-Means vs DBSCAN | DBSCAN | 无法预设知识点数量，DBSCAN 自动识别离群独特内容 |
| LLM 部署 | API vs 本地 | 本地 Qwen3-32B | 百本书Token量巨大，API 成本不可接受 |
| 向量数据库 | ChromaDB vs Qdrant vs Milvus | Qdrant | 轻量嵌入式、支持过滤查询、Python 原生 |
| 前端框架 | React vs 原生 | 单HTML+原生JS/CSS | 零部署，本地浏览器直接打开 |
| 百科存储 | 数据库 vs JSON | JSON文件 | 百科内容结构化、一次性生成、前端直接加载 |

## Risks / Trade-offs

- [扫描版PDF OCR准确率] → 使用 PaddleOCR + 千问后处理纠错，对古籍繁体和竖排需额外调优
- [流派标签模糊] → LLM 支持多标签输出（一个块可同时属于"旺衰派"和"格局派"）
- [去重误判] → 两轮去重 + 人工审校接口，保留原文溯源可追溯
- [LLM 输出幻觉] → 所有输出保留来源引用，用户可回溯原文验证

## Architecture

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
