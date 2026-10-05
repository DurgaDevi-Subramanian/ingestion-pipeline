import sys
import time
from pathlib import Path

from app.extract_pdf_azure import extract_pdf_azure

pdf_path = sys.argv[1]  # e.g. data/pdfs/paper1.pdf
name = Path(pdf_path).stem
out_dir = Path("data/output") / name / "azure"
out_dir.mkdir(parents=True, exist_ok=True)

start = time.perf_counter()
max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else None
markdown = extract_pdf_azure(pdf_path, max_pages=max_pages)
elapsed = time.perf_counter() - start

(out_dir / "azure_layout.md").write_text(markdown, encoding="utf-8")
print(f"{name}: {len(markdown)} characters of Markdown in {elapsed:.1f}s")