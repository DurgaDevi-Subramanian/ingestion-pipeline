import os
from pathlib import Path

import pdfplumber
import pytesseract
from dotenv import load_dotenv
from PIL import Image
from pypdf import PdfReader

load_dotenv()
if os.environ.get("TESSERACT_CMD"):
    pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_CMD"]

MIN_TEXT_CHARS = 50  # a page with less text than this is treated as "scanned"


# ---------- Function 1: text ----------
def extract_text_pypdf(pdf_path: str) -> str:
    """Pull plain text from every page using pypdf."""
    reader = PdfReader(pdf_path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"--- Page {number} ---\n{text}")
    return "\n\n".join(pages)


# ---------- Function 2: tables and images ----------
TABLE_STRATEGIES = [
    ("lines", {}),
    ("hybrid", {"vertical_strategy": "text", "horizontal_strategy": "lines"}),
    ("text", {"vertical_strategy": "text", "horizontal_strategy": "text"}),
]


def find_tables_on_page(page):
    """Try each strategy in order and return the first sensible result."""
    for name, settings in TABLE_STRATEGIES:
        found = page.extract_tables(table_settings=settings)
        found = [t for t in found if len(t) >= 2 and max(len(r) for r in t) >= 2]
        if found:
            return name, found
    return None, []


def extract_tables_and_images(pdf_path: str, out_dir: str):
    """Pull tables (pdfplumber) and save embedded images as files."""
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


# ---------- Function 3 (new): OCR ----------
def ocr_images(image_files: list[str]) -> dict[str, str]:
    """Run OCR on each saved image (charts, diagrams, tables stored as pictures)."""
    results = {}
    for path in image_files:
        with Image.open(path) as img:
            text = pytesseract.image_to_string(img, config="--psm 6").strip()
        results[path] = text
    return results


def extract_text_with_ocr_fallback(pdf_path: str, resolution: int = 200):
    """Use normal text where it exists; OCR the page where it is (almost) empty."""
    reader = PdfReader(pdf_path)
    pages = []
    ocr_pages = []

    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            if len(text) < MIN_TEXT_CHARS:
                image = pdf.pages[index].to_image(resolution=resolution).original
                text = pytesseract.image_to_string(image).strip()
                ocr_pages.append(index + 1)
            pages.append(f"--- Page {index + 1} ---\n{text}")

    return "\n\n".join(pages), ocr_pages