"""mase metrics — actual token telemetry or explicitly labeled context proxies."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, Mapping, Optional, Union

from mase_cli.schema import load_yaml_document
from mase_cli.test_selection import load_test_manifest


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


def collect_test_automation_metrics(
    project_root: Union[str, Path],
    *,
    manual_regression_minutes: Optional[float] = None,
    manual_regression_source: str = "",
) -> dict:
    root = Path(project_root).expanduser().resolve()
    manifest = load_test_manifest(root, required=False)
    ui_tiers = {"ui_contract", "p0_journey", "p1_regression"}
    eligible_capabilities = {
        capability
        for item in manifest.tests
        if item.tier in ui_tiers
        for capability in item.capabilities
    }
    covered_capabilities = {
        capability
        for item in manifest.tests
        if item.tier == "p0_journey"
        for capability in item.capabilities
    }
    records = []
    changes = root / "openspec" / "changes"
    if changes.is_dir():
        for state_path in sorted(changes.glob("*/mase-state.yaml")):
            payload = load_yaml_document(state_path)
            records.extend(
                item
                for item in payload.get("evidence", [])
                if item.get("gate") == "p0_e2e" and item.get("kind") == "automatic"
            )
    with_attempts = [item for item in records if item.get("first_attempt_result")]
    first_passes = sum(
        1 for item in with_attempts if item.get("first_attempt_result") == "passed"
    )
    flaky = sum(1 for item in records if item.get("failure_classification") == "flaky")
    failures = [item for item in records if item.get("result") == "failed"]
    classified_failures = sum(
        1
        for item in failures
        if item.get("failure_classification")
        not in (None, "", "unknown")
    )

    def ratio(numerator: int, denominator: int):
        return round(numerator / denominator, 4) if denominator else None

    if manual_regression_minutes is not None:
        if manual_regression_minutes < 0:
            raise ValueError("manual regression minutes cannot be negative")
        if not manual_regression_source.strip():
            raise ValueError("manual regression source is required for an actual metric")
        manual = {
            "kind": "actual",
            "minutes": float(manual_regression_minutes),
            "source": manual_regression_source.strip(),
        }
    else:
        manual = {
            "kind": "unavailable",
            "note": "No sourced manual regression duration was supplied; no proxy was invented.",
        }
    return {
        "kind": "actual_test_evidence",
        "p0": {
            "runs": len(records),
            "first_pass_rate": ratio(first_passes, len(with_attempts)),
            "flaky_rate": ratio(flaky, len(records)),
            "duration_seconds": round(sum(float(item.get("duration_seconds", 0) or 0) for item in records), 3),
            "classified_failure_rate": ratio(classified_failures, len(failures)),
        },
        "capability_journey_coverage": {
            "covered": len(covered_capabilities),
            "eligible": len(eligible_capabilities),
            "rate": ratio(len(covered_capabilities), len(eligible_capabilities)),
        },
        "manual_regression": manual,
        "sources": {
            "manifest": str(manifest.path.relative_to(root)) if not manifest.legacy else "missing",
            "evidence": "openspec/changes/*/mase-state.yaml",
        },
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
