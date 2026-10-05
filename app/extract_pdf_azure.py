import io
import os

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from pypdf import PdfReader, PdfWriter

load_dotenv()

client = DocumentIntelligenceClient(
    os.environ["AZURE_DI_ENDPOINT"],
    AzureKeyCredential(os.environ["AZURE_DI_KEY"]),
)


def _analyze_bytes(data: bytes) -> str:
    """Send one small PDF to the 'layout' model and get Markdown back."""
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        body=data,
        output_content_format="markdown",
    )
    return poller.result().content


def extract_pdf_azure(pdf_path: str, pages_per_request: int = 2, max_pages: int | None = None) -> str:
    """Split the PDF into small pieces (free-tier limit) and join the results."""
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    if max_pages:
        total = min(total, max_pages)
    parts = []

    for start in range(0, total, pages_per_request):
        writer = PdfWriter()
        for i in range(start, min(start + pages_per_request, total)):
            writer.add_page(reader.pages[i])
        buffer = io.BytesIO()
        writer.write(buffer)

        end = min(start + pages_per_request, total)
        parts.append(f"<!-- pages {start + 1}-{end} -->\n" + _analyze_bytes(buffer.getvalue()))

    return "\n\n".join(parts)