# 🚀 Docling Ultra-Fast Performance Benchmark - Execution Guide

## Overview
This benchmark suite targets **80% GPU/CPU utilization** for maximum throughput with comprehensive document pre-classification and quality assessment.

## Quick Start

### 1. Activate Environment
```bash
cd /home/corey/projects/docling/cli
source .venv/bin/activate
```

### 2. Run Performance Benchmark
```bash
# Simple execution
./run_benchmark.sh

# Or run directly with Python
python3 performance_benchmark.py
```

### 3. View Results
```bash
# Latest results (symlinked)
ls -la output/latest/

# All timestamped runs
ls -la output/
```

## What Gets Tested

### Document Inventory (359 files across 15+ formats)
- **PDF**: 12 files (complex layout testing)
- **DOCX**: 13 files (office documents)
- **PPTX**: 3 files (presentations)
- **XLSX**: 2 files (spreadsheets)
- **CSV**: 8 files (data formats)
- **HTML**: 18 files (web content)
- **Images**: TIFF, WebP formats
- **Scientific**: USPTO patents, JATS articles
- **Audio**: MP3 for ASR testing
- **Markup**: Markdown, AsciiDoc

### Pre-Classification Strategy
Documents are automatically classified for optimal processing:

1. **Simple docs** → Standard pipeline (fast)
2. **Complex docs** → VLM pipeline (better quality)
3. **Large docs** → Special handling (reduced batch size)
4. **Image-heavy** → OCR optimized
5. **Data docs** → CSV/Excel specific processing

Each document gets tagged for vector database indexing:
- Content type: `['research', 'legal', 'technical', 'office']`
- Format: `['pdf', 'structured', 'image', 'data']`
- Complexity: `['simple', 'complex', 'standard']`

## 80% Utilization Optimization

### GPU Targeting (RTX 3090)
- **Memory**: 80% of 24GB = ~19GB utilization
- **Batch Size**: Dynamically optimized (8-20 docs/batch)
- **Pipeline**: VLM for complex, Standard for simple docs
- **Backend**: Latest dlparse_v4 for maximum speed

### CPU Targeting
- **Threads**: 80% of available CPU cores
- **Parallel Processing**: Multiple document types simultaneously
- **Memory Management**: Smart batching to prevent OOM

## Output Structure

### Timestamped Runs
```
output/
├── run_20250910_143022/          # Timestamped run
│   ├── benchmark.log             # Comprehensive execution log
│   ├── performance_results.json  # Detailed metrics
│   ├── PERFORMANCE_REPORT.md     # Executive summary
│   ├── pdf/                      # PDF outputs
│   ├── docx/                     # DOCX outputs
│   └── ...                       # Other formats
├── run_20250910_151045/          # Another run
└── latest -> run_20250910_151045 # Symlink to latest
```

### Clean Separation
- **Source data**: `/data/` (never modified)
- **Outputs**: `/output/run_TIMESTAMP/` (clean per run)
- **Logs**: Both console and file logging

## Key Metrics Tracked

### Performance
- **Throughput**: Files per minute
- **GPU Utilization**: Memory usage %
- **CPU Efficiency**: Thread utilization
- **Success Rate**: % of successful conversions
- **Cost Analysis**: Processing cost per 1000 docs

### Quality (when enabled)
- **Content Similarity**: Against groundtruth
- **Structure Preservation**: Headers, lists, tables
- **Format Accuracy**: Markdown quality

## Expected Results

### Performance Targets
- **Simple docs**: 15-30 files/minute
- **Complex docs**: 5-15 files/minute (VLM)
- **Overall capacity**: 20K-50K docs/day (single GPU)
- **GPU utilization**: 75-85% target range

### Cost Efficiency
- **Power cost**: ~$0.042/hour (RTX 3090)
- **Processing cost**: <$0.10 per 1000 documents
- **ROI**: 10-50x improvement over CPU-only

## Troubleshooting

### Common Issues
1. **GPU not detected**: Check `nvidia-smi`
2. **Out of memory**: Reduce batch size in config
3. **Timeout errors**: Increase document timeout
4. **Permission errors**: Check file permissions

### Logs
- **Live progress**: Watch `tail -f output/latest/benchmark.log`
- **Error details**: Check error messages in log file
- **GPU monitoring**: Use `nvidia-smi` during execution

## Production Recommendations

Based on benchmark results:

1. **Single GPU Setup**: Handles 10K-50K docs/day
2. **Multi-GPU Cluster**: For 100K+ docs/day enterprise scale
3. **Pipeline Routing**: Automatic classification for optimal processing
4. **Cost Optimization**: GPU provides 10-50x ROI vs CPU-only

## Next Steps After Benchmark

1. **Review Reports**: Analyze performance and quality metrics
2. **Optimize Configuration**: Tune based on specific document mix
3. **Production Deployment**: Scale configuration for enterprise load
4. **Monitoring Setup**: Implement continuous performance tracking

## Command Line Examples

```bash
# Quick benchmark run
./run_benchmark.sh

# View latest results
cat output/latest/PERFORMANCE_REPORT.md

# Monitor GPU during execution
watch -n 1 nvidia-smi

# Check logs in real-time
tail -f output/latest/benchmark.log

# Compare multiple runs
ls -la output/run_*/PERFORMANCE_REPORT.md
```

---

**Ready for ultra-fast document processing with comprehensive quality validation!** 🚀