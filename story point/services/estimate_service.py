"""故事点估算服务。

编排检索 → 加权 → LLM 裁决 → 记录历史的完整流程。
"""

import json

from core.embedding import EmbeddingClient
from core.reporter import ReportGenerator
from db.models import BaselineRepository, HistoryRepository
from db.vector_store import VectorStore, VectorStoreError


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
            结构化估算报告，包含 estimate/confidence/top_matches 等字段。
            错误时返回 {"status": "error", "errors": [...]}。
        """
        # 检查是否有基线故事
        all_stories = self._baseline_repo.get_all()
        if not all_stories:
            return {"status": "error", "errors": ["请先上传基准故事集"]}

        # 阶段一：数值计算
        try:
            combined_text = f"{title} {description}"
            new_vector = self._embedding_client.embed(combined_text)

            # 从 FAISS 检索 TopK，返回 [(faiss_index, similarity), ...]
            top_indices = self._vector_store.search(new_vector, k=3)
        except VectorStoreError as e:
            return {"status": "error", "errors": [f"向量检索失败: {e}"]}

        # 获取对应的故事详情和点数
        top_stories = []
        top_sims = []
        baseline_points = [s["points"] for s in all_stories]

        for faiss_idx, sim in top_indices:
            story = self._baseline_repo.get_by_faiss_index(faiss_idx)
            if story:
                top_stories.append(story)
                top_sims.append(sim)

        # 加权平均：直接使用 FAISS 返回的相似度
        if top_stories and top_sims:
            # normalized weighted average: Σ(sim_i × points_i) / Σ(sim_i)
            total_weight = sum(top_sims)
            if total_weight > 0:
                w_avg = sum(
                    sim * story["points"] for sim, story in zip(top_sims, top_stories)
                ) / total_weight
            else:
                w_avg = 3.0
        else:
            # 无检索结果时使用整体点数中位数作为 fallback
            w_avg = sorted(baseline_points)[len(baseline_points) // 2] if baseline_points else 3.0

        # 阶段二：LLM 裁决（top_stories 为空时直接降级为数值报告）
        if top_stories:
            report = self._report_generator.generate(
                title=title,
                description=description,
                top_k_stories=top_stories,
                similarities=top_sims,
                weighted_avg=w_avg,
            )
        else:
            # 无 TopK 结果，生成纯数值降级报告
            report = self._report_generator.generate(
                title=title,
                description=description,
                top_k_stories=[],
                similarities=[],
                weighted_avg=w_avg,
            )

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
