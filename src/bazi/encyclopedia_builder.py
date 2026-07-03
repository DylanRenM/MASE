"""阶段4: 百科全书编排引擎"""

import json
from pathlib import Path
from .config import config
from .content_vectorizer import GENRE_TAGS, TOPIC_TAGS


class EncyclopediaBuilder:
    """百科全书编排器"""

    ENTRY_PROMPT = """你是一个八字命理编撰专家。请基于以下来自多本书籍的互补内容，撰写一条百科全书条目。

条目主题: {genre} × {topic}

素材块:
{source_blocks}

如果有多个来源对同一话题提供了互补信息，请融合为一篇连贯的阐述。
如果有观点分歧，请在"流派分歧"部分标注。

输出格式（Markdown）:

## 核心观点
（融合所有互补块，提炼出核心观点，2-3段）

## 各家论述
{quote_sections}

## 流派分歧
（如有冲突观点，逐一标注来源和观点，没有则写"暂无"）

## 经典命例
（如有案例块，列出；没有则写"暂无"）

## 参见
（列出本专题在其他流派中的视角，用 [流派·专题] 格式）"""

    def __init__(self):
        pass

    def _format_source_blocks(self, blocks: list[dict]) -> str:
        """格式化素材块为Prompt"""
        parts = []
        for i, block in enumerate(blocks):
            parts.append(
                f"[块{i+1}] 来源:《{block.get('source_book', '未知')}》\n"
                f"内容: {block.get('text', '')[:800]}"
            )
        return "\n\n".join(parts)

    def _format_quote_sections(self, blocks: list[dict]) -> str:
        """生成引用小节"""
        parts = []
        for block in blocks:
            parts.append(
                f"> 来源:《{block.get('source_book', '未知')}》\n"
                f"> \"{block.get('text', '')[:300]}...\""
            )
        return "\n\n".join(parts) if parts else "暂无引用"

    def build_entry(self, genre: str, topic: str, blocks: list[dict]) -> dict:
        """构建一个百科条目（无LLM，直接拼接块内容）"""
        if not blocks:
            return {"genre": genre, "topic": topic, "content": "暂无内容"}

        # 去重后按来源分组
        from collections import defaultdict
        by_source = defaultdict(list)
        for block in blocks:
            source = block.get("source_book", "未知来源")
            by_source[source].append(block)

        # 构建条目标题和内容
        parts = [f"## {genre} · {topic}\n"]
        parts.append(f"共收录 {len(blocks)} 段相关内容，来自 {len(by_source)} 本书籍。\n")

        for source, source_blocks in by_source.items():
            parts.append(f"\n### 《{source}》\n")
            for block in source_blocks:
                text = block.get("text", "")
                if text:
                    parts.append(f"\n{text.strip()}\n")

        content = "\n".join(parts)

        # 生成参见链接
        see_also = []
        for g in GENRE_TAGS:
            if g != genre:
                see_also.append(f"{g}·{topic}")

        return {
            "genre": genre,
            "topic": topic,
            "content": content,
            "see_also": see_also,
            "source_count": len(blocks),
        }

    def build_encyclopedia(self, knowledge_pool: dict) -> dict:
        """从知识池构建完整百科全书 JSON — 双索引结构"""
        all_blocks = knowledge_pool.get("unique_blocks", [])
        all_blocks.extend(knowledge_pool.get("distinct_blocks", []))

        # 按流派×专题分组（使用单主标签）
        by_genre = {}
        for block in all_blocks:
            genre_tags = block.get("genre_tags", [])
            topic_tags = block.get("topic_tags", [])
            primary_genre = genre_tags[0] if genre_tags else "综合"
            primary_topic = topic_tags[0] if topic_tags else "基础理论"

            by_genre.setdefault(primary_genre, {}).setdefault(primary_topic, []).append(block)

        # 为 by_genre 生成条目
        for genre, topics in by_genre.items():
            for topic, blocks in topics.items():
                entry = self.build_entry(genre, topic, blocks)
                topics[topic] = entry

        # 生成反向索引: by_topic（专题→流派）
        by_topic = {}
        for genre, topics in by_genre.items():
            for topic, entry in topics.items():
                by_topic.setdefault(topic, {})[genre] = entry

        return {"by_genre": by_genre, "by_topic": by_topic}

    def build_case_database(self, case_blocks: list[dict]) -> list[dict]:
        """构建命例数据库"""
        cases = []
        for block in case_blocks:
            cases.append({
                "case_id": block.get("block_id", ""),
                "text": block.get("text", ""),
                "source_book": block.get("source_book", ""),
                "topic_tags": block.get("topic_tags", []),
                "genre_tags": block.get("genre_tags", []),
                # 八字特征待 LLM 提取
                "bazi_features": [],
            })
        return cases

    def save(self, encyclopedia: dict, cases: list[dict]):
        """保存百科和命例到 JSON 文件"""
        config.encyclopedia_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config.encyclopedia_path, "w", encoding="utf-8") as f:
            json.dump(encyclopedia, f, ensure_ascii=False, indent=2)

        with open(config.cases_path, "w", encoding="utf-8") as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
