"""MASE — Measures AI Software Engineering CLI."""

import re
from pathlib import Path


_source_pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
if _source_pyproject.exists():
    _match = re.search(
        r'^version = "([^"]+)"', _source_pyproject.read_text(encoding="utf-8"), re.MULTILINE
    )
    __version__ = _match.group(1) if _match else "0+unknown"
else:
    try:
        from importlib.metadata import version
    except ImportError:  # pragma: no cover - Python 3.7 compatibility fallback
        from importlib_metadata import version
    try:
        __version__ = version("mase")
    except Exception:
        __version__ = "0+unknown"
