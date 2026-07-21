"""故事点估算服务。

编排特征提取→检索→加权→LLM裁决→记录历史的完整流程。
"""

import json

from core.feature_encoder import FeatureEncoder
from core.reporter import ReportGenerator
from db.models import BaselineRepository, HistoryRepository
from db.vector_store import VectorStore, VectorStoreError
from utils.feature_extractor import FeatureExtractor


class EstimateService:
    """故事点估算服务。"""

    def __init__(self, baseline_repo: BaselineRepository,
                 history_repo: HistoryRepository,
                 vector_store: VectorStore,
                 feature_extractor: FeatureExtractor,
                 feature_encoder: FeatureEncoder,
                 report_generator: ReportGenerator):
        self._baseline_repo = baseline_repo
        self._history_repo = history_repo
        self._vector_store = vector_store
        self._feature_extractor = feature_extractor
        self._feature_encoder = feature_encoder
        self._report_generator = report_generator

    def estimate(self, title: str, description: str, acceptance_criteria: str = "") -> dict:
        """估算单个用户故事的复杂度。

        Args:
            title: 故事标题。
            description: 故事描述。
            acceptance_criteria: 验收准则（可选）。

        Returns:
            包含 estimate/reasoning/risk_notes/split_suggestion 等的 dict。
        """
        # 检查是否有基线故事
        all_stories = self._baseline_repo.get_all()
        if not all_stories:
            return {"status": "error", "errors": ["请先上传基准故事集"]}

        # 阶段一：特征提取 + 编码
        try:
            features = self._feature_extractor.extract(title, description, acceptance_criteria)
            new_vector = self._feature_encoder.encode(features)

            # 从FAISS检索TopK，返回 [(faiss_index, similarity), ...]
            top_indices = self._vector_store.search(new_vector, k=3)
        except VectorStoreError as e:
            return {"status": "error", "errors": [f"向量检索失败: {e}"]}
        except Exception as e:
            return {"status": "error", "errors": [f"特征提取失败: {e}"]}

        # 获取对应的故事详情和点数
        top_stories = []
        top_sims = []
        baseline_points = [s["points"] for s in all_stories]

        for faiss_idx, sim in top_indices:
            story = self._baseline_repo.get_by_faiss_index(faiss_idx)
            if story:
                top_stories.append(story)
                top_sims.append(sim)

        # 加权平均：直接使用FAISS返回的相似度
        if top_stories and top_sims:
            total_weight = sum(top_sims)
            if total_weight > 0:
                w_avg = sum(
                    sim * story["points"] for sim, story in zip(top_sims, top_stories)
                ) / total_weight
            else:
                w_avg = 3.0
        else:
            w_avg = sorted(baseline_points)[len(baseline_points) // 2] if baseline_points else 3.0

        # 阶段二：LLM裁决
        if top_stories:
            report = self._report_generator.generate(
                title=title,
                description=description,
                top_k_stories=top_stories,
                similarities=top_sims,
                weighted_avg=w_avg,
                new_features=features,
                acceptance_criteria=acceptance_criteria,
            )
        else:
            report = self._report_generator.generate(
                title=title,
                description=description,
                top_k_stories=[],
                similarities=[],
                weighted_avg=w_avg,
                new_features=features,
                acceptance_criteria=acceptance_criteria,
            )

        # 拆分建议：估算结果达到13点上限时提示
        if w_avg > 13:
            report["split_suggestion"] = {
                "suggested": True,
                "weighted_avg": round(w_avg, 1),
                "message": (
                    f"该故事复杂度超出13点估算上限（加权均值 {w_avg:.1f}），"
                    "建议拆分为多个更小的用户故事，以便更准确地估算和管理。"
                ),
            }
        elif report.get("estimate") == "13" and w_avg >= 10.5:
            report["split_suggestion"] = {
                "suggested": True,
                "weighted_avg": round(w_avg, 1),
                "message": (
                    "该故事已达到13点估算上限，复杂度较高，"
                    "建议考虑拆分为多个更小的用户故事，以便更精准地评估和管理。"
                ),
            }
        else:
            report["split_suggestion"] = None

        # 记录历史
        self._history_repo.add(
            title=title,
            description=description,
            estimate=report["estimate"],
            confidence_min=report.get("confidence_min"),
            confidence_max=report.get("confidence_max"),
            report_json=json.dumps(report, ensure_ascii=False),
            degraded=report["degraded"],
        )

        return report
