import sys
import time
from pathlib import Path

from app.extract_pdf_oss import (
    extract_text_pypdf,
    extract_tables_and_images,
    ocr_images,
    extract_text_with_ocr_fallback,
)

pdf_path = sys.argv[1]  # e.g. data/pdfs/paper1.pdf
name = Path(pdf_path).stem
out_dir = Path("data/output") / name / "oss"
out_dir.mkdir(parents=True, exist_ok=True)

# 1. Plain text
start = time.perf_counter()
text = extract_text_pypdf(pdf_path)
(out_dir / "text.txt").write_text(text, encoding="utf-8")
t_text = time.perf_counter() - start

# 2. Tables and images
start = time.perf_counter()
tables, images = extract_tables_and_images(pdf_path, str(out_dir / "images"))
t_tables = time.perf_counter() - start

lines = []
for t in tables:
    lines.append(f"## Table (page {t['page']}, strategy: {t['strategy']})")
    for row in t["rows"]:
        lines.append(" | ".join((cell or "").replace("\n", " ") for cell in row))
    lines.append("")
(out_dir / "tables.txt").write_text("\n".join(lines), encoding="utf-8")

# 3. OCR on the extracted images
start = time.perf_counter()
ocr_results = ocr_images(images)
t_ocr_images = time.perf_counter() - start

ocr_lines = []
for path, ocr_text in ocr_results.items():
    ocr_lines.append(f"## {Path(path).name}")
    ocr_lines.append(ocr_text or "(no text found)")
    ocr_lines.append("")
(out_dir / "ocr_images.txt").write_text("\n".join(ocr_lines), encoding="utf-8")

# 4. Text with OCR fallback for pages that have no real text
start = time.perf_counter()
full_text, ocr_pages = extract_text_with_ocr_fallback(pdf_path)
(out_dir / "text_with_ocr_fallback.txt").write_text(full_text, encoding="utf-8")
t_fallback = time.perf_counter() - start

print(f"{name}: {len(text)} characters of text in {t_text:.1f}s")
print(f"{len(tables)} tables and {len(images)} images in {t_tables:.1f}s")
print(f"OCR on {len(images)} images in {t_ocr_images:.1f}s")
print(f"Pages that needed OCR fallback: {ocr_pages or 'none'} ({t_fallback:.1f}s)")