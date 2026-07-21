"""应用配置加载。

从环境变量加载 Embedding、Chat 和应用配置，支持供应商无关的灵活切换。
"""

import os
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    """Embedding 模型配置。"""
    base_url: str
    api_key: str
    model: str


@dataclass
class ChatConfig:
    """Chat 模型配置。"""
    base_url: str
    api_key: str
    model: str


@dataclass
class AppConfig:
    """应用通用配置。"""
    top_k: int = 3
    database_path: str = "data/storypoint.db"
    faiss_index_path: str = "data/faiss_baseline.index"
    flask_secret_key: str = "dev-secret-key"


def load_config() -> tuple[EmbeddingConfig, ChatConfig, AppConfig]:
    """从环境变量加载全部配置。

    Returns:
        (EmbeddingConfig, ChatConfig, AppConfig) 三元组。

    Raises:
        ValueError: 缺少必需的环境变量时抛出。
    """
    embedding = EmbeddingConfig(
        base_url=_require("EMBEDDING_BASE_URL"),
        api_key=_require("EMBEDDING_API_KEY"),
        model=_require("EMBEDDING_MODEL"),
    )

    chat = ChatConfig(
        base_url=_require("CHAT_BASE_URL"),
        api_key=_require("CHAT_API_KEY"),
        model=_require("CHAT_MODEL"),
    )

    app = AppConfig(
        top_k=int(os.getenv("TOP_K", "3")),
        database_path=os.getenv("DATABASE_PATH", "data/storypoint.db"),
        faiss_index_path=os.getenv("FAISS_INDEX_PATH", "data/faiss_baseline.index"),
        flask_secret_key=os.getenv("FLASK_SECRET_KEY", "dev-secret-key"),
    )

    return embedding, chat, app


def _require(key: str) -> str:
    """获取必需的环境变量，缺失时抛 ValueError。"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"缺少必需的环境变量: {key}")
    return value
