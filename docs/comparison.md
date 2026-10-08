# Comparison: Open-source Libraries vs Docling / MarkItDown vs Azure AI Document Intelligence

*Prepared 8 October 2026. All timings and counts come from the scripts in this repository, run on a Windows laptop (CPU only, no GPU).*

## Summary of findings

- **No single tool handled every kind of content.** Each approach failed somewhere that another one succeeded, which is why the recommendation at the end is a combination.
- **Open-source libraries (pypdf, pdfplumber, OCR)** were the fastest and gave us the only saved image files. But on research papers, the **tables were not aligned properly even after we added several table-detection strategies**, and **two-column text was not extracted in the right order**. This carried into the Markdown we built from them. On one of the three PDFs, the output did not render properly at all.
- **MarkItDown** behaved much like the open-source libraries, as a better version of them: easy to use and fast, with better output than raw pypdf, but with the same weaknesses on complex layouts.
- **Docling** was by far the **slowest** tool (218.7 s against 6.5 s for MarkItDown on the same 5-page paper).
- **Azure AI Document Intelligence** produced the most content per document and read the text inside images accurately, but it gave **no image extraction at all**. The text it read from images was **meaningless when viewed as a whole**, because it came out as detached fragments with no link to what the figure shows. Some **textured images had symbols that did not match the original exactly**.
- The cost of all three approaches was very low for this prototype: about 43 Azure pages out of the 500 free pages per month.

---

## 1. Test set

| ID | File | What it is | Pages | Why it is a hard test |
|---|---|---|---|---|
| paperA | `paperA.pdf` | *TSGuard: A Real-Time Framework for Detecting and Imputing Missing Data in Streaming Time Series* (CIKM '26 demo paper, arXiv:2610.03147) | 5 | Two-column layout, author and metadata blocks, an inline equation, a results table, an architecture diagram and a screenshot figure with captions, reference list |
| paperB | `paperB.pdf` | *Improving Fluency of Neural Machine Translation Using Large Language Models* (Machine Translation Summit XX proceedings, 2025) | 11 | Two-column layout, eight numbered equations, seven tables (including bold and italic result cells and sub-tables), seven figures (bar charts and training curves), a prompt block, footnotes, long reference list |
| paperC | `paperC.pdf` | *Multimodal Document Parsing & OCR Stress Test*, a synthetic technical report designed for this kind of testing | 5 | Key-value configuration table, formulas, a 42-row table that continues over a page break with a repeated header, a raster image containing independent text and a barcode, and a line chart |
| web1 | https://en.wikipedia.org/wiki/Artificial_intelligence | Long article | n/a | Many tables and images, very long text |
| web2 | https://docs.python.org/3/tutorial/introduction.html | Documentation page | n/a | Code samples, no HTML tables, a couple of images |
| web3 | https://en.wikipedia.org/wiki/Periodic_table | Long article | n/a | Very table-heavy and image-heavy |

The PDFs are not included in the repository for copyright reasons. paperC is a synthetic document, not a published paper. Only pages that are permitted by each site's terms and `robots.txt` were scraped.

## 2. The three approaches

| # | Approach | Tools used | What it is |
|---|---|---|---|
| 1 | **Open-source libraries** | pypdf, pdfplumber, pytesseract (OCR), requests + BeautifulSoup | Low-level building blocks. They return raw pieces (text, table cells, image files), and our own code assembles them into one reading-order output. |
| 2 | **Document converters** | Docling, MarkItDown | Higher-level tools that take a whole document and return Markdown. Docling uses AI layout and OCR models. MarkItDown is a lightweight converter. |
| 3 | **Enterprise cloud service** | Azure AI Document Intelligence (`prebuilt-layout`, Markdown output) | A managed AI service. Documents are uploaded and structured Markdown is returned. Billed per page. |

For web pages, Azure cannot read a live URL, so each page was first printed to PDF and then sent to Azure with a page cap. The other tools read the HTML directly.

---

## 3. Accuracy

### 3.1 What we observed, tool by tool

**Open-source libraries (pypdf, pdfplumber, OCR, BeautifulSoup)**
- **Tables on research papers were not aligned properly at all**, even though we changed the code to try three detection strategies in turn (ruled lines, a hybrid, and text-position based). Papers format their tables with few or no cell borders, so cells landed in the wrong columns or tables were missed.
- **Two-column text was not extracted properly.** Lines from the two columns were mixed, which breaks reading order. The same problems appeared in the Markdown built from these outputs.
- **On one of the three PDFs, the open-source output did not render properly at all.**
- Images were extracted well as files (7 from paperA, 13 from paperB, 2 from paperC), and OCR read the text inside them, but OCR returns plain lines with no structure.
- For web pages, BeautifulSoup was accurate on clean HTML: it found 18 and 25 tables on the two Wikipedia articles and correctly found 0 on the Python documentation page, which has none.

**MarkItDown**
- Behaved much like the open-source libraries, but as a better version of them: more complete, cleaner, and trivial to run.
- Still weak on complex layouts, because it mainly works from the text layer of the PDF. It does not extract PDF images by itself (we added them back with our pdfplumber step).

**Docling**
- The main problem we hit was **processing time**: 218.7 s for paperA, far beyond every other tool (see section 4).

**Azure AI Document Intelligence**
- Produced the largest Markdown output on every document (section 3.2).
- **No image extraction at all**: no image files were produced in our pipeline.
- **Text inside images was read correctly, but it was meaningless as a whole.** It appears as detached fragments (for example chart axis numbers or label fields as separate lines), with nothing connecting them to the figure's meaning or caption. A reader or an AI model cannot tell what the picture shows from this text alone.
- **Some images with textured backgrounds had symbols that did not match the original exactly.**
- On the free tier, each request could read only two pages, so every PDF was split into two-page pieces. By construction this cuts a table that crosses a boundary. paperC's 42-row table crosses the page 2 to 3 boundary, so it is returned in two separate tables (rows 1 to 38 and rows 39 to 42).

### 3.2 Size of the extracted output

Character counts include Markdown syntax (table bars, headings), so they show how much was captured, not a quality score.

| Document | pypdf plain text | Azure Markdown | Difference |
|---|---|---|---|
| paperA (5 pages) | 21,894 | 24,388 | +11% |
| paperB (11 pages) | 36,319 | 42,488 | +17% |
| paperC (5 pages) | 5,148 | 11,892 | +131% |

The big gap on paperC is expected: it is mostly tables, key-value blocks, and image text, which plain text extraction cannot represent.

### 3.3 Extraction counts from the open-source pipeline

| Document | Tables found by pdfplumber | Images saved | Pages needing OCR fallback |
|---|---|---|---|
| paperA | 5 | 7 | none |
| paperB | 12 | 13 | none |
| paperC | 5 | 2 | none |

Counts are what the tool reported, not what is correct. The tables we saw in the PDFs were not reproduced correctly (section 3.1).

### 3.4 Web pages

| Page | Text blocks | Tables | Images found | Images downloaded |
|---|---|---|---|---|
| web1 (Artificial intelligence) | 2,848 | 18 | 41 | 15 |
| web2 (Python tutorial) | 111 | 0 | 2 | 2 |
| web3 (Periodic table) | 1,117 | 25 | 62 | 15 |

Image downloads are capped at 15 per page to keep the prototype small. All image URLs were recorded.

### 3.5 Element-by-element summary

Each cell is marked **(O)** if we observed it in this project, or **(D)** if it describes how the tool is designed to behave and was not separately verified here.

| Element | Open-source libraries | MarkItDown | Docling | Azure |
|---|---|---|---|---|
| Two-column text | (O) Columns mixed, wrong reading order | (O) Similar to open-source, slightly better | (D) Layout models target reading order | (D) Layout model targets reading order |
| Tables in papers | (O) Not aligned, even after multiple strategies | (O) Similar to open-source, slightly better | (D) Table-structure model | (D) Layout model returns table structure |
| Table across a page break | (O) Split by page | (O) Same limitation | (D) Depends on page handling | (O) Returned as two tables because of the 2-page free-tier requests |
| Images as files | (O) Yes, saved from the PDF | (O) None by itself, added with pdfplumber | (D) Can export picture images | (O) None in our pipeline |
| Text inside images | (O) OCR text lines, no structure | (O) Not read | (D) Built-in OCR | (O) Read accurately, but fragmented and meaningless as a whole |
| Symbols and textured images | (O) OCR on images, unstructured | (O) Not read | (D) Built-in OCR | (O) Some symbols did not match exactly |
| Equations | (D) Characters usually garbled | (D) Plain-text approximation | (D) Can output LaTeX when formula option is on | (D) Depends on enabled features |
| Clean HTML tables | (O) Accurate, read directly from tags | (D) Converts tags to Markdown tables | (D) Reads HTML structure | (O) Works only after the page is printed to PDF |

---

## 4. Performance

### 4.1 PDFs (seconds)

| Document | Pages | pypdf text | pdfplumber tables + images | OCR on saved images | Open-source combined reading-order file | Azure | Docling | MarkItDown |
|---|---|---|---|---|---|---|---|---|
| paperA | 5 | 0.5 | 5.3 | 5.1 | 6.6 | 22.7 | 218.7 | 6.5 |
| paperB | 11 | 0.8 | 6.2 | 5.8 | 12.3 | 61.9 | 1534.0 | 8.8 |
| paperC | 5 | 0.4 | 1.1 | 1.5 | 2.4 | 16.1 | 117.1 | 1.6 |

Docling and MarkItDown were timed on paperA only in the recorded run; the other two documents were converted without their times being recorded.

- **Open-source** was the fastest: plain text took under a second for every PDF. Table and image extraction took 1 to 6 seconds, and OCR added a similar amount.
- **MarkItDown** took 6.5 s on paperA. Most of that is our own pdfplumber step that crops and saves the images (about 5.3 s, from the table above), so MarkItDown's own conversion took only about a second.
- **Docling** took 218.7 s on paperA, which is **about 34 times slower than MarkItDown**. paperA was the first document of the run, so this figure includes loading Docling's AI models. The start-up log showed the OCR models and two large transformer models being loaded. Even so, Docling was clearly the slowest tool in every run.
- **Azure** took 3 to 6 seconds per page: 22.7 s for 5 pages (4.5 s per page), 61.9 s for 11 pages (5.6 s per page) and 16.1 s for 5 pages (3.2 s per page). This time includes upload, waiting for the result, and our splitting into two-page requests, but does not depend on the speed of the local machine.

### 4.2 Web pages

| Page | Open-source scrape (s) | Azure pages sent | Azure Markdown (characters) | Azure time (s) |
|---|---|---|---|---|
| web1 | 9.5 | 7 (earlier test with 5 pages: 14,592 characters, 16.5 s) | 20,946 | 26.9 |
| web2 | 1.6 | 4 | 8,293 | 11.5 |
| web3 | 10.2 | 6 | 66,699 | 28.8 |

web3 (the periodic table) produced the most Azure output (66,699 characters from only 6 pages) because it is dominated by large tables.

### 4.3 Pros and cons for performance

- **Open-source libraries:** fastest and the lightest on memory. OCR is the slowest part of that pipeline because every image is processed separately.
- **MarkItDown:** very fast and suitable for interactive use.
- **Docling:** too slow for interactive use on a CPU. A GPU or a long-running server that keeps the models loaded would help, but it needs more resources.
- **Azure:** moderate per-page speed that does not depend on your hardware, and many documents can be sent in parallel. The two-page splitting we needed on the free tier added extra waiting.

---

## 5. Ease of use

| Aspect | Open-source libraries | MarkItDown | Docling | Azure |
|---|---|---|---|---|
| Setup | `pip install`, plus installing the Tesseract OCR program and configuring its path | `pip install` | `pip install` with a very large download, plus model files on the first run | Azure account, resource, endpoint and key, SDK |
| Code we had to write | The most: text, tables with fallback strategies, image cropping, OCR, web scraping, link and file handling | A few lines, plus our own image step for PDFs | A few lines | A short function plus the two-page splitting logic |
| Debugging | Easy to see what happened, but each problem needs custom code | Easy | Harder: long start-up logs and model warnings | Depends on service responses |
| Problems we hit | Table detection kept failing on research-paper tables; Wikipedia returned **403 Forbidden** until we sent a proper User-Agent | The same 403 on Wikipedia; no PDF images | Very slow; web pages had to be downloaded as HTML first | Free tier reads two pages per request, so documents had to be split; web pages had to be printed to PDF first |

Other practical points from this project:
- Saving `pip freeze` output from Windows PowerShell created a UTF-16 file, which needed to be re-saved as UTF-8 before it could be used for deployment.
- Backend deployment needed a separate, smaller requirements file because the full environment is too large for a free host.

**Pros and cons**
- **Open-source libraries:** maximum control and zero cost, but the most work and the most maintenance.
- **MarkItDown:** the easiest of all and a better version of the open-source approach, but limited on complex layouts.
- **Docling:** little code, but heavy to install and slow to run.
- **Azure:** little code and managed infrastructure, but needs cloud setup, credentials, cost monitoring, and extra work to fit the free-tier page limits.

---

## 6. Cost

| Approach | Direct cost | Hidden costs |
|---|---|---|
| Open-source libraries | $0 | Developer time to write and maintain the extraction code (the biggest cost here); compute to run it |
| MarkItDown | $0 | Minimal compute |
| Docling | $0 | Compute: memory (several GB) and long processing time per page |
| Azure Document Intelligence | Pay per page after a free allowance of 500 pages per month | Cost grows with volume; documents are sent to a cloud service |

**What this project used:** about **43 Azure pages**: 21 from the three PDFs (5 + 11 + 5) and 22 from the web-page PDFs (7 + 5 + 4 + 6, including the earlier 5-page test of web1). That is under 9% of the free monthly allowance. S3 storage for the outputs was only a few megabytes.

**Volume estimates**

Azure prices change, so confirm the current per-page rate on Azure's pricing page. A rough, unverified figure of about **$10 per 1,000 pages** is used here as an indicative price for the Layout model. Volume discounts and commitment pricing may lower it.

| Volume | Open-source | MarkItDown | Docling | Azure (at about $10 per 1,000 pages) |
|---|---|---|---|---|
| About 100 pages | $0 | $0 | $0 | $0 (inside the free allowance) |
| About 100,000 pages | Server cost only | Server cost only | Server cost only, but the most compute | about $1,000 |

**Self-hosted cost estimate from our measurements.** Using `cost per 1,000 pages = (seconds per page × 1,000 ÷ 3,600) × server price per hour` and an assumed server price of $0.10 per hour:

| Tool | Measured | Seconds per page | Hours per 1,000 pages | Estimated cost per 1,000 pages |
|---|---|---|---|---|
| MarkItDown | 6.5 s for 5 pages | 1.3 | 0.36 | about $0.04 |
| Docling | 218.7 s for 5 pages | 43.7 | 12.2 | about $1.20 |

Docling is cheaper per page than Azure at scale, but it needs many hours of server time for every 1,000 pages on a CPU. A faster machine or GPU would reduce that.

**Pros and cons for cost**
- Open-source and MarkItDown are the cheapest per page.
- Azure is the simplest to budget at small volume (free, then pay as you go) with no servers to run, but at high volume it becomes the largest expense.
- Docling's cost is in compute time, which is large on a CPU.

---

## 7. Scalability and integration

| Aspect | Open-source libraries | MarkItDown | Docling | Azure |
|---|---|---|---|---|
| Scaling out | Easy: many workers, small memory | Easy | Possible but each worker needs several GB of memory and long processing time | Easiest: managed, limited by request-rate quotas and budget |
| Memory | Small | Small | Large | None on your side |
| Fit with FastAPI | Straightforward | Straightforward | Works, but slow requests need a background job queue | Straightforward (call, wait, collect result) |
| Data privacy | Stays with you | Stays with you | Stays with you | Documents are sent to a cloud service |
| Operations | You maintain everything | You maintain a light dependency | You maintain models and heavy dependencies | Microsoft runs the service; you manage keys and quotas |

**What deployment taught us**
- The free Render instance has roughly 512 MB of memory, so **Docling could not run there**. The live backend therefore offers **MarkItDown only**, controlled by a setting that switches Docling off.
- Hugging Face's Docker Spaces, which could have hosted the full version with Docling, were not available on the free plan.
- The full version runs locally and can be deployed from the included `Dockerfile` on a host with several GB of memory.
- The API protects itself with an API key, file-size limits, and checks that a submitted web address is public, because every conversion costs compute and S3 storage.
- All outputs, whichever tool made them, go into the same private, encrypted S3 layout with metadata and tags. This makes the extraction tools interchangeable behind one storage layer.

---

## 8. Docling vs MarkItDown

| | Docling | MarkItDown |
|---|---|---|
| Speed | Very slow: 218.7 s for paperA (including model loading) | Fast: 6.5 s for paperA, about 1 s of it MarkItDown itself |
| Behaviour on our documents | Not measured on the other documents in the recorded run | Behaved much like the open-source libraries, but as a better, cleaner version |
| Images | Can export picture images | None from PDFs by itself; we add them back with pdfplumber |
| Install and hosting | Heavy: PyTorch, large model downloads, several GB of memory | Light, easy to host, which is why it powers the live API |
| Integration | Needs a long-running server or job queue | Easy to call inside a web request |
| Best used for | Complex PDFs when processing time does not matter | Quick conversions of web pages and simple documents |

---

## 9. Which approach for which content

| Content type | Best approach | Why |
|---|---|---|
| Web pages with clean HTML tables | BeautifulSoup, or MarkItDown for quick Markdown | Reads the real HTML structure; 18, 0 and 25 tables were found correctly across our three pages |
| Simple text PDFs | MarkItDown or pypdf | Fast and free |
| Research papers with two columns and borderless tables | A layout-aware tool (Azure, or Docling when time allows) | Open-source libraries mixed the columns and misaligned the tables |
| Extracting image files from PDFs | pdfplumber | The only approach in our tests that saved the images (Azure saved none) |
| Text inside images | Azure or OCR, kept together with the saved image and its caption | Azure read the text accurately, but in isolation it was meaningless, so it must be linked to the image |
| Long tables across page breaks | Azure on a paid tier or Docling (send the whole document) | The free-tier two-page requests cut such tables |
| Scanned pages | Azure, or OCR for budget cases | Text exists only as pixels |

---

## 10. Overall recommendation

No single tool did everything well in our tests, so the recommended pipeline combines them:

1. **Web pages:** use BeautifulSoup when precise control of the HTML is needed, and MarkItDown for fast Markdown. Both were fast (1.6 to 10.2 s per page) and reliable on HTML tables.
2. **Complex PDFs such as research papers:** use a layout-aware tool, because the open-source libraries failed on two-column text and tables. Choose **Azure** for interactive and low-volume work (about 3 to 6 seconds per page, no servers to run, 500 free pages per month) and **Docling** when data must stay in-house or volume is high enough that compute time is cheaper than per-page fees (about 44 seconds per page on our CPU, so it should run in the background on a stronger server).
3. **Always add pdfplumber for images.** Azure returned no image files, and MarkItDown returns none from PDFs. Store the saved image next to any text read from it, with the caption, so the text keeps its meaning.
4. **Keep MarkItDown as the lightweight default** for the hosted API and for simple documents. It is easy to deploy and in our experience was a better version of the open-source approach.
5. **Keep OCR for image-only content,** but treat its output as supporting text, not as a faithful copy of the figure. Symbols in textured images may not match exactly, so check important values.

If the startup had to choose one tool today, the best single choice for research-paper PDFs is **Azure Document Intelligence**, because it is fast, needs no infrastructure, and captured the most content (up to 2.3 times the text of pypdf on paperC). It must be paired with pdfplumber image extraction to fill its biggest gap, and run on a paid tier so that long tables are not cut.

---

## 11. Limitations of this comparison

- The test set is small: three PDFs (one of them a synthetic test document) and three web pages. The findings are indicative, not statistical.
- Quality was judged by inspecting the output next to the original documents, not by an automated accuracy score.
- Docling and MarkItDown were timed only on paperA in the recorded run. Docling's time includes loading its models, and MarkItDown's time includes our image-cropping step.
- Azure ran on the free tier, which reads two pages per request, so tables that cross a request boundary were split. A paid tier would likely do better on those tables.
- Azure web-page runs used PDF prints of the pages with a page cap (7, 4 and 6 pages), so they cover only the first part of each page.
- Timings come from one laptop and one network connection, with no GPU.
- Equations were not scored individually, and the Azure price used for projections is an indicative figure to be confirmed on Azure's pricing page.
- Scanned documents and JavaScript-rendered web pages were not part of the test set.

## 12. Reproducing these results

All scripts are in the repository root and are described in the README:

```
python run_task1.py data/pdfs/paperA.pdf        # open-source PDF extraction, OCR, combined output
python run_task1_azure.py data/pdfs/paperA.pdf  # Azure Document Intelligence
python run_task2.py                             # web scraping with requests + BeautifulSoup
python download_pages.py                        # save pages as HTML for Docling and MarkItDown
python run_task4.py                             # Docling and MarkItDown on every input
python run_task5.py                             # upload outputs to the S3 bucket
```
