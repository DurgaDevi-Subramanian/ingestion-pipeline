import re
from datetime import date
from pathlib import Path

from app.storage import make_doc_id, upload_file

today = date.today().isoformat()
urls = [u.strip() for u in Path("data/urls.txt").read_text().splitlines() if u.strip()]
web_sources = {}
for line in Path("data/sources.txt").read_text(encoding="utf-8").splitlines():
    if line.strip():
        page, site = line.split(",")
        web_sources[page.strip()] = site.strip().lower()

IMAGE_LINK = re.compile(r"\]\((images/[^)\s]+)\)")


def process(name: str, raw_path: str, doc_type: str, source: str, source_url: str):
    doc_id = make_doc_id(raw_path)
    raw_prefix = "raw/pdf" if doc_type == "pdf" else "raw/html"
    ext = Path(raw_path).suffix

    # 1. raw file
    upload_file(
        raw_path, f"{raw_prefix}/{source}/{today}/{name}{ext}",
        metadata={"source-url": source_url, "doc-type": doc_type, "processed-date": today},
        tags={"doc-type": doc_type, "source": source, "processed-date": today},
    )

    for tool in ("docling", "markitdown"):
        tool_dir = Path("data/output") / name / tool
        md_path = tool_dir / f"{name}.md"
        if not md_path.exists():
            continue
        meta = {"source-url": source_url, "tool": tool, "doc-type": doc_type,
                "processed-date": today, "doc-id": doc_id}
        tags = {"tool": tool, "doc-type": doc_type, "source": source, "processed-date": today}

        # 2. images, then rewrite their links in the Markdown
        markdown = md_path.read_text(encoding="utf-8")

        def replace(match):
            local = tool_dir / match.group(1)
            if not local.exists():
                return match.group(0)
            key = f"assets/images/{source}/{doc_id}/{tool}_{local.name}"
            return f"]({upload_file(str(local), key, metadata=meta, tags=tags)})"

        markdown = IMAGE_LINK.sub(replace, markdown)

        # 3. Markdown with S3 image links
        s3_md = tool_dir / f"{name}_s3.md"
        s3_md.write_text(markdown, encoding="utf-8")
        link = upload_file(str(s3_md), f"processed/markdown/{tool}/{source}/{doc_id}.md",
                           metadata=meta, tags=tags)
        print(f"{name} [{tool}] -> {link}")


for pdf in sorted(Path("data/pdfs").glob("*.pdf")):
    process(pdf.stem, str(pdf), "pdf", "arxiv", f"local-file:{pdf.name}")

for index, url in enumerate(urls, start=1):
    name = f"web{index}"
    html = Path(f"data/web_html/{name}.html")
    if html.exists():
        process(name, str(html), "html", web_sources.get(name, "web"), url)