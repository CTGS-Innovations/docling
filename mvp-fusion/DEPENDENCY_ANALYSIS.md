# MVP-Fusion Dependency Analysis

**Generated:** 2025-10-17

## Summary

Your current `requirements.txt` has **71 packages**. After analyzing actual usage, only **14 core packages** are directly used in your code.

## Current State vs Minimal

| Metric | Current | Minimal | Savings |
|--------|---------|---------|---------|
| Direct dependencies | 71 | 14 | 57 fewer |
| Reduction | - | - | 80% smaller |

## Core Packages Actually Used

These 14 packages are directly imported in your source code:

```
beautifulsoup4   # HTML parsing
flpc             # Fast pattern matching (critical for performance)
html2text        # HTML to text conversion
markdownify      # HTML to Markdown
orjson           # Fast JSON (performance-critical)
pandas           # Data processing
psutil           # System utilities
pyahocorasick    # Aho-Corasick automaton (entity extraction)
PyMuPDF          # PDF processing (fitz module)
PyYAML           # YAML configuration
requests         # HTTP requests
spacy            # NLP processing
ujson            # Fast JSON (alternative)
xxhash           # Fast hashing
```

## Packages That Can Be Removed

These 22 packages are NOT used in your code:

```
✗ Jinja2           # Template engine - not used
✗ MarkupSafe       # Jinja2 dependency
✗ Pygments         # Syntax highlighting - not used
✗ annotated-types  # Pydantic internals
✗ cffi             # C Foreign Function Interface
✗ cloudpathlib     # Cloud storage paths - not used
✗ cryptography     # Encryption - not used
✗ lxml             # XML parser - not used
✗ marisa-trie      # Trie data structure - not used
✗ markdown-it-py   # Markdown parser - not used
✗ mdurl            # Markdown URL utilities
✗ pdfminer.six     # PDF mining - replaced by PyMuPDF
✗ pdfplumber       # PDF extraction - not used
✗ pillow           # Image processing - not used
✗ pycparser        # C parser
✗ pypdf            # PDF library - replaced by PyMuPDF
✗ pypdfium2        # PDF rendering - not used
✗ rich             # Terminal formatting - not used
✗ setuptools       # Usually in system Python
✗ shellingham      # Shell detection
✗ typing-inspection # Type utilities
✗ utils            # Generic utils package
```

## Migration Strategy

### Option 1: Fresh Install (Recommended)

Create a new clean environment from scratch:

```bash
# 1. Deactivate current environment
deactivate

# 2. Create new environment
python3.12 -m venv .venv-minimal

# 3. Activate new environment
source .venv-minimal/bin/activate

# 4. Install minimal requirements
pip install -r requirements-minimal.txt

# 5. Install spaCy language model
python -m spacy download en_core_web_sm

# 6. Test the application
python fusion_cli.py --help
```

### Option 2: Test Before Migrating

Keep your current environment and test minimal one side-by-side:

```bash
# Create test environment
python3.12 -m venv .venv-test-minimal
source .venv-test-minimal/bin/activate
pip install -r requirements-minimal.txt
python -m spacy download en_core_web_sm

# Run your tests
python fusion_cli.py --file <test-file>

# If everything works, rename environments:
mv .venv-clean .venv-old-backup
mv .venv-test-minimal .venv-clean
```

### Option 3: Verify with pip-check

Install `pip-check` to find unused dependencies:

```bash
pip install pip-check
pip-check

# Or use pipdeptree to see dependency tree
pip install pipdeptree
pipdeptree
```

## Benefits of Migration

1. **Faster Installation**: 80% fewer packages to download/install
2. **Smaller Size**: Reduced disk usage
3. **Cleaner Environment**: Only what you actually use
4. **Easier Maintenance**: Fewer packages to update
5. **Better Performance**: Less potential for conflicts

## Validation Checklist

After migrating to minimal requirements, verify:

- [ ] `python fusion_cli.py --help` works
- [ ] File processing works: `python fusion_cli.py --file <test-doc>`
- [ ] URL processing works: `python fusion_cli.py --url <test-url>`
- [ ] Batch processing works: `python fusion_cli.py --directory <test-dir>`
- [ ] All entity extractors function correctly
- [ ] JSON output is generated properly
- [ ] Performance metrics are similar or better

## Notes

- **spaCy language model** (`en_core_web_sm`) must be installed separately
- Transitive dependencies (like `numpy`, `pydantic`, etc.) are installed automatically by the core packages
- Your current `requirements.txt` will be preserved as backup
- The analysis tool is in `throwaway_tests/analyze_dependencies.py`
