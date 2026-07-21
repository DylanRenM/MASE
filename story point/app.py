"""故事点估算助手 — Flask Web 应用入口。

对齐 PILOT 项目 cosmic_web.py 的架构模式：
Flask 路由 + Jinja2 模板渲染 + Services 层业务编排。
"""

from flask import Flask, render_template

from config import load_config


def create_app() -> Flask:
    """创建并配置 Flask 应用。

    Returns:
        配置完成的 Flask 应用实例。
    """
    app = Flask(__name__)

    embedding_config, chat_config, app_config = load_config()
    app.secret_key = app_config.flask_secret_key

    # 注入配置到 app 上下文
    app.config["EMBEDDING_CONFIG"] = embedding_config
    app.config["CHAT_CONFIG"] = chat_config
    app.config["APP_CONFIG"] = app_config

    # ── 路由注册 ──────────────────────────────────

    @app.route("/")
    def index():
        """首页：上传区 + 估算区 + 历史侧栏。"""
        return render_template("index.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
