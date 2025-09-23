# MVP-Fusion Documentation

Welcome to the MVP-Fusion documentation directory.

## Contents

- [PIPELINE_DESIGN.md](PIPELINE_DESIGN.md) - Clean pipeline architecture design and implementation guide

## Overview

MVP-Fusion is a high-performance document processing pipeline designed for:

- **Speed**: Target <30ms per document processing
- **Scalability**: Handle 10,000+ pages/sec throughput  
- **Flexibility**: Configurable processors and A/B testing
- **Maintainability**: Clean architecture with phase separation

## Quick Start

```bash
# Process a single file
python fusion_cli.py --file document.pdf

# Process a directory
python fusion_cli.py --directory ~/documents/

# Use configuration file
python fusion_cli.py --config config/config.yaml
```

## Architecture

MVP-Fusion uses a clean pipeline architecture with:

1. **Configurable Phases** - PDF conversion, document processing, classification, etc.
2. **Pluggable Processors** - ServiceProcessor, FusionPipeline, or custom implementations  
3. **A/B Testing** - Compare processor performance via configuration
4. **Performance Monitoring** - Real-time timing and throughput metrics

See [PIPELINE_DESIGN.md](PIPELINE_DESIGN.md) for detailed architecture information.