"""mase metrics — actual token telemetry or explicitly labeled context proxies."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union


TOKEN_ENVIRONMENT = {
    "input": "MASE_INPUT_TOKENS",
    "output": "MASE_OUTPUT_TOKENS",
    "cache": "MASE_CACHE_TOKENS",
}


def _normalized_usage(payload: Mapping[str, object]) -> dict[str, int]:
    result = {}
    for name in ("input", "output", "cache"):
        value = int(payload.get(name, 0) or 0)
        if value < 0:
            raise ValueError(f"{name} tokens cannot be negative")
        result[name] = value
    return result


def resolve_token_usage(
    token_usage: Optional[Mapping[str, int]] = None,
    usage_file: Optional[Union[str, Path]] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> tuple[Optional[dict[str, int]], str]:
    if token_usage is not None:
        return _normalized_usage(token_usage), "explicit"
    if usage_file is not None:
        payload = json.loads(Path(usage_file).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("usage file must contain a JSON object")
        nested = payload.get("tokens", payload)
        if not isinstance(nested, dict):
            raise ValueError("usage tokens must be a JSON object")
        return _normalized_usage(nested), "usage_file"
    environment = os.environ if environ is None else environ
    if any(environment.get(variable) not in (None, "") for variable in TOKEN_ENVIRONMENT.values()):
        return _normalized_usage({
            name: environment.get(variable, 0)
            for name, variable in TOKEN_ENVIRONMENT.items()
        }), "environment"
    return None, "proxy"


def collect_metrics(
    files: Iterable[Union[str, Path]],
    token_usage: Optional[Mapping[str, int]] = None,
    *,
    usage_file: Optional[Union[str, Path]] = None,
    tool_output_characters: int = 0,
    environ: Optional[Mapping[str, str]] = None,
) -> dict:
    paths = [Path(path) for path in files]
    readable = [path for path in paths if path.is_file()]
    characters = sum(len(path.read_text(encoding="utf-8", errors="replace")) for path in readable)
    resolved_usage, source = resolve_token_usage(token_usage, usage_file, environ)
    if resolved_usage is not None:
        return {
            "kind": "actual_tokens",
            "source": source,
            "tokens": resolved_usage,
            "files": len(readable),
            "characters": characters,
            "tool_output_characters": max(0, int(tool_output_characters or 0)),
        }
    return {
        "kind": "context_proxy",
        "files": len(readable),
        "characters": characters,
        "tool_output_characters": max(0, int(tool_output_characters or 0)),
        "note": "No platform token usage was supplied; characters are not tokens.",
    }


def run(
    files: Iterable[Union[str, Path]],
    token_usage: Optional[Mapping[str, int]] = None,
    *,
    usage_file: Optional[Union[str, Path]] = None,
    tool_output_characters: int = 0,
) -> dict:
    report = collect_metrics(
        files,
        token_usage,
        usage_file=usage_file,
        tool_output_characters=tool_output_characters,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report
