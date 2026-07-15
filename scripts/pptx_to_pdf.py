"""
Convert PPTX to PDF using LibreOffice for visual verification.
"""
import subprocess
import os

pptx_path = '/Users/dylanren/Documents/trae_projects/日常办公/projects/unified-dev-framework-training.pptx'
pdf_path = '/Users/dylanren/Documents/trae_projects/日常办公/projects/unified-dev-framework-training.pdf'

if os.path.exists('/Applications/LibreOffice.app/Contents/MacOS/soffice'):
    cmd = [
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', os.path.dirname(pdf_path),
        pptx_path
    ]
    print(f"Converting PPTX to PDF with LibreOffice...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.returncode == 0:
        print(f"PDF saved to: {pdf_path}")
        print(f"PDF size: {os.path.getsize(pdf_path) / 1024:.1f} KB")
    else:
        print(f"Error: {result.stderr}")
else:
    print("LibreOffice not found")
