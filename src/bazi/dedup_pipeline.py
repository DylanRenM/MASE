"""阶段3: 聚类去重管道"""

import numpy as np
from sklearn.cluster import DBSCAN
from .config import config
from .qdrant_store import get_client, get_vectors_by_tags, get_all_vectors
from .content_vectorizer import LLMClassifier, Vectorizer, GENRE_TAGS, TOPIC_TAGS


class DedupPipeline:
    """聚类去重管道"""

    DEDUP_PROMPT = """你是一个八字命理专家。以下是一组来自不同书籍的文本块，它们被初步判定为可能相似。请逐一判断它们之间的关系。

输入信息：
- 流派: {genre}
- 专题: {topic}
- 文本块列表:
{blocks_text}

请对每个文本块对进行分析，输出JSON格式：
{{
  "verdict": "duplicate" | "complementary" | "conflicting" | "distinct",
  "recommended_action": "keep_one" | "merge" | "keep_all" | "keep_all_with_note",
  "best_block_index": <如果是duplicate，指出哪个块质量最好(1-based)>,
  "explanation": "一句话解释"
}}

判定标准：
- duplicate: 讲完全相同的知识点，只是表述不同 → keep_one
- complementary: 同一知识点但提供不同角度/补充细节 → merge
- conflicting: 同一知识点但观点相左 → keep_all_with_note
- distinct: 向量相似但本质是不同的知识点 → keep_all"""

    def __init__(self):
        self._vectorizer = None
        self._classifier = None
        self.client = get_client()

    @property
    def vectorizer(self):
        if self._vectorizer is None:
            self._vectorizer = Vectorizer()
        return self._vectorizer

    @property
    def classifier(self):
        if self._classifier is None:
            self._classifier = LLMClassifier()
        return self._classifier

    def cluster_by_group(self, genre_tag: str, topic_tag: str) -> list[list[dict]]:
        """在指定流派×专题组内做 DBSCAN 聚类"""
        points = get_vectors_by_tags(self.client, genre_tag=genre_tag, topic_tag=topic_tag)

        if len(points) < 2:
            return [[p] for p in points] if points else []

        # 提取向量矩阵
        vectors = np.array([p.vector for p in points])
        ids = [p.id for p in points]

        # DBSCAN 聚类
        clustering = DBSCAN(
            eps=config.dbscan_eps,
            min_samples=config.dbscan_min_samples,
            metric="cosine",
        )
        labels = clustering.fit_predict(vectors)

        # 按标签分组
        clusters = {}
        for i, label in enumerate(labels):
            clusters.setdefault(int(label), []).append({
                "id": ids[i],
                "point": points[i],
                "index": i,
            })

        return list(clusters.values())

    def judge_cluster(self, cluster: list[dict], genre_tag: str, topic_tag: str) -> dict:
        """LLM 精判一个知识簇"""
        if len(cluster) < 2:
            point = cluster[0]["point"]
            return {
                "verdict": "unique",
                "action": "keep",
                "block_id": point.payload.get("block_id"),
                "text": point.payload.get("block_text"),
                "source_book": point.payload.get("source_book"),
            }

        # 构建块文本列表
        blocks_text = ""
        for i, item in enumerate(cluster):
            payload = item["point"].payload
            blocks_text += f"  [块{i+1}] 来源:《{payload.get('source_book', '未知')}》\n  文本: {payload.get('block_text', '')[:500]}\n\n"

        prompt = self.DEDUP_PROMPT.format(
            genre=genre_tag,
            topic=topic_tag,
            blocks_text=blocks_text,
        )

        try:
            result = self.classifier._call_llm(prompt)
            parsed = self.classifier._parse_classify_result(result)
            parsed["cluster"] = cluster
            return parsed
        except Exception as e:
            return {
                "verdict": "error",
                "action": "keep_all",
                "error": str(e),
                "cluster": cluster,
            }

    def run_full_dedup(self) -> dict:
        """运行完整的去重流程，返回处理后的知识池。
        
        优化版：一次性加载所有向量，按标签在内存中分组，避免重复 Qdrant 查询。
        """
        knowledge_pool = {
            "unique_blocks": [],     # 独有内容
            "merge_groups": [],      # 待融合组
            "conflict_groups": [],   # 争议组
            "distinct_blocks": [],   # 被误聚类的独立块
        }

        # 一次性加载所有向量
        all_points = get_all_vectors(self.client)
        if not all_points:
            print("[Dedup] Qdrant 中无数据，跳过去重", flush=True)
            return knowledge_pool

        # 按 (genre, topic) 在内存中分组（支持多标签：一个块可出现在多个组）
        from collections import defaultdict
        groups = defaultdict(list)
        for point in all_points:
            payload = point.payload
            genre_tags = payload.get("genre_tags", []) or ["综合"]
            topic_tags = payload.get("topic_tags", []) or ["基础理论"]
            for genre in genre_tags:
                for topic in topic_tags:
                    groups[(genre, topic)].append(point)

        total_groups = len(groups)
        total_placements = sum(len(pts) for pts in groups.values())
        print(f"[Dedup] 共 {len(all_points)} 条向量, {total_groups} 个标签组, {total_placements} 次放置", flush=True)

        # 跟踪已添加的 block_id，避免同一块被多次加入
        seen_blocks = set()
        # 跟踪已处理的 (genre, topic, block_id) 组合
        processed_clusters = set()

        # 逐组运行 DBSCAN + LLM 精判
        for idx, ((genre, topic), points) in enumerate(sorted(groups.items())):
            if (idx + 1) % 10 == 0 or idx == 0:
                print(f"[Dedup] 分组去重进度: {idx+1}/{total_groups} ({genre}/{topic}, {len(points)}块)", flush=True)

            if len(points) < 2:
                # 单块组，直接保留（去重：同一 block_id 只保留一次）
                for point in points:
                    block_id = point.payload.get("block_id")
                    if block_id not in seen_blocks:
                        seen_blocks.add(block_id)
                        knowledge_pool["unique_blocks"].append(self._make_block(point, genre, topic))
                continue

            # DBSCAN 聚类
            vectors = np.array([p.vector for p in points])
            clustering = DBSCAN(
                eps=config.dbscan_eps,
                min_samples=config.dbscan_min_samples,
                metric="cosine",
            )
            labels = clustering.fit_predict(vectors)

            # 按聚类标签分组
            cluster_dict = defaultdict(list)
            for i, (point, label) in enumerate(zip(points, labels)):
                cluster_dict[int(label)].append({
                    "id": point.id,
                    "point": point,
                    "index": i,
                })

            # 处理每个簇（纯 DBSCAN，无 LLM 调用）
            for label, cluster in cluster_dict.items():
                if label == -1:
                    # 噪声点：都视为独立块
                    for item in cluster:
                        point = item["point"]
                        block_id = point.payload.get("block_id")
                        if block_id not in seen_blocks:
                            seen_blocks.add(block_id)
                            knowledge_pool["unique_blocks"].append(self._make_block(point, genre, topic))
                elif len(cluster) == 1:
                    # 独有块
                    point = cluster[0]["point"]
                    block_id = point.payload.get("block_id")
                    if block_id not in seen_blocks:
                        seen_blocks.add(block_id)
                        knowledge_pool["unique_blocks"].append(self._make_block(point, genre, topic))
                else:
                    # 多块簇：保留文本最长/质量最好的块
                    best_item = max(cluster, key=lambda item: len(item["point"].payload.get("block_text", "")))
                    point = best_item["point"]
                    block_id = point.payload.get("block_id")
                    if block_id not in seen_blocks:
                        seen_blocks.add(block_id)
                        knowledge_pool["unique_blocks"].append(self._make_block(point, genre, topic))

        print(f"[Dedup] 去重完成: {len(knowledge_pool['unique_blocks'])} 唯一条目, "
              f"{len(knowledge_pool['merge_groups'])} 待融合组, "
              f"{len(knowledge_pool['conflict_groups'])} 争议组", flush=True)
        return knowledge_pool

    def _make_block(self, point, genre: str, topic: str) -> dict:
        """构建知识块字典"""
        return {
            "block_id": point.payload.get("block_id"),
            "text": point.payload.get("block_text"),
            "source_book": point.payload.get("source_book"),
            "genre_tags": [genre],
            "topic_tags": [topic],
        }
