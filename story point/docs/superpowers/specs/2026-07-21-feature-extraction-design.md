# 设计文档：文本Embedding → 特征提取+向量检索 方案迁移

> 关联项目：StoryPoint Estimator AI v1.0 | 2026-07-21

## 1. 动机

当前方案：用户故事标题+描述 → Embedding API → 1024维语义向量 → FAISS余弦相似度检索。

问题：
- Embedding向量不可解释（1024个浮点数无法映射到具体复杂度维度）
- 需要独立的Embedding服务（硅基流动），增加运维成本
- 无法向用户展示"为什么相似"的可解释理由

新方案：用户故事 → LLM特征提取 → 10维可解释特征向量 → FAISS相似度检索。

## 2. 架构变更

```
旧：title+desc → Embedding API → 1024d vector → FAISS → topK → LLM report
新：title+desc → Feature Extractor(LLM) → 10d vector → FAISS → topK → LLM report + 复杂度表格
```

### 2.1 模块变更清单

| 模块 | 操作 | 说明 |
|------|------|------|
| `core/feature_encoder.py` | **新增** | FeatureEncoder：特征JSON→10维归一化向量 |
| `utils/feature_extractor.py` | **新增** | FeatureExtractor：调用LLM提取复杂度特征 |
| `core/embedding.py` | **废弃** | EmbeddingClient不再使用，保留文件供回退 |
| `core/estimator.py` | **修改** | 移除文本向量化逻辑，仅保留相似度计算函数 |
| `core/reporter.py` | **修改** | Prompt增加复杂度特征上下文，输出增加features字段 |
| `services/baseline_service.py` | **修改** | EmbeddingClient → FeatureExtractor + FeatureEncoder |
| `services/estimate_service.py` | **修改** | 同上 |
| `app.py` | **修改** | 移除EmbeddingClient初始化，新增FeatureExtractor |
| `config.py` | **修改** | 移除EmbeddingConfig，新增FeatureExtractionConfig |
| `.env` | **修改** | 移除EMBEDDING_*，新增FEATURE_EXTRACTION_* |
| `db/vector_store.py` | **修改** | 默认维度1024→10 |

### 2.2 新增模块设计

#### FeatureEncoder（core/feature_encoder.py）

```python
class FeatureEncoder:
    """将特征JSON编码为10维归一化数值向量。"""
    
    def encode(self, features: dict) -> np.ndarray:
        # frontend_pages:  0-3 → /3
        # backend_interfaces: 0-3 → /3  
        # db_change/external_dependency/async_processing/
        #   transaction_required/permission_control/
        #   data_migration/cache_design: "是"/"否" → 1/0
        # business_branches: 1-5+ → (v-1)/4
        
    def encode_batch(self, features_list: list[dict]) -> np.ndarray:
        # (N, 10) 向量矩阵
```

归一化规则：
- `frontend_pages`: value/3（范围0-3）
- `backend_interfaces`: value/3（范围0-3）
- `business_branches`: (value-1)/4（范围1-5，5+视为5）
- 其余7个布尔字段: "是"→1.0, "否"→0.0

#### FeatureExtractor（utils/feature_extractor.py）

```python
class FeatureExtractor:
    """调用LLM提取用户故事的复杂度特征。"""
    
    def __init__(self, base_url, api_key, model, max_retries=3)
    def extract(self, title, description) -> dict:
        # 返回10个特征字段的dict
    def extract_batch(self, stories: list[dict]) -> list[dict]:
        # 批量提取
```

LLM Prompt：按照用户提供的特征提取Prompt模板，强制输出JSON格式。重试3次（含JSON解析失败的重试）。

### 2.3 Prompt 模板设计

与用户提供的Prompt模板一致，接收 `{story_title}` 和 `{story_description}` 占位符，输出10维特征JSON。

## 3. 数据流变更

### 上传入库流程

```
Excel → parse → validate → FeatureExtractor.extract_batch(rows)
  → FeatureEncoder.encode_batch(features) → 10d vectors
  → DB write + FAISS build
```

### 估算流程

```
title+desc → FeatureExtractor.extract(title, desc) → features dict
  → FeatureEncoder.encode(features) → 10d query vector
  → FAISS search → topK → weighted avg
  → ReportGenerator.generate(title, desc, topK, sims, w_avg, features)
  → report + complexity_table
```

### 报告增强

ReportGenerator.generate() 新增参数 `new_features: dict`，输出增加：
- `features`: 新需求的10维特征（前端展示复杂度分析表格用）

Prompt中增加复杂度特征上下文，帮助LLM做更精准的裁决。

## 4. config.py 变更

```python
# 移除 EmbeddingConfig，新增 FeatureExtractionConfig
@dataclass
class FeatureExtractionConfig:
    base_url: str      # 特征提取LLM的base_url（默认与Chat共用）
    api_key: str       # 特征提取LLM的api_key（默认与Chat共用）
    model: str         # 特征提取模型（默认 deepseek-chat）

# AppConfig 移除 embedding_dimension，新增 vector_dimension
@dataclass  
class AppConfig:
    vector_dimension: int = 10  # 特征向量维度
```

## 5. 兼容性

- `core/embedding.py` 保留文件（加注释标记为废弃），不修改其代码
- FAISS索引不兼容（维度1024→10），数据库重建
- 历史数据：旧history记录保留，report_json中的top_matches.similarity语义不变
