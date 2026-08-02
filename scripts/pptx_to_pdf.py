#!/usr/bin/env python3
"""Convert a selected PPTX to PDF with LibreOffice for visual verification."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PPTX = ROOT / "training/mase-framework/MASE框架培训讲义V2.4.pptx"


def convert(pptx: Path, output_dir: Path) -> Path:
    if not pptx.is_file():
        raise FileNotFoundError(pptx)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        macos_soffice = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
        if macos_soffice.is_file():
            soffice = str(macos_soffice)
    if not soffice:
        raise RuntimeError("LibreOffice/soffice is not installed")

    output_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(pptx)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "conversion failed")
    pdf = output_dir / f"{pptx.stem}.pdf"
    if not pdf.is_file():
        raise RuntimeError(f"LibreOffice reported success but did not create {pdf}")
    return pdf


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", nargs="?", type=Path, default=DEFAULT_PPTX)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".build/training-preview")
    args = parser.parse_args()
    pdf = convert(args.pptx.resolve(), args.output_dir.resolve())
    print(f"PDF saved to: {pdf}")
    print(f"PDF size: {pdf.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
