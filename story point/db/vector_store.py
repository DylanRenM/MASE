"""FAISS 向量索引封装。

管理基线故事向量的构建、检索、保存和加载。
"""

import numpy as np

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False


class VectorStoreError(Exception):
    """向量存储操作异常。"""


class VectorStore:
    """FAISS 向量索引封装。

    内部使用 IndexFlatIP（内积），等效于余弦相似度（向量已归一化时）。
    """

    def __init__(self, dimension: int = 10):
        """
        Args:
            dimension: 向量维度，默认 10（10个复杂度特征）。
        """
        self._dimension = dimension
        self._index = None

    @property
    def is_built(self) -> bool:
        """索引是否已构建。"""
        return self._index is not None and self._index.ntotal > 0

    def build_index(self, vectors: np.ndarray):
        """从向量数组构建 FAISS 索引。

        前置条件: vectors.shape == (N, D), N >= 1。
        后置条件: 索引可检索。

        Args:
            vectors: (N, D) 形状的向量数组。

        Raises:
            VectorStoreError: FAISS 未安装。
        """
        if not HAS_FAISS:
            raise VectorStoreError("FAISS 未安装，请执行 pip install faiss-cpu")

        # 归一化向量，使内积等价于余弦相似度
        faiss.normalize_L2(vectors)

        self._index = faiss.IndexFlatIP(self._dimension)
        self._index.add(vectors)

    def get_vectors(self) -> np.ndarray:
        """获取索引中所有向量。

        前置条件: 索引已构建。
        后置条件: result.shape == (ntotal, dimension)。

        Returns:
            (N, D) 形状的向量数组。
        """
        if self._index is None or self._index.ntotal == 0:
            return np.empty((0, self._dimension), dtype=np.float32)
        return np.array([self._index.reconstruct(i) for i in range(self._index.ntotal)], dtype=np.float32)

    def search(self, query: np.ndarray, k: int = 3) -> list[tuple[int, float]]:
        """检索最相似的 k 个向量。

        前置条件: 索引已构建, query.shape == (1, D) 或 (D,)。
        后置条件: len(result) == k。

        Args:
            query: 查询向量。
            k: 返回结果数。

        Returns:
            [(索引, 相似度), ...] 列表，按相似度降序。

        Raises:
            VectorStoreError: 索引未构建。
        """
        if self._index is None:
            raise VectorStoreError("索引未构建，请先上传基准故事")

        if query.ndim == 1:
            query = query.reshape(1, -1)

        # 归一化查询向量
        faiss.normalize_L2(query)

        distances, indices = self._index.search(query, k)
        return [(int(indices[0][i]), float(distances[0][i])) for i in range(k)]

    def save(self, filepath: str):
        """保存索引到文件。

        前置条件: 索引已构建，filepath 目录可写。

        Raises:
            VectorStoreError: FAISS 未安装或索引未构建。
        """
        if not HAS_FAISS:
            raise VectorStoreError("FAISS 未安装")

        if self._index is None:
            raise VectorStoreError("索引未构建，无法保存")

        faiss.write_index(self._index, filepath)

    def load(self, filepath: str) -> bool:
        """从文件加载索引。

        Args:
            filepath: 索引文件路径。

        Returns:
            True 加载成功，False 文件不存在或损坏。
        """
        if not HAS_FAISS:
            return False

        try:
            self._index = faiss.read_index(filepath)
            return self._index.ntotal > 0
        except Exception:
            return False
