"""Qdrant 向量数据库管理模块"""

import os
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchAny,
    MatchValue,
)

from .config import config


def get_client() -> QdrantClient:
    """获取 Qdrant 客户端"""
    path = Path(config.qdrant_path)
    lock_file = path / ".lock"
    # 清理可能残留的锁文件（上次未正常退出导致）
    if lock_file.exists():
        try:
            lock_file.unlink()
        except Exception:
            pass

    client = QdrantClient(path=str(path))

    # 确保 collection 存在
    collections = [c.name for c in client.get_collections().collections]
    if config.qdrant_collection not in collections:
        client.create_collection(
            collection_name=config.qdrant_collection,
            vectors_config=VectorParams(
                size=config.embedding_dim,
                distance=Distance.COSINE,
            ),
        )
    return client


def init_collection():
    """初始化 Qdrant collection（向后兼容）"""
    return get_client()


def upsert_points(client: QdrantClient, points: list[PointStruct]):
    """批量插入向量点"""
    client.upsert(
        collection_name=config.qdrant_collection,
        points=points,
    )


def search_similar(
    client: QdrantClient,
    vector: list[float],
    genre_tag: str = None,
    topic_tag: str = None,
    limit: int = 10,
) -> list:
    """搜索相似向量，可按标签过滤"""
    must_conditions = []
    if genre_tag:
        must_conditions.append(
            FieldCondition(key="genre_tags", match=MatchAny(any=[genre_tag]))
        )
    if topic_tag:
        must_conditions.append(
            FieldCondition(key="topic_tags", match=MatchAny(any=[topic_tag]))
        )

    query_filter = Filter(must=must_conditions) if must_conditions else None

    results = client.search(
        collection_name=config.qdrant_collection,
        query_vector=vector,
        query_filter=query_filter,
        limit=limit,
    )
    return results


def get_vectors_by_tags(
    client: QdrantClient,
    genre_tag: str = None,
    topic_tag: str = None,
) -> list[dict]:
    """按标签获取所有匹配的向量和payload"""
    must_conditions = []
    if genre_tag:
        must_conditions.append(
            FieldCondition(key="genre_tags", match=MatchAny(any=[genre_tag]))
        )
    if topic_tag:
        must_conditions.append(
            FieldCondition(key="topic_tags", match=MatchAny(any=[topic_tag]))
        )

    query_filter = Filter(must=must_conditions) if must_conditions else None

    # Scroll through all matching points
    points = []
    offset = None
    while True:
        result, offset = client.scroll(
            collection_name=config.qdrant_collection,
            scroll_filter=query_filter,
            limit=1000,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )
        points.extend(result)
        if offset is None:
            break
    return points


def get_all_vectors(client: QdrantClient) -> list:
    """一次性获取所有向量（用于全量重建）"""
    points = []
    offset = None
    print(f"[Qdrant] 开始加载所有向量...", flush=True)
    while True:
        result, offset = client.scroll(
            collection_name=config.qdrant_collection,
            limit=1000,
            offset=offset,
            with_vectors=True,
            with_payload=True,
        )
        points.extend(result)
        if len(points) % 10000 == 0:
            print(f"[Qdrant] 已加载 {len(points)} 条...", flush=True)
        if offset is None:
            break
    print(f"[Qdrant] 加载完成: {len(points)} 条", flush=True)
    return points
