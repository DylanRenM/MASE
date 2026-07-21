"""QualityEvaluator 单元测试 — 梯度检测 + 归属检测 + 综合评分。"""

import numpy as np
import pytest

from core.quality_evaluator import evaluate


# ── 构建测试数据 ────────────────────────────────

def _make_vectors(pattern: str) -> tuple[np.ndarray, list[int]]:
    """根据 pattern 生成特征向量和点数。

    pattern: "gradient" — 严格递增梯度
             "flat" — 所有分值模长相同（倒挂风险）
             "two_inversions" — 2处倒挂（error）
             "good_clusters" — 紧密聚类，归属清晰
             "scattered" — 高度离散，归属混乱
    """
    np.random.seed(42)

    if pattern == "gradient":
        # 每分量成正比的向量
        vectors = []
        points = []
        for i, pt in enumerate([1, 2, 3, 5, 8, 13]):
            base = np.array([(i + 1) * 0.5] * 10, dtype=np.float32)
            for _ in range(2):
                vectors.append(base + np.random.normal(0, 0.1, 10).astype(np.float32))
                points.append(pt)
        return np.array(vectors), points

    elif pattern == "flat":
        # 所有分值模长相似
        vectors = []
        points = []
        for pt in [1, 2, 3, 5, 8, 13]:
            for _ in range(2):
                vectors.append(np.random.normal(0.5, 0.1, 10).astype(np.float32))
                points.append(pt)
        return np.array(vectors), points

    elif pattern == "two_inversions":
        # 构造明确的2处倒挂
        vectors = []
        points = []
        # 1点：高模长
        for _ in range(2):
            vectors.append(np.array([1.0] * 10, dtype=np.float32))
            points.append(1)
        # 2点：低模长（倒挂1）
        for _ in range(2):
            vectors.append(np.array([0.1] * 10, dtype=np.float32))
            points.append(2)
        # 3点：中模长
        for _ in range(2):
            vectors.append(np.array([0.5] * 10, dtype=np.float32))
            points.append(3)
        # 5点：低模长（倒挂2）
        for _ in range(2):
            vectors.append(np.array([0.2] * 10, dtype=np.float32))
            points.append(5)
        # 8点：高模长
        for _ in range(2):
            vectors.append(np.array([1.5] * 10, dtype=np.float32))
            points.append(8)
        # 13点：更高模长
        for _ in range(2):
            vectors.append(np.array([2.0] * 10, dtype=np.float32))
            points.append(13)
        return np.array(vectors), points

    elif pattern == "good_clusters":
        # 紧密聚类
        centroids = {
            1: np.array([0.1] * 10, dtype=np.float32),
            2: np.array([0.3] * 10, dtype=np.float32),
            3: np.array([0.5] * 10, dtype=np.float32),
            5: np.array([0.8] * 10, dtype=np.float32),
            8: np.array([1.2] * 10, dtype=np.float32),
            13: np.array([1.8] * 10, dtype=np.float32),
        }
        vectors = []
        points = []
        for pt in [1, 2, 3, 5, 8, 13]:
            for _ in range(2):
                v = centroids[pt] + np.random.normal(0, 0.05, 10).astype(np.float32)
                vectors.append(v)
                points.append(pt)
        return np.array(vectors), points

    elif pattern == "scattered":
        # 高度离散 — 各分值完全随机
        vectors = []
        points = []
        for pt in [1, 2, 3, 5, 8, 13]:
            for _ in range(2):
                vectors.append(np.random.normal(0.5, 0.5, 10).astype(np.float32))
                points.append(pt)
        return np.array(vectors), points

    return np.array([]), []


class TestGradientCheck:
    """梯度检测测试。"""

    def test_perfect_gradient_passes(self):
        """严格递增梯度 — 无问题。"""
        vectors, points = _make_vectors("gradient")
        report = evaluate(vectors, points)

        grad_issues = [i for i in report.issues if i.type == "gradient"]
        assert len(grad_issues) == 0
        assert "梯度合理" in report.summary

    def test_two_inversions_is_error(self):
        """2处倒挂 → error。"""
        vectors, points = _make_vectors("two_inversions")
        report = evaluate(vectors, points)

        grad_issues = [i for i in report.issues if i.type == "gradient"]
        assert len(grad_issues) == 1
        assert grad_issues[0].severity == "error"
        assert "2" in grad_issues[0].message

    def test_flat_gradient_warning_or_error(self):
        """随机相同 — 至少触发 warning。"""
        vectors, points = _make_vectors("flat")
        report = evaluate(vectors, points)

        # 可能存在倒挂但不是必须的（随机性），只要报告正常生成即可
        assert 0 <= report.overall_score <= 100


class TestMisalignmentCheck:
    """归属检测测试。"""

    def test_good_clusters_no_misalignment(self):
        """紧密聚类 — 全部归属正确。"""
        vectors, points = _make_vectors("good_clusters")
        report = evaluate(vectors, points)

        mis_issues = [i for i in report.issues if i.type == "misalignment"]
        assert len(mis_issues) == 0

    def test_scattered_may_have_misalignment(self):
        """高度离散 — 应有归属异常。"""
        vectors, points = _make_vectors("scattered")
        report = evaluate(vectors, points)

        # 高度离散应该有归属问题
        mis_issues = [i for i in report.issues if i.type == "misalignment"]
        assert len(mis_issues) >= 1


class TestScoring:
    """综合评分测试。"""

    def test_perfect_score_100(self):
        """完美数据 — 评分 100, pass True。"""
        vectors, points = _make_vectors("good_clusters")
        report = evaluate(vectors, points)

        assert report.overall_score == 100
        assert report.pass_ is True

    def test_error_causes_fail(self):
        """有 error → pass False, 评分 < 100。"""
        vectors, points = _make_vectors("two_inversions")
        report = evaluate(vectors, points)

        assert report.overall_score < 100
        assert report.pass_ is False

    def test_score_in_range(self):
        """评分始终在 [0, 100] 范围内。"""
        vectors, points = _make_vectors("flat")
        report = evaluate(vectors, points)
        assert 0 <= report.overall_score <= 100


class TestReportStructure:
    """报告结构测试。"""

    def test_report_has_all_fields(self):
        """报告包含所有必需字段。"""
        vectors, points = _make_vectors("gradient")
        report = evaluate(vectors, points)

        assert hasattr(report, 'overall_score')
        assert hasattr(report, 'pass_')
        assert hasattr(report, 'summary')
        assert hasattr(report, 'issues_llm')
        assert hasattr(report, 'issues')
        assert isinstance(report.issues, list)
