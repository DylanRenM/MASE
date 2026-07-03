#!/usr/bin/env python3
"""端到端测试脚本"""
import sys
print("Script started", flush=True)

from bazi.pipeline import PipelineOrchestrator
print("Import OK", flush=True)

orch = PipelineOrchestrator()
print("Orchestrator OK", flush=True)

try:
    orch.run_pipeline(
        file_path='/Users/dylanren/Documents/个人兴趣/自己整理/断六亲/宫位与六亲关系.docx',
        filename='宫位与六亲关系.docx',
        fmt='.docx',
        title='宫位与六亲关系',
    )
    print("PIPELINE SUCCESS", flush=True)
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
