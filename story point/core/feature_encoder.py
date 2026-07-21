"""特征编码器。

将LLM提取的复杂度特征JSON编码为10维归一化数值向量，用于FAISS向量检索。
"""

import numpy as np

# 特征字段列表（保持固定顺序以确向量一致性）
FEATURE_FIELDS = [
    "frontend_pages",
    "backend_interfaces",
    "db_change",
    "external_dependency",
    "async_processing",
    "transaction_required",
    "business_branches",
    "permission_control",
    "data_migration",
    "cache_design",
]

VECTOR_DIMENSION = len(FEATURE_FIELDS)  # 10


class FeatureEncoder:
    """特征JSON → 10维归一化向量。

    编码规则：
    - frontend_pages(0-3): value/3
    - backend_interfaces(0-3): value/3
    - business_branches(1-5+): (value-1)/4，上限5
    - 其余7个布尔字段: "是"→1.0, "否"→0.0
    """

    def encode(self, features: dict) -> np.ndarray:
        """将单个特征字典编码为10维向量。

        前置条件: features 包含全部 FEATURE_FIELDS 键。
        后置条件: result.shape == (10,), dtype=float32。

        Args:
            features: 10个复杂度特征字段的字典。

        Returns:
            (10,) 形状的 float32 向量，各维度值域 [0, 1]。
        """
        return self.encode_batch([features])[0]

    def encode_batch(self, features_list: list[dict]) -> np.ndarray:
        """将特征字典列表编码为向量矩阵。

        前置条件: 每个dict包含全部 FEATURE_FIELDS 键。
        后置条件: result.shape == (N, 10), dtype=float32。

        Args:
            features_list: 特征字典列表。

        Returns:
            (N, 10) 形状的 float32 向量矩阵。

        Raises:
            ValueError: 特征字典缺少必需字段时抛出。
        """
        vectors = np.zeros((len(features_list), VECTOR_DIMENSION), dtype=np.float32)

        for i, feat in enumerate(features_list):
            self._validate_features(feat)
            v = vectors[i]

            # 连续型特征（归一化到[0,1]）
            v[0] = self._normalize_count(feat["frontend_pages"], max_val=3)
            v[1] = self._normalize_count(feat["backend_interfaces"], max_val=3)

            # 布尔型特征
            v[2] = self._bool_to_float(feat["db_change"])
            v[3] = self._bool_to_float(feat["external_dependency"])
            v[4] = self._bool_to_float(feat["async_processing"])
            v[5] = self._bool_to_float(feat["transaction_required"])

            # 业务分支数（1→0, 2→0.25, 3→0.5, 4→0.75, 5+→1.0）
            v[6] = self._normalize_branches(feat["business_branches"])

            v[7] = self._bool_to_float(feat["permission_control"])
            v[8] = self._bool_to_float(feat["data_migration"])
            v[9] = self._bool_to_float(feat["cache_design"])

        return vectors

    @staticmethod
    def _normalize_count(value, max_val: int = 3) -> float:
        """归一化计数型特征到[0,1]。"""
        try:
            v = float(value)
        except (ValueError, TypeError):
            v = 0.0
        return min(max(v, 0.0) / max_val, 1.0)

    @staticmethod
    def _normalize_branches(value) -> float:
        """归一化业务分支数（1-5+）到[0,1]。

        1→0.0, 2→0.25, 3→0.5, 4→0.75, 5+→1.0
        """
        try:
            v = int(value)
        except (ValueError, TypeError):
            v = 1
        v = min(max(v, 1), 5)  # clamp到[1, 5]
        return (v - 1) / 4.0

    @staticmethod
    def _bool_to_float(value) -> float:
        """将"是"/"否"转换为1.0/0.0。兼容True/False和1/0。"""
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, (int, float)):
            return 1.0 if value else 0.0
        s = str(value).strip().lower()
        return 1.0 if s in ("是", "true", "yes", "1") else 0.0

    @staticmethod
    def _validate_features(features: dict):
        """校验特征字典包含全部必需字段。"""
        missing = [f for f in FEATURE_FIELDS if f not in features]
        if missing:
            raise ValueError(f"特征字典缺少必需字段: {missing}")
