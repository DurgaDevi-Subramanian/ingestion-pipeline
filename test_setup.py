import os
import requests
from dotenv import load_dotenv
from markitdown import MarkItDown

load_dotenv()  # reads your .env file
email = os.environ.get("CONTACT_EMAIL", "unknown")

session = requests.Session()
session.headers.update({
    "User-Agent": f"ingestion-pipeline-learning-project/0.1 ({email})"
})

md = MarkItDown(requests_session=session)
result = md.convert("https://en.wikipedia.org/wiki/Markdown")
print("All good!")
print(result.text_content[:300])