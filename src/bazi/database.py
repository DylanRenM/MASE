"""SQLite 数据库管理模块"""

import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import config


def get_conn() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(config.db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            title TEXT,
            author TEXT,
            format TEXT,
            status TEXT DEFAULT 'pending',
            progress REAL DEFAULT 0.0,
            block_count INTEGER DEFAULT 0,
            file_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            merged_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pipeline_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id TEXT REFERENCES books(id),
            stage TEXT,
            status TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS encyclopedia_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()


def add_book(filename: str, file_path: str, fmt: str, title: Optional[str] = None, author: Optional[str] = None) -> str:
    """添加一本书到数据库，返回 book_id"""
    book_id = str(uuid.uuid4())[:8]
    conn = get_conn()
    conn.execute(
        "INSERT INTO books (id, filename, title, author, format, file_path) VALUES (?, ?, ?, ?, ?, ?)",
        (book_id, filename, title or filename, author, fmt, file_path),
    )
    conn.commit()
    conn.close()
    return book_id


def update_book_status(book_id: str, status: str, progress: float = 0.0):
    """更新书籍处理状态"""
    conn = get_conn()
    updates = {"status": status, "progress": progress}
    if status == "done":
        updates["merged_at"] = datetime.now().isoformat()
    conn.execute(
        "UPDATE books SET status = ?, progress = ? WHERE id = ?",
        (status, progress, book_id),
    )
    conn.commit()
    conn.close()


def update_block_count(book_id: str, count: int):
    """更新书籍的分块数量"""
    conn = get_conn()
    conn.execute("UPDATE books SET block_count = ? WHERE id = ?", (count, book_id))
    conn.commit()
    conn.close()


def add_pipeline_log(book_id: str, stage: str, status: str, message: str = ""):
    """添加管道处理日志"""
    conn = get_conn()
    conn.execute(
        "INSERT INTO pipeline_logs (book_id, stage, status, message) VALUES (?, ?, ?, ?)",
        (book_id, stage, status, message),
    )
    conn.commit()
    conn.close()


def get_book(book_id: str) -> Optional[dict]:
    """获取单本书的信息"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_books() -> list[dict]:
    """获取所有书籍信息"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM books ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pending_books() -> list[dict]:
    """获取待处理的书籍"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM books WHERE status = 'pending' ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]
