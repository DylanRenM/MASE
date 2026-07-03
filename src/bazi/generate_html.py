"""生成独立 HTML — 百科 + 命例库一体化"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime


# JS 字符串字面量中非法的 Unicode 字符（JSON 合法但会破坏嵌入 JS）
_JS_UNSAFE_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\u0085\u2028\u2029]")

def clean_for_js(text: str) -> str:
    """移除 JS 字符串字面量中非法的 Unicode 控制字符"""
    return _JS_UNSAFE_CHARS.sub("", text)


def build_light_entry(entry: dict, genre: str, topic: str) -> dict:
    """构建轻量百科条目：保留LLM摘要，原文截断"""
    content = entry.get("content", "")
    source_blocks = entry.get("source_blocks", [])
    see_also = entry.get("see_also", [])
    source_count = entry.get("source_count", len(source_blocks))
    block_count = entry.get("block_count", 0)

    summary_part = content
    source_part = ""

    raw_marker = "原始素材"
    if raw_marker in content:
        idx = content.index(raw_marker)
        summary_part = content[:idx].strip()
        source_part = content[idx:]

    if len(source_part) > 1200:
        source_part = source_part[:1200] + "\n  ... (更多内容见完整版)"

    truncated = summary_part
    if source_part:
        truncated += "\n\n" + source_part
    if len(truncated) > 8000:
        truncated = truncated[:8000] + "\n  ... (更多内容见完整版)"

    return {
        "genre": clean_for_js(genre),
        "topic": clean_for_js(topic),
        "content": clean_for_js(truncated),
        "source_count": source_count,
        "block_count": block_count,
        "see_also": [clean_for_js(s) for s in see_also],
    }


def build_light_case(case: dict) -> dict:
    """构建轻量命例：清理JS非法字符 + 广告过滤 + 截断文本到80字"""
    text = clean_for_js(case.get("text", ""))
    if len(text) > 80:
        text = text[:80] + "…"
    return {
        "t": text,
        "s": clean_for_js(case.get("source_book", "未知")),
        "tp": [clean_for_js(t) for t in case.get("topic_tags", [])],
        "gn": [clean_for_js(g) for g in case.get("genre_tags", [])],
    }


def generate_html(encyclopedia: dict, cases: list, output_path: Path):
    by_genre = encyclopedia.get("by_genre", {})

    # 百科条目
    all_entries = []
    for genre, topics in sorted(by_genre.items()):
        for topic, entry in sorted(topics.items()):
            if not entry:
                continue
            all_entries.append(build_light_entry(entry, genre, topic))

    # 命例（全量但截断，分块嵌入以避免浏览器 JS 解析器过载）
    light_cases = [build_light_case(c) for c in cases]
    CHUNK = 5000
    case_chunks_json = []
    for i in range(0, len(light_cases), CHUNK):
        chunk = light_cases[i:i + CHUNK]
        chunk_json = json.dumps(chunk, ensure_ascii=False, separators=(",", ":"))
        # 校验：确保生成的 JSON 能被解析（捕获控制字符等边缘情况）
        try:
            json.loads(chunk_json)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"CASES chunk {i//CHUNK} JSON invalid: {e}") from e
        case_chunks_json.append(chunk_json)

    entries_json = json.dumps(all_entries, ensure_ascii=False, separators=(",", ":"))

    # 将 CASES 数据嵌入为 <script type="application/json"> 标签，避免 JS 内联解析
    # 防止 JSON 中的 </ 提前关闭 script 标签
    def escape_script_json(j: str) -> str:
        return j.replace("</", "<\\/")

    case_script_tags = ""
    for idx, chunk_json in enumerate(case_chunks_json):
        safe_json = escape_script_json(chunk_json)
        case_script_tags += f'<script id="cases-p{idx}" type="application/json">{safe_json}</script>\n'

    genres = sorted(by_genre.keys())
    first_genre = next(iter(by_genre.values())) if by_genre else {}
    all_topics = sorted(first_genre.keys())

    stats = {
        "genres": genres,
        "topics": all_topics,
        "entry_count": len(all_entries),
        "case_count": len(light_cases),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    stats_json = json.dumps(stats, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>八字命理百科全书</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; display: flex; height: 100vh; overflow: hidden; background: #f5f0e8; }}

#sidebar {{ width: 260px; min-width: 260px; height: 100vh; overflow-y: auto; background: #2c2416; color: #e8dcc8; display: flex; flex-direction: column; flex-shrink: 0; }}
#sidebar h2 {{ padding: 20px 16px 12px; font-size: 17px; color: #f0c060; border-bottom: 1px solid #4a3a20; }}

.view-tabs {{ display: flex; margin: 8px 12px; border-radius: 4px; overflow: hidden; border: 1px solid #5a4a28; }}
.view-tab {{ flex: 1; padding: 7px 0; font-size: 12px; cursor: pointer; text-align: center; border: none; color: #8a7a50; background: #352a18; }}
.view-tab.active {{ background: #c4b070; color: #fff; }}
.view-tab + .view-tab {{ border-left: 1px solid #5a4a28; }}

#search-box {{ margin: 4px 12px 8px; padding: 7px 10px; background: #3a2e1a; border: 1px solid #5a4a28; border-radius: 6px; color: #e8dcc8; font-size: 12px; outline: none; }}
#search-box::placeholder {{ color: #8a7a50; }}

.genre-group {{ border-bottom: 1px solid #3a2e1a; }}
.genre-title {{ display: flex; justify-content: space-between; align-items: center; padding: 9px 16px; cursor: pointer; font-size: 13px; font-weight: 600; color: #d4b860; background: #352a18; user-select: none; }}
.genre-title:hover {{ background: #3e321c; }}
.genre-title .arrow {{ font-size: 9px; transition: transform 0.2s; display: inline-block; margin-right: 4px; }}
.genre-title .arrow.open {{ transform: rotate(90deg); }}
.genre-title .count {{ font-size: 10px; color: #8a7a50; font-weight: normal; }}
.topics-list {{ display: none; }}
.topics-list.open {{ display: block; }}
.topic-item {{ padding: 7px 16px 7px 32px; cursor: pointer; font-size: 12px; color: #c4b898; border-left: 3px solid transparent; transition: all 0.15s; }}
.topic-item:hover {{ background: #3e321c; color: #f0d060; }}
.topic-item.active {{ background: #4a3a20; color: #f0c040; border-left-color: #f0c040; }}

#case-btn {{ margin: 6px 12px; padding: 8px 12px; background: #3e321c; border: 1px solid #5a4a28; border-radius: 6px; color: #d4b860; font-size: 12px; cursor: pointer; text-align: left; }}
#case-btn:hover {{ background: #4a3a20; }}
#case-btn .badge {{ float: right; font-size: 10px; color: #8a7a50; }}

#stats-bar {{ padding: 8px 16px; font-size: 11px; color: #8a7a50; border-top: 1px solid #3a2e1a; margin-top: auto; }}

#content {{ flex: 1; height: 100vh; overflow-y: auto; padding: 28px 40px; }}
#content h1 {{ font-size: 22px; color: #5a3a10; border-bottom: 2px solid #c4a060; padding-bottom: 10px; margin-bottom: 16px; }}
#content h2 {{ font-size: 18px; color: #6a4a18; margin: 24px 0 12px; }}
#content h3 {{ font-size: 16px; color: #7a5a28; margin: 18px 0 8px; }}
#content p {{ font-size: 14px; line-height: 1.85; color: #4a3a20; margin-bottom: 10px; text-align: justify; }}
#content li {{ font-size: 14px; line-height: 1.75; color: #4a3a20; margin-bottom: 3px; margin-left: 18px; }}
#content hr {{ border: none; border-top: 1px solid #d4c4a0; margin: 14px 0; }}
#content strong {{ color: #5a3a10; }}
#content pre {{ background: #f0e8d8; padding: 10px 14px; border-radius: 6px; font-size: 13px; line-height: 1.6; overflow-x: auto; margin: 10px 0; border: 1px solid #d4c4a0; }}
#content .meta {{ color: #8a7a50; font-size: 12px; margin-bottom: 16px; }}
#content .meta span {{ margin-right: 14px; }}
#content .see-also {{ margin-top: 20px; padding: 14px; background: #f0e8d8; border-radius: 8px; }}
#content .see-also h3 {{ font-size: 14px; margin-bottom: 6px; }}
#content .see-also a {{ display: inline-block; margin: 3px 6px 3px 0; padding: 3px 10px; background: #e8dcc8; border-radius: 4px; font-size: 12px; color: #5a3a10; text-decoration: none; cursor: pointer; }}
#content .see-also a:hover {{ background: #d4c4a0; }}
#content .more-hint {{ color: #b4a470; font-size: 12px; font-style: italic; margin-top: 10px; }}

.empty-state {{ display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #8a7a50; }}
.empty-state .icon {{ font-size: 56px; margin-bottom: 14px; opacity: 0.4; }}
.empty-state p {{ font-size: 15px; }}

.case-filters {{ display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; padding: 10px; background: #faf7f2; border-radius: 6px; }}
.case-filters select, .case-filters input {{ padding: 5px 8px; border: 1px solid #d0c8b8; border-radius: 4px; font-size: 12px; }}
.case-filters input {{ flex: 1; min-width: 120px; }}
.case-card {{ padding: 10px 14px; margin-bottom: 6px; border: 1px solid #e0d5c7; border-radius: 6px; }}
.case-card .case-source {{ font-size: 11px; color: #999; }}
.case-card .case-text {{ margin: 4px 0; line-height: 1.65; font-size: 13px; }}
.case-card .case-tags {{ display: flex; gap: 3px; flex-wrap: wrap; }}
.case-tag {{ font-size: 10px; padding: 1px 5px; background: #ede0c8; border-radius: 8px; color: #5c2d0a; }}
.loading {{ text-align: center; padding: 40px; color: #999; }}

@media (max-width: 768px) {{
    body {{ flex-direction: column; }}
    #sidebar {{ width: 100%; min-width: unset; height: auto; max-height: 35vh; }}
    #content {{ padding: 16px; }}
}}
</style>
</head>
<body>

<div id="sidebar">
    <h2>&#x1F4DA; 八字命理百科全书</h2>
    <div class="view-tabs">
        <button class="view-tab active" id="tabGenre" onclick="switchView('genre')">按流派</button>
        <button class="view-tab" id="tabTopic" onclick="switchView('topic')">按专题</button>
    </div>
    <input type="text" id="search-box" placeholder="&#x1F50D; 搜索条目..." oninput="doSearch(this.value)">
    <div id="tree"></div>
    <button id="case-btn" onclick="showCases()">
        &#x1F4CB; 命例数据库 <span class="badge" id="caseBadge">{len(light_cases):,} 条</span>
    </button>
    <div id="stats-bar"></div>
</div>

<div id="content">
    <div class="empty-state">
        <div class="icon">&#x1F4D6;</div>
        <p>请从左侧选择一个专题查看</p>
    </div>
</div>

{case_script_tags}

<script>
// ==== 数据 ====
var STATS = {stats_json};
var ENTRIES = {entries_json};
var CASES = null;

// ==== 全局状态 ====
var currentView = 'genre';
var entryMap = {{}};
var genreMap = {{}};
var topicMap = {{}};

// 建立索引
ENTRIES.forEach(function(e) {{
    entryMap[e.genre + "|" + e.topic] = e;
    if (!genreMap[e.genre]) genreMap[e.genre] = [];
    if (genreMap[e.genre].indexOf(e.topic) === -1) genreMap[e.genre].push(e.topic);
    if (!topicMap[e.topic]) topicMap[e.topic] = [];
    if (topicMap[e.topic].indexOf(e.genre) === -1) topicMap[e.topic].push(e.genre);
}});

// ==== 构建树 ====
var treeEl = document.getElementById('tree');
var sortedGenres = Object.keys(genreMap).sort();
var sortedTopics = Object.keys(topicMap).sort();

function renderGenreTree() {{
    var h = '';
    sortedGenres.forEach(function(genre, gi) {{
        h += '<div class="genre-group" data-g="' + genre + '">';
        h += '<div class="genre-title" onclick="toggleGroup(' + gi + ')">';
        h += '<span class="arrow" id="arr' + gi + '">&#9654;</span> ' + genre;
        h += '<span class="count">(' + genreMap[genre].length + ')</span>';
        h += '</div><div class="topics-list" id="tl' + gi + '">';
        genreMap[genre].sort().forEach(function(topic) {{
            h += '<div class="topic-item" data-g="' + genre + '" data-t="' + topic + '" onclick="showEntry(\\'' + genre + '\\',\\'' + topic + '\\')">' + topic + '</div>';
        }});
        h += '</div></div>';
    }});
    treeEl.innerHTML = h;
}}

function renderTopicTree() {{
    var h = '';
    sortedTopics.forEach(function(topic, ti) {{
        h += '<div class="genre-group" data-t="' + topic + '">';
        h += '<div class="genre-title" onclick="toggleGroup(' + ti + ')">';
        h += '<span class="arrow" id="arr' + ti + '">&#9654;</span> ' + topic;
        h += '<span class="count">(' + topicMap[topic].length + ')</span>';
        h += '</div><div class="topics-list" id="tl' + ti + '">';
        topicMap[topic].sort().forEach(function(genre) {{
            h += '<div class="topic-item" data-g="' + genre + '" data-t="' + topic + '" onclick="showEntry(\\'' + genre + '\\',\\'' + topic + '\\')">' + genre + '派</div>';
        }});
        h += '</div></div>';
    }});
    treeEl.innerHTML = h;
}}

function toggleGroup(i) {{
    var list = document.getElementById('tl' + i);
    var arr = document.getElementById('arr' + i);
    var open = list.classList.toggle('open');
    if (arr) {{ arr.classList.toggle('open', open); }}
}}

function switchView(view) {{
    if (currentView === view) return;
    currentView = view;
    document.getElementById('tabGenre').classList.toggle('active', view === 'genre');
    document.getElementById('tabTopic').classList.toggle('active', view === 'topic');
    document.getElementById('search-box').value = '';
    showEmpty();
    if (view === 'genre') renderGenreTree(); else renderTopicTree();
    updateStats();
}}

// ==== 搜索 ====
function doSearch(q) {{
    q = q.toLowerCase();
    document.querySelectorAll('.genre-group').forEach(function(g, gi) {{
        var text = g.textContent.toLowerCase();
        var items = g.querySelectorAll('.topic-item');
        var any = false;
        items.forEach(function(item) {{
            if (!q || text.indexOf(q) !== -1 || item.textContent.toLowerCase().indexOf(q) !== -1) {{
                item.style.display = ''; any = true;
            }} else {{ item.style.display = 'none'; }}
        }});
        g.style.display = (!q || any) ? '' : 'none';
        if (any && q) toggleGroup(gi);
    }});
}}

// ==== Markdown 渲染 ====
function renderMd(md) {{
    if (!md) return '';
    if (typeof marked === 'undefined') {{
        // Fallback: 简单的段落渲染
        return '<p>' + md.replace(/\\n/g, '<br>') + '</p>';
    }}
    try {{
        return marked.parse(md, {{ breaks: true, gfm: true }});
    }} catch(e) {{
        return '<p>' + md.replace(/\\n/g, '<br>') + '</p>';
    }}
}}

// ==== 渲染百科条目 ====
function showEntry(genre, topic) {{
    var entry = entryMap[genre + "|" + topic];
    var ct = document.getElementById('content');
    if (!entry) {{ ct.innerHTML = '<div class="empty-state"><div class="icon">&#x1F615;</div><p>该条目暂无内容</p></div>'; return; }}

    var see = '';
    if (entry.see_also && entry.see_also.length) {{
        see = '<div class="see-also"><h3>&#x1F517; 参见其他流派</h3>';
        entry.see_also.forEach(function(ref) {{
            var p = ref.split('·');
            see += '<a onclick="showEntry(\\'' + p[0].replace(/'/g,"\\\\'") + '\\',\\'' + p[1].replace(/'/g,"\\\\'") + '\\')">' + ref + '</a>';
        }});
        see += '</div>';
    }}

    var h = '<h1>' + entry.genre + ' · ' + entry.topic + '</h1>';
    h += '<div class="meta"><span>&#x1F4D8; ' + entry.source_count + ' 本书籍</span><span>&#x1F4C4; ' + entry.block_count + ' 段内容</span></div>';
    h += renderMd(entry.content) + see;
    if (entry.content.indexOf('(更多内容见完整版)') !== -1) {{
        h += '<p class="more-hint">&#x2139; 轻量预览版。完整版请通过服务器查看。</p>';
    }}
    ct.innerHTML = h;
    window.scrollTo(0, 0);
}}

// ==== 命例库 ====
function loadCases() {{
    if (CASES) return CASES;
    var arr = [];
    for (var i = 0; i < 16; i++) {{
        var el = document.getElementById('cases-p' + i);
        if (el) {{
            var chunk = JSON.parse(el.textContent);
            arr = arr.concat(chunk);
        }}
    }}
    CASES = arr;
    return CASES;
}}

function showCases() {{
    loadCases();
    var ct = document.getElementById('content');
    var topics = sortedTopics;
    var gnrs = sortedGenres;
    ct.innerHTML =
        '<h1>命例数据库</h1>' +
        '<div class="meta"><span>共 ' + CASES.length.toLocaleString() + ' 条命例</span></div>' +
        '<div class="case-filters">' +
        '<select id="cfTopic" onchange="filterCases()"><option value="">全部专题</option>' + topics.map(function(t){{return '<option>' + t + '</option>';}}).join('') + '</select>' +
        '<select id="cfGenre" onchange="filterCases()"><option value="">全部流派</option>' + gnrs.map(function(g){{return '<option>' + g + '</option>';}}).join('') + '</select>' +
        '<input type="text" placeholder="搜索命例..." oninput="filterCases()" id="cfText">' +
        '</div>' +
        '<div id="caseList" class="loading">加载中...</div>';
    setTimeout(function(){{ filterCases(); }}, 50);
}}

var _filteredCases = [];
function filterCases() {{
    var topic = document.getElementById('cfTopic')?.value || '';
    var genre = document.getElementById('cfGenre')?.value || '';
    var text = (document.getElementById('cfText')?.value || '').toLowerCase();

    var filtered = CASES;
    if (topic) filtered = filtered.filter(function(c){{ return c.tp.indexOf(topic) !== -1; }});
    if (genre) filtered = filtered.filter(function(c){{ return c.gn.indexOf(genre) !== -1; }});
    if (text) filtered = filtered.filter(function(c){{ return c.t.toLowerCase().indexOf(text) !== -1; }});

    var el = document.getElementById('caseList');
    if (!el) return;
    if (filtered.length === 0) {{
        el.innerHTML = '<div style="text-align:center;padding:30px;color:#999;">无匹配命例</div>';
        return;
    }}
    // 只渲染前2000条，避免DOM爆炸
    var toShow = filtered.slice(0, 2000);
    var h = '';
    toShow.forEach(function(c) {{
        h += '<div class="case-card">';
        h += '<div class="case-source">&#x1F4CC; 来源: ' + c.s + '</div>';
        h += '<div class="case-text">' + c.t + '</div>';
        h += '<div class="case-tags">';
        c.tp.forEach(function(t){{ h += '<span class="case-tag">' + t + '</span>'; }});
        c.gn.forEach(function(g){{ h += '<span class="case-tag">' + g + '</span>'; }});
        h += '</div></div>';
    }});
    if (filtered.length > 2000) h += '<p style="text-align:center;color:#999;padding:10px;">仅显示前 2,000 条（共 ' + filtered.length.toLocaleString() + ' 条匹配）</p>';
    el.innerHTML = h;
}}

// ==== 工具函数 ====
function showEmpty() {{
    document.getElementById('content').innerHTML =
        '<div class="empty-state"><div class="icon">&#x1F4D6;</div><p>请从左侧选择一个条目浏览</p></div>';
}}

function updateStats() {{
    document.getElementById('stats-bar').innerHTML =
        STATS.genres.length + ' 流派 · ' +
        STATS.topics.length + ' 专题 · ' +
        STATS.entry_count + ' 条目 · ' +
        STATS.case_count.toLocaleString() + ' 命例';
}}

// ==== 初始化 ====
renderGenreTree();
updateStats();
</script>

</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"独立HTML已生成: {output_path} ({size_mb:.1f}MB)")
    print(f"  百科: {len(genres)} 流派 × {len(all_topics)} 专题 = {len(all_entries)} 条目")
    print(f"  命例: {len(light_cases):,} 条")
    return output_path


def main():
    data_dir = Path(__file__).parent.parent.parent / "data"
    encyclopedia_path = data_dir / "encyclopedia.json"
    cases_path = data_dir / "cases.json"

    if not encyclopedia_path.exists():
        print(f"错误: 找不到 {encyclopedia_path}", file=sys.stderr)
        sys.exit(1)
    if not cases_path.exists():
        print(f"警告: 找不到 {cases_path}，命例库将为空", file=sys.stderr)

    with open(encyclopedia_path, "r", encoding="utf-8") as f:
        encyclopedia = json.load(f)
    cases = []
    if cases_path.exists():
        with open(cases_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

    output_path = data_dir / "八字命理百科全书.html"
    generate_html(encyclopedia, cases, output_path)


if __name__ == "__main__":
    main()
