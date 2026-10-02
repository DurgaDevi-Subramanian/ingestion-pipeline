from pathlib import Path
import time

import pdfplumber
from pypdf import PdfReader


def extract_text_pypdf(pdf_path: str) -> str:
    """Function 1: pull plain text from every page using pypdf."""
    reader = PdfReader(pdf_path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"--- Page {number} ---\n{text}")
    return "\n\n".join(pages)


TABLE_STRATEGIES = [
    ("lines", {}),
    ("hybrid", {"vertical_strategy": "text", "horizontal_strategy": "lines"}),
    ("text", {"vertical_strategy": "text", "horizontal_strategy": "text"}),
]


def find_tables_on_page(page):
    """Try each strategy in order and return the first sensible result."""
    for name, settings in TABLE_STRATEGIES:
        found = page.extract_tables(table_settings=settings)
        # Keep only real-looking tables: at least 2 rows and 2 columns
        found = [t for t in found if len(t) >= 2 and max(len(r) for r in t) >= 2]
        if found:
            return name, found
    return None, []


def extract_tables_and_images(pdf_path: str, out_dir: str):
    """Function 2: pull tables (pdfplumber) and save images as files."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tables = []
    image_files = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            strategy, page_tables = find_tables_on_page(page)
            for table in page_tables:
                tables.append({"page": page_number, "strategy": strategy, "rows": table})

            for index, img in enumerate(page.images, start=1):
                x0 = max(img["x0"], 0)
                top = max(img["top"], 0)
                x1 = min(img["x1"], page.width)
                bottom = min(img["bottom"], page.height)
                if x1 - x0 < 20 or bottom - top < 20:
                    continue
                path = out / f"page{page_number}_img{index}.png"
                page.crop((x0, top, x1, bottom)).to_image(resolution=150).save(str(path))
                image_files.append(str(path))

    return tables, image_files