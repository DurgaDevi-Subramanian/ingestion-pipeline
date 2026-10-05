from pathlib import Path

from app.extract_web_oss import HEADERS, allowed_by_robots

import requests

urls = [u.strip() for u in Path("data/urls.txt").read_text().splitlines() if u.strip()]
Path("data/web_html").mkdir(parents=True, exist_ok=True)

for index, url in enumerate(urls, start=1):
    if not allowed_by_robots(url):
        print(f"web{index}: skipped (robots.txt)")
        continue
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    Path(f"data/web_html/web{index}.html").write_bytes(response.content)
    print(f"web{index}: saved")