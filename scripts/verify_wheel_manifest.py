#!/usr/bin/env python3
"""Verify that a built MASE wheel contains exactly the manifest runtime resources."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import yaml


IGNORED_NAMES = {".DS_Store"}


def expected_runtime_files(root: Path) -> set[str]:
    manifest_path = root / "framework-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    entries = [str(item).rstrip("/") for item in manifest["runtime"]]
    duplicates = []
    for index, left in enumerate(entries):
        for right in entries[index + 1:]:
            if left == right or left.startswith(f"{right}/") or right.startswith(f"{left}/"):
                duplicates.append((left, right))
    if duplicates:
        rendered = ", ".join(f"{left} <> {right}" for left, right in duplicates)
        raise ValueError(f"manifest runtime entries overlap: {rendered}")

    expected = {"framework-manifest.yaml"}
    for relative in entries:
        source = root / relative
        if not source.exists():
            raise FileNotFoundError(f"manifest runtime entry is missing: {relative}")
        if source.is_file():
            expected.add(relative)
            continue
        expected.update(
            item.relative_to(root).as_posix()
            for item in source.rglob("*")
            if item.is_file()
            and item.name not in IGNORED_NAMES
            and "__pycache__" not in item.parts
        )
    return expected


def wheel_runtime_files(wheel: Path) -> set[str]:
    marker = ".data/data/share/mase/"
    with zipfile.ZipFile(wheel) as archive:
        return {
            name.split(marker, 1)[1]
            for name in archive.namelist()
            if marker in name and not name.endswith("/")
        }


def verify(root: Path, wheel: Path) -> dict[str, object]:
    expected = expected_runtime_files(root.resolve())
    actual = wheel_runtime_files(wheel.resolve())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    return {
        "ok": not missing and not extra,
        "expected": len(expected),
        "actual": len(actual),
        "missing": missing,
        "extra": extra,
        "wheel": str(wheel),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = verify(args.root, args.wheel)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif report["ok"]:
        print(f"wheel runtime contract passed: {report['actual']} resources")
    else:
        print("wheel runtime contract failed")
        for key in ("missing", "extra"):
            for item in report[key]:
                print(f"  {key}: {item}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
