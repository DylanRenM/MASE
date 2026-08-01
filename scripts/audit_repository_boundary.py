#!/usr/bin/env python3
"""Audit that a MASE checkout contains only process-framework content."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_TOP_LEVEL_DIRECTORIES = frozenset(
    {
        ".git", ".github", ".mase", "agents", "docs", "mase_cli", "openspec",
        "profiles", "schemas", "scripts", "skills", "templates", "tests", "training",
    }
)
ALLOWED_TOP_LEVEL_FILES = frozenset(
    {
        ".gitignore", ".mase.yaml", "AGENTS.md", "CLAUDE.md", "CONVENTIONS.md",
        "LICENSE", "README.md", "framework-manifest.yaml", "install.sh", "package-lock.json",
        "package.json", "project-rules.md", "pyproject.toml", "requirements-offline.txt",
        "requirements-runtime.txt", "sandbox.config.json", "vitest.config.js",
    }
)
ALLOWED_DOCS = frozenset(
    {
        "MASE-framework.md", "coding-standards.md", "design-principles.md", "glossary.md",
        "project-structure-spec.md", "user-guide.md",
    }
)
ALLOWED_TRAINING_ROOTS = frozenset({"mase-framework"})
ALLOWED_MASE_TRAINING_FILES = frozenset(
    {
        "MASE框架培训大纲.xlsx", "MASE框架培训讲义V1.pptx",
        "MASE框架培训讲义V2.3.pptx", "MASE框架培训讲义V2.4.pptx",
        "mase-training-v2.4.yaml",
    }
)
GENERATED_DIRECTORY_NAMES = frozenset(
    {"node_modules", "build", ".build", "dist"}
)


def audit_repository(root: Path, *, ignore_os_metadata: bool = True) -> dict[str, Any]:
    root = root.expanduser().resolve()
    issues: dict[str, dict[str, str]] = {}

    def add(path: Path, code: str, message: str) -> None:
        relative = path.relative_to(root).as_posix()
        issues.setdefault(relative, {"path": relative, "code": code, "message": message})

    for entry in root.iterdir():
        if entry.name == ".DS_Store":
            continue
        if entry.is_dir() and entry.name not in ALLOWED_TOP_LEVEL_DIRECTORIES:
            add(entry, "unexpected_root", "directory is not owned by the MASE framework")
        elif entry.is_file() and entry.name not in ALLOWED_TOP_LEVEL_FILES:
            add(entry, "unexpected_root", "file is not owned by the MASE framework")

    docs = root / "docs"
    if docs.is_dir():
        for entry in docs.iterdir():
            if entry.name == ".DS_Store":
                continue
            if entry.name not in ALLOWED_DOCS:
                add(entry, "noncanonical_docs", "only current manifest-routed docs belong here")

    training = root / "training"
    if training.is_dir():
        for entry in training.iterdir():
            if entry.name == ".DS_Store":
                continue
            if entry.name not in ALLOWED_TRAINING_ROOTS:
                add(entry, "non_mase_training", "only MASE framework training belongs here")
        mase_training = training / "mase-framework"
        if mase_training.is_dir():
            for entry in mase_training.iterdir():
                if entry.name == ".DS_Store":
                    continue
                if entry.name not in ALLOWED_MASE_TRAINING_FILES:
                    add(entry, "obsolete_training", "training file is not part of the guarded current deck")

    skipped = {root / ".git", root / ".mase" / "evidence"}
    for entry in root.rglob("*"):
        if any(parent == entry or parent in entry.parents for parent in skipped):
            continue
        if "__pycache__" in entry.parts or entry.name == ".pytest_cache" or ".pytest_cache" in entry.parts:
            continue
        if entry.name == ".DS_Store":
            continue
        if entry.is_dir() and (
            entry.name in GENERATED_DIRECTORY_NAMES or entry.name.endswith(".egg-info")
        ):
            add(entry, "generated_debris", "generated directory must not remain in MASE")
        elif entry.name == ".git" and entry != root / ".git":
            add(entry, "nested_repository", "embedded repositories must be sibling projects")

    ordered = [issues[path] for path in sorted(issues)]
    return {"ok": not ordered, "issues": ordered}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--ignore-os-metadata",
        action="store_true",
        help="deprecated compatibility flag; Finder metadata is always ignored",
    )
    args = parser.parse_args(argv)
    result = audit_repository(args.root, ignore_os_metadata=args.ignore_os_metadata)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["ok"]:
        print("MASE repository boundary is clean")
    else:
        print("MASE repository boundary violations:")
        for issue in result["issues"]:
            print(f"- {issue['path']}: {issue['message']} [{issue['code']}]")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
