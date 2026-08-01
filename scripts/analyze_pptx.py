#!/usr/bin/env python3
"""Analyze a selected PPTX for canvas bounds and editable-text density."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PPTX = ROOT / "training/mase-framework/MASE框架培训讲义V2.4.pptx"


def analyze(path: Path) -> dict[str, object]:
    prs = Presentation(path)
    slides: list[dict[str, object]] = []
    total_out_of_bounds = 0
    for number, slide in enumerate(prs.slides, 1):
        text_shapes = [
            shape
            for shape in slide.shapes
            if getattr(shape, "has_text_frame", False) and shape.text.strip()
        ]
        out_of_bounds = [
            shape.name
            for shape in slide.shapes
            if shape.left < 0
            or shape.top < 0
            or shape.left + shape.width > prs.slide_width
            or shape.top + shape.height > prs.slide_height
        ]
        total_out_of_bounds += len(out_of_bounds)
        slides.append(
            {
                "number": number,
                "editable_text_shapes": len(text_shapes),
                "characters": sum(len(shape.text) for shape in text_shapes),
                "out_of_bounds": out_of_bounds,
            }
        )
    return {
        "path": str(path),
        "slide_count": len(prs.slides),
        "canvas": {"width": prs.slide_width, "height": prs.slide_height},
        "out_of_bounds_shapes": total_out_of_bounds,
        "max_characters": max((item["characters"] for item in slides), default=0),
        "slides": slides,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", nargs="?", type=Path, default=DEFAULT_PPTX)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = analyze(args.pptx.resolve())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Slides: {result['slide_count']}")
        print(f"Out-of-bounds shapes: {result['out_of_bounds_shapes']}")
        print(f"Maximum characters on one slide: {result['max_characters']}")
        dense = sorted(result["slides"], key=lambda item: item["characters"], reverse=True)[:10]
        print("Densest slides: " + ", ".join(f"{item['number']}({item['characters']})" for item in dense))
    return 0 if result["out_of_bounds_shapes"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
