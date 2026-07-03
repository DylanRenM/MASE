#!/usr/bin/env python3
"""批量导入测试书籍"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

TEST_DIR = Path("/Users/dylanren/Documents/个人兴趣/自己整理/断六亲")

SUPPORTED_SUFFIXES = {".txt": "txt", ".pdf": "pdf", ".docx": "docx", ".doc": "doc"}

def main():
    from bazi.pipeline import PipelineOrchestrator
    from bazi.database import get_all_books

    orch = PipelineOrchestrator()

    files = sorted(TEST_DIR.iterdir())
    print(f"共发现 {len(files)} 个文件\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for f in files:
        if f.name.startswith("."):
            continue

        suffix = f.suffix.lower()
        if suffix not in SUPPORTED_SUFFIXES:
            print(f"[跳过] {f.name} - 不支持的格式 {suffix}")
            skip_count += 1
            continue

        print(f"[处理] {f.name}...", flush=True)
        try:
            orch.run_pipeline(
                file_path=str(f),
                filename=f.name,
                fmt=suffix,
                title=f.stem,
            )
            print(f"  ✓ 成功", flush=True)
            success_count += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}", flush=True)
            fail_count += 1

    print(f"\n{'='*50}")
    print(f"导入完成: 成功 {success_count}, 失败 {fail_count}, 跳过 {skip_count}")
    print(f"{'='*50}")

    # 列出所有书籍状态
    books = get_all_books()
    print(f"\n书籍状态汇总:")
    for b in books:
        print(f"  [{b['status']:>12}] {b['filename']} ({b.get('block_count', 0)}块)")


if __name__ == "__main__":
    main()
