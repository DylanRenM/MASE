"""应用配置加载。

从环境变量加载 Chat、特征提取和应用配置，支持供应商无关的灵活切换。
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# 自动加载 .env 文件
load_dotenv()


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
    flask_secret_key: str = ""  # 必须由环境变量提供
    vector_dimension: int = 10  # 特征向量维度（10个复杂度特征）


def load_config() -> tuple[ChatConfig, AppConfig]:
    """从环境变量加载全部配置。

    Returns:
        (ChatConfig, AppConfig) 二元组。

    Raises:
        ValueError: 缺少必需的环境变量时抛出。
    """
    chat = ChatConfig(
        base_url=_require("CHAT_BASE_URL"),
        api_key=_require("CHAT_API_KEY"),
        model=_require("CHAT_MODEL"),
    )

    app = AppConfig(
        top_k=int(os.getenv("TOP_K", "3")),
        database_path=os.getenv("DATABASE_PATH", "data/storypoint.db"),
        faiss_index_path=os.getenv("FAISS_INDEX_PATH", "data/faiss_baseline.index"),
        flask_secret_key=_require("FLASK_SECRET_KEY"),
        vector_dimension=int(os.getenv("VECTOR_DIMENSION", "10")),
    )

    return chat, app


def _require(key: str) -> str:
    """获取必需的环境变量，缺失时抛 ValueError。"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"缺少必需的环境变量: {key}")
    return value
