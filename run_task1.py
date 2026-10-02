import sys
import time
from pathlib import Path

from app.extract_pdf_oss import extract_text_pypdf, extract_tables_and_images

pdf_path = sys.argv[1]                      # e.g. data/pdfs/paper1.pdf
name = Path(pdf_path).stem
out_dir = Path("data/output") / name / "oss"
out_dir.mkdir(parents=True, exist_ok=True)

start = time.perf_counter()
text = extract_text_pypdf(pdf_path)
(out_dir / "text.txt").write_text(text, encoding="utf-8")
t_text = time.perf_counter() - start

start = time.perf_counter()
tables, images = extract_tables_and_images(pdf_path, str(out_dir / "images"))
t_tables = time.perf_counter() - start

lines = []
for t in tables:
    lines.append(f"## Table (page {t['page']})")
    for row in t["rows"]:
        lines.append(" | ".join(cell or "" for cell in row))
    lines.append("")
(out_dir / "tables.txt").write_text("\n".join(lines), encoding="utf-8")

print(f"{name}: {len(text)} characters of text in {t_text:.1f}s")
print(f"{len(tables)} tables and {len(images)} images in {t_tables:.1f}s")