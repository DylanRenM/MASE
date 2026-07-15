#!/usr/bin/env python3
"""恢复卡住的processing状态书籍，重置为pending后重新处理"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from bazi.database import get_all_books, update_book_status
    from bazi.pipeline import PipelineOrchestrator

    books = get_all_books()
    stuck = [b for b in books if b['status'] == 'processing' and b['title'] != '系统内部操作']

    if not stuck:
        print("没有卡住的书籍，全部已处理完毕！")
        return

    print(f"发现 {len(stuck)} 本卡住的书籍，重置状态并重新处理...\n")

    for b in stuck:
        # 重置为pending
        update_book_status(b['id'], 'pending', 0.0)
        print(f"  [重置] {b['filename'][:50]}", flush=True)

    print(f"\n重置完成，开始重新处理...\n")

    orch = PipelineOrchestrator()
    success = 0
    fail = 0

    for b in stuck:
        print(f"[处理] {b['filename'][:50]}...", flush=True)
        try:
            orch.run_pipeline(
                file_path=b['file_path'],
                filename=b['filename'],
                fmt=b['format'],
                title=b['title'],
            )
            print(f"  ✓ 成功", flush=True)
            success += 1
        except Exception as e:
            print(f"  ✗ 失败: {e}", flush=True)
            fail += 1

    print(f"\n恢复完成: 成功 {success}, 失败 {fail}")


if __name__ == "__main__":
    main()
