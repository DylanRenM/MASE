#!/usr/bin/env python3
"""八字百科全书 - 启动入口"""

import sys
from pathlib import Path

# 确保项目根目录在 path 中
sys.path.insert(0, str(Path(__file__).parent / "src"))

import uvicorn
from bazi.config import config
from bazi.database import init_db
from bazi.qdrant_store import init_collection


def main():
    print("=" * 50)
    print("  八字百科全书 - BaziEncyclopedia")
    print("=" * 50)

    # 初始化
    print("[1/4] 初始化数据库...")
    init_db()

    print("[2/4] 初始化向量数据库...")
    init_collection()

    print("[3/4] 检查预处理工具...")
    try:
        from markitdown import MarkItDown
        print("   MarkItDown: 已安装")
    except ImportError:
        print("   MarkItDown: 未安装 (将使用内置解析器)")

    try:
        from paddleocr import PaddleOCR
        print("   PaddleOCR: 已安装 (扫描版PDF支持)")
    except Exception:
        print("   PaddleOCR: 不可用 (扫描版PDF将跳过)")

    print("[4/4] 启动 Web 服务...")
    print(f"\n  打开浏览器访问: http://localhost:8000\n")

    uvicorn.run(
        "bazi.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
