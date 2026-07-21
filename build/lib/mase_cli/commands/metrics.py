"""mase metrics — actual token telemetry or explicitly labeled context proxies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union


def collect_metrics(
    files: Iterable[Union[str, Path]],
    token_usage: Optional[Mapping[str, int]] = None,
) -> dict:
    paths = [Path(path) for path in files]
    readable = [path for path in paths if path.is_file()]
    characters = sum(len(path.read_text(encoding="utf-8", errors="replace")) for path in readable)
    if token_usage is not None:
        return {
            "kind": "actual_tokens",
            "tokens": {name: int(value) for name, value in token_usage.items()},
            "files": len(readable),
            "characters": characters,
        }
    return {
        "kind": "context_proxy",
        "files": len(readable),
        "characters": characters,
        "note": "No platform token usage was supplied; characters are not tokens.",
    }


def run(files: Iterable[Union[str, Path]], token_usage: Optional[Mapping[str, int]] = None) -> dict:
    report = collect_metrics(files, token_usage)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report
