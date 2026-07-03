#!/usr/bin/env python3
"""将百科全书导出为独立的静态HTML文件（使用marked.js渲染）"""
import json
import re
import sys
from pathlib import Path


# 兜底广告过滤（LLM未能清理的残留）
_AD_PATTERN = re.compile(
    r"(?:添加|加|联系)?微信[：:]\s*[a-zA-Z0-9_\-]{4,}|"
    r"公众号[：:]\s*\S+|"
    r"www\.[a-zA-Z0-9_\-.]+\.[a-z]{2,}|"
    r"http[s]?://[^\s]+|"
    r"好又全资源网|"
    r"命理预测，更多命理资料获取",
    re.IGNORECASE,
)


def load_json(path="data/encyclopedia.json"):
    with open(path) as f:
        return json.load(f)


def generate_html(encyclopedia_data: dict, cases_data: list = None):
    """生成独立HTML"""
    by_genre = encyclopedia_data.get("by_genre", {})

    # 构建条目列表
    genres = []
    for genre_name in sorted(by_genre.keys()):
        topics_dict = by_genre[genre_name]  # {topic_name: entry_dict, ...}
        topics = []
        for topic_name, entry in sorted(topics_dict.items()):
            if not entry:
                continue
            content = entry.get("content", "")
            # 过滤 [AD] 垃圾行（LLM规范化标记）
            lines = content.split("\n")
            clean_lines = [l for l in lines if not l.strip().startswith("[AD]")]
            content = "\n".join(clean_lines)
            # 兜底正则过滤（LLM未能清理的广告残留）
            content = _AD_PATTERN.sub("", content)
            topics.append({
                "topic": topic_name,
                "content": content,
                "source_count": entry.get("source_count", 0),
                "block_count": entry.get("block_count", 0),
                "see_also": entry.get("see_also", []),
            })
        topics.sort(key=lambda t: t["topic"])
        genres.append({
            "name": genre_name,
            "topics": topics,
        })

    genres.sort(key=lambda g: g["name"])
    total_topics = sum(len(g["topics"]) for g in genres)

    # 命例数据（如果有）
    case_count = len(cases_data) if cases_data else 0
    cases_json = json.dumps(cases_data or [], ensure_ascii=False)

    encyclopedia_json = json.dumps(genres, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>八字命理百科全书</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; display: flex; height: 100vh; overflow: hidden; background: #f5f0e8; }}
#sidebar {{ width: 280px; min-width: 280px; height: 100vh; overflow-y: auto; background: #2c2416; color: #e8dcc8; display: flex; flex-direction: column; }}
#sidebar h2 {{ padding: 20px 16px 12px; font-size: 18px; color: #f0c060; border-bottom: 1px solid #4a3a20; }}
.view-tabs {{ display: flex; margin: 8px 12px; border-radius: 4px; overflow: hidden; border: 1px solid #5a4a28; }}
.view-tab {{ flex: 1; padding: 7px 0; font-size: 12px; cursor: pointer; text-align: center; border: none; color: #8a7a50; background: #352a18; }}
.view-tab.active {{ background: #c4b070; color: #fff; }}
.view-tab + .view-tab {{ border-left: 1px solid #5a4a28; }}
#search-box {{ margin: 4px 12px 8px; padding: 7px 10px; background: #3a2e1a; border: 1px solid #5a4a28; border-radius: 6px; color: #e8dcc8; font-size: 12px; outline: none; }}
#search-box::placeholder {{ color: #8a7a50; }}
.genre-group {{ border-bottom: 1px solid #3a2e1a; }}
.genre-title {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; cursor: pointer; font-size: 14px; font-weight: 600; color: #d4b860; background: #352a18; user-select: none; }}
.genre-title:hover {{ background: #3e321c; }}
.genre-title .arrow {{ font-size: 10px; transition: transform 0.2s; }}
.genre-title .arrow.open {{ transform: rotate(90deg); }}
.genre-title .count {{ font-size: 11px; color: #8a7a50; font-weight: normal; }}
.topics-list {{ display: none; }}
.topics-list.open {{ display: block; }}
.topic-item {{ padding: 8px 16px 8px 32px; cursor: pointer; font-size: 13px; color: #c4b898; border-left: 3px solid transparent; transition: all 0.15s; }}
.topic-item:hover {{ background: #3e321c; color: #f0d060; }}
.topic-item.active {{ background: #4a3a20; color: #f0c040; border-left-color: #f0c040; }}
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
#content .see-also {{ margin-top: 24px; padding-top: 16px; border-top: 1px solid #d4c4a0; }}
#content .see-also a {{ color: #5a3a10; cursor: pointer; text-decoration: underline; }}
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
    <div id="stats-bar">共 {len(genres)} 流派 · {total_topics} 专题 · {case_count} 命例</div>
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

// Markdown rendering via marked.js
function renderMd(md) {{
    if (!md) return '';
    if (typeof marked === 'undefined') {{
        return '<p>' + md.replace(/\\n/g, '<br>') + '</p>';
    }}
    try {{
        return marked.parse(md, {{ breaks: true, gfm: true }});
    }} catch(e) {{
        return '<p>' + md.replace(/\\n/g, '<br>') + '</p>';
    }}
}}

function buildTree(genres) {{
    const tree = document.getElementById('tree');
    tree.innerHTML = '';
    genres.forEach(function(g, gi) {{
        const group = document.createElement('div');
        group.className = 'genre-group';
        group.setAttribute('data-genre', g.name);

        const title = document.createElement('div');
        title.className = 'genre-title';
        title.innerHTML = '<span class="arrow">▶</span> ' + g.name + ' <span class="count">' + g.topics.length + '专题</span>';
        title.onclick = function() {{ toggleGenre(gi, title); }};

        const list = document.createElement('div');
        list.className = 'topics-list';
        list.id = 'topics-' + gi;

        g.topics.forEach(function(t, ti) {{
            const item = document.createElement('div');
            item.className = 'topic-item';
            item.textContent = t.topic + ' (' + t.block_count + ')';
            item.onclick = function(e) {{ e.stopPropagation(); selectTopic(gi, ti, item); }};
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
    document.querySelectorAll('.topic-item').forEach(function(el) {{ el.classList.remove('active'); }});
    itemEl.classList.add('active');
    activeGenre = gi;
    activeTopic = ti;
    renderContent(ENCYCLOPEDIA[gi], ENCYCLOPEDIA[gi].topics[ti]);
}}

function renderContent(genre, topic) {{
    const content = document.getElementById('content');
    const meta = '<div class="meta"><span>来源: ' + topic.source_count + '本书</span><span>内容块: ' + topic.block_count + '条</span></div>';
    let seeAlso = '';
    if (topic.see_also && topic.see_also.length > 0) {{
        let links = topic.see_also.map(function(s) {{ return '<a onclick="navigateTo(\\'' + s + '\\')">' + s + '</a>'; }}).join(' · ');
        seeAlso = '<div class="see-also"><strong>参见：</strong>' + links + '</div>';
    }}
    content.innerHTML = '<h1>' + genre.name + ' · ' + topic.topic + '</h1>' + meta + renderMd(topic.content) + seeAlso;
    content.scrollTop = 0;
}}

function navigateTo(entryKey) {{
    // entryKey format: "流派/专题"
    const parts = entryKey.split('/');
    if (parts.length < 2) return;
    const genreName = parts[0];
    const topicName = parts.slice(1).join('/');
    for (let gi = 0; gi < ENCYCLOPEDIA.length; gi++) {{
        if (ENCYCLOPEDIA[gi].name === genreName) {{
            const g = ENCYCLOPEDIA[gi];
            for (let ti = 0; ti < g.topics.length; ti++) {{
                if (g.topics[ti].topic === topicName) {{
                    // Expand the genre
                    const list = document.getElementById('topics-' + gi);
                    const title = document.querySelector('[data-genre="' + genreName + '"] .genre-title');
                    if (list && title) {{
                        list.classList.add('open');
                        title.querySelector('.arrow').classList.add('open');
                    }}
                    // Select the topic
                    const items = document.getElementById('topics-' + gi).querySelectorAll('.topic-item');
                    selectTopic(gi, ti, items[ti]);
                    return;
                }}
            }}
        }}
    }}
}}

function filterTree() {{
    const q = document.getElementById('search-box').value.toLowerCase();
    const groups = document.querySelectorAll('.genre-group');
    groups.forEach(function(g) {{
        const gn = (g.getAttribute('data-genre') || '').toLowerCase();
        const items = g.querySelectorAll('.topic-item');
        let anyVisible = false;
        items.forEach(function(item) {{
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
    enc_data = load_json("data/encyclopedia.json")

    # 尝试加载命例
    cases_data = None
    if Path("data/cases.json").exists():
        try:
            with open("data/cases.json") as f:
                cases_data = json.load(f)
        except Exception:
            pass

    html = generate_html(enc_data, cases_data)
    output = "八字命理百科全书.html"
    with open(output, "w", encoding="utf-8") as f:
        f.write(html)
    size_mb = Path(output).stat().st_size / 1024 / 1024
    print(f"导出完成: {output}")
    print(f"文件大小: {size_mb:.1f} MB")
    print(f"可直接用浏览器打开")
