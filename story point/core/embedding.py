"""Embedding API 封装。

[DEPRECATED — v2.0]
本模块已废弃。项目已从文本Embedding方案迁移到特征提取+向量检索方案。
新模块: core/feature_encoder.py + utils/feature_extractor.py
保留下仅供参考，后续版本将删除。

支持供应商无关的 Embedding API 调用，含指数退避重试。
"""

import time

import numpy as np
from openai import OpenAI


class EmbeddingAPIError(Exception):
    """Embedding API 调用失败异常。"""


class EmbeddingClient:
    """Embedding 模型客户端。

    Attributes:
        model: 模型名称。
    """

    def __init__(self, base_url: str, api_key: str, model: str, max_retries: int = 3):
        self.model = model
        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._max_retries = max_retries

    def embed(self, text: str) -> np.ndarray:
        """生成单条文本的 Embedding 向量。

        前置条件: text 非空。
        后置条件: result.shape == (D,)，D 取决于模型。
        异常: EmbeddingAPIError — 重试 max_retries 次后仍失败。

        Args:
            text: 待向量化的文本。

        Returns:
            1-D numpy 向量。
        """
        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = self._client.embeddings.create(
                    input=text,
                    model=self.model,
                )
                return np.array(response.data[0].embedding, dtype=np.float32)
            except Exception as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s...
                    time.sleep(wait)

        raise EmbeddingAPIError(
            f"Embedding API 调用失败（重试 {self._max_retries} 次）: {last_error}"
        )

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """批量生成 Embedding 向量。

        前置条件: 所有 text 非空。
        后置条件: result.shape == (N, D)。
        不变量: result[i] 对应 texts[i]。

        Args:
            texts: 文本列表。

        Returns:
            (N, D) 形状的 numpy 数组。
        """
        vectors = [self.embed(t) for t in texts]
        return np.stack(vectors)
