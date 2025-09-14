# MVP Hyper-Core: Ultra-High-Performance Document Processor

## 🎯 Target: 1,000+ Pages Per Second

Ultra-optimized document processing system designed for maximum throughput with minimal dependencies.

## Features

- **🚀 Ultra-Fast Extraction**: Target 1,000+ pages/second
- **⚡ Parallel Processing**: Multi-core CPU utilization
- **💾 Memory Mapping**: Zero-copy operations for large files
- **🗄️ Smart Caching**: In-memory cache for repeated access
- **📊 Minimal Metadata**: Fast extraction of essential metadata
- **🔄 Batch Processing**: Process entire directories in parallel

## Architecture

```
┌─────────────────────────────────────┐
│         Input Documents             │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      Memory-Mapped Reading          │
│         (mmap for <500MB)           │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│     Parallel Page Extraction        │
│   (ThreadPool with N workers)       │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│        In-Memory Cache              │
│    (xxhash/blake2b keying)         │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      Markdown Output with           │
│     Metadata Header (YAML)          │
└─────────────────────────────────────┘
```

## Quick Start

### 1. Setup
```bash
# Install dependencies
./setup.sh

# Or manually:
pip install pymupdf
pip install xxhash  # Optional, for faster caching
pip install numba   # Optional, for JIT compilation
```

### 2. Single File Processing
```bash
# Process a single PDF
./mvp-hyper-core.py document.pdf

# With output
./mvp-hyper-core.py document.pdf --output output_dir/

# With custom workers
./mvp-hyper-core.py document.pdf --workers 16
```

### 3. Batch Processing
```bash
# Process entire directory
./mvp-hyper-core.py /path/to/pdfs/

# With output directory
./mvp-hyper-core.py /path/to/pdfs/ --output results/
```

### 4. Benchmark
```bash
# Run performance benchmark
./benchmark.py --num-files 10

# Run stress test (60 seconds)
./benchmark.py --stress --duration 60

# Custom test directory
./benchmark.py --test-dir /mnt/ramdisk/pdfs --num-files 100
```

## Performance Optimizations

### System-Level Optimizations

1. **CPU Performance Mode**
```bash
sudo cpupower frequency-set -g performance
```

2. **Increase File Descriptors**
```bash
ulimit -n 65536
```

3. **Use RAM Disk for Testing**
```bash
sudo mkdir -p /mnt/ramdisk
sudo mount -t tmpfs -o size=2G tmpfs /mnt/ramdisk
cp test_files/*.pdf /mnt/ramdisk/
```

4. **Disable CPU Throttling**
```bash
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Code-Level Optimizations

The system uses several optimization techniques:

1. **Memory Mapping**: Files <500MB are memory-mapped for zero-copy access
2. **Parallel Extraction**: Pages are processed in parallel chunks
3. **Smart Caching**: LRU cache with xxhash for ultra-fast lookups
4. **Pre-allocated Buffers**: Memory pool to avoid allocation overhead
5. **Batch Processing**: Multiple files processed simultaneously

## Performance Metrics

### Expected Performance

| Configuration | Pages/Second | Files/Minute |
|--------------|--------------|--------------|
| Single Worker | 100-200 | 50-100 |
| Half CPUs | 400-600 | 200-300 |
| All CPUs | 800-1200 | 400-600 |
| Oversubscribed | 1000-1500 | 500-750 |

### Factors Affecting Performance

- **Storage Type**: NVMe SSD > SATA SSD > HDD
- **File Size**: Smaller files process faster per page
- **CPU Cores**: More cores = better parallelization
- **Memory Speed**: Faster RAM improves memory-mapped performance
- **Cache Hits**: Repeated files process at 10,000+ pages/second

## Output Format

Documents are output as Markdown with YAML metadata header:

```markdown
---
filename: document.pdf
pages: 42
size_bytes: 1048576
format: PDF
title: Document Title
author: Author Name
subject: Document Subject
---

[Extracted text content...]
```

## Troubleshooting

### Not Reaching 1000 Pages/Second?

1. **Check CPU Frequency Scaling**
   ```bash
   cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
   # Should show "performance"
   ```

2. **Verify PyMuPDF Installation**
   ```bash
   python3 -c "import fitz; print(fitz.version)"
   # Should be latest version
   ```

3. **Test with RAM Disk**
   - Copy files to RAM disk to eliminate I/O bottleneck
   
4. **Profile the Code**
   ```bash
   python3 -m cProfile -o profile.stats mvp-hyper-core.py test.pdf
   python3 -m pstats profile.stats
   ```

5. **Check System Resources**
   ```bash
   htop  # Monitor CPU usage
   iotop # Monitor I/O usage
   ```

## Advanced Usage

### Python API

```python
from mvp_hyper_core import UltraFastExtractor

# Create extractor
extractor = UltraFastExtractor(
    num_workers=16,
    use_mmap=True,
    batch_size=100,
    cache_size_mb=512
)

# Process single file
result = extractor.extract_pdf_ultrafast(Path("document.pdf"))
print(f"Speed: {result.pages_per_second:.1f} pages/sec")

# Process batch
results = extractor.process_batch(pdf_files)

# Async processing
import asyncio
results = asyncio.run(extractor.process_batch_async(pdf_files))

# Cleanup
extractor.shutdown()
```

### Batch Processing with Statistics

```python
from mvp_hyper_core import HyperBatchProcessor

processor = HyperBatchProcessor(num_extractors=4)
stats = processor.process_directory(Path("/path/to/pdfs"))

print(f"Pages/second: {stats['pages_per_second']:.1f}")
print(f"Files/second: {stats['files_per_second']:.1f}")

processor.shutdown()
```

## Limitations

- **Text Only**: Focuses on text extraction, no OCR or visual analysis
- **PDF Focused**: Optimized for PDF, basic support for other formats
- **Memory Usage**: Large batches may use significant memory
- **No OCR**: Scanned PDFs without text layer won't extract

## Future Enhancements

- [ ] GPU acceleration for batch operations
- [ ] Distributed processing across machines
- [ ] Advanced caching with Redis/Memcached
- [ ] Streaming output for real-time processing
- [ ] WebAssembly version for browser usage

## License

MIT