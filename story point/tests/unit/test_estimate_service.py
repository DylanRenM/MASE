"""EstimateService 单元测试 — 拆分建议逻辑。"""

from unittest.mock import MagicMock

import pytest

from core.feature_encoder import FeatureEncoder
from services.estimate_service import EstimateService


@pytest.fixture
def mock_deps():
    """构建 mock 依赖。"""
    baseline_repo = MagicMock()
    baseline_repo.get_all.return_value = [
        {"id": "S001", "title": "story 1", "description": "desc", "points": 8},
        {"id": "S002", "title": "story 2", "description": "desc", "points": 13},
    ]

    history_repo = MagicMock()
    vector_store = MagicMock()
    vector_store.search.return_value = []

    feature_extractor = MagicMock()
    feature_extractor.extract.return_value = {
        "frontend_pages": 2,
        "backend_interfaces": 3,
        "db_change": True,
        "external_dependency": False,
        "async_processing": False,
        "transaction_required": False,
        "business_branches": 2,
        "permission_control": True,
        "data_migration": False,
        "cache_design": False,
    }

    feature_encoder = FeatureEncoder()

    report_generator = MagicMock()
    report_generator.generate.return_value = {
        "estimate": "8",
        "confidence_min": "5",
        "confidence_max": "13",
        "reasoning": "测试依据",
        "risk_notes": "",
        "degraded": False,
    }

    return {
        "baseline_repo": baseline_repo,
        "history_repo": history_repo,
        "vector_store": vector_store,
        "feature_extractor": feature_extractor,
        "feature_encoder": feature_encoder,
        "report_generator": report_generator,
    }


class TestSplitSuggestion:
    """拆分建议逻辑测试。"""

    def test_split_suggestion_when_below_threshold(self, mock_deps):
        """加权均值低于10.5且估算结果非13时，split_suggestion 为 None。"""
        # 空搜索结果 → w_avg = median([8,13]) = 13，但 estimate="8" → 不触发

        svc = EstimateService(**mock_deps)
        result = svc.estimate("test", "description")

        assert result["split_suggestion"] is None

    def test_split_suggestion_when_estimate_is_13_and_high_wavg(self, mock_deps):
        """估算结果为13且加权均值≥10.5时，触发拆分建议。"""
        mock_deps["baseline_repo"].get_all.return_value = [
            {"id": "S001", "title": "story 1", "description": "desc", "points": 13},
            {"id": "S002", "title": "story 2", "description": "desc", "points": 13},
        ]
        # 空搜索结果 → w_avg = median([13,13]) = 13 >= 10.5 ✓
        mock_deps["report_generator"].generate.return_value["estimate"] = "13"

        svc = EstimateService(**mock_deps)
        result = svc.estimate("test", "description")

        assert result["split_suggestion"] is not None
        assert result["split_suggestion"]["suggested"] is True
        assert result["split_suggestion"]["weighted_avg"] >= 10.5

    def test_split_suggestion_not_triggered_when_wavg_low(self, mock_deps):
        """估算结果为13但加权均值低于10.5时，不触发拆分建议。"""
        mock_deps["baseline_repo"].get_all.return_value = [
            {"id": "S001", "title": "story 1", "description": "desc", "points": 5},
            {"id": "S002", "title": "story 2", "description": "desc", "points": 8},
        ]
        # 空搜索结果 → w_avg = median([5,8]) = 8 < 10.5
        mock_deps["report_generator"].generate.return_value["estimate"] = "13"

        svc = EstimateService(**mock_deps)
        result = svc.estimate("test", "description")

        assert result["split_suggestion"] is None

    def test_split_suggestion_field_always_present(self, mock_deps):
        """返回结果中 split_suggestion 字段始终存在。"""
        svc = EstimateService(**mock_deps)
        result = svc.estimate("test", "description")

        assert "split_suggestion" in result
