"""基准故事上传服务。

编排上传→校验→特征提取→质量评价→编码→入库的完整流程。
"""

import numpy as np

from core.feature_encoder import FeatureEncoder
from core.quality_evaluator import QualityReport, evaluate
from core.validator import ValidationResult, validate_baseline
from db.models import BaselineRepository, HistoryRepository
from db.vector_store import VectorStore
from utils.excel_handler import parse_upload
from utils.feature_extractor import FeatureExtractor

# ── 质量分析 LLM Prompt ──────────────────────────────

QUALITY_ANALYSIS_PROMPT = """你是一位故事点估算专家。请审查以下基准故事集的合理性，从两个角度：

1. 梯度合理性：同一分值的复杂度水平是否一致？不同分值间是否有合理的复杂度梯度？
2. 归属一致性：每条故事的点数标定是否合理？有没有明显标定错误的故事？

基准故事集：
{stories_summary}

统计层已发现的异常（供参考）：
{summary}

请用简洁的中文输出你的分析和建议（控制在150字以内）。如果基准故事整体合理，明确说明"整体合理"。
不要输出JSON，直接用自然语言。"""


class BaselineService:
    """基准故事管理服务。

    负责 Excel 解析、校验、特征提取和向量化入库的流程编排。
    """

    def __init__(self, baseline_repo: BaselineRepository,
                 history_repo: HistoryRepository,
                 vector_store: VectorStore,
                 feature_extractor: FeatureExtractor,
                 feature_encoder: FeatureEncoder,
                 quality_llm_base_url: str = "",
                 quality_llm_api_key: str = "",
                 quality_llm_model: str = ""):
        self._baseline_repo = baseline_repo
        self._history_repo = history_repo
        self._vector_store = vector_store
        self._feature_extractor = feature_extractor
        self._feature_encoder = feature_encoder
        self._quality_llm_base_url = quality_llm_base_url
        self._quality_llm_api_key = quality_llm_api_key
        self._quality_llm_model = quality_llm_model
        self._quality_client = None  # 延迟初始化

    def parse_and_validate(self, filepath: str) -> dict:
        """解析上传的 Excel 并校验（含合理性评价）。

        Args:
            filepath: 上传的 Excel 文件路径。

        Returns:
            {
                "status": "ok" | "error",
                "rows": [...],              # 仅 status=ok
                "points_distribution": {...},  # 仅 status=ok
                "quality_report": {...},     # 仅 status=ok，合理性评价
                "errors": [...]              # 仅 status=error
            }
        """
        try:
            rows = parse_upload(filepath)
        except Exception as e:
            return {"status": "error", "errors": [f"文件解析失败: {e}"]}

        result: ValidationResult = validate_baseline(rows)
        if not result.valid:
            return {"status": "error", "errors": result.errors}

        # 统计点数分布
        distribution: dict[int, int] = {pt: 0 for pt in [1, 2, 3, 5, 8, 13]}
        for row in rows:
            pt = row["points"]
            if pt in distribution:
                distribution[pt] += 1

        # ── 合理性评价 ────────────────────────────
        quality_report = self._evaluate_quality(rows)

        return {
            "status": "ok",
            "rows": rows,
            "points_distribution": distribution,
            "quality_report": quality_report,
        }

    def _evaluate_quality(self, rows: list[dict]) -> dict:
        """对基准故事做合理性评价（统计层 + LLM 分析）。

        Args:
            rows: 校验通过的行列表。

        Returns:
            可序列化的 quality_report 字典。
        """
        # 统计层评价
        try:
            features_list = self._feature_extractor.extract_batch(rows)
            vectors = self._feature_encoder.encode_batch(features_list)
            # 缓存向量供 confirm 复用，避免重复特征提取
            self._cached_vectors = vectors
            points = [r["points"] for r in rows]
            report: QualityReport = evaluate(vectors, points)
        except Exception as e:
            return {
                "overall_score": 100,
                "pass": True,
                "summary": f"统计评价失败（{e}），跳过合理性检查",
                "issues_llm": "",
                "issues": [],
            }

        # LLM 分析（仅在有统计异常时调用）
        if report.issues and self._quality_llm_api_key:
            try:
                stories_summary = self._build_stories_summary(rows)
                analysis = self._call_quality_llm(stories_summary, report.summary)
                report.issues_llm = analysis
            except Exception:
                report.issues_llm = ""

        return {
            "overall_score": report.overall_score,
            "pass": report.pass_,
            "summary": report.summary,
            "issues_llm": report.issues_llm,
            "issues": [
                {"severity": i.severity, "type": i.type, "message": i.message}
                for i in report.issues
            ],
        }

    @staticmethod
    def _build_stories_summary(rows: list[dict]) -> str:
        """构建按分值分组的基准故事文本摘要（供 LLM 分析用）。"""
        from core.quality_evaluator import FIB_POINTS
        groups: dict[int, list[dict]] = {p: [] for p in FIB_POINTS}
        for r in rows:
            pt = r["points"]
            if pt in groups:
                groups[pt].append(r)

        parts = []
        for pt in FIB_POINTS:
            if groups[pt]:
                parts.append(f"【{pt}点】")
                for r in groups[pt]:
                    parts.append(
                        f"  - {r['id']}: {r['title']}（{r['description']}）"
                        f"验收准则：{r.get('acceptance_criteria', '') or '（无）'}"
                    )
        return "\n".join(parts)

    def _call_quality_llm(self, stories_summary: str, summary: str) -> str:
        """调用 LLM 做基准故事合理性分析。"""
        if self._quality_client is None:
            from openai import OpenAI
            self._quality_client = OpenAI(
                base_url=self._quality_llm_base_url,
                api_key=self._quality_llm_api_key,
            )

        prompt = QUALITY_ANALYSIS_PROMPT.format(
            stories_summary=stories_summary,
            summary=summary,
        )

        response = self._quality_client.chat.completions.create(
            model=self._quality_llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def confirm(self, rows: list[dict], action: str) -> dict:
        """确认入库（全量替换或追加合并）。

        Args:
            rows: 校验通过的行列表。
            action: "replace" 或 "append"。

        Returns:
            {"status": "ok", "count": N} 或 {"status": "error", "errors": [...]}
        """
        # 特征提取（优先使用缓存的向量）
        try:
            if hasattr(self, '_cached_vectors') and self._cached_vectors is not None \
                    and len(self._cached_vectors) == len(rows):
                new_vectors = self._cached_vectors
                self._cached_vectors = None  # 一次使用后清除
            else:
                features_list = self._feature_extractor.extract_batch(rows)
                new_vectors = self._feature_encoder.encode_batch(features_list)
        except Exception as e:
            return {"status": "error", "errors": [f"特征提取失败: {e}"]}

        # 给每行分配 faiss_index
        if action == "replace":
            for i, row in enumerate(rows):
                row["faiss_index"] = i
        else:
            # 追加模式：从已有数据偏移
            existing = self._baseline_repo.get_all()
            offset = len(existing)
            for i, row in enumerate(rows):
                row["faiss_index"] = offset + i

        # 写入数据库
        if action == "replace":
            self._baseline_repo.replace_all(rows)
        else:
            self._baseline_repo.insert_batch(rows)

        # 重建 FAISS 索引
        all_stories = self._baseline_repo.get_all()
        try:
            if action == "replace":
                # 替换模式：复用第一次编码的结果
                all_vectors = new_vectors
            else:
                # 追加模式：取已有向量 + 新向量
                existing_vectors = self._vector_store.get_vectors()
                all_vectors = np.vstack([existing_vectors, new_vectors]) if len(existing_vectors) > 0 else new_vectors
            self._vector_store.build_index(all_vectors)
        except Exception as e:
            return {"status": "error", "errors": [f"FAISS 索引重建失败（数据库已更新）: {e}"]}

        return {"status": "ok", "count": len(all_stories)}
