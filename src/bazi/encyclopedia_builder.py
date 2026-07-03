"""阶段4: 百科全书编排引擎"""

import json
import time
from pathlib import Path
from .config import config
from .content_vectorizer import LLMClassifier, GENRE_TAGS, TOPIC_TAGS


class EncyclopediaBuilder:
    """百科全书编排器"""

    ENTRY_PROMPT = """你是一个八字命理编撰专家。请基于以下来自多本书籍的素材摘要，撰写百科全书条目。

条目主题: {genre} × {topic}
共 {block_count} 段素材，来自 {source_count} 本书籍。

素材摘要:
{source_blocks}

要求：
1. 提炼核心观点（2-3段）
2. 标注不同来源的不同观点（如有）
3. 保持学术严谨，不编造内容
4. 【经典命例】提取所有 case_study 类型的命例，按专题分类（婚姻/财运/事业/健康/六亲/学业/性格/用神/大运/流年）
   - 每个命例标注：八字干支、性别、结论摘要、来源书籍
   - 命例独立列出，不混入理论分析中
5. 【垃圾跳过】素材中带有 [AD] 标记的行是广告/水印，直接忽略，不要纳入任何分析
6. 用 Markdown 格式

输出格式：

## 核心观点
（融合提炼）

## 各家视角
（分来源简述不同观点，没有则写"各书观点基本一致"）

## 经典命例
（如有命例，按专题列出；无则写"本条目暂无命例"）"""

    def __init__(self):
        self._classifier = None

    @property
    def classifier(self):
        if self._classifier is None:
            self._classifier = LLMClassifier()
        return self._classifier

    def _format_source_blocks(self, blocks: list[dict], max_blocks: int = 15) -> str:
        """格式化素材块为 Prompt（精选 + 截断 + 去广告，控制 token 数）"""
        # 按文本长度排序，取最长的 max_blocks 块作为代表性素材
        sorted_blocks = sorted(blocks, key=lambda b: len(b.get("text", "")), reverse=True)
        selected = sorted_blocks[:max_blocks]

        parts = []
        for i, block in enumerate(selected):
            text = block.get("text", "")
            # 过滤 [AD] 垃圾行
            lines = text.split("\n")
            clean_lines = [l for l in lines if not l.strip().startswith("[AD]")]
            text = "\n".join(clean_lines)
            text = text[:400]  # 每块最多400字
            source = block.get("source_book", "未知")
            parts.append(f"[素材{i+1}]《{source}》: {text}")
        return "\n\n".join(parts)

    def build_entry(self, genre: str, topic: str, blocks: list[dict]) -> dict:
        """构建百科条目：LLM 摘要 + 完整原文"""
        if not blocks:
            return {"genre": genre, "topic": topic, "content": "暂无内容", "sources": []}

        # 按来源去重统计
        from collections import defaultdict
        by_source = defaultdict(list)
        for block in blocks:
            source = block.get("source_book", "未知来源")
            by_source[source].append(block)

        # 生成参见链接
        see_also = []
        for g in GENRE_TAGS:
            if g != genre:
                see_also.append(f"{g}·{topic}")

        # LLM 摘要
        source_text = self._format_source_blocks(blocks)
        prompt = self.ENTRY_PROMPT.format(
            genre=genre,
            topic=topic,
            block_count=len(blocks),
            source_count=len(by_source),
            source_blocks=source_text,
        )

        try:
            summary = self.classifier._call_llm(prompt)
        except Exception as e:
            summary = f"*LLM摘要生成失败: {e}*"

        # 构建完整内容：LLM摘要 + 原文出处
        parts = [summary, "", "---", "", "## 原始素材"]
        parts.append(f"共收录 {len(blocks)} 段相关内容，来自 {len(by_source)} 本书籍。\n")

        for source, source_blocks in sorted(by_source.items()):
            parts.append(f"\n### 《{source}》（{len(source_blocks)}段）\n")
            for block in source_blocks:
                text = block.get("text", "")
                if text:
                    # 过滤 [AD] 垃圾行
                    lines = text.split("\n")
                    clean_lines = [l for l in lines if not l.strip().startswith("[AD]")]
                    text = "\n".join(clean_lines)
                    if text.strip():
                        parts.append(f"\n{text.strip()}\n")

        content = "\n".join(parts)

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

        # 为 by_genre 生成条目（带进度）
        entry_count = 0
        total_entries = sum(len(topics) for topics in by_genre.values())
        for genre, topics in by_genre.items():
            for topic, blocks in topics.items():
                entry_count += 1
                print(f"[百科] 生成进度: {entry_count}/{total_entries} ({genre}/{topic}, {len(blocks)}块)",
                      flush=True)
                t0 = time.time()
                entry = self.build_entry(genre, topic, blocks)
                topics[topic] = entry
                elapsed = time.time() - t0
                print(f"        耗时: {elapsed:.1f}s", flush=True)

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
