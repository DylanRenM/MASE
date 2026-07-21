"""斐波那契刻度（1, 2, 3, 5, 8, 13）舍入工具。"""

FIB_SCALES: list[int] = [1, 2, 3, 5, 8, 13]


def round_to_fibonacci(value: float) -> int:
    """将数值四舍五入到最近的斐波那契刻度。

    前置条件: value >= 0
    后置条件: result ∈ {1, 2, 3, 5, 8, 13}

    Args:
        value: 任意非负浮点数。

    Returns:
        最近的斐波那契刻度整数值。
        value < 1 → 1, value > 13 → 13。
        平局时（如 6.5 距 5 和 8 等距）取较大的刻度，避免低估。
    """
    # 按距离排序，距离相同时取较大的刻度（-x 实现降序优先级）
    return min(FIB_SCALES, key=lambda x: (abs(x - value), -x))
