# My Scope and Approach: Unstructured Data Ingestion Pipeline

**Prepared by:** Durga Devi **Assessment:** Build an Unstructured Data Ingestion Pipeline **Status:** Completed (October 8, 2026) **Effort:** About 9 working days, worked part-time **Purpose of this document:** to explain how I understood the problem, how I approached it, and the reasoning behind the choices I made.

---

## 1. How I understood the problem

Most useful data for AI products is stuck inside messy formats: PDFs with tables, equations and charts, and web pages full of layout noise. That data can't be used until it has been cleaned up and put in a consistent shape.

I read the assessment as one question: **can I take a messy PDF or web page, pull the content out, convert it to clean Markdown, store it properly in the cloud, and let anyone use it through a simple app?** A second goal was an honest comparison of tools, so a team could decide which stack to commit to.

I broke the problem into four layers:

1. **Extraction:** get text, tables and images out of the source.
2. **Standardization:** put those pieces back together, in reading order, as one Markdown file.
3. **Storage:** save everything in S3 in an organized, secure way.
4. **Access:** a FastAPI backend and a Streamlit app so anyone can use the pipeline.

---

## 2. My approach: build from the bottom up

I built one layer at a time and made sure each worked before starting the next. Since I'm still learning these tools, this kept problems small and easy to trace. When something broke in the app, I already knew the extraction underneath it worked.

| Step | What I did | Why in this order |
| --- | --- | --- |
| 0. Setup | Created the project folder with a Python virtual environment (`.venv`), installed the libraries, and set up the cloud accounts | A clean, isolated environment avoids version conflicts later |
| 1. PDF extraction | Built open-source extraction, then ran the same PDFs through Azure AI Document Intelligence | PDFs are the hardest input, so I wanted to learn their problems first |
| 2. Web page extraction | Used `requests` + `BeautifulSoup`, then an enterprise service on the same pages | Similar idea to PDFs but simpler, so it came second |
| 3. Docling and MarkItDown | Ran every document through both tools to produce Markdown | These needed the earlier extraction results to compare against |
| 4. S3 storage | Designed the bucket and folder layout, metadata and security | Easier to design once I knew which files the pipeline produces |
| 5. FastAPI and Streamlit | Wrapped the pipeline in an API and a simple app, tested locally, then deployed | The app only makes sense once the pipeline underneath works |
| 6. Comparison, README | Compared the three approaches, documented the architecture and setup | A fair comparison needs everything to have run on the same test set |

---

## 3. Tool choices and my reasoning

**Open-source PDF extraction (`pypdf` + `pdfplumber`).** `pypdf` is good at pulling plain text. `pdfplumber` can detect tables and layout, so I used each for what it does best. It's free, and I could see exactly what my own code was doing.

**Enterprise service (Azure AI Document Intelligence).** It uses trained models to understand layout, tables and structure, so I expected it to handle complex pages better than hand-written code, at a cost per page. It let me compare "free and manual" against "paid and managed."

**Web scraping (`requests` + `BeautifulSoup`).** Simple, widely used, and enough for pages with text, tables and images. I only scraped pages I was permitted to and respected `robots.txt`.

**Docling and MarkItDown.** Both convert documents to Markdown directly. I ran both so I could see how each handles reading order, tables, formulas and images, and where each one drops or scrambles content.

**Amazon S3.** Required by the assessment, and well suited to the job: cheap, secure, and easy to organize with prefixes.

**FastAPI and Streamlit.** FastAPI gave me a clean backend I could test on its own. Streamlit let me build a working front end in Python without learning web development.

**Render for backend hosting.** I first looked at Hugging Face Spaces, but running a Docker-based backend there needs a paid plan, and only static sites are free. I moved the FastAPI backend to Render instead, which let me deploy publicly while staying within the budget.

---

## 4. Test set

I deliberately chose **hard** documents, because easy text-only files wouldn't show any difference between the tools.

- **PDFs (3, each 5+ pages):** two research papers from arXiv and one synthetic (purpose-built) test document. Together they cover multi-column layouts, tables, equations, key-value blocks such as hyperparameter lists, and figures with captions.
- **Web pages (3):** pages containing tables and images that may be scraped under each site's terms of use and `robots.txt`.

I used the **same test set for all three approaches**, so the comparison was fair.

---

## 5. Challenges I ran into and how I solved them

**Tables were not extracting properly (PDF).** My first open-source version missed or garbled tables. Tables don't have a single standard structure in PDFs, so I reworked the extraction to try more than one `pdfplumber` strategy: lines first, then a hybrid, then a text-based strategy as a fallback.

**Scanned or image-only pages.** Some pages contain pictures of text rather than real text. I added OCR with `pytesseract` as a fallback so those pages weren't lost.

**Images.** I exported embedded images as separate files so the Markdown could link to them, and those links point to the copies stored in S3.

**Azure output not as expected.** I checked it side by side against the original PDFs to work out whether the issue was in my conversion step or in the service's output, rather than assuming either one.

**Backend hosting.** As described above, the free Hugging Face option wasn't available for a Docker backend, so I switched to Render.

**What I learned:** no single tool is perfect, and the right choice depends on the type of content. That is what the three-way comparison in the repo captures.

---

## 6. Risks I planned for

| Risk | How I handled it |
| --- | --- |
| Cloud costs growing past the budget (about $5) | Set a billing alert before starting, used free tiers, kept the test set small, and cleaned up resources at the end |
| Credentials accidentally exposed | Kept keys in environment variables or a `.env` file listed in `.gitignore`; nothing sensitive was committed |
| S3 data exposed | Kept the bucket private with encryption on and limited access |
| Free-tier hosting being slow or sleeping | Tested the deployment early and warmed up the backend |
| Poor extraction quality on complex pages | Compared against the original PDF side by side and documented where each tool fails |

---

## 7. Effort

I worked on this part-time and it took about **9 working days** in total. The assessment suggests about one week of full-time effort, so this is in line with that once part-time hours are taken into account. My approximate breakdown:

| Work | Approx. effort |
| --- | --- |
| Setup and test-set selection | 0.5 day |
| PDF extraction (open-source and Azure), including table and OCR fixes | 2 days |
| Web page extraction | 1 day |
| Docling and MarkItDown | 1.5 days |
| S3 design and implementation | 1 day |
| FastAPI backend, Streamlit app and deployment | 2 days |
| Comparison write-up, README, architecture diagram | 1 day |

---

## 8. What I delivered

- A pipeline that extracts text, tables and images from PDFs and web pages using open-source libraries and an enterprise service
- Clean Markdown for every test document from both Docling and MarkItDown
- An organized, private, encrypted S3 bucket with a documented naming scheme and metadata, with images linked from the Markdown
- A FastAPI backend, deployed on Render
- A Streamlit app where a user can upload a PDF or paste a URL, choose a tool, and view or download the Markdown
- A three-way comparison of open-source libraries, Docling/MarkItDown, and the enterprise service, with a recommendation
- A public GitHub repository with a README (architecture diagram and setup steps)

---

## 9. How I checked that it was done

- Every test document has open-source output, enterprise output, and Markdown from both Docling and MarkItDown.
- The Markdown matches the original document's structure and reading order, with images linked from S3.
- The S3 layout is easy to explain, so anyone can find a document's Markdown and images.
- The live app works for someone who has never seen it: upload a PDF or paste a URL, and get Markdown back.
- The comparison gives a clear recommendation of which approach suits which content, backed by examples from my test set.
- The repository and README are complete, with no secrets committed.