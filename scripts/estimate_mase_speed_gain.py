#!/usr/bin/env python3
"""Estimate MASE stage latency from local structured gate evidence."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Any, DefaultDict

import yaml


MIN_PERCENTILE_SAMPLES = 3


def _automatic_durations(root: Path) -> dict[str, list[float]]:
    durations: DefaultDict[str, list[float]] = defaultdict(list)
    seen: set[Any] = set()
    for state_path in root.glob("openspec/changes/**/mase-state.yaml"):
        try:
            state = yaml.safe_load(state_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        for record in state.get("evidence", []) or []:
            if not isinstance(record, dict) or record.get("kind") != "automatic":
                continue
            duration = record.get("duration_seconds")
            if not isinstance(duration, (int, float)):
                continue
            identity = record.get("execution_id") or (
                state_path.as_posix(), record.get("gate"), record.get("at")
            )
            if identity in seen:
                continue
            seen.add(identity)
            durations[str(record.get("gate", ""))].append(float(duration))
    return dict(durations)


def estimate_from_repository(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    registry = yaml.safe_load((root / ".mase/gates.yaml").read_text(encoding="utf-8"))
    definitions = dict(registry.get("gates", {}))
    durations = _automatic_durations(root)

    gate_statistics: dict[str, dict[str, Any]] = {}
    stage_observed_medians: DefaultDict[str, float] = defaultdict(float)
    insufficient: list[str] = []
    for gate, samples in sorted(durations.items()):
        if gate not in definitions or not samples:
            continue
        required_at = str(definitions[gate].get("required_at", "unknown"))
        observed_median = float(median(samples))
        percentile_ready = len(samples) >= MIN_PERCENTILE_SAMPLES
        if not percentile_ready:
            insufficient.append(gate)
        gate_statistics[gate] = {
            "required_at": required_at,
            "sample_count": len(samples),
            "observed_median_seconds": round(observed_median, 4),
            "p50_seconds": round(observed_median, 4) if percentile_ready else None,
        }
        stage_observed_medians[required_at] += observed_median

    development = stage_observed_medians["development"]
    old_pre_hand_test = sum(
        stage_observed_medians[stage]
        for stage in ("development", "merge", "release")
    )
    directional_gain = (
        1 - development / old_pre_hand_test if old_pre_hand_test else None
    )
    return {
        "automatic_evidence_records": sum(len(items) for items in durations.values()),
        "minimum_percentile_samples": MIN_PERCENTILE_SAMPLES,
        "percentile_ready": not insufficient,
        "insufficient_sample_gates": insufficient,
        "gate_statistics": gate_statistics,
        "development_observed_median_serial_seconds": round(development, 2),
        "merge_observed_median_serial_seconds": round(stage_observed_medians["merge"], 2),
        "release_observed_median_serial_seconds": round(stage_observed_medians["release"], 2),
        "old_pre_hand_test_observed_median_serial_seconds": round(old_pre_hand_test, 2),
        "hand_test_wait_reduction_estimate": (
            round(directional_gain, 4) if directional_gain is not None else None
        ),
        "confidence": "low" if insufficient else "calibrated",
        "universal_commitment": False,
        "note": (
            "Observed-median serial proxy only; gates with fewer than three samples "
            "remain percentile-unknown. Recalculate with equivalent project evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = estimate_from_repository(args.root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        gain = report["hand_test_wait_reduction_estimate"]
        gain_text = "unknown" if gain is None else f"{gain:.1%}"
        print(f"可手测等待方向性收益：{gain_text}")
        print(f"置信度：{report['confidence']}")
        print(report["note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
