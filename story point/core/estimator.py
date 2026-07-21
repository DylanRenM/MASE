"""估算器核心算法。

提供余弦相似度计算、TopK 检索和加权平均功能。
"""

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def compute_similarities(new_vector: np.ndarray, baseline_vectors: np.ndarray) -> np.ndarray:
    """计算新需求与所有基准故事的余弦相似度。

    前置条件: new_vector.shape == (D,), baseline_vectors.shape == (N, D)。
    后置条件: result.shape == (N,), 0 <= result[i] <= 1。
    不变量: 相同向量 → 1.0。

    Args:
        new_vector: (D,) 形状的查询向量。
        baseline_vectors: (N, D) 形状的基准向量矩阵。

    Returns:
        (N,) 形状的相似度数组。
    """
    return cosine_similarity(new_vector.reshape(1, -1), baseline_vectors).flatten()


def get_top_k(similarities: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
    """获取相似度最高的 k 个索引。

    前置条件: len(similarities) >= k。
    后置条件: len(result) == k, result 按相似度降序。

    Args:
        similarities: (N,) 相似度数组。
        k: 返回数量。

    Returns:
        [(索引, 相似度), ...] 按相似度降序。
    """
    if len(similarities) < k:
        k = len(similarities)

    indices = np.argsort(similarities)[::-1][:k]
    return [(int(i), float(similarities[i])) for i in indices]


def weighted_average(indices: list[int], similarities: np.ndarray,
                     points: list[int]) -> float:
    """计算加权平均点数。

    weighted_avg = Σ(similarity_i × points_i) / Σ(similarity_i)

    前置条件: len(indices) >= 1, 所有 similarities > 0。
    后置条件: min(points) <= result <= max(points)。

    Args:
        indices: 参与计算的基准故事索引列表。
        similarities: (N,) 相似度数组。
        points: 所有基准故事的点数列表。

    Returns:
        加权平均点数（float）。
    """
    weights = np.array([similarities[i] for i in indices])
    pts = np.array([points[i] for i in indices])
    return float(np.average(pts, weights=weights))
