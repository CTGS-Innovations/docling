# Docling CLI Reference Guide

A comprehensive guide to using the Docling command-line interface for document processing and conversion.

## Directory Structure

This CLI toolkit is organized for optimal performance benchmarking and analysis:

```
/home/corey/projects/docling/cli/
├── README.md                          # This comprehensive CLI guide
├── run_benchmark.sh                   # Main benchmark runner script
├── performance_benchmark.py           # Core benchmarking suite (GPU-optimized)
├── benchmark_with_vllm_server.py      # vLLM server benchmarking
├── vllm_server_manager.py            # vLLM server management utilities
├── recover_results.py                # Results recovery and analysis
├── data/                             # Test documents (359 files across 15+ formats)
├── output/                           # Timestamped benchmark results
│   └── latest/                       # Latest performance reports
├── info/                             # Documentation and guides
│   ├── doclineHelp.md               # Complete CLI options reference
│   ├── EXECUTION_GUIDE.md           # Step-by-step execution instructions
│   ├── IMPROVEMENT_ROADMAP.md       # Future optimization roadmap
│   ├── STATUS_REPORT.md            # Current status and findings
│   └── lscpu.md                     # System hardware information
├── analysis_scripts/                 # Analysis and configuration testing
│   ├── debug_basic_docling.py       # Basic functionality debugging
│   ├── find_docling_model.py        # Model discovery utilities
│   ├── test_enrichment_flags.py     # Enrichment configuration testing
│   ├── test_visual_format_optimization.py  # Visual format optimization
│   ├── test_vlm_models.py           # VLM model comparison
│   ├── quality_assessment.py        # Output quality analysis
│   └── run_comprehensive_analysis.py # Comprehensive analysis suite
└── tests/                           # Testing utilities and problem analysis
```

### Usage Guide by Purpose

#### 🚀 **Quick Benchmarking** (Most Users)
```bash
# Run complete performance benchmark
./run_benchmark.sh

# View latest results
cat output/latest/PERFORMANCE_REPORT.md
```

#### 🔧 **Configuration Analysis** (Advanced Users)
```bash
# Test different enrichment options
python analysis_scripts/test_enrichment_flags.py

# Optimize visual format processing 
python analysis_scripts/test_visual_format_optimization.py

# Compare VLM models
python analysis_scripts/test_vlm_models.py
```

#### 📊 **Custom Analysis** (Researchers/Developers)
```bash
# Debug basic functionality
python analysis_scripts/debug_basic_docling.py

# Quality assessment
python analysis_scripts/quality_assessment.py

# Comprehensive analysis
python analysis_scripts/run_comprehensive_analysis.py
```

#### 📚 **Documentation Reference**
- `info/doclineHelp.md` - Complete CLI options and flags
- `info/EXECUTION_GUIDE.md` - Step-by-step execution instructions
- `info/IMPROVEMENT_ROADMAP.md` - Future optimization plans

## Table of Contents

- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Structure](#command-structure)
- [Input Sources](#input-sources)
- [Processing Pipelines](#processing-pipelines)
- [Output Formats](#output-formats)
- [GPU Usage](#gpu-usage)
- [Advanced Options](#advanced-options)
- [Model Management](#model-management)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

# 1) make sure venv is available
sudo apt update
sudo apt install -y python3-venv

# 2) create & activate a venv in your project
cd ~/projects/docling/cli
python3 -m venv .venv
source .venv/bin/activate

# 3) upgrade pip in the venv and install
python -m pip install -U pip

### Basic Installation

```bash
pip install docling
```

### GPU Support

For CUDA GPU support:
```bash
pip install docling[gpu]
```

For CPU-only (lighter installation):
```bash
pip install docling --extra-index-url https://download.pytorch.org/whl/cpu
```

### Using Docker

```bash
docker run --rm -v $(pwd):/workspace docling/docling:latest docling /workspace/document.pdf
```

## Quick Start

### Basic Document Conversion

```bash
# Convert PDF to Markdown (default)
docling document.pdf

# Convert from URL
docling https://arxiv.org/pdf/2408.09869

# Convert with specific output format
docling document.pdf --to json

# Convert entire directory
docling ./documents/ --output ./converted/
```

## Command Structure

```bash
docling [OPTIONS] input_sources...
```

- `input_sources`: PDF files to convert. Can be local file/directory paths or URLs [required]
- `OPTIONS`: Various configuration flags and parameters

### Complete CLI Options Reference

#### Arguments
- `input_sources` - Source files, directories, or URLs to process [required]

#### Input/Output Format Options
- `--from [docx|pptx|html|image|pdf|asciidoc|md|csv|xlsx|xml_uspto|xml_jats|mets_gbs|json_docling|audio]` - Specify input formats to convert from. Defaults to all formats
- `--to [md|json|html|html_split_page|text|doctags]` - Specify output formats. Defaults to Markdown
- `--output PATH` - Output directory where results are saved [default: .]

#### Processing Pipeline Options
- `--pipeline [standard|vlm|asr]` - Choose the pipeline to process files [default: standard]
- `--vlm-model [smoldocling|smoldocling_vllm|granite_vision|granite_vision_vllm|granite_vision_ollama|got_ocr_2]` - Choose VLM model [default: smoldocling]
- `--asr-model [whisper_tiny|whisper_small|whisper_medium|whisper_base|whisper_large|whisper_turbo]` - Choose ASR model [default: whisper_tiny]

#### OCR Options
- `--ocr / --no-ocr` - Enable/disable OCR processing [default: ocr]
- `--force-ocr / --no-force-ocr` - Replace existing text with OCR generated text [default: no-force-ocr]
- `--ocr-engine TEXT` - OCR engine: easyocr, ocrmac, rapidocr, tesserocr, tesseract [default: easyocr]
- `--ocr-lang TEXT` - Comma-separated list of languages for OCR engine

#### PDF Processing Options
- `--pdf-backend [pypdfium2|dlparse_v1|dlparse_v2|dlparse_v4]` - PDF backend to use [default: dlparse_v2]
- `--table-mode [fast|accurate]` - Table structure model mode [default: accurate]

#### Content Enrichment Options
- `--enrich-code / --no-enrich-code` - Enable code enrichment model [default: no-enrich-code]
- `--enrich-formula / --no-enrich-formula` - Enable formula enrichment model [default: no-enrich-formula]
- `--enrich-picture-classes / --no-enrich-picture-classes` - Enable picture classification [default: no-enrich-picture-classes]
- `--enrich-picture-description / --no-enrich-picture-description` - Enable picture description [default: no-enrich-picture-description]

#### Performance and Device Options
- `--device [auto|cpu|cuda|mps]` - Accelerator device [default: auto]
- `--num-threads INTEGER` - Number of threads [default: 4]
- `--page-batch-size INTEGER` - Number of pages processed in one batch [default: 4]
- `--document-timeout FLOAT` - Timeout for processing each document, in seconds

#### Image and Layout Options
- `--image-export-mode [placeholder|embedded|referenced]` - Image export mode [default: embedded]
- `--show-layout / --no-show-layout` - Show bounding-boxes of items [default: no-show-layout]

#### Debug and Visualization Options
- `--debug-visualize-cells / --no-debug-visualize-cells` - Visualize PDF cells [default: no-debug-visualize-cells]
- `--debug-visualize-ocr / --no-debug-visualize-ocr` - Visualize OCR cells [default: no-debug-visualize-ocr]
- `--debug-visualize-layout / --no-debug-visualize-layout` - Visualize layout clusters [default: no-debug-visualize-layout]
- `--debug-visualize-tables / --no-debug-visualize-tables` - Visualize table cells [default: no-debug-visualize-tables]

#### Advanced Options
- `--headers TEXT` - HTTP request headers as JSON string for URL sources
- `--artifacts-path PATH` - Location of model artifacts for offline use
- `--enable-remote-services / --no-enable-remote-services` - Enable remote model services [default: no-enable-remote-services]
- `--allow-external-plugins / --no-allow-external-plugins` - Enable third-party plugins [default: no-allow-external-plugins]
- `--show-external-plugins / --no-show-external-plugins` - List available third-party plugins [default: no-show-external-plugins]
- `--abort-on-error / --no-abort-on-error` - Abort on first error [default: no-abort-on-error]

#### Utility Options
- `--verbose, -v INTEGER` - Verbosity level: -v for info, -vv for debug [default: 0]
- `--version` - Show version information
- `--logo` - Show Docling logo
- `--help` - Show help message and exit

## Input Sources

### File Types Supported

```bash
# PDF documents
docling document.pdf

# Microsoft Office files
docling presentation.pptx
docling spreadsheet.xlsx
docling document.docx

# Images (PNG, JPG, TIFF, etc.)
docling image.png
docling photo.jpg
docling scan.tiff

# Audio/Video files
docling recording.wav
docling video.mp4
docling audio.mp3

# Web and markup formats
docling page.html
docling document.md
docling content.asciidoc

# Data formats
docling data.csv
docling spreadsheet.xlsx

# Scientific/Technical formats
docling patent.xml  # USPTO XML
docling article.xml  # JATS XML
docling collection.xml  # METS GBS
docling document.json  # Docling JSON

# Multiple files and mixed formats
docling file1.pdf file2.docx file3.png data.csv
```

#### Format-Specific Examples

```bash
# Process only specific formats from directory
docling ./mixed_docs/ --from pdf --from docx
docling ./data_files/ --from csv --from xlsx
docling ./web_content/ --from html --from md

# Scientific document processing
docling research_papers/ --from pdf --from xml_jats
docling patent_docs/ --from xml_uspto

# Media processing
docling audio_collection/ --from audio --pipeline asr
```

### Directory Processing

```bash
# Process all supported files in directory
docling ./input_folder/

# Process specific formats from directory
docling ./input_folder/ --from pdf --from docx

# Recursive directory processing (automatic)
docling ./input_folder/ --output ./output_folder/
```

### URL Processing

```bash
# Direct PDF URLs
docling https://arxiv.org/pdf/2408.09869

# Web pages
docling https://en.wikipedia.org/wiki/Machine_Learning

# With custom headers
docling https://secure-site.com/doc.pdf --headers '{"Authorization": "Bearer token123"}'
```

## Processing Pipelines

### Standard Pipeline (Default)

```bash
# Basic PDF processing with OCR and table extraction
docling document.pdf

# Disable OCR
docling document.pdf --no-ocr

# Force OCR on all text
docling document.pdf --force-ocr

# OCR engine options (when external plugins not enabled)
docling document.pdf --ocr-engine easyocr      # Default
docling document.pdf --ocr-engine tesseract    # Tesseract OCR
docling document.pdf --ocr-engine tesserocr    # Tesseract Python wrapper
docling document.pdf --ocr-engine rapidocr     # Rapid OCR
docling document.pdf --ocr-engine ocrmac       # macOS native OCR

# OCR with specific languages
docling document.pdf --ocr-lang "en,fr,de"
docling document.pdf --ocr-engine tesseract --ocr-lang "eng,fra,deu"
```

### Vision Language Model (VLM) Pipeline

#### SmolDocling (Recommended)

```bash
# Default SmolDocling with auto-acceleration
docling document.pdf --pipeline vlm --vlm-model smoldocling

# Force MLX acceleration (Apple Silicon)
docling document.pdf --pipeline vlm --vlm-model smoldocling

# Force vLLM acceleration (GPU)
docling document.pdf --pipeline vlm --vlm-model smoldocling_vllm
```

#### Other VLM Models

```bash
# Granite Vision model (Transformers)
docling document.pdf --pipeline vlm --vlm-model granite_vision

# Granite Vision with vLLM acceleration
docling document.pdf --pipeline vlm --vlm-model granite_vision_vllm

# Granite Vision with Ollama
docling document.pdf --pipeline vlm --vlm-model granite_vision_ollama

# GOT OCR 2.0
docling document.pdf --pipeline vlm --vlm-model got_ocr_2
```

### Audio/Speech Recognition (ASR) Pipeline

```bash
# Basic ASR with Whisper Tiny
docling audio.wav --pipeline asr

# Different Whisper models
docling audio.wav --pipeline asr --asr-model whisper_tiny
docling audio.wav --pipeline asr --asr-model whisper_small
docling audio.wav --pipeline asr --asr-model whisper_medium
docling audio.wav --pipeline asr --asr-model whisper_base
docling audio.wav --pipeline asr --asr-model whisper_large
docling audio.wav --pipeline asr --asr-model whisper_turbo
```

## Output Formats

### Format Options

```bash
# Markdown (default)
docling document.pdf --to markdown

# JSON with full document structure
docling document.pdf --to json

# HTML output
docling document.pdf --to html

# HTML with split page view
docling document.pdf --to html_split_page

# Plain text
docling document.pdf --to text

# DocTags format
docling document.pdf --to doctags

# Multiple formats
docling document.pdf --to markdown --to json --to html
```

### Image Export Modes

```bash
# Embedded base64 images (default)
docling document.pdf --image-export-mode embedded

# Referenced PNG files
docling document.pdf --image-export-mode referenced

# Placeholder markers only
docling document.pdf --image-export-mode placeholder
```

### Layout Visualization

```bash
# Show bounding boxes in output
docling document.pdf --show-layout

# Debug visualizations
docling document.pdf --debug-visualize-layout
docling document.pdf --debug-visualize-tables
docling document.pdf --debug-visualize-cells
docling document.pdf --debug-visualize-ocr
```

## GPU Usage

### Automatic GPU Detection

```bash
# Auto-detect and use best available accelerator
docling document.pdf --device auto
```

### Specific Device Selection

```bash
# Force CPU usage
docling document.pdf --device cpu

# Use CUDA GPU
docling document.pdf --device cuda

# Use Apple Metal Performance Shaders
docling document.pdf --device mps

# Use ROCm (AMD GPU)
docling document.pdf --device rocm
```

### GPU-Optimized Workflows

```bash
# VLM with GPU acceleration
docling document.pdf --pipeline vlm --vlm-model smoldocling_vllm --device cuda

# High-performance batch processing
docling ./large_dataset/ --device cuda --num-threads 8 --page-batch-size 10
```

## Advanced Options

### PDF Backend Selection

```bash
# Docling Parse v2 (default, recommended)
docling document.pdf --pdf-backend dlparse_v2

# Docling Parse v4 (latest)
docling document.pdf --pdf-backend dlparse_v4

# Docling Parse v1 (legacy)
docling document.pdf --pdf-backend dlparse_v1

# PyPdfium2 backend
docling document.pdf --pdf-backend pypdfium2
```

### Table Processing

```bash
# High accuracy table extraction (default)
docling document.pdf --table-mode accurate

# Faster table processing
docling document.pdf --table-mode fast
```

### Content Enrichment

```bash
# Enable code block enrichment
docling document.pdf --enrich-code

# Enable formula enrichment
docling document.pdf --enrich-formula

# Enable picture classification
docling document.pdf --enrich-picture-classes

# Enable picture description
docling document.pdf --enrich-picture-description

# Enable all enrichments
docling document.pdf --enrich-code --enrich-formula --enrich-picture-classes --enrich-picture-description
```

### Performance Tuning

```bash
# Control thread usage
docling document.pdf --num-threads 8

# Set document timeout (seconds)
docling document.pdf --document-timeout 300

# Batch processing optimization
docling ./documents/ --page-batch-size 16

# Memory optimization for large files
export OMP_NUM_THREADS=2
docling large_document.pdf --num-threads 2
```

### Error Handling

```bash
# Stop on first error
docling ./documents/ --abort-on-error

# Continue processing despite errors (default)
docling ./documents/ --no-abort-on-error
```

## Model Management

### Download Models for Offline Use

```bash
# Download default model set
docling-tools models download

# Download all available models
docling-tools models download --all

# Download specific models
docling-tools models download layout tableformer

# Download to custom directory
docling-tools models download --output-dir /custom/path

# Download HuggingFace models
docling-tools models download-hf-repo ds4sd/SmolDocling-256M-preview
```

### Use Local Models

```bash
# Use downloaded models
docling document.pdf --artifacts-path /path/to/models

# Via environment variable
export DOCLING_ARTIFACTS_PATH=/path/to/models
docling document.pdf
```

### External Plugins

```bash
# Show available external OCR plugins
docling --show-external-plugins

# Enable external plugins
docling document.pdf --allow-external-plugins --ocr-engine custom_plugin
```

## Examples

### Basic Document Processing

```bash
# Simple PDF to Markdown
docling research_paper.pdf

# Process with high verbosity
docling document.pdf -vv

# Quick conversion with minimal processing
docling document.pdf --no-ocr --to text
```

### Batch Processing

```bash
# Convert all PDFs in directory
docling ./pdf_collection/ --from pdf --to markdown --output ./markdown_output/

# Process mixed document types
docling ./mixed_docs/ --to json --to markdown --output ./converted/

# Large batch with progress tracking
docling ./enterprise_docs/ -v --num-threads 6 --output ./processed/
```

### URL and Web Content

```bash
# Convert ArXiv paper
docling https://arxiv.org/pdf/2408.09869 --output ./papers/

# Process Wikipedia page
docling https://en.wikipedia.org/wiki/Natural_language_processing --to markdown

# Secure site with authentication
docling https://internal.company.com/doc.pdf --headers '{"Cookie": "session=abc123"}'
```

### Advanced VLM Processing

```bash
# Best quality with SmolDocling
docling complex_document.pdf --pipeline vlm --vlm-model smoldocling --device auto

# Fast processing for simple documents
docling simple_doc.pdf --pipeline vlm --vlm-model smoldocling --table-mode fast

# Multi-language document
docling multilang.pdf --pipeline vlm --vlm-model granite_vision --ocr-lang "en,es,fr"
```

### Audio/Video Processing

```bash
# Transcribe meeting recording
docling meeting.wav --pipeline asr --asr-model whisper_large --to json

# Process video file
docling presentation.mp4 --pipeline asr --asr-model whisper_medium --output ./transcripts/

# Batch audio processing
docling ./audio_files/ --pipeline asr --asr-model whisper_base --to markdown
```

### Specialized Use Cases

```bash
# Scientific papers with formulas
docling research.pdf --enrich-formula --enrich-code --to json

# Corporate documents with images
docling report.pdf --enrich-picture-description --image-export-mode referenced

# Scanned documents with advanced OCR
docling scanned.pdf --force-ocr --ocr-engine tesseract --ocr-lang "eng,spa,fra"

# Technical documentation with layout analysis
docling manual.pdf --enrich-code --debug-visualize-layout --show-layout

# Patent documents (USPTO XML)
docling patent_docs/ --from xml_uspto --to json --output ./patents/

# Scientific articles (JATS XML)
docling journal_articles/ --from xml_jats --enrich-formula --to markdown

# Library collections (METS GBS)
docling digital_library/ --from mets_gbs --to html --output ./collection/

# Data processing workflows
docling data_reports/ --from csv --from xlsx --to json

# Multi-language documents
docling multilingual.pdf --ocr-lang "en,zh,ja,ar" --ocr-engine easyocr

# High-performance GPU processing
docling large_corpus/ --device cuda --num-threads 8 --page-batch-size 16

# Memory-constrained processing
docling huge_file.pdf --num-threads 1 --page-batch-size 1 --document-timeout 600
```

### Output Customization

```bash
# Multiple output formats
docling document.pdf --to markdown --to json --to html --output ./multi_format/

# Custom image handling
docling illustrated_doc.pdf --image-export-mode referenced --to html

# Layout debugging
docling complex_layout.pdf --show-layout --debug-visualize-tables --to html_split_page
```

### Performance Optimization

```bash
# GPU-accelerated processing
docling large_doc.pdf --device cuda --page-batch-size 8 --num-threads 4

# Memory-efficient processing
OMP_NUM_THREADS=1 docling huge_document.pdf --num-threads 1 --page-batch-size 1

# Network-optimized for URLs
docling https://example.com/doc.pdf --document-timeout 120 --headers '{"User-Agent": "DoclingBot/1.0"}'

# High-throughput batch processing
docling ./enterprise_docs/ --device auto --num-threads 8 --page-batch-size 16 --no-abort-on-error

# Optimized for different device types
docling docs/ --device mps --num-threads 4     # Apple Silicon
docling docs/ --device cuda --num-threads 6    # NVIDIA GPU
docling docs/ --device cpu --num-threads 12    # CPU-only
```

### Advanced Workflow Examples

```bash
# Complete document processing pipeline
docling academic_papers/ \
  --from pdf --from xml_jats \
  --to markdown --to json \
  --enrich-formula --enrich-code \
  --pipeline standard \
  --pdf-backend dlparse_v4 \
  --table-mode accurate \
  --image-export-mode referenced \
  --output ./processed_papers/ \
  --verbose

# VLM-powered document understanding
docling complex_layouts/ \
  --pipeline vlm \
  --vlm-model smoldocling_vllm \
  --device cuda \
  --to json \
  --image-export-mode embedded \
  --show-layout \
  --output ./vlm_results/

# Multi-format enterprise document processing
docling enterprise_content/ \
  --from pdf --from docx --from pptx --from html \
  --to markdown --to json \
  --enrich-picture-description \
  --enrich-picture-classes \
  --image-export-mode referenced \
  --num-threads 6 \
  --page-batch-size 8 \
  --output ./enterprise_processed/

# Comprehensive media transcription
docling media_archive/ \
  --from audio \
  --pipeline asr \
  --asr-model whisper_large \
  --to json --to text \
  --document-timeout 1800 \
  --output ./transcriptions/

# Debug and development workflow
docling test_docs/ \
  --debug-visualize-layout \
  --debug-visualize-tables \
  --debug-visualize-ocr \
  --show-layout \
  --to html_split_page \
  --verbose --verbose \
  --output ./debug_output/

# Offline processing with local models
docling sensitive_docs/ \
  --artifacts-path /local/models \
  --no-enable-remote-services \
  --device cpu \
  --to json \
  --output ./offline_results/
```

## Troubleshooting

### Common Issues

#### Memory Issues
```bash
# Reduce memory usage
export OMP_NUM_THREADS=1
docling large_file.pdf --num-threads 1 --page-batch-size 1
```

#### GPU Issues
```bash
# Force CPU if GPU issues
docling document.pdf --device cpu

# Check GPU availability
docling --version
nvidia-smi  # For CUDA
```

#### Model Download Issues
```bash
# Download models manually
docling-tools models download --force

# Use specific artifacts path
docling document.pdf --artifacts-path /path/to/models
```

#### Processing Errors
```bash
# Enable debug logging
docling document.pdf -vv

# Try different backend
docling document.pdf --pdf-backend pypdfium2
```

### Debug and Logging

```bash
# Basic info logging
docling document.pdf -v

# Full debug logging
docling document.pdf -vv

# Check version and system info
docling --version

# Show Docling logo
docling --logo
```

### Performance Monitoring

```bash
# Time the conversion
time docling document.pdf

# Monitor with verbose output
docling document.pdf -v --output ./results/

# Profile memory usage
/usr/bin/time -v docling large_document.pdf
```

### Environment Variables

```bash
# Model artifacts location
export DOCLING_ARTIFACTS_PATH="/path/to/models"

# Thread control
export OMP_NUM_THREADS=4

# Debug settings
export DOCLING_DEBUG=1
```

## Additional Resources

- [Official Documentation](https://docling-project.github.io/docling/)
- [GitHub Repository](https://github.com/docling-project/docling)
- [Python API Examples](https://docling-project.github.io/docling/examples/)
- [Model Specifications](https://docling-project.github.io/docling/usage/vision_models/)
- [CLI Reference](https://docling-project.github.io/docling/reference/cli/)

---

For more examples and advanced usage, visit the [official documentation](https://docling-project.github.io/docling/).