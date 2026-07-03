"""项目配置模块"""

import os
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Config:
    """全局配置"""

    # 路径配置
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    db_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "bazi.db")
    qdrant_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "qdrant")
    encyclopedia_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "encyclopedia.json")
    cases_path: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "cases.json")
    ui_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent / "ui")

    # 模型配置
    # Embedding: 使用 Ollama 的 nomic-embed-text (768维) 或 bge-m3 (1024维)
    embedding_model: str = "nomic-embed-text"
    embedding_dim: int = 768
    embedding_backend: str = "ollama"  # "ollama" | "sentence_transformers"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.2:latest"
    llm_temperature: float = 0.1
    # 分类器: "llm" | "rule" (rule 基于关键词，快速)
    classifier_backend: str = "rule"
    # HuggingFace 镜像 (国内用户推荐使用 hf-mirror.com)
    hf_endpoint: str = field(default_factory=lambda: os.environ.get("HF_ENDPOINT", "https://hf-mirror.com"))

    # 分块配置
    chunk_min_size: int = 200
    chunk_max_size: int = 800
    chunk_overlap: int = 0  # 语义分块不再使用重叠

    # 聚类配置
    cluster_similarity_threshold: float = 0.85
    dbscan_eps: float = 0.12  # 更严格的余弦距离
    dbscan_min_samples: int = 2

    # Ollama 超时/重试
    classifier_timeout: float = 120.0
    classifier_max_retries: int = 3

    # LLM 兜底
    llm_fallback_enabled: bool = True

    # OCR 配置
    ocr_enabled: bool = True
    ocr_lang: str = "ch"

    # MarkItDown 配置
    markitdown_enabled: bool = True

    # Qdrant 配置
    qdrant_collection: str = "bazi_knowledge"

    def __post_init__(self):
        """确保目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.qdrant_path.mkdir(parents=True, exist_ok=True)


# 全局配置实例
config = Config()
