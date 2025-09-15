# MVP Hyper Core Pipeline

High-performance document processing pipeline with progressive enhancement strategy for maximum efficiency and unified output structure.

**⚠️ CRITICAL REQUIREMENTS**:
1. **Working Directory**: All commands must be run from `/home/corey/projects/docling/mvp-hyper/` directory
2. **Python Environment**: Use `/home/corey/projects/docling/cli/.env/bin/python` (has PyMuPDF and other PDF libraries installed)
   - System Python (`/usr/bin/python`) will fail with "PyMuPDF not available" error
   - PDF processing will produce empty files without the correct environment

## Performance Targets
- **Conversion**: Ultra-fast PDF to Markdown (700+ pages/sec)
- **Classification**: Document type identification (2,000+ pages/sec)
- **Enrichment**: Domain-specific tagging (1,500+ pages/sec) 
- **Extraction**: Semantic fact generation (300+ pages/sec)

## 🚀 PRIMARY PIPELINE (Recommended)

### mvp-hyper-pipeline-progressive.py ⭐ PRODUCTION READY
**Unified output directory strategy with progressive in-place enhancement.**

```bash
# Complete pipeline - ALL STEPS (Recommended)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py ~/projects/docling/cli/data_osha --output results --full --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

python core/mvp-hyper-pipeline-progressive.py ~/projects/docling/cli/data_osha --output output  --full --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# Individual steps (all work in same directory)
# Step 1: Convert PDFs to markdown (uses config input directories)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --step conversion --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# Step 2: Classify documents (in-place enhancement - works on output/ directory)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --step classification --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# Step 3: Add domain tags (in-place enhancement - works on output/ directory)  
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --step enrichment --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# Step 4: Extract semantic facts (creates .semantic.json alongside .md in output/ directory)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --step extraction --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

**🎯 Key Advantages:**
- **Single Directory**: All files (markdown + semantic JSON) in one location
- **Storage Efficient**: ~70% less disk usage vs multi-directory approach
- **Progressive Enhancement**: Files enriched in-place, no duplication
- **Better Context**: Semantic extraction uses full classification + enrichment context
- **Unified Output**: `document.md` + `document.semantic.json` side-by-side

**📁 Output Structure:**
```
results/
├── document1.md                    # Progressively enhanced markdown
├── document1.semantic.json         # Semantic facts extracted with full context
├── document2.md
├── document2.semantic.json
└── ...
```

## Alternative Components (Legacy)

### 1. mvp-hyper-core.py
Ultra-high-performance document processor targeting 1,000 pages/sec for text extraction.
```bash
# Run from mvp-hyper/ directory with correct Python environment
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-core.py input_directory/ --output output/
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-core.py --output output/ '/path/to/specific/file.pdf'
```

### 2. mvp-hyper-pipeline.py
Three-tier progressive refinement system with individual stage control.
```bash
# Full pipeline (input directories specified in config file)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline.py --output output/ --config core/.config/mvp-hyper-config.yaml

# Individual tiers
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline.py --tier1-only --config core/.config/mvp-hyper-config.yaml
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline.py --tier2-only --config core/.config/mvp-hyper-config.yaml  
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline.py --tier3-only --config core/.config/mvp-hyper-config.yaml
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline.py --baseline --config core/.config/mvp-hyper-config.yaml
```

### 3. mvp-hyper-pipeline-progressive.py (NOW PRIMARY METHOD)
Progressive enhancement pipeline - **use this for all new work.**

### 4. mvp-hyper-pipeline-clean.py
Original step-by-step pipeline with separate directories for each stage.
```bash
# Step 1: Classification
python core/mvp-hyper-pipeline-clean.py test-output-pipeline/1-markdown --output test-output-pipeline --step classification

# Step 2: Enrichment
python core/mvp-hyper-pipeline-clean.py test-output-pipeline/2-classified --output test-output-pipeline --step enrichment --config core/.config/mvp-hyper-pipeline-clean-config.yaml

# Step 3: Semantic Extraction
python core/mvp-hyper-pipeline-clean.py test-output-pipeline/3-enriched --output test-output-pipeline --step extraction --config core/.config/mvp-hyper-pipeline-clean-config.yaml
```

### 5. mvp-hyper-semantic.py
Advanced semantic extraction and fact generation.
```bash
python core/mvp-hyper-semantic.py test-output-tagged test-output-semantic
```

### 6. mvp-hyper-tagger.py
Sidecar document tagging system for intelligent metadata and classification.
```bash
python core/mvp-hyper-tagger.py input/ --output output/ --enable-tagging
```

## 📋 Pipeline Architecture Comparison

### ⭐ Progressive Pipeline (PRODUCTION - Primary Method)
**File:** `mvp-hyper-pipeline-progressive.py`
**Config:** `mvp-hyper-pipeline-progressive-config.yaml`

**✅ Production Advantages:**
- 📁 **Unified Directory** - All files in single location
- 🔄 **In-place Enhancement** - No file duplication across steps
- 💾 **Storage Efficient** - ~70% less disk usage
- 🎯 **Enhanced Context** - Semantic extraction uses full classification + enrichment
- 🐛 **Simplified Debugging** - Track progressive enhancement in single files
- 🚀 **Better Performance** - Reduced I/O operations

**Production Output Structure:**
```
results/
├── doc1.md                # Progressively enhanced markdown
├── doc1.semantic.json     # Semantic facts using full context
├── doc2.md               
├── doc2.semantic.json     
└── ...                   # All files side-by-side
```

### Legacy Clean Pipeline 
**File:** `mvp-hyper-pipeline-clean.py` *(Legacy - use progressive instead)*
**Config:** `mvp-hyper-pipeline-clean-config.yaml`

**Legacy Multi-Directory Structure:**
```
output/
├── 1-markdown/     # Original conversions
├── 2-classified/   # Copies with classification  
├── 3-enriched/     # Copies with enrichment
└── 4-extracted/    # Semantic extractions
```
*⚠️ Note: Creates file duplicates, uses more storage*

## Important: PDF Processing Workflow

**PDFs must be converted to markdown BEFORE running the pipeline stages**

The pipeline expects markdown files as input. When you see:
```
⚠️  Skipping .pdf file - run mvp-hyper-core.py first to convert to markdown
```

This means you need to first convert PDFs to markdown using `mvp-hyper-core.py`.

## 🧪 PRODUCTION Testing Workflow

### ⭐ Primary Testing Method (Progressive Pipeline)
**⚠️ Run all commands from `/home/corey/projects/docling/mvp-hyper/` directory**

**Complete Pipeline Test (Recommended):**
```bash
# Single command runs all steps with unified output
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py ~/projects/docling/cli/data_osha --output test-results --full --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

**Step-by-Step Testing:**
```bash
# 1. Convert PDFs to markdown (uses config directories, outputs to test-results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output test-results --step conversion --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 2. Add classification (in-place on test-results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output test-results --step classification --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 3. Add enrichment (in-place on test-results/) 
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output test-results --step enrichment --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 4. Extract semantic facts (creates .semantic.json alongside .md in test-results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output test-results --step extraction --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

**✅ Expected Output Structure:**
```
test-results/
├── document1.md                # Enhanced with classification + enrichment  
├── document1.semantic.json     # Semantic facts using full context
├── document2.md               
├── document2.semantic.json     
└── ...                        # All pairs side-by-side
```

### Legacy Testing Method (Multi-Directory)
*⚠️ Use progressive pipeline instead for new testing*

## Configuration Files

### 🚀 Primary Configuration (Production)

**Progressive Pipeline Configuration:**
- `core/.config/mvp-hyper-pipeline-progressive-config.yaml` - **PRODUCTION CONFIG** ⭐
  - Progressive enhancement with in-place updates
  - Unified output directory strategy  
  - Performance targets for all steps
  - Input directory specifications

### Legacy Configurations
- `core/.config/mvp-hyper-config.yaml` - For legacy mvp-hyper-pipeline.py
- `core/.config/mvp-hyper-pipeline-clean-config.yaml` - For legacy clean pipeline
- `core/.config/pipeline-config.yaml` - Tier configurations only (no input directories)

**Other Configurations:**
- `core/.config/config.yaml` - General configuration
- `core/.config/test_config.yaml` - Testing configuration
- `core/.config/docker-config.yaml` - Docker environment settings

### Key Configuration Parameters
- **Speed targets** for each tier
- **Regex patterns** for classification and entity extraction
- **Domain-specific** processing rules
- **Output formats** and naming conventions
- **Performance monitoring** settings

## Performance Enhancement Notes

### Current Focus Areas
- **Regular expressions** are being used for most pattern matching for maximum performance
- **Minimal dependencies** approach to reduce overhead
- **Multi-processing** and **async** support for parallel processing
- **Memory mapping** for large file handling
- **Optional accelerators** (numba, xxhash) for speed optimization

### Benchmark Testing
The pipeline is designed for benchmark-tier performance testing with:
- Configurable speed targets per tier
- Performance logging and statistics
- Memory-efficient processing
- Scalable parallel processing

## 🚀 PRODUCTION Usage Examples

### ⭐ Quick Start (Progressive Pipeline - Recommended)
**⚠️ Run from `/home/corey/projects/docling/mvp-hyper/` directory**

**Single Command - Complete Processing:**
```bash
# Process all documents with unified output (RECOMMENDED)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py ~/projects/docling/cli/data_osha --output results --full --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

**Step-by-Step Processing (Progressive):**
```bash
# 1. Convert PDFs to markdown (uses config directories, outputs to results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output results --step conversion --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 2. Classify documents (enhances files in-place in results/)  
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output results --step classification --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 3. Add domain enrichment (enhances files in-place in results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output results --step enrichment --config core/.config/mvp-hyper-pipeline-progressive-config.yaml

# 4. Extract semantic facts (creates .semantic.json alongside .md in results/)
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py --output results --step extraction --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

### Performance Testing (Progressive)
```bash
# Complete performance test with unified output
/home/corey/projects/docling/cli/.env/bin/python core/mvp-hyper-pipeline-progressive.py ~/projects/docling/cli/data_osha --output perf-test --full --config core/.config/mvp-hyper-pipeline-progressive-config.yaml
```

### Legacy Usage Examples
*⚠️ Use progressive pipeline instead for new work*

## Dependencies

### Required
- Python 3.9+
- PyMuPDF (fitz) for PDF processing
- Standard library modules

### Optional Performance Accelerators
- `numba` - JIT compilation for numerical operations
- `xxhash` - Fast hashing algorithms
- Additional packages as specified in configuration

## Performance Monitoring

All scripts include built-in performance monitoring:
- Pages per second metrics
- Processing time breakdowns
- Memory usage tracking
- Error reporting and statistics

Results are saved as `.stats.json` files alongside processed documents.

## Troubleshooting

### Common Issues and Solutions

#### 1. "PyMuPDF not available" Error
**Problem**: Using system Python instead of environment Python
**Solution**: Use `/home/corey/projects/docling/cli/.env/bin/python` for all commands

#### 2. Empty or Small Markdown Files (6-8 lines)
**Problem**: PDF processing failed due to missing libraries
**Solution**: Ensure you're using the correct Python environment with PyMuPDF installed

#### 3. "Skipping .pdf file - run mvp-hyper-core.py first"
**Problem**: Pipeline expects markdown files, not PDFs
**Solution**: First convert PDFs using `mvp-hyper-core.py`, then run pipeline stages

#### 4. "No input specified" Error
**Problem**: Wrong config file or missing input directories in config
**Solution**: Use `core/.config/mvp-hyper-config.yaml` which contains input directories

#### 5. "File needs to be converted to markdown first" in Output
**Problem**: Pipeline processed a placeholder instead of actual content
**Solution**: Re-run with correct Python environment to properly convert PDFs