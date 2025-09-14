# MVP Hyper-Core: Ultra-High-Performance Document Processor

## 🎯 Target: 1,000+ Pages Per Second

Ultra-optimized document processing system designed for maximum throughput with minimal dependencies and resource constraints.

## 📁 Project Structure

```
mvp-hyper/
├── mvp-hyper-core.py          # Main processing engine
├── config_loader.py           # Configuration management system
├── config.yaml               # Default configuration file
├── docker-config.yaml        # Resource-constrained config (1 CPU/1GB RAM)
├── benchmark.py              # Performance benchmarking suite
├── diagnose_pdfs.py          # PDF diagnostic tool
├── clean.sh                  # Output directory cleanup script
├── setup.sh                  # Dependency installation script
├── run-docker-test.sh        # Docker resource-constrained testing
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose setup
├── test_config.yaml         # Test configuration (auto-generated)
├── composite_data/          # Symbolic links to multiple data directories
├── output/                  # Generated markdown files
└── README.md               # This documentation
```

## Features

### Core Capabilities
- **🚀 Ultra-Fast Extraction**: Target 1,000+ pages/second
- **📄 Multi-Format Support**: PDF, DOCX, PPTX, XLSX, HTML, TXT, MD, CSV
- **⚡ Universal Processing**: Handles any file type (text extraction or metadata)
- **🔧 Configuration-Based**: YAML-driven processing with flexible settings
- **💾 Smart Caching**: In-memory cache for repeated access
- **📊 Real-time Progress**: Live processing updates with timing analysis
- **🐳 Docker Support**: Containerized deployment with resource limits

### Processing Strategies
- **PDF**: Fast text extraction with page limits and fallback methods
- **Office Docs**: Native library extraction with ZIP fallbacks
- **Text Files**: Direct UTF-8 reading with encoding detection
- **Binary Files**: String extraction or intelligent skipping
- **Unknown Files**: Progressive fallback strategies

## Quick Start

### 1. Installation
```bash
# Install Python dependencies
pip install pymupdf pyyaml psutil openpyxl python-docx python-pptx beautifulsoup4

# Or use setup script
./setup.sh
```

### 2. Configuration-Based Processing (Recommended)
```bash
# Clean previous output
./clean.sh

# Process using config.yaml (default)
python mvp-hyper-core.py

# Process with custom config
python mvp-hyper-core.py --config docker-config.yaml

# Create test config for troubleshooting
python mvp-hyper-core.py --test-config
python mvp-hyper-core.py --config test_config.yaml
```

### 3. Command Line Processing (Legacy)
```bash
# Process multiple directories
python mvp-hyper-core.py ~/data/pdfs ~/data/docs ~/data/office --output results/

# Process single file
python mvp-hyper-core.py document.pdf --output output/

# Override config settings
python mvp-hyper-core.py --workers 4 --config config.yaml
```

## Configuration System

### Main Configuration Files

#### `config.yaml` (Default Production Config)
```yaml
inputs:
  files: []                    # Individual files to process
  directories:                 # Directories to scan recursively
    - "~/projects/docling/cli/data"
    - "~/projects/docling/cli/data_complex"
    - "~/projects/docling/cli/data_osha"

processing:
  max_workers: 8               # CPU cores to use
  max_file_size_mb: 100        # Skip files larger than this
  timeout_per_file: 10         # Timeout per file (seconds)
  slow_file_threshold: 5.0     # Warn about files slower than this
  
  skip_extensions:             # File types to skip entirely
    - ".jpg"
    - ".png"
    # ... (binary files)

pdf:
  max_pages_to_extract: 25     # Limit pages for speed
  skip_if_pages_over: 100      # Skip PDFs with too many pages
  skip_patterns:               # Skip PDFs matching these patterns
    - "training-requirements"
    - "shipyard-industry"

output:
  directory: "output"          # Output directory
  save_performance_log: true   # Save detailed performance logs
  save_error_log: true         # Save error logs

debug:
  progress_interval: 50        # Show progress every N files
  timing_threshold: 1.0        # Warn about slow files
  max_files_to_process: 0      # Limit for testing (0 = all)
```

#### `docker-config.yaml` (Resource-Constrained Config)
- Optimized for 1 CPU core, 1GB RAM
- Aggressive page limits (15 pages max)
- Smaller file size limits (25MB max)
- Skip PDFs with >75 pages

### Configuration Commands
```bash
# Use default config
python mvp-hyper-core.py

# Use custom config
python mvp-hyper-core.py --config docker-config.yaml

# Generate test config with problematic files
python mvp-hyper-core.py --test-config

# Override specific settings
python mvp-hyper-core.py --workers 1 --output test_output/
```

## Docker Deployment

### Resource-Constrained Testing
```bash
# Build and run with 1 CPU core, 1GB RAM limits
./run-docker-test.sh

# Manual Docker run
docker build -t mvp-hyper:test .
docker run --rm --cpus="1.0" --memory="1g" \
  -v "$(pwd)/output:/app/output" \
  -v "$(pwd)/docker-config.yaml:/app/config.yaml" \
  mvp-hyper:test
```

### Docker Compose
```bash
# Run with docker-compose
docker-compose up

# Run with resource limits
docker-compose --profile constrained up
```

## Diagnostic Tools

### PDF Analysis
```bash
# Diagnose slow PDFs
python diagnose_pdfs.py

# Shows: file size, page count, complexity, extraction speeds
# Identifies: why specific PDFs are slow
```

### Performance Benchmarking
```bash
# Run comprehensive benchmark
python benchmark.py --num-files 50

# Run stress test
python benchmark.py --stress --duration 60

# Custom benchmark
python benchmark.py --test-dir /path/to/test/files --num-files 100
```

### Progress Monitoring
The system provides real-time feedback:
```
🔧 CONFIGURATION:
  Workers: 1
  Output: output
  Total files found: 943
  Config file: config.yaml

🔄 PROCESSING 943 FILES:
============================================================
[  50/943] Processing: document.pdf (.pdf)
  ⚠️  SLOW FILE: large-doc.pdf took 3.02s (.pdf)
[ 100/943] Processing: spreadsheet.xlsx (.xlsx)
  ⏭️  SKIPPED: image.jpg (.jpg) - binary file
```

## Performance Analysis

### Real-World Performance Results

#### Native Performance (Multi-core)
```
Total files: 943
Successful: 934
Pages/second: 515.4
Top bottlenecks:
  .pdf: 590 files, 12.46s total, 0.021s avg, 530.9 pages/sec
  .xlsx: 1 files, 0.10s total, 0.099s avg, 40.3 pages/sec
```

#### Docker Performance (1 core/1GB RAM)
```
Total files: 943
Successful: 943
Pages/second: 265.3
Resource constraints impact: ~50% reduction
Memory usage: <1GB sustained
```

### Performance Bottlenecks Identified

1. **High Page Count PDFs**
   - `training-requirements-by-standard.pdf`: 270 pages (7.40s)
   - `shipyard-industry-standards.pdf`: 340 pages (3.02s)
   - **Solution**: Page limits (`max_pages_to_extract: 25`)

2. **Large File Sizes**
   - Files >10MB cause memory pressure
   - **Solution**: File size limits (`max_file_size_mb: 25`)

3. **Binary File Processing**
   - Images, audio, video files slow down processing
   - **Solution**: Skip binary extensions

### Optimization Strategies

#### For Speed (Target: 1000+ pages/sec)
```yaml
pdf:
  max_pages_to_extract: 15     # Very aggressive page limiting
  skip_if_pages_over: 50       # Skip moderate-sized PDFs
processing:
  max_workers: 8               # Use all CPU cores
  max_file_size_mb: 50         # Skip large files
```

#### For Resource Constraints (1 core/1GB RAM)
```yaml
pdf:
  max_pages_to_extract: 10     # Minimal page extraction
  skip_if_pages_over: 25       # Skip most multi-page PDFs
processing:
  max_workers: 1               # Single core
  max_file_size_mb: 10         # Very small files only
```

#### For Accuracy (Process everything)
```yaml
pdf:
  max_pages_to_extract: 999999 # No page limits
  skip_if_pages_over: 999999   # No file limits
  skip_patterns: []            # Don't skip any patterns
```

## Output Format

### Markdown Files
Each processed document generates a markdown file:

```markdown
---
filename: document.pdf
pages: 42
size_bytes: 1048576
format: PDF
title: Document Title
author: Author Name
extracted: text_content
---

[Extracted text content...]

[Note: Only extracted first 25 of 42 pages for speed]
```

### Output Management
```bash
# Clean output before processing
./clean.sh

# Check output files
ls -la output/ | head -10

# Count generated files
find output -name "*.md" | wc -l
```

## Advanced Features

### File Processing Strategies

#### Progressive Fallback System
1. **Format-Specific Extraction** (PDF → PyMuPDF, DOCX → python-docx)
2. **ZIP Fallback** (Office docs → direct XML parsing)
3. **Text Extraction** (UTF-8 reading with encoding detection)
4. **Binary String Extraction** (Extract readable strings from binary files)
5. **Metadata Only** (File info when all else fails)

#### Smart File Skipping
```python
# Automatic skipping based on:
- File extension (.jpg, .png, .mp4, etc.)
- File size (>100MB default)
- Page count (>100 pages for PDFs)
- Filename patterns ("training-requirements", etc.)
- Processing time (>5 seconds default)
```

### Error Handling
- **Fail Fast**: Don't hang on problematic files
- **Per-page Error Handling**: Extract what's possible from corrupt PDFs
- **Graceful Degradation**: Multiple fallback strategies
- **Detailed Error Reporting**: Full error analysis in output

## Troubleshooting

### Common Issues

#### No Output Files Generated
```bash
# Check if output directory is configured
python mvp-hyper-core.py  # Should show "💾 SAVING OUTPUT FILES..."

# Verify output directory exists
ls -la output/

# Check for permission issues
mkdir -p output && chmod 755 output
```

#### Low Performance (<500 pages/sec)
```bash
# Run diagnostics on slow PDFs
python diagnose_pdfs.py

# Check CPU frequency scaling
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Profile the application
python -m cProfile mvp-hyper-core.py > profile.txt
```

#### Memory Issues (Docker)
```bash
# Monitor memory usage
docker stats mvp-hyper-test

# Use more aggressive limits
# Edit docker-config.yaml:
#   max_pages_to_extract: 5
#   skip_if_pages_over: 25
```

### Performance Debugging

#### Individual File Analysis
```bash
# Create test config with specific files
python mvp-hyper-core.py --test-config

# Edit test_config.yaml to include problem files:
inputs:
  files:
    - "/path/to/slow/file.pdf"

# Run single-threaded analysis
python mvp-hyper-core.py --config test_config.yaml --workers 1
```

#### System Resource Monitoring
```bash
# Monitor during processing
htop          # CPU usage
iotop         # I/O usage
free -h       # Memory usage
df -h         # Disk space
```

## Deployment Scenarios

### High-Performance Server (Multi-core, High RAM)
```yaml
processing:
  max_workers: 32              # All CPU cores
  max_file_size_mb: 500        # Large files OK
pdf:
  max_pages_to_extract: 100    # More complete extraction
  skip_if_pages_over: 500      # Handle large documents
```

### Edge Device (1 core, 1GB RAM)
```yaml
processing:
  max_workers: 1               # Single core only
  max_file_size_mb: 10         # Small files only
pdf:
  max_pages_to_extract: 5      # Minimal extraction
  skip_if_pages_over: 20       # Skip most PDFs
```

### Batch Processing Server (Focus on Throughput)
```yaml
processing:
  max_workers: 16              # High parallelism
  timeout_per_file: 2          # Fast timeout
pdf:
  max_pages_to_extract: 1      # First page only
  skip_patterns:               # Skip known slow patterns
    - "training"
    - "manual"
    - "specification"
```

## Future Enhancements

- [ ] **GPU Acceleration**: CUDA-based PDF processing
- [ ] **Distributed Processing**: Multi-machine coordination
- [ ] **Streaming Processing**: Real-time document processing
- [ ] **ML-Based Classification**: Automatic document categorization
- [ ] **OCR Integration**: Scanned document processing
- [ ] **WebAssembly Version**: Browser-based processing
- [ ] **Redis Caching**: Persistent distributed cache
- [ ] **Kubernetes Deployment**: Cloud-native scaling

## License

MIT License - See LICENSE file for details.