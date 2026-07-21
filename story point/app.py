"""故事点估算助手 — Flask Web 应用入口。

对齐 PILOT 项目 cosmic_web.py 的架构模式：
Flask 路由 + Jinja2 模板渲染 + Services 层业务编排。

v2.0: 文本Embedding方案 → 特征提取+向量检索方案
"""

import os
import sqlite3
import tempfile
import uuid

from flask import Flask, jsonify, render_template, request, send_file, session

from config import load_config
from core.feature_encoder import FeatureEncoder
from core.reporter import ReportGenerator
from db.models import BaselineRepository, HistoryRepository, init_db
from db.vector_store import VectorStore
from services.baseline_service import BaselineService
from services.estimate_service import EstimateService
from utils.feature_extractor import FeatureExtractor


def create_app() -> Flask:
    """创建并配置 Flask 应用。

    Returns:
        配置完成的 Flask 应用实例。
    """
    app = Flask(__name__)

    chat_config, app_config = load_config()
    app.secret_key = app_config.flask_secret_key

    # ── 数据层初始化 ────────────────────────────────
    os.makedirs(os.path.dirname(app_config.database_path) or ".", exist_ok=True)
    conn = sqlite3.connect(app_config.database_path, check_same_thread=False)
    init_db(conn)

    baseline_repo = BaselineRepository(conn)
    history_repo = HistoryRepository(conn)

    vector_store = VectorStore(dimension=app_config.vector_dimension)

    # 尝试加载已有 FAISS 索引
    if os.path.exists(app_config.faiss_index_path):
        vector_store.load(app_config.faiss_index_path)

    # 特征提取器（共用 Chat API）
    feature_extractor = FeatureExtractor(
        base_url=chat_config.base_url,
        api_key=chat_config.api_key,
        model=chat_config.model,
    )

    feature_encoder = FeatureEncoder()

    # 报告生成器（共用 Chat API）
    report_generator = ReportGenerator(
        base_url=chat_config.base_url,
        api_key=chat_config.api_key,
        model=chat_config.model,
    )

    baseline_service = BaselineService(
        baseline_repo, history_repo, vector_store,
        feature_extractor, feature_encoder,
        quality_llm_base_url=chat_config.base_url,
        quality_llm_api_key=chat_config.api_key,
        quality_llm_model=chat_config.model,
    )

    estimate_service = EstimateService(
        baseline_repo, history_repo, vector_store,
        feature_extractor, feature_encoder, report_generator,
    )

    # ── 批量结果暂存（token → 临时文件路径）─────
    _batch_results: dict[str, str] = {}

    # ── 路由注册 ──────────────────────────────────

    @app.route("/")
    def index():
        """首页。"""
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

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            result = baseline_service.parse_and_validate(tmp_path)
        finally:
            os.unlink(tmp_path)

        if result["status"] == "ok":
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
            vector_store.save(app_config.faiss_index_path)

        return jsonify(result), (200 if result["status"] == "ok" else 400)

    @app.route("/baseline/list")
    def list_baseline():
        """获取当前已加载的全部基线故事。"""
        stories = baseline_repo.get_all()
        return jsonify([
            {"id": s["id"], "title": s["title"],
             "description": s["description"],
             "acceptance_criteria": s.get("acceptance_criteria", ""),
             "points": s["points"]}
            for s in stories
        ])

    @app.route("/estimate", methods=["POST"])
    def estimate():
        """估算新需求的故事点。"""
        data = request.get_json()
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        acceptance_criteria = data.get("acceptance_criteria", "").strip()

        if not title or not description:
            return jsonify({"status": "error", "errors": ["请填写故事标题和描述"]}), 400

        result = estimate_service.estimate(title, description, acceptance_criteria)

        if result.get("status") == "error":
            return jsonify(result), 400

        return jsonify(result)

    # ── 批量估算 ──────────────────────────────────

    @app.route("/batch/template")
    def download_batch_template():
        """下载批量估算模板。"""
        from utils.excel_handler import generate_batch_template
        filepath = os.path.join(app.static_folder or "static", "batch_estimate_template.xlsx")
        generate_batch_template(filepath)
        return send_file(filepath, as_attachment=True,
                         download_name="批量估算模板.xlsx")

    @app.route("/batch/estimate", methods=["POST"])
    def batch_estimate():
        """批量估算：上传Excel，返回JSON结果。"""
        if len(baseline_repo.get_all()) == 0:
            return jsonify({"status": "error", "errors": ["请先上传基准故事集"]}), 400

        if "file" not in request.files:
            return jsonify({"status": "error", "errors": ["请上传文件"]}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"status": "error", "errors": ["请选择文件"]}), 400

        from utils.excel_handler import generate_batch_result, parse_batch_upload

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        try:
            stories = parse_batch_upload(tmp_path)
        finally:
            os.unlink(tmp_path)

        if not stories:
            return jsonify({"status": "error", "errors": ["文件中没有有效数据"]}), 400

        # 逐行估算
        rows = []
        for s in stories:
            result = estimate_service.estimate(s["title"], s["description"], s.get("acceptance_criteria", ""))
            rows.append({
                "id": s["id"],
                "title": s["title"],
                "description": s["description"],
                "acceptance_criteria": s.get("acceptance_criteria", ""),
                "estimate": result.get("estimate", ""),
                "confidence_min": result.get("confidence_min", ""),
                "confidence_max": result.get("confidence_max", ""),
                "reasoning": result.get("reasoning", ""),
                "risk_notes": result.get("risk_notes", ""),
            })

        # 生成结果 Excel 并暂存
        result_path = generate_batch_result(rows)
        token = uuid.uuid4().hex[:12]
        _batch_results[token] = result_path

        return jsonify({
            "status": "ok",
            "count": len(rows),
            "download_token": token,
            "rows": rows,
        })

    @app.route("/batch/download")
    def batch_download():
        """下载批量估算结果Excel。"""
        token = request.args.get("token", "")
        result_path = _batch_results.pop(token, None)
        if not result_path or not os.path.exists(result_path):
            return jsonify({"status": "error", "errors": ["文件不存在或已过期"]}), 404
        return send_file(result_path, as_attachment=True,
                         download_name="估算结果.xlsx")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8080)
