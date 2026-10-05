import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from markitdown import MarkItDown

from app.extract_pdf_oss import extract_tables_and_images

load_dotenv()


def convert_with_markitdown(source: str, out_dir: str, name: str, with_images: bool = True) -> str:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": f"ingestion-pipeline-learning-project/0.1 ({os.environ.get('CONTACT_EMAIL', 'unknown')})"
    })
    markdown = MarkItDown(requests_session=session).convert(source).text_content

    if with_images and source.lower().endswith(".pdf"):
        _, image_files = extract_tables_and_images(source, str(out / "images"))
        if image_files:
            markdown += "\n\n## Extracted figures\n\n"
            for path in image_files:
                file_name = Path(path).name
                markdown += f"![{file_name}](images/{file_name})\n\n"

    md_path = out / f"{name}.md"
    md_path.write_text(markdown, encoding="utf-8")
    return str(md_path)