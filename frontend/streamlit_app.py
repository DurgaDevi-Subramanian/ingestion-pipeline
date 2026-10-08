import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def setting(name: str, default: str = "") -> str:
    try:
        return st.secrets[name]          # used when deployed
    except Exception:
        return os.environ.get(name, default)   # used locally


API_URL = setting("API_URL", "http://localhost:8000").rstrip("/")
API_KEY = setting("API_KEY")

st.set_page_config(page_title="Document to Markdown", page_icon="📄")
st.title("📄 Document to Markdown")
st.write("Upload a PDF or paste a web page URL and get clean Markdown back.")

@st.cache_data(ttl=300)
def get_tools():
    try:
        return requests.get(f"{API_URL}/tools", timeout=60).json()["tools"]
    except Exception:
        return ["docling", "markitdown"]
    
tool = st.selectbox(
    "Conversion tool",
    get_tools(),
    help="Docling is slower but better with tables and equations. MarkItDown is fast and simple.",
)
tab_pdf, tab_url = st.tabs(["Upload a PDF", "Enter a URL"])

result = None
headers = {"x-api-key": API_KEY}

with tab_pdf:
    pdf = st.file_uploader("PDF file (max 20 MB)", type="pdf")
    if st.button("Convert PDF", disabled=pdf is None):
        with st.spinner("Converting... Docling can take a few minutes."):
            try:
                r = requests.post(
                    f"{API_URL}/convert/pdf", headers=headers,
                    files={"file": (pdf.name, pdf.getvalue(), "application/pdf")},
                    data={"tool": tool}, timeout=900,
                )
                result = r
            except requests.RequestException as e:
                st.error(f"Could not reach the API: {e}")

with tab_url:
    url = st.text_input("Web page URL", placeholder="https://en.wikipedia.org/wiki/Markdown")
    if st.button("Convert URL", disabled=not url):
        with st.spinner("Fetching and converting..."):
            try:
                result = requests.post(
                    f"{API_URL}/convert/url", headers=headers,
                    data={"url": url, "tool": tool}, timeout=900,
                )
            except requests.RequestException as e:
                st.error(f"Could not reach the API: {e}")

if result is not None:
    if result.ok:
        out = result.json()
        st.success(f"Done in {out['seconds']} s with {out['tool']} "
                   f"({out['image_count']} images stored in S3)")
        rendered, raw = st.tabs(["Rendered", "Raw Markdown"])
        with rendered:
            st.markdown(out["markdown"])
        with raw:
            st.code(out["markdown"], language="markdown")
        st.download_button("Download Markdown", out["markdown"],
                           file_name=f"{out['doc_id']}.md", mime="text/markdown")
        st.caption(f"Stored at: {out['markdown_s3_uri']}")
    else:
        st.error(f"Error {result.status_code}: {result.text}")