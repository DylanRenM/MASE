"""LLM 报告生成器单元测试（mock Chat API）。"""

from unittest.mock import MagicMock, patch

import pytest

from core.reporter import ReportGenerator


class TestReportGenerator:
    """ReportGenerator 测试。"""

    def test_generate_returns_valid_report_on_success(self):
        """API 成功时返回完整报告。"""
        gen = ReportGenerator("http://localhost", "sk-test", "test-model")

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"estimate": 8, "confidence_min": 5, '
                                               '"confidence_max": 13, "reasoning": "测试依据", '
                                               '"risk_notes": "测试风险"}'))
        ]

        stories = [
            {"id": "S1", "title": "支付", "points": 8, "description": "集成支付"},
        ]
        sims = [0.92]

        with patch.object(gen, "_call_chat_api", return_value=mock_response.choices[0].message.content):
            result = gen.generate("微信登录", "集成OAuth", stories, sims, 8.0)

        assert result["estimate"] == 8
        assert result["confidence_min"] == 5
        assert result["confidence_max"] == 13
        assert result["degraded"] is False
        assert len(result["top_matches"]) == 1

    def test_generate_degraded_on_api_failure(self):
        """API 失败时降级为纯数值报告。"""
        gen = ReportGenerator("http://localhost", "sk-test", "test-model")

        stories = [{"id": "S1", "title": "支付", "points": 8, "description": "desc"}]
        sims = [0.92]

        with patch.object(gen, "_call_chat_api", side_effect=Exception("API Error")):
            result = gen.generate("test", "desc", stories, sims, 6.5)

        assert result["degraded"] is True
        assert result["estimate"] == 8  # 6.5 → 8
        assert "LLM 不可用" in result["reasoning"]

    def test_generate_degraded_on_invalid_json(self):
        """API 返回非 JSON 时降级。"""
        gen = ReportGenerator("http://localhost", "sk-test", "test-model")

        stories = [{"id": "S1", "title": "支付", "points": 5, "description": "desc"}]
        sims = [0.80]

        with patch.object(gen, "_call_chat_api", return_value="这不是 JSON"):
            result = gen.generate("test", "desc", stories, sims, 5.0)

        assert result["degraded"] is True
        assert result["estimate"] == 5

    def test_parse_json_from_markdown_code_block(self):
        """解析 markdown 代码块中的 JSON。"""
        gen = ReportGenerator("http://localhost", "sk", "m")
        result = gen._parse_json('```json\n{"estimate": 3}\n```')
        assert result["estimate"] == 3
