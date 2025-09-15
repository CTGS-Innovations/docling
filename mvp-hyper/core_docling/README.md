# MVP Docling Core

A high-performance document processing system using Docling for conversion with intelligent fallbacks.

## Overview

This directory contains a Docling-based implementation of the MVP Hyper Core system, designed for performance comparison and quality improvement over the original PyMuPDF-based system.

## Key Features

- **Docling Integration**: Uses Docling's DocumentConverter for high-quality document conversion
- **Intelligent Fallbacks**: Falls back to PyMuPDF when Docling is too slow (configurable threshold)
- **Performance Monitoring**: Tracks conversion methods and performance metrics
- **Progressive Enhancement**: Same 4-step pipeline as original MVP Hyper Core
- **Quality vs Speed**: Configurable balance between conversion quality and processing speed

## Files

### Core Components
- `mvp-docling-core.py` - Main document converter using Docling
- `mvp-docling-pipeline-progressive.py` - Full progressive enhancement pipeline

### Configuration
- `.config/mvp-docling-config.yaml` - Main Docling configuration
- `.config/mvp-docling-pipeline-config.yaml` - Pipeline configuration
- `.config/config.yaml` - Simple compatibility configuration

## Quick Start

### Basic Document Conversion
```bash
# Convert documents using Docling
python mvp-docling-core.py ~/Documents/pdfs --output ./output

# With GPU acceleration (if available)
python mvp-docling-core.py ~/Documents/pdfs --output ./output --gpu

# With custom fallback threshold
python mvp-docling-core.py ~/Documents/pdfs --output ./output --fallback-threshold 3.0
```

### Full Progressive Pipeline
```bash
# Run complete 4-step pipeline
python mvp-docling-pipeline-progressive.py --output ./pipeline_output

# Run individual steps
python mvp-docling-pipeline-progressive.py --step conversion --output ./output
python mvp-docling-pipeline-progressive.py ./output --step classification
python mvp-docling-pipeline-progressive.py ./output --step enrichment
python mvp-docling-pipeline-progressive.py ./output --step extraction
```

## Performance Comparison

### Expected Performance Characteristics

| Method | Speed | Quality | Use Case |
|--------|-------|---------|----------|
| Original MVP Hyper | 700+ pages/sec | Basic | High-volume processing |
| Docling Only | 100-300 pages/sec | High | Quality-focused processing |
| **Hybrid (This)** | **400-600 pages/sec** | **High** | **Balanced approach** |

### Hybrid Strategy Benefits

1. **Quality First**: Uses Docling for superior markdown output
2. **Speed Fallback**: Switches to PyMuPDF for slow files
3. **Configurable**: Adjustable fallback threshold based on requirements
4. **Monitoring**: Tracks which method is used for each file

## Configuration

### Fallback Threshold Tuning

The `fallback_threshold` setting controls when to switch from Docling to PyMuPDF:

```yaml
docling:
  fallback_threshold: 5.0  # Switch to PyMuPDF if Docling takes >5 seconds
```

- **Lower values (1-3s)**: Favor speed, use PyMuPDF more often
- **Higher values (5-10s)**: Favor quality, give Docling more time
- **Very high (>10s)**: Quality-first, rarely use fallback

### GPU Acceleration

Enable GPU processing for better performance on complex documents:

```yaml
docling:
  use_gpu: true
```

### Document Type Settings

Configure processing for different document types:

```yaml
docling:
  conversion:
    pdf:
      extract_tables: true     # Docling excels at table extraction
      extract_figures: false   # Skip for speed
      max_pages_per_document: 25
```

## Performance Monitoring

The system tracks detailed metrics:

- **Conversion Method**: Which engine was used (Docling vs fallback)
- **Processing Speed**: Pages per second for each method
- **Success Rates**: Conversion success by method
- **Resource Usage**: Memory and CPU utilization

### Sample Output
```
╔═══════════════════════════════════════════════════════════════╗
║                    DOCLING PERFORMANCE SUMMARY               ║
╚═══════════════════════════════════════════════════════════════╝

📊 OVERALL METRICS:
   Total Files:    45
   Total Pages:    1,250
   Total Time:     12.5s
   Avg Speed:      100.0 pages/sec

🔄 CONVERSION METHOD BREAKDOWN:
   DOCLING      32 files,  900 pages,   85.7 pages/sec
   FALLBACK     13 files,  350 pages,  175.0 pages/sec
```

## Dependencies

Required packages:
```bash
# Core Docling
pip install docling

# Fallback engine
pip install PyMuPDF

# Standard packages
pip install pyyaml pathlib
```

## Comparison with Original

| Aspect | Original MVP Hyper | Docling Core | Improvement |
|--------|-------------------|--------------|-------------|
| **Text Quality** | Basic extraction | High-quality markdown | ✅ Significant |
| **Table Handling** | Limited | Excellent preservation | ✅ Major |
| **Layout Preservation** | Minimal | Good structure | ✅ Notable |
| **Processing Speed** | 700+ pages/sec | 400-600 pages/sec | ⚠️ Moderate decrease |
| **Resource Usage** | Low | Medium | ⚠️ Increase |
| **Error Handling** | Basic | Robust with fallbacks | ✅ Improved |

## Use Cases

### When to Use Docling Core

1. **Quality Requirements**: When markdown quality is important
2. **Table-Heavy Documents**: Documents with complex tables
3. **Mixed Workflows**: Balance of speed and quality needed
4. **Research/Analysis**: When document structure matters

### When to Use Original MVP

1. **Pure Speed**: Maximum processing throughput required
2. **Large Scale**: Processing thousands of documents
3. **Basic Text**: Simple text extraction sufficient
4. **Resource Constraints**: Limited CPU/memory available

## Troubleshooting

### Common Issues

1. **Slow Performance**: Adjust `fallback_threshold` to use PyMuPDF more
2. **Quality Issues**: Increase `fallback_threshold` to use Docling more
3. **Memory Usage**: Reduce `batch_size` and `max_concurrent_files`
4. **GPU Errors**: Set `use_gpu: false` if GPU issues occur

### Debug Mode

Enable detailed logging:
```bash
python mvp-docling-core.py --debug ~/Documents/pdfs --output ./output
```

## Future Enhancements

1. **Adaptive Thresholds**: Dynamic fallback based on document characteristics
2. **Quality Metrics**: Automatic quality assessment of conversion results
3. **Caching**: Cache conversion results for repeated processing
4. **Batch Optimization**: Intelligent batching based on document complexity