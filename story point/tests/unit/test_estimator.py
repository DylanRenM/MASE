"""估算器核心算法测试。"""

import numpy as np
import pytest

from core.estimator import compute_similarities, get_top_k, weighted_average
from utils.fibonacci import round_to_fibonacci


class TestComputeSimilarities:
    """compute_similarities 测试。"""

    def test_identical_vectors_yield_1(self):
        """相同向量返回 1.0。"""
        v = np.array([1.0, 0.0, 0.0])
        similarities = compute_similarities(v, np.array([v]))
        assert pytest.approx(similarities[0], abs=1e-6) == 1.0

    def test_orthogonal_vectors_yield_0(self):
        """正交向量返回 0.0。"""
        v = np.array([1.0, 0.0])
        baseline = np.array([[0.0, 1.0]])
        similarities = compute_similarities(v, baseline)
        assert pytest.approx(similarities[0], abs=1e-6) == 0.0

    def test_returns_array_of_correct_shape(self):
        """返回 (N,) 形状数组。"""
        v = np.array([1.0, 2.0, 3.0])
        baseline = np.random.randn(5, 3)
        similarities = compute_similarities(v, baseline)
        assert similarities.shape == (5,)


class TestGetTopK:
    """get_top_k 测试。"""

    def test_returns_k_results_in_descending_order(self):
        """返回 k 个结果，按相似度降序。"""
        sims = np.array([0.1, 0.9, 0.5, 0.3])
        top = get_top_k(sims, k=3)
        assert len(top) == 3
        assert top[0] == (1, 0.9)
        assert top[1] == (2, 0.5)
        assert top[2] == (3, 0.3)


class TestWeightedAverage:
    """weighted_average 测试。"""

    def test_all_same_weight(self):
        """所有权重相同时等于算术平均。"""
        points = [1, 5, 9]
        sims = np.array([0.5, 0.5, 0.5])
        result = weighted_average([0, 1, 2], sims, points)
        assert pytest.approx(result) == 5.0

    def test_weighted_by_similarity(self):
        """高相似度权重更大。"""
        points = [5, 3]
        sims = np.array([1.0, 0.5])
        # (1.0*5 + 0.5*3) / (1.0+0.5) = 6.5/1.5 = 4.333...
        result = weighted_average([0, 1], sims, points)
        assert pytest.approx(result) == 4.333333333333333
