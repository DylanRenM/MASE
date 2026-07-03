#!/usr/bin/env python3
"""自动监控：等全部书籍处理完毕后自动重建百科"""
import sys, time, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from bazi.database import get_conn

    last_done = 0
    stable_count = 0

    print("🔍 开始监控管线进度，全部完成后自动重建百科...", flush=True)
    print("   检查间隔: 30秒，完成数连续3次不变即触发重建\n", flush=True)

    while True:
        conn = get_conn()
        cur = conn.execute(
            "SELECT status, COUNT(*) FROM books WHERE title != '系统内部操作' GROUP BY status"
        )
        rows = {r[0]: r[1] for r in cur.fetchall()}
        conn.close()

        done = rows.get("done", 0)
        processing = rows.get("processing", 0)
        failed = rows.get("failed", 0)
        total = done + processing + failed

        progress = done / total * 100 if total > 0 else 0
        timestamp = time.strftime("%H:%M:%S")
        print(f"  [{timestamp}] 完成 {done}/{total} ({progress:.0f}%) | 处理中 {processing} | 失败 {failed}",
              flush=True)

        if processing == 0 and total > 0:
            print(f"\n✅ 全部 {done} 本书处理完毕！开始重建百科...\n", flush=True)
            break

        # 连续3次done数不变且processing>0 → 可能卡住了
        if done == last_done and processing > 0:
            stable_count += 1
        else:
            stable_count = 0
        last_done = done

        if stable_count >= 6:  # 3分钟没进展
            print(f"  ⚠️ 进度已 {stable_count*30} 秒未变化，继续等待...", flush=True)

        time.sleep(30)

    # 运行快速重建
    result = subprocess.run(
        [sys.executable, "-u", str(Path(__file__).parent / "quick_rebuild.py")],
        capture_output=True, text=True, timeout=300,
        env={**__import__("os").environ, "PYTHONPATH": str(Path(__file__).parent / "src")},
    )
    print(result.stdout, flush=True)
    if result.stderr:
        print("STDERR:", result.stderr[:500], flush=True)

    print(f"\n🎉 全流程完成！刷新浏览器 http://localhost:8000 查看最新百科。", flush=True)


if __name__ == "__main__":
    main()
