import json
import time
from pathlib import Path

from app.extract_web_oss import (
    allowed_by_robots, fetch_soup, scrape_text_and_tables, scrape_images,
)

urls = [u.strip() for u in Path("data/urls.txt").read_text().splitlines() if u.strip()]

for index, url in enumerate(urls, start=1):
    name = f"web{index}"
    print(f"\n{name}: {url}")

    if not allowed_by_robots(url):
        print("  Skipped: robots.txt does not allow this page.")
        continue

    out_dir = Path("data/output") / name / "oss"
    out_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()
    soup = fetch_soup(url)
    title, blocks, tables = scrape_text_and_tables(soup)
    images = scrape_images(soup, url, str(out_dir / "images"))
    elapsed = time.perf_counter() - start

    text_lines = [f"{b['tag'].upper()}: {b['text']}" for b in blocks]
    (out_dir / "text.txt").write_text("\n".join(text_lines), encoding="utf-8")

    table_lines = []
    for number, rows in enumerate(tables, start=1):
        table_lines.append(f"## Table {number}")
        for row in rows:
            table_lines.append(" | ".join(row))
        table_lines.append("")
    (out_dir / "tables.txt").write_text("\n".join(table_lines), encoding="utf-8")

    (out_dir / "images.json").write_text(json.dumps(images, indent=2), encoding="utf-8")

    downloaded = sum(1 for i in images if i["file"])
    print(f"  {len(blocks)} text blocks, {len(tables)} tables, "
          f"{len(images)} images ({downloaded} downloaded) in {elapsed:.1f}s")