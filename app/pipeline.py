import re
import time
import os
from datetime import date
from pathlib import Path

from app.storage import make_doc_id, presigned_url, upload_file

def get_converter(tool: str):
    """Import lazily so a light deployment never loads Docling or PyTorch."""
    if tool == "docling":
        from app.convert_docling import convert_with_docling
        return convert_with_docling
    from app.convert_markitdown import convert_with_markitdown
    return convert_with_markitdown


def available_tools() -> list[str]:
    tools = ["markitdown"]
    if os.environ.get("ENABLE_DOCLING", "1") == "1":
        tools.insert(0, "docling")
    return tools

IMAGE_LINK = re.compile(r"\]\((images/[^)\s]+)\)")


def run_pipeline(local_path: str, name: str, doc_type: str, source: str,
                 source_url: str, tool: str, work_dir: str) -> dict:
    started = time.perf_counter()
    today = date.today().isoformat()
    doc_id = make_doc_id(local_path)

    meta = {"source-url": source_url, "tool": tool, "doc-type": doc_type,
            "processed-date": today, "doc-id": doc_id}
    tags = {"tool": tool, "doc-type": doc_type, "source": source,
            "processed-date": today}

    # 1. raw file
    raw_prefix = "raw/pdf" if doc_type == "pdf" else "raw/html"
    ext = Path(local_path).suffix
    upload_file(local_path, f"{raw_prefix}/{source}/{today}/{name}{ext}", meta, tags)

    # 2. convert
    out_dir = Path(work_dir) / tool
    md_path = Path(get_converter(tool)(local_path, str(out_dir), name))
    markdown = md_path.read_text(encoding="utf-8")

    # 3. upload images, then build two versions of the Markdown:
    #    s3:// links for storage, temporary https links for display
    s3_markdown, view_markdown = markdown, markdown
    image_count = 0
    for rel in set(IMAGE_LINK.findall(markdown)):
        local = out_dir / rel
        if not local.exists():
            continue
        key = f"assets/images/{source}/{doc_id}/{tool}_{local.name}"
        uri = upload_file(str(local), key, meta, tags)
        s3_markdown = s3_markdown.replace(f"]({rel})", f"]({uri})")
        view_markdown = view_markdown.replace(f"]({rel})", f"]({presigned_url(key)})")
        image_count += 1

    # 4. upload the Markdown itself
    s3_md_path = out_dir / f"{name}_s3.md"
    s3_md_path.write_text(s3_markdown, encoding="utf-8")
    md_key = f"processed/markdown/{tool}/{source}/{doc_id}.md"
    md_uri = upload_file(str(s3_md_path), md_key, meta, tags)

    return {
        "doc_id": doc_id,
        "tool": tool,
        "source": source,
        "markdown": view_markdown,
        "markdown_s3_uri": md_uri,
        "markdown_download_url": presigned_url(md_key),
        "image_count": image_count,
        "seconds": round(time.perf_counter() - started, 1),
    }