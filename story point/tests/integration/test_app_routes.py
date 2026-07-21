"""Flask 路由集成测试。"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app import create_app


@pytest.fixture(autouse=True)
def _set_env():
    """设置测试环境变量。"""
    os.environ["EMBEDDING_BASE_URL"] = "http://test-embed"
    os.environ["EMBEDDING_API_KEY"] = "sk-test-embed"
    os.environ["EMBEDDING_MODEL"] = "test-embed-model"
    os.environ["CHAT_BASE_URL"] = "http://test-chat"
    os.environ["CHAT_API_KEY"] = "sk-test-chat"
    os.environ["CHAT_MODEL"] = "test-chat-model"
    os.environ["FLASK_SECRET_KEY"] = "test-secret"


@pytest.fixture
def app():
    """创建测试用 Flask 应用。"""
    with patch("app.sqlite3.connect") as mock_connect, \
         patch("app.os.makedirs"), \
         patch("app.os.path.exists", return_value=False):
        conn = MagicMock()
        mock_connect.return_value = conn

        flask_app = create_app()
        flask_app.config["TESTING"] = True

        yield flask_app


@pytest.fixture
def client(app):
    """创建测试客户端。"""
    return app.test_client()


class TestAppRoutes:
    """Flask 路由测试。"""

    def test_index_returns_html(self, client):
        """GET / 返回 HTML。"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "故事点估算助手".encode("utf-8") in resp.data

    def test_template_download_returns_xlsx(self, client):
        """GET /template/download 返回 Excel。"""
        resp = client.get("/template/download")
        assert resp.status_code == 200
        assert "spreadsheet" in resp.content_type

    def test_history_returns_json_array(self, client):
        """GET /history 返回 JSON 数组。"""
        resp = client.get("/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_estimate_without_title_returns_error(self, client):
        """POST /estimate 缺少标题返回 400。"""
        resp = client.post("/estimate", json={"title": "", "description": "test"})
        assert resp.status_code == 400

    def test_upload_without_file_returns_error(self, client):
        """POST /baseline/upload 无文件返回 400。"""
        resp = client.post("/baseline/upload")
        assert resp.status_code == 400
