# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- Use `uv sync` to create/update virtual environment and install dependencies
- Use `uv add <package>` to add new dependencies (updates pyproject.toml and uv.lock)
- Use `uv venv --python 3.12` for specific Python versions if needed

### Code Quality and Testing
- `uv run ruff format` - Format code with Ruff
- `uv run ruff check --fix` - Lint and auto-fix with Ruff
- `uv run mypy docling` - Run type checking with MyPy
- `pre-commit run --all-files` - Run all pre-commit hooks
- `uv run pytest` - Run tests
- `DOCLING_GEN_TEST_DATA=1 uv run pytest` - Regenerate reference test data

### Documentation
- `mkdocs serve` - Start local documentation server (http://localhost:8000)
- `mkdocs gh-deploy` - Deploy documentation to GitHub Pages

### CLI Usage
- `docling <file_or_url>` - Convert document to Markdown
- `docling --pipeline vlm --vlm-model smoldocling <file_or_url>` - Use VLM pipeline

## Directory Structure

### Protected Source Directory
- **`/home/corey/projects/docling/docline-github/`** - PROTECTED: Source of truth from GitHub. DO NOT MODIFY any files in this directory or subdirectories.
- **`/home/corey/projects/docling/scout-docs/`** - Working directory for new files, documentation, and modifications.

## Architecture Overview

### Core Components
- **DocumentConverter** (`docling/document_converter.py`) - Main entry point for document conversion
- **Backend System** (`docling/backend/`) - Format-specific backends that handle different document types:
  - `abstract_backend.py` - Base classes for all backends
  - Format backends: `pdf_backend.py`, `docling_parse_v4_backend.py`, `msword_backend.py`, etc.
  - Each backend implements `AbstractDocumentBackend` with format-specific conversion logic
- **DataModel** (`docling/datamodel/`) - Core data structures and models
- **Pipeline** (`docling/pipeline/`) - Processing pipeline components
- **CLI** (`docling/cli/`) - Command-line interface

### Document Processing Flow
1. **Input Processing**: Document format detection and validation
2. **Backend Selection**: Route to appropriate format-specific backend
3. **Conversion**: Transform document to unified `DoclingDocument` representation
4. **Pipeline Processing**: Apply enrichment and processing steps
5. **Output Generation**: Export to desired format (Markdown, HTML, JSON, etc.)

### Key Design Patterns
- **Backend Pattern**: Pluggable backends for different document formats
- **Pipeline Pattern**: Modular processing stages with optional components
- **Plugin System**: Extensible through entry points and plugins

### Technology Stack
- **Python 3.9-3.13** with Pydantic v2 for data validation
- **uv** for package management and virtual environments
- **Ruff** for code formatting and linting
- **MyPy** for static type checking
- **MkDocs** with Material theme for documentation
- **pytest** for testing with coverage reporting

### Testing Philosophy
- Reference test data stored in `tests/data_scanned/groundtruth/`
- Tests require regeneration when conversion results improve
- All PRs modifying reference data require double review
- Use `DOCLING_GEN_TEST_DATA=1` environment variable to regenerate test fixtures