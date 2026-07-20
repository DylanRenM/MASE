"""Install only manifest-declared MASE runtime resources."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Union

from mase_cli.config import framework_home, load_manifest


def install_runtime(
    source: Union[str, Path],
    destination: Union[str, Path],
    dry_run: bool = False,
) -> list[str]:
    root = Path(source).expanduser().resolve()
    target = Path(destination).expanduser().resolve()
    manifest = load_manifest(root)
    resources = ["framework-manifest.yaml"] + list(manifest.get("runtime", []))
    installed: list[str] = []
    for relative in resources:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Unsafe manifest resource path: {relative}")
        src = root / relative_path
        if not src.exists():
            raise FileNotFoundError(f"Manifest resource does not exist: {relative}")
        installed.append(relative)
        if dry_run:
            continue
        dst = target / relative_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(
                src,
                dst,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
            )
        else:
            shutil.copy2(src, dst)
    return installed


def run(args):
    source = framework_home(getattr(args, "source", None))
    destination = Path(args.destination).expanduser() if args.destination else Path.home() / ".measures-framework"
    installed = install_runtime(source, destination, getattr(args, "dry_run", False))
    verb = "Would install" if getattr(args, "dry_run", False) else "Installed"
    print(f"{verb} {len(installed)} MASE runtime resources to {destination}")
    return installed
