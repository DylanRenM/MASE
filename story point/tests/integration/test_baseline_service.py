"""基线服务集成测试。"""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.embedding import EmbeddingClient
from db.models import BaselineRepository, HistoryRepository, init_db
from db.vector_store import VectorStore
from services.baseline_service import BaselineService
from utils.excel_handler import generate_template


@pytest.fixture
def db_path():
    """创建临时数据库。"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def conn(db_path):
    """创建数据库连接并初始化。"""
    c = sqlite3.connect(db_path)
    init_db(c)
    yield c
    c.close()


@pytest.fixture
def mock_embedding_client():
    """创建 mock EmbeddingClient。"""
    client = MagicMock(spec=EmbeddingClient)
    # 12 条故事各返回一个随机向量
    client.embed_batch.return_value = np.random.randn(12, 1536).astype(np.float32)
    return client


@pytest.fixture
def service(conn, mock_embedding_client):
    """创建 BaselineService 实例。"""
    baseline_repo = BaselineRepository(conn)
    history_repo = HistoryRepository(conn)
    vector_store = VectorStore(dimension=1536)
    return BaselineService(baseline_repo, history_repo, vector_store, mock_embedding_client)


def _make_12_valid_stories() -> str:
    """创建包含 12 条合法故事的 Excel 文件，返回路径。"""
    filepath = tempfile.mktemp(suffix=".xlsx")

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "故事标题", "故事描述", "故事点"])

    # 每个点数 2 条
    stories = [
        ("S1", "修改Logo", "替换公司Logo", 1),
        ("S2", "文案修改", "修改首页文案", 1),
        ("S3", "邮箱校验", "前端校验邮箱格式", 2),
        ("S4", "手机校验", "前端校验手机号", 2),
        ("S5", "分页查询", "列表分页", 3),
        ("S6", "排序功能", "列表排序", 3),
        ("S7", "用户搜索", "含后端接口", 5),
        ("S8", "导出CSV", "含导出接口", 5),
        ("S9", "第三方支付", "集成微信支付", 8),
        ("S10", "消息推送", "集成推送服务", 8),
        ("S11", "数据迁移", "历史数据迁移", 13),
        ("S12", "架构升级", "微服务拆分", 13),
    ]
    for s in stories:
        ws.append(list(s))

    wb.save(filepath)
    return filepath


class TestBaselineService:
    """BaselineService 测试套件。"""

    def test_parse_and_validate_valid_file(self, service):
        """有效文件校验通过。"""
        filepath = _make_12_valid_stories()
        result = service.parse_and_validate(filepath)
        os.unlink(filepath)

        assert result["status"] == "ok"
        assert len(result["rows"]) == 12
        assert result["points_distribution"][1] == 2
        assert result["points_distribution"][13] == 2

    def test_parse_and_validate_invalid_file(self, service):
        """无效文件校验失败。"""
        # 创建一个只有 1 条的 Excel（点数不足）
        from openpyxl import Workbook
        fp = tempfile.mktemp(suffix=".xlsx")
        wb = Workbook()
        ws = wb.active
        ws.append(["ID", "故事标题", "故事描述", "故事点"])
        ws.append(["S1", "test", "desc", 1])
        wb.save(fp)

        result = service.parse_and_validate(fp)
        os.unlink(fp)
        assert result["status"] == "error"
        assert len(result["errors"]) > 0

    def test_confirm_replace(self, service):
        """全量替换 → 入库成功。"""
        filepath = _make_12_valid_stories()
        result = service.parse_and_validate(filepath)
        os.unlink(filepath)

        confirm_result = service.confirm(result["rows"], action="replace")
        assert confirm_result["status"] == "ok"
        assert confirm_result["count"] == 12

    def test_confirm_append(self, service):
        """追加合并 → 总数增加。"""
        filepath = _make_12_valid_stories()
        result = service.parse_and_validate(filepath)
        os.unlink(filepath)

        # 先替换入 12 条
        service.confirm(result["rows"], action="replace")

        # 用不同的 ID 追加
        append_rows = [
            {"id": "SA1", "title": "新功能", "description": "测试", "points": 3},
            {"id": "SA2", "title": "新功能2", "description": "测试2", "points": 5},
        ]
        service._embedding_client.embed_batch.return_value = np.random.randn(14, 1536).astype(np.float32)

        confirm_result = service.confirm(append_rows, action="append")
        assert confirm_result["status"] == "ok"
        assert confirm_result["count"] == 14

    def test_replace_clears_old_data(self, service):
        """全量替换后旧数据被清除。"""
        filepath1 = _make_12_valid_stories()
        r1 = service.parse_and_validate(filepath1)
        os.unlink(filepath1)
        service.confirm(r1["rows"], action="replace")

        # 上传另一个 12 条
        filepath2 = _make_12_valid_stories()
        r2 = service.parse_and_validate(filepath2)
        os.unlink(filepath2)
        confirm = service.confirm(r2["rows"], action="replace")

        assert confirm["count"] == 12
