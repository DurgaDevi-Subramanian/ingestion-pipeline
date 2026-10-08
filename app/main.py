import ipaddress
import os
import re
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile

from app.extract_pdf_oss import extract_tables_and_images, extract_text_pypdf
from app.extract_web_oss import HEADERS, allowed_by_robots, fetch_soup, scrape_text_and_tables
from app.pipeline import available_tools, run_pipeline

load_dotenv()
API_KEY = os.environ.get("API_KEY")
MAX_PDF_MB = 20
MAX_HTML_MB = 5

app = FastAPI(title="Unstructured Data Ingestion API")


def require_key(x_api_key: str = Header(default="")):
    """Simple shared secret so strangers can't run up your cloud bill."""
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", Path(text).stem)[:60] or "document"


def check_tool(tool: str):
    if tool not in available_tools():
        raise HTTPException(400, f"tool must be one of {available_tools()}")


def check_url(url: str):
    parts = urlparse(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise HTTPException(400, "Please enter a valid http(s) URL")
    try:  # block localhost / private addresses (a basic safety check)
        infos = socket.getaddrinfo(parts.hostname, None)
        if not all(ipaddress.ip_address(i[4][0]).is_global for i in infos):
            raise ValueError
    except Exception:
        raise HTTPException(400, "That address is not allowed")
    if not allowed_by_robots(url):
        raise HTTPException(403, "The site's robots.txt does not allow scraping this page")


def read_pdf_upload(file: UploadFile) -> bytes:
    data = file.file.read()
    if len(data) > MAX_PDF_MB * 1024 * 1024:
        raise HTTPException(413, f"PDF is larger than {MAX_PDF_MB} MB")
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "That file is not a PDF")
    return data


def download_page(url: str) -> bytes:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    if len(response.content) > MAX_HTML_MB * 1024 * 1024:
        raise HTTPException(413, f"Page is larger than {MAX_HTML_MB} MB")
    return response.content


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"service": "Unstructured Data Ingestion API",
            "docs": "/docs", "health": "/health", "tools": "/tools"}

@app.get("/tools")
def tools():
    return {"tools": available_tools()}


# ---------- open-source extraction (Tasks 1 and 2) ----------
@app.post("/extract/pdf", dependencies=[Depends(require_key)])
def extract_pdf(file: UploadFile = File(...)):
    data = read_pdf_upload(file)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "input.pdf"
        path.write_bytes(data)
        text = extract_text_pypdf(str(path))
        tables, images = extract_tables_and_images(str(path), str(Path(tmp) / "images"))
    return {"characters": len(text), "text": text, "tables": tables, "image_count": len(images)}


@app.post("/extract/url", dependencies=[Depends(require_key)])
def extract_url(url: str = Form(...)):
    check_url(url)
    soup = fetch_soup(url)
    title, blocks, tables = scrape_text_and_tables(soup)
    return {"title": title, "text_blocks": blocks, "tables": tables,
            "image_count": len(soup.find_all("img"))}


# ---------- Docling / MarkItDown standardization (Task 4) + S3 (Task 5) ----------
@app.post("/convert/pdf", dependencies=[Depends(require_key)])
def convert_pdf(file: UploadFile = File(...), tool: str = Form("docling")):
    check_tool(tool)
    data = read_pdf_upload(file)
    name = safe_name(file.filename or "upload")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{name}.pdf"
        path.write_bytes(data)
        return run_pipeline(str(path), name, "pdf", "uploaded", f"upload:{file.filename}", tool, tmp)


@app.post("/convert/url", dependencies=[Depends(require_key)])
def convert_url(url: str = Form(...), tool: str = Form("markitdown")):
    check_tool(tool)
    check_url(url)
    html = download_page(url)
    host = urlparse(url).hostname
    name = safe_name(urlparse(url).path.strip("/").replace("/", "_") or host)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / f"{name}.html"
        path.write_bytes(html)
        return run_pipeline(str(path), name, "html", host, url, tool, tmp)