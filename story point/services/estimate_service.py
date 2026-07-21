"""故事点估算服务。

编排检索 → 加权 → LLM 裁决 → 记录历史的完整流程。
"""

import numpy as np

from core.embedding import EmbeddingClient
from core.estimator import compute_similarities, get_top_k, weighted_average
from core.reporter import ReportGenerator
from db.models import BaselineRepository, HistoryRepository
from db.vector_store import VectorStore


class EstimateService:
    """故事点估算服务。"""

    def __init__(self, baseline_repo: BaselineRepository,
                 history_repo: HistoryRepository,
                 vector_store: VectorStore,
                 embedding_client: EmbeddingClient,
                 report_generator: ReportGenerator):
        self._baseline_repo = baseline_repo
        self._history_repo = history_repo
        self._vector_store = vector_store
        self._embedding_client = embedding_client
        self._report_generator = report_generator

    def estimate(self, title: str, description: str) -> dict:
        """估算新需求的故事点。

        前置条件: 基线故事已加载（至少 12 条）。

        Args:
            title: 新需求标题。
            description: 新需求描述。

        Returns:
            结构化估算报告。

        Raises:
            ValueError: 无基线故事时抛出。
        """
        # 检查是否有基线故事
        all_stories = self._baseline_repo.get_all()
        if not all_stories:
            return {"status": "error", "errors": ["请先上传基准故事集"]}

        # 阶段一：数值计算
        combined_text = f"{title} {description}"
        new_vector = self._embedding_client.embed(combined_text)

        # 从 FAISS 检索 TopK
        top_indices = self._vector_store.search(new_vector, k=3)

        # 获取对应的故事和点数
        top_stories = []
        top_sims = []
        baseline_points = [s["points"] for s in all_stories]

        for idx, sim in top_indices:
            story = self._baseline_repo.get_by_faiss_index(idx)
            if story:
                top_stories.append(story)
                top_sims.append(sim)

        # 加权平均
        if top_stories:
            indices_for_avg = [s["faiss_index"] for s in top_stories]
            all_sims = compute_similarities(new_vector,
                                            np.array([self._embedding_client.embed(
                                                f"{s['title']} {s['description']}"
                                            ) for s in all_stories]))
            w_avg = weighted_average(indices_for_avg, all_sims, baseline_points)
        else:
            w_avg = 3.0  # fallback

        # 阶段二：LLM 裁决
        report = self._report_generator.generate(
            title=title,
            description=description,
            top_k_stories=top_stories,
            similarities=top_sims,
            weighted_avg=w_avg,
        )

        # 记录历史
        import json
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
