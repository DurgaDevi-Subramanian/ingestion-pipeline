import os
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "User-Agent": f"ingestion-pipeline-learning-project/0.1 ({os.environ.get('CONTACT_EMAIL', 'unknown')})"
}


def allowed_by_robots(url: str) -> bool:
    """Check the site's robots.txt before scraping."""
    parts = urlparse(url)
    robots_url = f"{parts.scheme}://{parts.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return True  # no readable robots.txt: no stated restrictions
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        return parser.can_fetch(HEADERS["User-Agent"], url)
    except requests.RequestException:
        return True


def fetch_soup(url: str) -> BeautifulSoup:
    """Download the page and parse it."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    # Remove layout noise that isn't content
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]):
        tag.decompose()
    return soup


# ---------- Function 1: text and tables ----------
def scrape_text_and_tables(soup: BeautifulSoup):
    """Return the page's text blocks in order, plus every table as rows."""
    title = soup.title.get_text(strip=True) if soup.title else ""

    blocks = []
    for element in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = element.get_text(" ", strip=True)
        if text:
            blocks.append({"tag": element.name, "text": text})

    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if len(rows) >= 2:  # skip layout-only tables
            tables.append(rows)

    return title, blocks, tables


# ---------- Function 2: images ----------
def scrape_images(soup: BeautifulSoup, page_url: str, out_dir: str,
                  download: bool = True, max_images: int = 15):
    """Record every image URL and (optionally) download the files."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    records = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src")
        if not src or src.startswith("data:"):
            continue
        full_url = urljoin(page_url, src)  # turns //site/x.png into https://site/x.png
        record = {"url": full_url, "alt": img.get("alt", ""), "file": None}

        if download and len(records) < max_images:
            suffix = Path(urlparse(full_url).path).suffix or ".img"
            path = out / f"img{len(records) + 1}{suffix}"
            try:
                r = requests.get(full_url, headers=HEADERS, timeout=30)
                r.raise_for_status()
                path.write_bytes(r.content)
                record["file"] = str(path)
            except requests.RequestException:
                pass

        records.append(record)
    return records