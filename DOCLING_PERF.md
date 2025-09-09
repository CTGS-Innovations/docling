Yep—looked through Docling’s repo and docs for the fastest “Markdown-only, no images/tables” path. Here’s the short version that will actually speed things up at scale.

# Fastest settings (what to turn off / pick)

* **Backend:** use `--pdf-backend pypdfium2` for born-digital PDFs. It’s the lightest backend focused on text; layout backends (dlparse) are heavier. ([Docling][1])
* **OCR:** disable it for born-digital; only enable when you detect scanned PDFs. Flags: `--no-ocr`, or programmatically `do_ocr=False`. ([Docling][1])
* **Tables & pictures:** skip them entirely. Programmatically set: `do_table_structure=False`, `do_picture_classification=False`, `do_picture_description=False`. (CLI doesn’t expose a hard “off” for table structure—so use the Python API for maximal speed.) ([Docling][2])
* **Generated artifacts:** avoid generating any page/picture/table images or parsed-page dumps: `generate_page_images=False`, `generate_picture_images=False`, `generate_table_images=False`, `generate_parsed_pages=False`. ([Docling][2])
* **Batching/threads:** for big jobs, increase `--num-threads` and tune `--page-batch-size` (defaults are 4). Use the threaded pipeline options if you’re in Python to control queue sizes and per-stage batch sizes. ([Docling][1])

# CLI (quickest to try)

If you’re OK with CLI and your docs are mostly born-digital PDFs/DOCX:

```bash
docling \
  --from pdf --to md \
  --pdf-backend pypdfium2 \
  --no-ocr \
  --num-threads 8 \
  --page-batch-size 8 \
  --output /path/to/out \
  /path/to/in
```

* `--pdf-backend`, `--no-ocr`, `--num-threads`, and `--page-batch-size` are all supported CLI options. If you need to kill table processing entirely, switch to the Python API (below). ([Docling][1])

# Python API (max control, *really* turns off heavy steps)

This is the “pure text, no images/tables/ocr” setup:

```python
from docling.document_converter import DocumentConverter
from docling.pipeline_options import PdfPipelineOptions, PdfBackend, ThreadedPdfPipelineOptions

opts = ThreadedPdfPipelineOptions(  # gives you batching/backpressure knobs
    # Core speed choices
    do_ocr=False,
    do_table_structure=False,
    do_picture_classification=False,
    do_picture_description=False,
    force_backend_text=True,

    # No image/aux outputs
    generate_page_images=False,
    generate_picture_images=False,
    generate_table_images=False,
    generate_parsed_pages=False,

    # Fastest PDF text backend
    layout_options=None,
    table_structure_options=None,
)

opts.kind = "pdf"  # default
opts.accelerator_options.device = "auto"  # leave auto
opts.layout_batch_size = 8
opts.table_batch_size = 0  # no tables anyway
opts.ocr_batch_size = 0    # no OCR
opts.queue_max_size = 16
opts.images_scale = 1.0

# Pick the backend explicitly
base_opts = PdfPipelineOptions()
base_opts.kind = "pdf"
base_opts.force_backend_text = True
base_opts.generate_page_images = False
base_opts.generate_picture_images = False
base_opts.generate_table_images = False
base_opts.do_table_structure = False
base_opts.do_ocr = False
base_opts.pdf_backend = PdfBackend.PYPDFIUM2

converter = DocumentConverter(pipeline_options=opts)
doc = converter.convert("/path/to/file.pdf").document
md = doc.export_to_markdown()
```

All flags shown above come directly from Docling’s pipeline options reference, including the `ThreadedPdfPipelineOptions` fields and the booleans to disable enrichment and image generation. ([Docling][2])

# Throughput tips for “thousands of docs”

* **Process pool > thread pool** at the *job* level. Run multiple Docling CLI (or Python workers) in parallel, each pinned to a subset of CPU cores; keep `--num-threads` moderate inside each process so you don’t oversubscribe. The CLI exposes `--num-threads`; the threaded pipeline controls batching/backpressure. ([Docling][1])
* **Separate scanned from digital** up front (e.g., check PDF text layer presence). Route scanned to a slower profile with OCR on (RapidOCR or Tesseract), and keep digital on the fast path with OCR off. OCR engine choices and options are documented if/when you need them. ([Docling][2])
* **Stay current:** latest release as of Sep 5, 2025 is `v2.51.0`—performance knobs occasionally improve across versions. ([GitHub][3])

If you want, I can drop a tiny batching script that walks a directory tree, auto-routes scanned vs digital PDFs, and writes just MD with the fast profile.

[1]: https://docling-project.github.io/docling/reference/cli/ "CLI reference - Docling"
[2]: https://docling-project.github.io/docling/reference/pipeline_options/ "Pipeline options - Docling"
[3]: https://github.com/docling-project/docling/releases?utm_source=chatgpt.com "Releases · docling-project/docling - GitHub"
