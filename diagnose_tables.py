import sys
import pdfplumber

pdf_path = sys.argv[1]

strategies = {
    "default (lines)": {},
    "hybrid (text columns, line rows)": {
        "vertical_strategy": "text",
        "horizontal_strategy": "lines",
    },
    "text only": {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
    },
}

with pdfplumber.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        counts = {
            name: len(page.find_tables(table_settings=settings))
            for name, settings in strategies.items()
        }
        print(f"Page {page_number}: {counts}")