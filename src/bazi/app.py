"""FastAPI 服务: API 端点 + 静态文件服务"""

import os
import json
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import config
from .database import get_all_books, get_book, get_pending_books
from .pipeline import orchestrator

app = FastAPI(title="八字百科全书 API", version="0.1.0")

# 上传目录
UPLOAD_DIR = config.data_dir / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/api/books")
def list_books(offset: int = 0, limit: int = 50):
    """获取所有书籍列表（分页）"""
    all_books = get_all_books()
    total = len(all_books)
    paged = all_books[offset:offset + limit]
    return {"books": paged, "total": total, "offset": offset, "limit": limit}


@app.get("/api/books/{book_id}")
def get_book_info(book_id: str):
    """获取单本书信息"""
    book = get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")
    return book


@app.get("/api/books/{book_id}/progress")
def get_merge_progress(book_id: str):
    """获取合并进度"""
    progress = orchestrator.get_progress(book_id)
    return progress


@app.post("/api/books/import")
async def import_book(file: UploadFile = File(...), title: str = Form(None)):
    """导入一本书并启动处理管道"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名为空")

    # 确定格式
    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".txt", ".pdf", ".epub", ".docx", ".doc"]:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {suffix}")

    # 保存上传文件
    dest_path = UPLOAD_DIR / file.filename
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 异步启动处理管道
    book_title = title or Path(file.filename).stem
    orchestrator.run_pipeline_async(
        file_path=str(dest_path),
        filename=file.filename,
        fmt=suffix,
        title=book_title,
    )

    # 从数据库获取刚添加的书籍（最新一条）
    books = get_all_books()
    return books[0] if books else {"message": "已提交处理"}


@app.post("/api/books/{book_id}/rem")
async def remerge_book(book_id: str):
    """重新合并一本书"""
    book = get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    orchestrator.run_pipeline_async(
        file_path=book["file_path"],
        filename=book["filename"],
        fmt=book["format"],
        title=book["title"],
    )
    return {"message": "已重新提交处理"}


@app.get("/api/encyclopedia")
def get_encyclopedia(view: str = "genre", genre: str = None, topic: str = None, summary_only: bool = False):
    """获取百科全书

    view=genre: 返回 by_genre 的顶层结构（流派→专题列表），不展开内容
    view=topic: 返回 by_topic 的顶层结构（专题→流派列表）

    指定 genre + topic: 返回单条目的完整内容
    summary_only=true: 仅返回摘要，不含完整 block_text
    """
    if not config.encyclopedia_path.exists():
        return {"view": view, "data": {}, "cases": []}

    with open(config.encyclopedia_path, "r", encoding="utf-8") as f:
        encyclopedia = json.load(f)

    # 指定具体条目 → 返回完整内容
    if genre and topic:
        if view == "genre":
            entry = encyclopedia.get("by_genre", {}).get(genre, {}).get(topic, {})
            if not entry:
                # 尝试从 by_topic 回退
                entry = encyclopedia.get("by_topic", {}).get(topic, {}).get(genre, {})
        else:
            entry = encyclopedia.get("by_topic", {}).get(topic, {}).get(genre, {})
            if not entry:
                entry = encyclopedia.get("by_genre", {}).get(genre, {}).get(topic, {})
        return {"entry": entry} if entry else {"entry": None, "message": "条目不存在"}

    # 顶层视图: 仅返回结构摘要（不展开内容）
    if view == "genre":
        by_genre = encyclopedia.get("by_genre", {})
        summary = {}
        for g, topics in by_genre.items():
            summary[g] = {
                "topics": list(topics.keys()),
                "entry_count": sum(1 for t in topics.values() if t),
            }
        return {"view": "genre", "genres": summary}

    elif view == "topic":
        by_topic = encyclopedia.get("by_topic", {})
        summary = {}
        for t, genres in by_topic.items():
            summary[t] = {
                "genres": list(genres.keys()),
                "entry_count": sum(1 for g in genres.values() if g),
            }
        return {"view": "topic", "topics": summary}

    return {"view": view, "data": encyclopedia}


@app.get("/api/cases")
def get_cases(topic: str = None, genre: str = None):
    """查询命例数据库"""
    if not config.cases_path.exists():
        return []

    with open(config.cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    # 过滤
    results = []
    for case in cases:
        if topic and topic not in case.get("topic_tags", []):
            continue
        if genre and genre not in case.get("genre_tags", []):
            continue
        results.append(case)

    return results


@app.post("/api/rebuild")
def rebuild():
    """全量重构百科全书"""
    orchestrator.rebuild_encyclopedia()
    return {"message": "重建完成"}


# 静态文件服务
ui_path = Path(__file__).parent.parent.parent / "ui"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path)), name="ui")


@app.get("/")
def serve_ui():
    """返回主界面"""
    ui_file = Path(__file__).parent.parent.parent / "ui" / "index.html"
    if not ui_file.exists():
        return {"message": "UI 尚未构建，请稍后刷新"}
    return FileResponse(str(ui_file))
