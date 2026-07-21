"""Embedding 客户端单元测试（mock OpenAI API）。"""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.embedding import EmbeddingAPIError, EmbeddingClient


class TestEmbeddingClient:
    """EmbeddingClient 测试套件。"""

    def test_embed_returns_vector_of_expected_dimension(self):
        """embed() 返回预期维度的向量。"""
        client = EmbeddingClient("http://localhost", "sk-test", "test-model")

        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]

        with patch.object(client._client.embeddings, "create", return_value=mock_response):
            vec = client.embed("测试文本")
            assert isinstance(vec, np.ndarray)
            assert vec.shape == (1536,)
            assert vec.dtype == np.float32

    def test_embed_retries_on_failure_then_raises(self):
        """API 失败时重试 3 次后抛 EmbeddingAPIError。"""
        client = EmbeddingClient("http://localhost", "sk-test", "test-model", max_retries=3)

        with patch.object(client._client.embeddings, "create", side_effect=Exception("API Error")):
            with pytest.raises(EmbeddingAPIError, match="重试 3 次"):
                client.embed("测试文本")

    def test_embed_batch_returns_all_vectors(self):
        """embed_batch() 返回所有文本的向量。"""
        client = EmbeddingClient("http://localhost", "sk-test", "test-model")

        def mock_create(**kwargs):
            text = kwargs.get("input", "")
            # 不同文本返回不同向量
            seed = len(text)
            mock = MagicMock()
            mock.data = [MagicMock(embedding=[seed * 0.01] * 1536)]
            return mock

        with patch.object(client._client.embeddings, "create", side_effect=mock_create):
            vecs = client.embed_batch(["短", "较长的文本"])
            assert vecs.shape == (2, 1536)
