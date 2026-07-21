"""SQLite 数据模型集成测试。"""

import os
import sqlite3
import tempfile

import pytest

from db.models import BaselineRepository, HistoryRepository, init_db


@pytest.fixture
def db_path():
    """创建临时数据库文件。"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def conn(db_path):
    """创建数据库连接并初始化表。"""
    c = sqlite3.connect(db_path)
    init_db(c)
    yield c
    c.close()


class TestBaselineRepository:
    """BaselineRepository 测试套件。"""

    def test_insert_batch_and_get_all(self, conn):
        """insert_batch 后 get_all 返回所有记录。"""
        repo = BaselineRepository(conn)
        stories = [
            {"id": "S1", "title": "t1", "description": "d1", "points": 1, "faiss_index": 0},
            {"id": "S2", "title": "t2", "description": "d2", "points": 2, "faiss_index": 1},
        ]
        count = repo.insert_batch(stories)
        assert count == 2

        all_stories = repo.get_all()
        assert len(all_stories) == 2
        assert all_stories[0]["id"] == "S1"

    def test_replace_all_clears_old_data(self, conn):
        """replace_all 清除旧数据再插入新数据。"""
        repo = BaselineRepository(conn)
        repo.insert_batch([
            {"id": "S1", "title": "t1", "description": "d1", "points": 1, "faiss_index": 0},
        ])
        new_stories = [
            {"id": "S2", "title": "t2", "description": "d2", "points": 3, "faiss_index": 0},
        ]
        count = repo.replace_all(new_stories)
        assert count == 1

        all_stories = repo.get_all()
        assert len(all_stories) == 1
        assert all_stories[0]["id"] == "S2"

    def test_insert_batch_skips_duplicate_ids(self, conn):
        """insert_batch 遇到重复 ID 时跳过。"""
        repo = BaselineRepository(conn)
        repo.insert_batch([
            {"id": "S1", "title": "t1", "description": "d1", "points": 1, "faiss_index": 0},
        ])
        count = repo.insert_batch([
            {"id": "S1", "title": "t1_new", "description": "d1_new", "points": 2, "faiss_index": 1},
            {"id": "S2", "title": "t2", "description": "d2", "points": 3, "faiss_index": 1},
        ])
        assert count == 1  # 仅 S2 插入成功
        assert len(repo.get_all()) == 2

    def test_points_check_constraint_rejects_14(self, conn):
        """点数 14 违反 CHECK 约束。"""
        repo = BaselineRepository(conn)
        with pytest.raises(sqlite3.IntegrityError):
            repo.insert_batch([
                {"id": "S1", "title": "t", "description": "d", "points": 14, "faiss_index": 0},
            ])

    def test_count_by_point_returns_distribution(self, conn):
        """count_by_point 返回各点数计数。"""
        repo = BaselineRepository(conn)
        repo.insert_batch([
            {"id": "S1", "title": "t1", "description": "d1", "points": 1, "faiss_index": 0},
            {"id": "S2", "title": "t2", "description": "d2", "points": 1, "faiss_index": 1},
            {"id": "S3", "title": "t3", "description": "d3", "points": 3, "faiss_index": 2},
        ])
        dist = repo.count_by_point()
        assert dist[1] == 2
        assert dist[3] == 1
        assert dist[2] == 0

    def test_get_by_faiss_index_returns_correct_story(self, conn):
        """按 faiss_index 查找返回正确故事。"""
        repo = BaselineRepository(conn)
        repo.insert_batch([
            {"id": "S1", "title": "t1", "description": "d1", "points": 1, "faiss_index": 5},
        ])
        story = repo.get_by_faiss_index(5)
        assert story is not None
        assert story["id"] == "S1"

    def test_get_by_faiss_index_returns_none_for_missing(self, conn):
        """不存在的 faiss_index 返回 None。"""
        repo = BaselineRepository(conn)
        assert repo.get_by_faiss_index(999) is None


class TestHistoryRepository:
    """HistoryRepository 测试。"""

    def test_add_and_get_recent(self, conn):
        """add 后 get_recent 返回记录，按时间倒序。"""
        repo = HistoryRepository(conn)
        repo.add("微信登录", "集成微信OAuth", 8, 5, 13, '{"test": true}', False)
        repo.add("导出Excel", "导出功能", 5, 3, 8, '{"test": false}', True)

        recent = repo.get_recent(limit=10)
        assert len(recent) == 2
        # 最近的在前面
        assert recent[0]["title"] == "导出Excel"
        assert recent[1]["title"] == "微信登录"
        assert recent[0]["degraded"] is True

    def test_get_recent_respects_limit(self, conn):
        """get_recent 遵守 limit 参数。"""
        repo = HistoryRepository(conn)
        for i in range(5):
            repo.add(f"t{i}", "d", i + 1, None, None, "{}", False)

        assert len(repo.get_recent(limit=3)) == 3
