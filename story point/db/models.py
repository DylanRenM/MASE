"""SQLite 数据模型。

提供 baseline_stories 和 estimate_history 两表的 CRUD 操作。
"""

import sqlite3


def init_db(conn: sqlite3.Connection) -> None:
    """初始化数据库表结构。

    Args:
        conn: SQLite 连接。
    """
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS baseline_stories (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            points      INTEGER NOT NULL CHECK(points IN (1,2,3,5,8,13)),
            faiss_index INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS estimate_history (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            title          TEXT NOT NULL,
            description    TEXT NOT NULL,
            estimate       INTEGER NOT NULL,
            confidence_min INTEGER,
            confidence_max INTEGER,
            report_json    TEXT,
            degraded       INTEGER DEFAULT 0,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_faiss_index
            ON baseline_stories(faiss_index);

        CREATE INDEX IF NOT EXISTS idx_history_created
            ON estimate_history(created_at DESC);
    """)


class BaselineRepository:
    """基线故事仓库。"""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def insert_batch(self, stories: list[dict]) -> int:
        """批量插入故事（跳过重复 ID）。

        Args:
            stories: 故事列表，每个含 id/title/description/points/faiss_index。

        Returns:
            实际插入的行数。
        """
        count = 0
        for s in stories:
            try:
                self._conn.execute(
                    """INSERT INTO baseline_stories (id, title, description, points, faiss_index)
                       VALUES (?, ?, ?, ?, ?)""",
                    (s["id"], s["title"], s["description"], s["points"], s.get("faiss_index")),
                )
                count += 1
            except sqlite3.IntegrityError as e:
                # 仅跳过 PRIMARY KEY 冲突，CHECK 约束等错误应传播
                if "UNIQUE constraint failed" in str(e):
                    continue
                raise
        self._conn.commit()
        return count

    def replace_all(self, stories: list[dict]) -> int:
        """清空旧数据后批量插入新故事。

        Args:
            stories: 新故事列表。

        Returns:
            插入的行数。
        """
        self._conn.execute("DELETE FROM baseline_stories")
        return self.insert_batch(stories)

    def get_all(self) -> list[dict]:
        """获取所有基线故事，按 faiss_index 升序。"""
        cursor = self._conn.execute(
            "SELECT id, title, description, points, faiss_index FROM baseline_stories "
            "ORDER BY faiss_index ASC"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_by_faiss_index(self, index: int):
        """按 FAISS 索引位置查找故事。

        Args:
            index: FAISS 索引中的位置。

        Returns:
            找到的故事 dict，不存在返回 None。
        """
        cursor = self._conn.execute(
            "SELECT id, title, description, points, faiss_index FROM baseline_stories "
            "WHERE faiss_index = ?",
            (index,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def count_by_point(self) -> dict[int, int]:
        """统计每个点数的故事数量。

        Returns:
            {1: count, 2: count, 3: count, 5: count, 8: count, 13: count}
        """
        distribution = {pt: 0 for pt in [1, 2, 3, 5, 8, 13]}
        cursor = self._conn.execute(
            "SELECT points, COUNT(*) as cnt FROM baseline_stories GROUP BY points"
        )
        for row in cursor.fetchall():
            pt = row["points"]
            if pt in distribution:
                distribution[pt] = row["cnt"]
        return distribution


class HistoryRepository:
    """估算历史仓库。"""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def add(self, title: str, description: str, estimate: int,
            confidence_min, confidence_max,
            report_json: str, degraded: bool) -> int:
        """添加一条估算历史记录。

        Returns:
            新增记录的 ID。
        """
        cursor = self._conn.execute(
            """INSERT INTO estimate_history
               (title, description, estimate, confidence_min, confidence_max, report_json, degraded)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (title, description, estimate, confidence_min, confidence_max,
             report_json, 1 if degraded else 0),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_recent(self, limit: int = 20) -> list[dict]:
        """获取最近的估算历史。

        Args:
            limit: 最大返回条数。

        Returns:
            按 created_at 降序排列的历史记录列表。
        """
        cursor = self._conn.execute(
            "SELECT id, title, description, estimate, confidence_min, confidence_max, "
            "degraded, created_at FROM estimate_history "
            "ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        )
        result = []
        for row in cursor.fetchall():
            d = dict(row)
            d["degraded"] = bool(d["degraded"])
            result.append(d)
        return result
