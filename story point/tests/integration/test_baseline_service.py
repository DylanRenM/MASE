"""基线服务集成测试（v2.0: 特征提取方案）。"""

import os
import sqlite3
import tempfile
from unittest.mock import MagicMock

import numpy as np
import pytest

from core.feature_encoder import FeatureEncoder, VECTOR_DIMENSION
from db.models import BaselineRepository, HistoryRepository, init_db
from db.vector_store import VectorStore
from services.baseline_service import BaselineService
from utils.feature_extractor import FeatureExtractor


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
def mock_feature_extractor():
    """创建 mock FeatureExtractor。"""
    extractor = MagicMock(spec=FeatureExtractor)
    # 每行返回一个默认特征字典
    default_features = {
        "frontend_pages": 1, "backend_interfaces": 1,
        "db_change": "否", "external_dependency": "否",
        "async_processing": "否", "transaction_required": "否",
        "business_branches": 1, "permission_control": "否",
        "data_migration": "否", "cache_design": "否",
    }
    extractor.extract_batch.return_value = [default_features.copy() for _ in range(12)]
    return extractor


@pytest.fixture
def feature_encoder():
    """创建 FeatureEncoder 实例。"""
    return FeatureEncoder()


@pytest.fixture
def service(conn, mock_feature_extractor, feature_encoder):
    """创建 BaselineService 实例。"""
    baseline_repo = BaselineRepository(conn)
    history_repo = HistoryRepository(conn)
    vector_store = VectorStore(dimension=VECTOR_DIMENSION)
    return BaselineService(
        baseline_repo, history_repo, vector_store,
        mock_feature_extractor, feature_encoder,
    )


def _make_12_valid_stories() -> str:
    """创建包含 12 条合法故事的 Excel 文件，返回路径。"""
    filepath = tempfile.mktemp(suffix=".xlsx")

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.append(["ID", "故事标题", "故事描述", "验收标准", "故事点"])

    stories = [
        ("S1", "修改Logo", "替换公司Logo", "页面Logo正确显示", 1),
        ("S2", "文案修改", "修改首页文案", "文案更新后显示正确", 1),
        ("S3", "邮箱校验", "前端校验邮箱格式", "输入合法邮箱通过校验", 2),
        ("S4", "手机校验", "前端校验手机号", "输入合法手机号通过", 2),
        ("S5", "分页查询", "列表分页", "翻页后数据正确", 3),
        ("S6", "排序功能", "列表排序", "按字段排序正确", 3),
        ("S7", "用户搜索", "含后端接口", "搜索结果正确", 5),
        ("S8", "导出CSV", "含导出接口", "导出文件内容正确", 5),
        ("S9", "第三方支付", "集成微信支付", "支付回调正确处理", 8),
        ("S10", "消息推送", "集成推送服务", "推送消息送达", 8),
        ("S11", "数据迁移", "历史数据迁移", "迁移后数据完整", 13),
        ("S12", "架构升级", "微服务拆分", "拆分后服务正常通信", 13),
    ]
    for s in stories:
        ws.append(list(s))

    wb.save(filepath)
    return filepath


class TestBaselineService:
    """BaselineService 测试套件（v2.0 特征提取方案）。"""

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

    def test_confirm_replace(self, service, mock_feature_extractor):
        """全量替换 → 入库成功。"""
        filepath = _make_12_valid_stories()
        result = service.parse_and_validate(filepath)
        os.unlink(filepath)

        confirm_result = service.confirm(result["rows"], action="replace")
        assert confirm_result["status"] == "ok"
        assert confirm_result["count"] == 12

    def test_confirm_append(self, service, mock_feature_extractor):
        """追加合并 → 总数增加。"""
        filepath = _make_12_valid_stories()
        result = service.parse_and_validate(filepath)
        os.unlink(filepath)

        service.confirm(result["rows"], action="replace")

        append_rows = [
            {"id": "SA1", "title": "新功能", "description": "测试", "acceptance_criteria": "", "points": 3},
            {"id": "SA2", "title": "新功能2", "description": "测试2", "acceptance_criteria": "验收通过", "points": 5},
        ]
        # 更新 mock 返回 14 个特征（现有 12 + 新增 2）
        default_features = {
            "frontend_pages": 1, "backend_interfaces": 1,
            "db_change": "否", "external_dependency": "否",
            "async_processing": "否", "transaction_required": "否",
            "business_branches": 1, "permission_control": "否",
            "data_migration": "否", "cache_design": "否",
        }
        mock_feature_extractor.extract_batch.return_value = [default_features.copy() for _ in range(2)]

        confirm_result = service.confirm(append_rows, action="append")
        assert confirm_result["status"] == "ok"
        assert confirm_result["count"] == 14

    def test_replace_clears_old_data(self, service):
        """全量替换后旧数据被清除。"""
        filepath1 = _make_12_valid_stories()
        r1 = service.parse_and_validate(filepath1)
        os.unlink(filepath1)
        service.confirm(r1["rows"], action="replace")

        filepath2 = _make_12_valid_stories()
        r2 = service.parse_and_validate(filepath2)
        os.unlink(filepath2)
        confirm = service.confirm(r2["rows"], action="replace")

        assert confirm["count"] == 12
