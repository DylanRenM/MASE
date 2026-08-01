#!/usr/bin/env python3
"""Run MASE's Python and JavaScript regression suites without leaving dependencies."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    completed = subprocess.run(command, cwd=ROOT, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if completed.returncode:
        raise SystemExit(completed.returncode)


def main() -> int:
    node_modules = ROOT / "node_modules"
    if node_modules.exists():
        raise SystemExit("node_modules already exists; remove or preserve it before canonical regression")
    try:
        run([sys.executable, "-m", "pytest", "-q"])
        run(["npm", "ci"])
        run(["npm", "test"])
    finally:
        if node_modules.exists():
            shutil.rmtree(node_modules)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
