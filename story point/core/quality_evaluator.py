"""基准故事合理性评价器。

使用统计方法（梯度检测 + 归属检测）评估基准故事集的质量。
不依赖LLM，仅使用特征向量做数值分析。

v1.0: 两条简单规则，适配小样本（12-24条）场景。
"""

from dataclasses import dataclass, field

import numpy as np

FIB_POINTS = (1, 2, 3, 5, 8, 13)


@dataclass
class QualityIssue:
    """单个合理性问题。

    Attributes:
        severity: "warning"（提示）或 "error"（阻断）。
        type: "gradient"（梯度异常）或 "misalignment"（归属异常）。
        message: 人类可读的问题描述。
    """
    severity: str
    type: str
    message: str


@dataclass
class QualityReport:
    """合理性评价报告。

    Attributes:
        overall_score: 综合评分 0-100。
        pass_: 是否允许入库。
        summary: 统计层发现的异常摘要。
        issues_llm: LLM 深度分析结果（可为空字符串）。
        issues: 问题列表。
    """
    overall_score: int
    pass_: bool
    summary: str
    issues_llm: str = ""
    issues: list[QualityIssue] = field(default_factory=list)


def evaluate(vectors: np.ndarray, points: list[int]) -> QualityReport:
    """评价基准故事集的合理性。

    前置条件:
        vectors: shape (N, 10) 的 numpy 数组，每行为一条故事的特征向量。
        points: 长度为 N 的 Fibonacci 点数列表。
        len(vectors) == len(points) >= 12（每组至少2条）。

    后置条件:
        返回 QualityReport，包含评分和问题列表。

    不变式:
        评分范围 [0, 100]。
        N 条故事全部被纳入分组分析。
    """
    _N, _D = vectors.shape
    issues: list[QualityIssue] = []

    # ── 按点数分组 ────────────────────────────────
    groups: dict[int, np.ndarray] = {}
    for pt in FIB_POINTS:
        mask = np.array([p == pt for p in points])
        if mask.any():
            groups[pt] = vectors[mask]

    present_pts = [p for p in FIB_POINTS if p in groups]

    # ── 1. 梯度检测 ────────────────────────────────
    centroids: dict[int, np.ndarray] = {
        pt: groups[pt].mean(axis=0) for pt in present_pts
    }
    norms: dict[int, float] = {
        pt: float(np.linalg.norm(centroids[pt])) for pt in present_pts
    }

    inversions = 0
    for i in range(len(present_pts) - 1):
        p1, p2 = present_pts[i], present_pts[i + 1]
        if norms[p2] <= norms[p1]:
            inversions += 1

    if inversions >= 2:
        issues.append(QualityIssue(
            severity="error", type="gradient",
            message=f"复杂度梯度出现 {inversions} 处倒挂，基准故事标定可能存在系统性问题",
        ))
    elif inversions == 1:
        issues.append(QualityIssue(
            severity="warning", type="gradient",
            message="复杂度梯度出现 1 处倒挂，部分分值间复杂度关系不理想",
        ))

    # ── 2. 归属检测 ────────────────────────────────
    misaligned = 0
    total = len(points)

    for i, pt in enumerate(points):
        if pt not in centroids:
            continue
        own_dist = float(np.linalg.norm(vectors[i] - centroids[pt]))
        nearest_pt = pt
        nearest_dist = own_dist
        for other_pt in present_pts:
            if other_pt == pt:
                continue
            d = float(np.linalg.norm(vectors[i] - centroids[other_pt]))
            if d < nearest_dist:
                nearest_dist = d
                nearest_pt = other_pt
        if nearest_pt != pt:
            misaligned += 1

    misalignment_ratio = misaligned / total if total > 0 else 0

    if misalignment_ratio > 0.2:
        issues.append(QualityIssue(
            severity="error", type="misalignment",
            message=f"{misaligned}/{total} 条故事（{misalignment_ratio:.0%}）的特征与自身分值不匹配",
        ))
    elif misaligned > 0:
        issues.append(QualityIssue(
            severity="warning", type="misalignment",
            message=f"{misaligned}/{total} 条故事的特征与自身分值不匹配",
        ))

    # ── 3. 综合评分 ────────────────────────────────
    score = 100
    for issue in issues:
        deduct = 25 if issue.severity == "error" else 10
        score -= deduct
    score = max(0, score)

    has_error = any(i.severity == "error" for i in issues)
    pass_ = score >= 60 and not has_error

    # ── 摘要 ───────────────────────────────────────
    if not issues:
        summary = "梯度合理，归属正常"
    else:
        parts = [f"[{i.severity}] {i.message}" for i in issues]
        summary = "；".join(parts)

    return QualityReport(
        overall_score=score,
        pass_=pass_,
        summary=summary,
        issues=issues,
    )
