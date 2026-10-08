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
            text = pytesseract.image_to_string(img, config="--psm 3").strip()
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


# ---------- Function 4: everything together, in reading order ----------
def inside_bbox(obj, bbox):
    """True if the middle of this object (a character) is inside the rectangle."""
    x0, top, x1, bottom = bbox
    cx = (obj["x0"] + obj["x1"]) / 2
    cy = (obj["top"] + obj["bottom"]) / 2
    return x0 <= cx <= x1 and top <= cy <= bottom


def table_to_markdown(rows):
    """Turn a list of rows into a Markdown table."""
    rows = [[(c or "").replace("\n", " ") for c in r] for r in rows]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]   # make every row equally wide
    lines = ["| " + " | ".join(rows[0]) + " |",
             "| " + " | ".join(["---"] * width) + " |"]
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def find_table_objects(page):
    """Same idea as find_tables_on_page, but returns Table objects (they have a bbox)."""
    for name, settings in TABLE_STRATEGIES:
        good = []
        for t in page.find_tables(table_settings=settings):
            rows = t.extract()
            if len(rows) >= 2 and max(len(r) for r in rows) >= 2:
                good.append((t.bbox, rows))
        if good:
            return name, good
    return None, []


def extract_in_reading_order(pdf_path: str, out_dir: str, ocr: bool = True) -> str:
    """Build ONE Markdown document: text, tables and images in page order."""
    out = Path(out_dir)
    (out / "images").mkdir(parents=True, exist_ok=True)
    document = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            blocks = []   # each block is (top, kind, content)

            # --- scanned page: just OCR the whole page ---
            if len(page.chars) < MIN_TEXT_CHARS:
                image = page.to_image(resolution=200).original
                blocks.append((0, "text", pytesseract.image_to_string(image).strip()))
            else:
                # --- tables ---
                strategy, tables = find_table_objects(page)
                table_boxes = []
                for bbox, rows in tables:
                    table_boxes.append(bbox)
                    blocks.append((bbox[1], "table", table_to_markdown(rows)))

                # --- images ---
                for index, img in enumerate(page.images, start=1):
                    x0 = max(img["x0"], 0)
                    top = max(img["top"], 0)
                    x1 = min(img["x1"], page.width)
                    bottom = min(img["bottom"], page.height)
                    if x1 - x0 < 20 or bottom - top < 20:
                        continue
                    filename = f"page{page_number}_img{index}.png"
                    cropped = page.crop((x0, top, x1, bottom))
                    cropped.to_image(resolution=150).save(str(out / "images" / filename))
                    content = f"![page {page_number} image {index}](images/{filename})"
                    if ocr:
                        with Image.open(out / "images" / filename) as im:
                            found = pytesseract.image_to_string(im, config="--psm 6").strip()
                        if found:
                            content += "\n\n> OCR text:\n> " + found.replace("\n", "\n> ")
                    blocks.append((top, "image", content))

                # --- text lines that are NOT inside a table ---
                outside = page.filter(
                    lambda o: not (o["object_type"] == "char"
                                   and any(inside_bbox(o, b) for b in table_boxes))
                )
                for line in outside.extract_text_lines():
                    blocks.append((line["top"], "text", line["text"]))

            # --- sort everything top-to-bottom ---
            blocks.sort(key=lambda b: b[0])

            # --- join: consecutive text lines stay together, others get blank lines ---
            parts = []
            previous = None
            for top, kind, content in blocks:
                if kind == "text" and previous == "text":
                    parts[-1] += "\n" + content
                else:
                    parts.append(content)
                previous = kind

            document.append(f"## Page {page_number}\n\n" + "\n\n".join(parts))

    return "\n\n---\n\n".join(document)