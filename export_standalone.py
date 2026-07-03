#!/usr/bin/env python3
"""将百科全书导出为独立的静态HTML文件"""
import json
import sys
from pathlib import Path

def load_encyclopedia(path="data/encyclopedia.json"):
    with open(path) as f:
        return json.load(f)

def markdown_to_html(text):
    """简单的 Markdown -> HTML 转换"""
    lines = text.split('\n')
    result = []
    in_code = False
    for line in lines:
        if line.startswith('```'):
            in_code = not in_code
            if in_code:
                result.append('<pre><code>')
            else:
                result.append('</code></pre>')
            continue
        if in_code:
            result.append(line)
            continue
        # headers
        if line.startswith('### '):
            result.append(f'<h3>{line[4:]}</h3>')
        elif line.startswith('## '):
            result.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith('# '):
            result.append(f'<h1>{line[2:]}</h1>')
        elif line.startswith('---'):
            result.append('<hr>')
        elif line.startswith('- '):
            result.append(f'<li>{md_inline(line[2:])}</li>')
        else:
            stripped = md_inline(line)
            if stripped:
                result.append(f'<p>{stripped}</p>')
    return '\n'.join(result)

def md_inline(text):
    """处理行内格式：粗体、斜体"""
    import re
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text

def generate_html(data):
    """生成独立HTML"""
    genres = []
    if isinstance(data, dict):
        for genre_name, topics in data.items():
            genre_topics = []
            if isinstance(topics, dict):
                for topic_name, entry in topics.items():
                    genre_topics.append({
                        "topic": topic_name,
                        "content": markdown_to_html(entry.get("content", "")),
                        "source_count": entry.get("source_count", 0),
                        "block_count": entry.get("block_count", 0),
                        "see_also": entry.get("see_also", []),
                    })
            genre_topics.sort(key=lambda t: t["topic"])
            genres.append({
                "name": genre_name,
                "topics": genre_topics,
            })
    elif isinstance(data, list):
        for g in data:
            genre_topics = []
            for t in g.get("topics", []):
                genre_topics.append({
                    "topic": t.get("topic", ""),
                    "content": markdown_to_html(t.get("content", "")),
                    "source_count": t.get("source_count", 0),
                    "block_count": t.get("block_count", 0),
                    "see_also": t.get("see_also", []),
                })
            genre_topics.sort(key=lambda t: t["topic"])
            genres.append({
                "name": g.get("genre", ""),
                "topics": genre_topics,
            })

    genres.sort(key=lambda g: g["name"])

    # 统计
    total_topics = sum(len(g["topics"]) for g in genres)
    total_blocks = sum(
        t["block_count"] for g in genres for t in g["topics"]
    )

    encyclopedia_json = json.dumps(genres, ensure_ascii=False)

    # 内联CSS
    css = """/* 内联CSS */"""  # placeholder, will be replaced

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>八字命理百科全书</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; display: flex; height: 100vh; overflow: hidden; background: #f5f0e8; }}
#sidebar {{ width: 280px; min-width: 280px; height: 100vh; overflow-y: auto; background: #2c2416; color: #e8dcc8; display: flex; flex-direction: column; }}
#sidebar h2 {{ padding: 20px 16px 12px; font-size: 18px; color: #f0c060; border-bottom: 1px solid #4a3a20; }}
.genre-group {{ border-bottom: 1px solid #3a2e1a; }}
.genre-title {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; cursor: pointer; font-size: 15px; font-weight: 600; color: #d4b860; background: #352a18; user-select: none; }}
.genre-title:hover {{ background: #3e321c; }}
.genre-title .arrow {{ font-size: 10px; transition: transform 0.2s; }}
.genre-title .arrow.open {{ transform: rotate(90deg); }}
.genre-title .count {{ font-size: 11px; color: #8a7a50; font-weight: normal; }}
.topics-list {{ display: none; }}
.topics-list.open {{ display: block; }}
.topic-item {{ padding: 10px 16px 10px 32px; cursor: pointer; font-size: 14px; color: #c4b898; border-left: 3px solid transparent; transition: all 0.15s; }}
.topic-item:hover {{ background: #3e321c; color: #f0d060; }}
.topic-item.active {{ background: #4a3a20; color: #f0c040; border-left-color: #f0c040; }}
#search-box {{ margin: 0 12px 12px; padding: 8px 12px; background: #3a2e1a; border: 1px solid #5a4a28; border-radius: 6px; color: #e8dcc8; font-size: 13px; outline: none; }}
#search-box::placeholder {{ color: #8a7a50; }}
#content {{ flex: 1; height: 100vh; overflow-y: auto; padding: 32px 48px; }}
#content h1 {{ font-size: 24px; color: #5a3a10; border-bottom: 2px solid #c4a060; padding-bottom: 12px; margin-bottom: 24px; }}
#content h2 {{ font-size: 20px; color: #6a4a18; margin: 28px 0 14px; }}
#content h3 {{ font-size: 17px; color: #7a5a28; margin: 22px 0 10px; }}
#content p {{ font-size: 15px; line-height: 1.85; color: #4a3a20; margin-bottom: 12px; text-align: justify; }}
#content li {{ font-size: 15px; line-height: 1.75; color: #4a3a20; margin-bottom: 4px; margin-left: 20px; }}
#content hr {{ border: none; border-top: 1px solid #d4c4a0; margin: 16px 0; }}
#content strong {{ color: #5a3a10; }}
#content pre {{ background: #f0e8d8; padding: 12px 16px; border-radius: 6px; font-size: 14px; line-height: 1.6; overflow-x: auto; margin: 12px 0; border: 1px solid #d4c4a0; }}
#content code {{ font-family: "SF Mono", "Fira Code", monospace; font-size: 13px; }}
#content .meta {{ color: #8a7a50; font-size: 13px; margin-bottom: 20px; }}
#content .meta span {{ margin-right: 16px; }}
#empty-state {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #8a7a50; }}
#empty-state .icon {{ font-size: 64px; margin-bottom: 16px; opacity: 0.4; }}
#empty-state p {{ font-size: 16px; }}
#stats-bar {{ padding: 10px 16px; font-size: 12px; color: #8a7a50; border-top: 1px solid #3a2e1a; }}
@media (max-width: 768px) {{
    body {{ flex-direction: column; }}
    #sidebar {{ width: 100%; min-width: unset; height: auto; max-height: 40vh; }}
    #content {{ padding: 20px 16px; }}
}}
</style>
</head>
<body>
<div id="sidebar">
    <h2>八字命理百科全书</h2>
    <input type="text" id="search-box" placeholder="搜索流派、专题..." oninput="filterTree()">
    <div id="tree"></div>
    <div id="stats-bar">共 {len(genres)} 流派 · {total_topics} 专题 · {total_blocks} 条内容</div>
</div>
<div id="content">
    <div id="empty-state">
        <div class="icon">📚</div>
        <p>请从左侧目录选择一个专题</p>
    </div>
</div>

<script>
const ENCYCLOPEDIA = {encyclopedia_json};

let activeGenre = null;
let activeTopic = null;

function buildTree(genres) {{
    const tree = document.getElementById('tree');
    tree.innerHTML = '';
    genres.forEach((g, gi) => {{
        const group = document.createElement('div');
        group.className = 'genre-group';
        group.setAttribute('data-genre', g.name);

        const title = document.createElement('div');
        title.className = 'genre-title';
        title.innerHTML = `<span class="arrow">▶</span> ${{g.name}} <span class="count">${{g.topics.length}}专题</span>`;
        title.onclick = () => toggleGenre(gi, title);

        const list = document.createElement('div');
        list.className = 'topics-list';
        list.id = 'topics-' + gi;

        g.topics.forEach((t, ti) => {{
            const item = document.createElement('div');
            item.className = 'topic-item';
            item.textContent = t.topic + ' (' + t.block_count + ')';
            item.onclick = (e) => {{ e.stopPropagation(); selectTopic(gi, ti, item); }};
            list.appendChild(item);
        }});

        group.appendChild(title);
        group.appendChild(list);
        tree.appendChild(group);
    }});
}}

function toggleGenre(gi, titleEl) {{
    const list = document.getElementById('topics-' + gi);
    const arrow = titleEl.querySelector('.arrow');
    list.classList.toggle('open');
    arrow.classList.toggle('open');
}}

function selectTopic(gi, ti, itemEl) {{
    document.querySelectorAll('.topic-item').forEach(el => el.classList.remove('active'));
    itemEl.classList.add('active');
    activeGenre = gi;
    activeTopic = ti;
    renderContent(ENCYCLOPEDIA[gi], ENCYCLOPEDIA[gi].topics[ti]);
}}

function renderContent(genre, topic) {{
    const content = document.getElementById('content');
    const meta = `<div class="meta"><span>来源: ${{topic.source_count}}本书</span><span>内容块: ${{topic.block_count}}条</span></div>`;
    let seeAlso = '';
    if (topic.see_also && topic.see_also.length > 0) {{
        seeAlso = '<hr><p><strong>参见：</strong>' + topic.see_also.join(' · ') + '</p>';
    }}
    content.innerHTML = `<h1>${{genre.name}} · ${{topic.topic}}</h1>${{meta}}${{topic.content}}${{seeAlso}}`;
    content.scrollTop = 0;
}}

function filterTree() {{
    const q = document.getElementById('search-box').value.toLowerCase();
    const groups = document.querySelectorAll('.genre-group');
    groups.forEach(g => {{
        const gn = (g.getAttribute('data-genre') || '').toLowerCase();
        const items = g.querySelectorAll('.topic-item');
        let anyVisible = false;
        items.forEach(item => {{
            const text = item.textContent.toLowerCase();
            if (!q || gn.includes(q) || text.includes(q)) {{
                item.style.display = '';
                anyVisible = true;
            }} else {{
                item.style.display = 'none';
            }}
        }});
        g.style.display = (!q || gn.includes(q) || anyVisible) ? '' : 'none';
    }});
}}

buildTree(ENCYCLOPEDIA);
</script>
</body>
</html>"""

if __name__ == "__main__":
    data = load_encyclopedia()
    html = generate_html(data)
    output = "八字命理百科全书.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    import os
    size_mb = os.path.getsize(output) / 1024 / 1024
    print(f"✅ 导出完成: {output}")
    print(f"   文件大小: {size_mb:.1f} MB")
    print(f"   可直接用浏览器打开")
