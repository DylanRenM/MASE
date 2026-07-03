#!/usr/bin/env python3
"""快速重建百科（跳过LLM去重，直接从Qdrant读取）"""
import sys, json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from bazi.qdrant_store import get_client, get_vectors_by_tags
    from bazi.content_vectorizer import GENRE_TAGS, TOPIC_TAGS
    from bazi.config import config
    from bazi.database import add_pipeline_log

    client = get_client()
    print("Qdrant 连接成功", flush=True)

    add_pipeline_log("global", "quick_rebuild", "running", "开始快速百科重建")

    # 从Qdrant读取所有向量
    all_points, _ = client.scroll(
        collection_name=config.qdrant_collection,
        limit=10000,
        with_payload=True,
        with_vectors=False,
    )
    print(f"读取到 {len(all_points)} 条向量", flush=True)

    # 按流派×专题分组，去重（按文本相似度？简单按文本精确匹配去重）
    seen_texts = set()
    grouped = defaultdict(list)

    for pt in all_points:
        payload = pt.payload
        text = (payload.get("block_text", "") or "")[:200].strip()
        if text in seen_texts:
            continue
        seen_texts.add(text)

        genre_tags = payload.get("genre_tags", ["综合"])
        topic_tags = payload.get("topic_tags", ["基础理论"])
        source = payload.get("source_book", "未知")

        for g in genre_tags:
            for t in topic_tags:
                grouped[(g, t)].append({
                    "text": payload.get("block_text", ""),
                    "source": source,
                    "content_type": payload.get("content_type", ""),
                })

    print(f"去重后: {len(grouped)} 个 (流派×专题) 组合", flush=True)

    # 构建百科JSON
    encyclopedia = {}
    cases = []

    for (genre, topic), blocks in sorted(grouped.items()):
        if genre not in encyclopedia:
            encyclopedia[genre] = {}

        # 提取案例块
        case_blocks = [b for b in blocks if b.get("content_type") in ("case_study", "mixed")]
        theory_blocks = [b for b in blocks if b.get("content_type") in ("theory", "mixed")]

        for b in case_blocks:
            cases.append({
                "topic": topic,
                "genre": genre,
                "text": b["text"],
                "source": b["source"],
            })

        # 构建条目内容
        sources = list(set(b["source"] for b in blocks))
        blocks_text = "\n\n---\n\n".join(
            f"**来源《{b['source']}》**\n{b['text'][:1000]}"
            for b in blocks[:10]
        )

        see_also = []
        for g in GENRE_TAGS:
            if g != genre:
                see_also.append(f"{g}·{topic}")

        encyclopedia[genre][topic] = {
            "genre": genre,
            "topic": topic,
            "content": f"## {genre} · {topic}\n\n"
                       f"共收录 {len(blocks)} 条相关内容，来自 {len(sources)} 本书籍。\n\n"
                       f"{blocks_text}\n\n"
                       f"## 参见\n" + "\n".join(f"- {sa}" for sa in see_also),
            "see_also": see_also,
            "source_count": len(sources),
            "block_count": len(blocks),
        }

    # 保存
    config.encyclopedia_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config.encyclopedia_path, "w", encoding="utf-8") as f:
        json.dump(encyclopedia, f, ensure_ascii=False, indent=2)
    with open(config.cases_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    # 统计
    total_entries = sum(len(topics) for topics in encyclopedia.values())
    print(f"\n{'='*50}", flush=True)
    print(f"百科重建完成!", flush=True)
    print(f"  流派数: {len(encyclopedia)}", flush=True)
    print(f"  条目数: {total_entries}", flush=True)
    print(f"  命例数: {len(cases)}", flush=True)
    for genre in sorted(encyclopedia.keys()):
        print(f"  {genre}: {len(encyclopedia[genre])} 个专题", flush=True)

    add_pipeline_log("global", "quick_rebuild", "done",
                     f"百科重建完成: {total_entries} 条目, {len(cases)} 命例")


if __name__ == "__main__":
    main()
