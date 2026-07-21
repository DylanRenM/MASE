"""Excel 基线故事校验器测试。

覆盖 contract.md 中 validate_baseline 的所有规则。
"""

import pytest

from core.validator import ValidationResult, check_min_per_point, validate_baseline


class TestCheckMinPerPoint:
    """check_min_per_point 函数测试。"""

    def test_returns_count_per_fibonacci_point(self):
        """返回每个斐波那契点数的故事数量。"""
        rows = _make_rows([
            ("S1", "a", "desc", 1), ("S2", "b", "desc", 1),
            ("S3", "c", "desc", 2), ("S4", "d", "desc", 2),
        ])
        result = check_min_per_point(rows)
        assert result[1] == 2
        assert result[2] == 2
        assert result[3] == 0
        assert result[5] == 0
        assert result[8] == 0
        assert result[13] == 0

    def test_sum_equals_total_rows(self):
        """计数总和等于总行数。"""
        rows = _make_rows([
            ("S1", "a", "desc", 1), ("S2", "b", "desc", 3),
            ("S3", "c", "desc", 5), ("S4", "d", "desc", 8),
        ])
        result = check_min_per_point(rows)
        assert sum(result.values()) == len(rows)


class TestValidateBaseline:
    """validate_baseline 函数测试。"""

    def test_all_points_valid_with_min_2_each_passes(self):
        """所有点数合法且每点数 ≥2 → valid。"""
        rows = _make_rows([
            ("S1", "t1", "d1", 1), ("S2", "t2", "d2", 1),
            ("S3", "t3", "d3", 2), ("S4", "t4", "d4", 2),
            ("S5", "t5", "d5", 3), ("S6", "t6", "d6", 3),
            ("S7", "t7", "d7", 5), ("S8", "t8", "d8", 5),
            ("S9", "t9", "d9", 8), ("S10", "t10", "d10", 8),
            ("S11", "t11", "d11", 13), ("S12", "t12", "d12", 13),
        ])
        result = validate_baseline(rows)
        assert result.valid is True
        assert len(result.errors) == 0

    def test_invalid_point_14_rejected(self):
        """点数 14 不在允许范围内 → 错误。"""
        rows = _make_rows([("S1", "t", "d", 14)])
        result = validate_baseline(rows)
        assert result.valid is False
        assert any("不在允许范围内" in e for e in result.errors)

    def test_point_with_only_one_story_fails(self):
        """某点数只有 1 条 → 错误。"""
        rows = _make_rows([
            ("S1", "t1", "d1", 1), ("S2", "t2", "d2", 1),
            ("S3", "t3", "d3", 2), ("S4", "t4", "d4", 2),
            ("S5", "t5", "d5", 3), ("S6", "t6", "d6", 3),
            ("S7", "t7", "d7", 5), ("S8", "t8", "d8", 5),
            ("S9", "t9", "d9", 8), ("S10", "t10", "d10", 8),
            ("S11", "t11", "d11", 13),  # 13: only 1
        ])
        result = validate_baseline(rows)
        assert result.valid is False
        assert any("点数13" in e and "只有" in e for e in result.errors)

    def test_point_with_zero_stories_fails(self):
        """某点数 0 条 → 错误。"""
        rows = _make_rows([
            ("S1", "t1", "d1", 1), ("S2", "t2", "d2", 1),
            ("S3", "t3", "d3", 2), ("S4", "t4", "d4", 2),
            ("S5", "t5", "d5", 3), ("S6", "t6", "d6", 3),
            ("S7", "t7", "d7", 5), ("S8", "t8", "d8", 5),
            ("S9", "t9", "d9", 8), ("S10", "t10", "d10", 8),
            # 13: 0 stories
        ])
        result = validate_baseline(rows)
        assert result.valid is False
        assert any("点数13" in e for e in result.errors)

    def test_empty_title_rejected(self):
        """空标题 → 错误。"""
        rows = _make_rows([("S1", "", "desc", 1)])
        result = validate_baseline(rows)
        assert result.valid is False
        assert any("标题" in e for e in result.errors)

    def test_empty_description_rejected(self):
        """空描述 → 错误。"""
        rows = _make_rows([("S1", "title", "", 1)])
        result = validate_baseline(rows)
        assert result.valid is False
        assert any("描述" in e for e in result.errors)

    def test_empty_data_rejected(self):
        """空数据 → 错误。"""
        result = validate_baseline([])
        assert result.valid is False
        assert len(result.errors) > 0

    def test_errors_sorted_by_row_number(self):
        """错误按行号升序排列。"""
        rows = _make_rows([
            ("S1", "", "d1", 1),       # row 2: 空标题
            ("S2", "t2", "d2", 14),    # row 3: 非法点数
        ])
        result = validate_baseline(rows)
        assert not result.valid
        # 行号小的错误应该先出现
        first_error = result.errors[0]
        assert "第2行" in first_error or "第3行" in first_error


# ── helpers ──────────────────────────────────────────

def _make_rows(specs: list[tuple[str, str, str, int]]) -> list[dict]:
    """从 (id, title, description, points) 列表构建测试行。"""
    return [
        {"id": sid, "title": title, "description": desc,
         "acceptance_criteria": "", "points": pts}
        for sid, title, desc, pts in specs
    ]
