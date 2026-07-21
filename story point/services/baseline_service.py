"""基准故事上传服务。

编排上传→校验→向量化→入库的完整流程。
"""

from core.embedding import EmbeddingClient
from core.validator import ValidationResult, validate_baseline
from db.models import BaselineRepository, HistoryRepository
from db.vector_store import VectorStore
from utils.excel_handler import parse_upload


class BaselineService:
    """基准故事管理服务。

    负责 Excel 解析、校验、向量化和入库的流程编排。
    """

    def __init__(self, baseline_repo: BaselineRepository,
                 history_repo: HistoryRepository,
                 vector_store: VectorStore,
                 embedding_client: EmbeddingClient):
        self._baseline_repo = baseline_repo
        self._history_repo = history_repo
        self._vector_store = vector_store
        self._embedding_client = embedding_client

    def parse_and_validate(self, filepath: str) -> dict:
        """解析上传的 Excel 并校验。

        Args:
            filepath: 上传的 Excel 文件路径。

        Returns:
            {
                "status": "ok" | "error",
                "rows": [...],           # 仅 status=ok
                "points_distribution": {...},  # 仅 status=ok
                "errors": [...]          # 仅 status=error
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

        return {
            "status": "ok",
            "rows": rows,
            "points_distribution": distribution,
        }

    def confirm(self, rows: list[dict], action: str) -> dict:
        """确认入库（全量替换或追加合并）。

        Args:
            rows: 校验通过的行列表。
            action: "replace" 或 "append"。

        Returns:
            {"status": "ok", "count": N} 或 {"status": "error", "errors": [...]}
        """
        # 生成 Embedding 向量（仅对新增行）
        try:
            texts = [f"{r['title']} {r['description']}" for r in rows]
            new_vectors = self._embedding_client.embed_batch(texts)
        except Exception as e:
            return {"status": "error", "errors": [f"向量化失败: {e}"]}

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
            all_vectors = self._embedding_client.embed_batch(
                [f"{s['title']} {s['description']}" for s in all_stories]
            )
            self._vector_store.build_index(all_vectors)
        except Exception as e:
            return {"status": "error", "errors": [f"FAISS 索引重建失败（数据库已更新）: {e}"]}

        return {"status": "ok", "count": len(all_stories)}
