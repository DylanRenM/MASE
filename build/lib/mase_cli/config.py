"""Shared manifest and package-data loading for MASE v2."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional, Union

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[1]


PathInput = Union[str, os.PathLike]


def framework_home(explicit: Optional[PathInput] = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    configured = os.environ.get("MASE_FRAMEWORK_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    working_tree = Path.cwd()
    if (working_tree / "framework-manifest.yaml").exists():
        return working_tree.resolve()
    packaged = Path(sys.prefix) / "share" / "mase"
    if (packaged / "framework-manifest.yaml").exists():
        return packaged
    installed = Path.home() / ".measures-framework"
    if (installed / "framework-manifest.yaml").exists():
        return installed
    if (PACKAGE_ROOT / "framework-manifest.yaml").exists():
        return PACKAGE_ROOT
    raise FileNotFoundError(
        "MASE runtime not found; run `mase install --source /path/to/MASE` or set MASE_FRAMEWORK_HOME"
    )


def load_yaml(path: PathInput) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected mapping in {path}")
    return payload


def load_manifest(home: Optional[PathInput] = None) -> dict[str, Any]:
    root = framework_home(home)
    return load_yaml(root / "framework-manifest.yaml")
