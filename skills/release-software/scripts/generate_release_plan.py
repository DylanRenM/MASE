#!/usr/bin/env python3
"""Generate a deterministic, evidence-neutral release plan from MASE YAML."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _load_runtime() -> None:
    try:
        import mase_cli.release  # noqa: F401
        return
    except ImportError:
        pass
    for parent in Path(__file__).resolve().parents:
        if (parent / "mase_cli" / "release.py").is_file():
            sys.path.insert(0, str(parent))
            return


_load_runtime()

from mase_cli.release import build_release_plan, load_release_context  # noqa: E402
from mase_cli.schema import GovernanceError  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a platform-neutral release plan without performing release actions."
    )
    parser.add_argument("--context", required=True, help="mase-release/v1 YAML context")
    parser.add_argument("--date", help="ISO date used in deterministic output")
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    parser.add_argument("--output", help="write to this path instead of stdout")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        generated_on = date.fromisoformat(args.date).isoformat() if args.date else date.today().isoformat()
        plan = build_release_plan(
            load_release_context(args.context), generated_on=generated_on
        )
    except (GovernanceError, ValueError) as exc:
        print(f"release-plan: error: {exc}", file=sys.stderr)
        return 3

    if args.json:
        output = json.dumps(
            plan.to_dict(), ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n"
    else:
        output = plan.to_markdown()
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
