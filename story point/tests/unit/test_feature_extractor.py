"""FeatureExtractor 单元测试。"""

import json
from unittest.mock import patch

import pytest
from utils.feature_extractor import (FEATURE_EXTRACTION_PROMPT,
                                      FeatureExtractionError, FeatureExtractor)


class TestFeatureExtractor:
    """FeatureExtractor 测试套件。"""

    @pytest.fixture
    def extractor(self):
        return FeatureExtractor("http://localhost", "sk-test", "test-model")

    @pytest.fixture
    def valid_llm_response(self):
        return json.dumps({
            "frontend_pages": 2,
            "backend_interfaces": 1,
            "db_change": "是",
            "external_dependency": "否",
            "async_processing": "否",
            "transaction_required": "否",
            "business_branches": 3,
            "permission_control": "是",
            "data_migration": "否",
            "cache_design": "否",
        }, ensure_ascii=False)

    def test_extract_returns_feature_dict(self, extractor, valid_llm_response):
        """extract 返回包含10个字段的特征字典。"""
        with patch.object(extractor, "_call_api", return_value=valid_llm_response):
            features = extractor.extract("测试标题", "测试描述")

        assert features["frontend_pages"] == 2
        assert features["backend_interfaces"] == 1
        assert features["db_change"] == "是"
        assert features["business_branches"] == 3

    def test_extract_with_markdown_code_block(self, extractor):
        """支持解析 markdown 代码块中的 JSON。"""
        markdown_response = """```json
{
  "frontend_pages": 0,
  "backend_interfaces": 2,
  "db_change": "否",
  "external_dependency": "是",
  "async_processing": "是",
  "transaction_required": "否",
  "business_branches": 4,
  "permission_control": "否",
  "data_migration": "否",
  "cache_design": "是"
}
```"""

        with patch.object(extractor, "_call_api", return_value=markdown_response):
            features = extractor.extract("测试", "描述")

        assert features["frontend_pages"] == 0
        assert features["backend_interfaces"] == 2

    def test_api_failure_after_retries(self, extractor):
        """API 调用失败且重试耗尽时抛出 FeatureExtractionError。"""
        with patch.object(extractor, "_call_api", side_effect=FeatureExtractionError("Network Error")):
            with pytest.raises(FeatureExtractionError, match="特征提取失败"):
                extractor.extract("标题", "描述")

    def test_invalid_json_retries(self, extractor):
        """LLM 返回非法 JSON 时重试。"""
        with patch.object(extractor, "_call_api", return_value="这不是JSON"):
            with pytest.raises(FeatureExtractionError, match="特征提取失败"):
                extractor.extract("标题", "描述")

    def test_validate_features_rejects_missing_field(self, extractor):
        """校验拒绝缺少字段的响应。"""
        with patch.object(extractor, "_call_api", return_value='{"frontend_pages": 1}'):
            with pytest.raises(FeatureExtractionError, match="特征提取失败"):
                extractor.extract("标题", "描述")

    def test_bool_value_true_is_ok(self, extractor):
        """布尔字段 "true" 值通过校验。"""
        resp = {
            "frontend_pages": 1, "backend_interfaces": 1,
            "db_change": "true", "external_dependency": "true",
            "async_processing": "true", "transaction_required": "true",
            "business_branches": 2, "permission_control": "true",
            "data_migration": "true", "cache_design": "true",
        }
        extractor._validate_features(resp)
        # 校验通过则不抛异常

    def test_bool_value_1_is_ok(self, extractor):
        """布尔字段 "1" 值通过校验。"""
        resp = {
            "frontend_pages": 1, "backend_interfaces": 1,
            "db_change": "1", "external_dependency": "1",
            "async_processing": "1", "transaction_required": "1",
            "business_branches": 2, "permission_control": "1",
            "data_migration": "1", "cache_design": "1",
        }
        extractor._validate_features(resp)

    def test_bool_value_invalid_raises(self, extractor):
        """布尔字段非法值时抛出 ValueError。"""
        resp = {
            "frontend_pages": 1, "backend_interfaces": 1,
            "db_change": "invalid", "external_dependency": "否",
            "async_processing": "否", "transaction_required": "否",
            "business_branches": 2, "permission_control": "否",
            "data_migration": "否", "cache_design": "否",
        }
        with pytest.raises(ValueError, match="db_change"):
            extractor._validate_features(resp)

    def test_prompt_template_contains_placeholders(self):
        """Prompt 模板包含必要的占位符。"""
        assert "{story_title}" in FEATURE_EXTRACTION_PROMPT
        assert "{story_description}" in FEATURE_EXTRACTION_PROMPT
