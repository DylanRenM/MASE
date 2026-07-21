"""故事点估算助手 — Flask Web 应用入口。

对齐 PILOT 项目 cosmic_web.py 的架构模式：
Flask 路由 + Jinja2 模板渲染 + Services 层业务编排。
"""

import os
import sqlite3
import tempfile

from flask import Flask, jsonify, render_template, request, send_file, session

from config import load_config
from core.embedding import EmbeddingClient
from core.reporter import ReportGenerator
from db.models import BaselineRepository, HistoryRepository, init_db
from db.vector_store import VectorStore
from services.baseline_service import BaselineService
from services.estimate_service import EstimateService


def create_app() -> Flask:
    """创建并配置 Flask 应用。

    Returns:
        配置完成的 Flask 应用实例。
    """
    app = Flask(__name__)

    embedding_config, chat_config, app_config = load_config()
    app.secret_key = app_config.flask_secret_key

    # ── 数据层初始化 ────────────────────────────────
    os.makedirs(os.path.dirname(app_config.database_path) or ".", exist_ok=True)
    conn = sqlite3.connect(app_config.database_path, check_same_thread=False)
    init_db(conn)

    baseline_repo = BaselineRepository(conn)
    history_repo = HistoryRepository(conn)

    embedding_client = EmbeddingClient(
        base_url=embedding_config.base_url,
        api_key=embedding_config.api_key,
        model=embedding_config.model,
    )

    vector_store = VectorStore()

    # 尝试加载已有 FAISS 索引
    if os.path.exists(app_config.faiss_index_path):
        vector_store.load(app_config.faiss_index_path)

    report_generator = ReportGenerator(
        base_url=chat_config.base_url,
        api_key=chat_config.api_key,
        model=chat_config.model,
    )

    baseline_service = BaselineService(
        baseline_repo, history_repo, vector_store, embedding_client,
    )

    estimate_service = EstimateService(
        baseline_repo, history_repo, vector_store,
        embedding_client, report_generator,
    )

    # ── 路由注册 ──────────────────────────────────

    @app.route("/")
    def index():
        """首页：上传区 + 估算区 + 历史侧栏。"""
        # 检查是否有已加载的基线故事
        story_count = len(baseline_repo.get_all())
        return render_template("index.html", story_count=story_count)

    @app.route("/template/download")
    def download_template():
        """下载 Excel 模板。"""
        filepath = os.path.join(app.static_folder or "static", "baseline_template.xlsx")
        from utils.excel_handler import generate_template
        generate_template(filepath)
        return send_file(filepath, as_attachment=True,
                         download_name="baseline_template.xlsx")

    @app.route("/baseline/upload", methods=["POST"])
    def upload_baseline():
        """上传并校验 Excel 文件。"""
        if "file" not in request.files:
            return jsonify({"status": "error", "errors": ["请上传文件"]}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"status": "error", "errors": ["请选择文件"]}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in (".xlsx", ".xls"):
            return jsonify({"status": "error", "errors": ["请上传 .xlsx 或 .xls 文件"]}), 400

        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            result = baseline_service.parse_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

        if result["status"] == "ok":
            # 缓存解析结果到 session（用于 confirm 步骤）
            session["pending_rows"] = result["rows"]

        return jsonify(result), (200 if result["status"] == "ok" else 400)

    @app.route("/baseline/confirm", methods=["POST"])
    def confirm_baseline():
        """确认入库（全量替换或追加合并）。"""
        data = request.get_json()
        action = data.get("action", "replace")

        rows = session.pop("pending_rows", None)
        if not rows:
            return jsonify({"status": "error", "errors": ["请先上传文件"]}), 400

        if action not in ("replace", "append"):
            return jsonify({"status": "error", "errors": ["无效的操作"]}), 400

        result = baseline_service.confirm(rows, action=action)

        if result["status"] == "ok":
            # 保存 FAISS 索引
            vector_store.save(app_config.faiss_index_path)

        return jsonify(result), (200 if result["status"] == "ok" else 500)

    @app.route("/estimate", methods=["POST"])
    def estimate():
        """估算新需求的故事点。"""
        data = request.get_json()
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()

        if not title or not description:
            return jsonify({"status": "error", "errors": ["请填写故事标题和描述"]}), 400

        result = estimate_service.estimate(title, description)

        if result.get("status") == "error":
            return jsonify(result), 400

        return jsonify(result)

    @app.route("/history")
    def history():
        """获取估算历史。"""
        recent = history_repo.get_recent(limit=20)
        return jsonify([
            {
                "id": r["id"],
                "title": r["title"],
                "estimate": r["estimate"],
                "degraded": r["degraded"],
                "created_at": r["created_at"],
            }
            for r in recent
        ])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
