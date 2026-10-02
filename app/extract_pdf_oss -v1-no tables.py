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


def extract_tables_and_images(pdf_path: str, out_dir: str):
    """Function 2: pull tables (pdfplumber) and save images as files."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    tables = []
    image_files = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            # Tables: each table is a list of rows, each row a list of cells
            for table in page.extract_tables():
                tables.append({"page": page_number, "rows": table})

            # Images: crop the region of the page where each image sits
            for index, img in enumerate(page.images, start=1):
                x0 = max(img["x0"], 0)
                top = max(img["top"], 0)
                x1 = min(img["x1"], page.width)
                bottom = min(img["bottom"], page.height)
                if x1 - x0 < 20 or bottom - top < 20:
                    continue  # skip tiny decorations
                path = out / f"page{page_number}_img{index}.png"
                page.crop((x0, top, x1, bottom)).to_image(resolution=150).save(str(path))
                image_files.append(str(path))

    return tables, image_files