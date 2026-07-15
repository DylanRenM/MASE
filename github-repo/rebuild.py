#!/usr/bin/env python3
"""运行去重和百科编排重建"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    from bazi.pipeline import PipelineOrchestrator
    
    orch = PipelineOrchestrator()
    
    print("=" * 50, flush=True)
    print("开始去重 + 百科编排重建", flush=True)
    print("=" * 50, flush=True)
    
    try:
        encyclopedia = orch.rebuild_encyclopedia()
        print(f"\n重建完成!", flush=True)
        
        # 统计结果
        total_entries = 0
        for genre, topics in encyclopedia.items():
            total_entries += len(topics)
        print(f"  流派数: {len(encyclopedia)}", flush=True)
        print(f"  条目数: {total_entries}", flush=True)
        
        for genre, topics in sorted(encyclopedia.items()):
            print(f"  {genre}: {len(topics)} 个专题", flush=True)
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
