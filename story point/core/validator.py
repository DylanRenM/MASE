"""Excel 基线故事校验器。

校验上传的 Excel 数据是否满足所有规则。
"""

from dataclasses import dataclass, field

FIB_SCALES = frozenset({1, 2, 3, 5, 8, 13})
MIN_PER_POINT = 2


@dataclass
class ValidationResult:
    """校验结果。

    Attributes:
        valid: 全部规则通过为 True。
        errors: 人类可读的错误描述列表，按行号升序排列。
    """
    valid: bool = True
    errors: list[str] = field(default_factory=list)


def validate_baseline(rows: list[dict]) -> ValidationResult:
    """校验上传的基线故事数据。

    规则（全部通过才为 valid）：
    1. 至少 1 行数据
    2. 故事点全部在 {1,2,3,5,8,13} 中
    3. 每个点数至少 2 条
    4. 标题和描述均不为空

    Args:
        rows: Excel 解析后的行列表，每行含 id/title/description/points。

    Returns:
        ValidationResult。
    """
    errors: list[str] = []

    # 规则1：至少 1 行
    if len(rows) == 0:
        errors.append("文件中没有数据行")
        return ValidationResult(valid=False, errors=errors)

    # 规则2 & 4：逐行检查
    for i, row in enumerate(rows):
        row_num = i + 2  # Excel 行号（表头占第1行）

        points = row.get("points")
        if points not in FIB_SCALES:
            errors.append(f"第{row_num}行故事点不在允许范围内（仅允许 1,2,3,5,8,13）")

        title = row.get("title", "")
        if not title or not str(title).strip():
            errors.append(f"第{row_num}行标题为空")

        desc = row.get("description", "")
        if not desc or not str(desc).strip():
            errors.append(f"第{row_num}行描述为空")

    # 规则3：每个点数至少 MIN_PER_POINT 条
    if not errors:  # 只在点数都合法时检查分布
        distribution = check_min_per_point(rows)
        for pt, count in distribution.items():
            if count < MIN_PER_POINT:
                errors.append(f"点数{pt}只有{count}条，至少需要{MIN_PER_POINT}条，请补充后重新上传")

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def check_min_per_point(rows: list[dict]) -> dict[int, int]:
    """统计每个斐波那契点数的故事数量。

    Args:
        rows: Excel 解析后的行列表。

    Returns:
        {点数: 数量} 的字典，缺失的点数返回 0。
    """
    distribution: dict[int, int] = {pt: 0 for pt in FIB_SCALES}
    for row in rows:
        pt = row.get("points")
        if pt in distribution:
            distribution[pt] += 1
    return distribution
