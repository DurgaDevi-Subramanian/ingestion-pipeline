import time
from pathlib import Path

from app.convert_docling import convert_with_docling
from app.convert_markitdown import convert_with_markitdown

inputs = []
for pdf in sorted(Path("data/pdfs").glob("*.pdf")):
    inputs.append((pdf.stem, str(pdf)))

print(f"{'document':<10} {'tool':<11} {'seconds':>8}  output")
for name, source in inputs:
    base = Path("data/output") / name

    start = time.perf_counter()
    path = convert_with_docling(source, str(base / "docling"), name)
    print(f"{name:<10} {'docling':<11} {time.perf_counter() - start:>8.1f}  {path}")

    start = time.perf_counter()
    path = convert_with_markitdown(source, str(base / "markitdown"), name)
    print(f"{name:<10} {'markitdown':<11} {time.perf_counter() - start:>8.1f}  {path}")