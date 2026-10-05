from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import ImageRefMode


def make_converter() -> DocumentConverter:
    options = PdfPipelineOptions()
    options.do_table_structure = True        # rebuild tables
    options.do_formula_enrichment = True     # try to output LaTeX for equations
    options.generate_picture_images = True   # keep figure images so we can save them
    options.images_scale = 2.0
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def convert_with_docling(source: str, out_dir: str, name: str) -> str:
    """Convert a PDF or HTML file to Markdown; images go to out_dir/images."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = make_converter().convert(source)
    md_path = out / f"{name}.md"
    result.document.save_as_markdown(
        md_path,
        artifacts_dir=Path("images"),        # relative, so links work anywhere
        image_mode=ImageRefMode.REFERENCED,  # link to image files instead of embedding
    )
    return str(md_path)