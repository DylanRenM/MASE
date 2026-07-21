"""斐波那契刻度舍入函数测试。

覆盖 contract.md 中 round_to_fibonacci 的所有边界条件。
"""

import pytest

from utils.fibonacci import round_to_fibonacci


class TestRoundToFibonacci:
    """round_to_fibonacci 函数测试套件。"""

    def test_exact_fibonacci_values_return_unchanged(self):
        """精确匹配斐波那契值时不改变。"""
        assert round_to_fibonacci(1.0) == 1
        assert round_to_fibonacci(2.0) == 2
        assert round_to_fibonacci(3.0) == 3
        assert round_to_fibonacci(5.0) == 5
        assert round_to_fibonacci(8.0) == 8
        assert round_to_fibonacci(13.0) == 13

    def test_boundary_4_5_rounds_up_to_avoid_underestimation(self):
        """4.5 → 5，向上取整避免低估。"""
        assert round_to_fibonacci(4.5) == 5

    def test_6_0_rounds_to_5(self):
        """6.0 更接近 5。"""
        assert round_to_fibonacci(6.0) == 5

    def test_6_5_rounds_to_8(self):
        """6.5 更接近 8（向上）。"""
        assert round_to_fibonacci(6.5) == 8

    def test_10_5_rounds_to_13(self):
        """10.5 更接近 13。"""
        assert round_to_fibonacci(10.5) == 13

    def test_value_below_1_clamps_to_1(self):
        """值 < 1 时 clamp 到最小值 1。"""
        assert round_to_fibonacci(0.5) == 1
        assert round_to_fibonacci(0.0) == 1

    def test_value_above_13_clamps_to_13(self):
        """值 > 13 时 clamp 到最大值 13。"""
        assert round_to_fibonacci(14.0) == 13
        assert round_to_fibonacci(100.0) == 13

    def test_return_type_is_int(self):
        """返回值永远是 int。"""
        result = round_to_fibonacci(3.14159)
        assert isinstance(result, int)
