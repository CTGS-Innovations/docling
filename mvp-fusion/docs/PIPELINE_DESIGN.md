# MVP-Fusion Pipeline Design

## Overview

MVP-Fusion implements a clean pipeline architecture that separates concerns, enables A/B testing, and provides excellent performance monitoring capabilities.

## Architecture Principles

### 1. Clean Phase Separation
```
PDF Conversion → Document Processing → Classification → Entity Extraction → Normalization → Semantic Analysis
```

Each phase:
- Has a single responsibility
- Can be configured independently  
- Reports timing and performance metrics
- Can be replaced with different implementations

### 2. Configurable Processors

```yaml
# In config.yaml
pipeline:
  document_processing:
    processor: "service_processor"    # Primary processor
    sidecar_test: "fusion_pipeline"  # Optional A/B test
    target_time_ms: 30               # Performance target
```

### 3. A/B Testing Framework

The pipeline supports sidecar testing to compare processor performance:

```python
# Automatic A/B testing
pipeline = CleanFusionPipeline(config)
results, metadata = pipeline.process(files, metadata)

# Results include both primary and sidecar performance
print(f"Primary: {metadata['pipeline_timing_ms']}ms")
print(f"Sidecar: {metadata['sidecar_results']['fusion_pipeline']['timing_ms']}ms")
```

## Performance Monitoring

### Real-time Metrics

```
🔧 CLEAN PIPELINE PERFORMANCE:
   🏗️  Pipeline Architecture: Clean Phase Separation
   🔧 Primary Processor: service_processor
   ⚡ Total Pipeline Time: 215.80ms
   • ✅ document_processing: 215.80ms (100.0%) - 1,186 pages/sec

🧪 SIDECAR A/B TEST RESULTS:
   • fusion_pipeline: 234.50ms (18.70ms slower)
```

### Performance Targets

| Phase | Target Time | Typical Range | Status |
|-------|------------|---------------|--------|
| PDF Conversion | <40ms | 35-45ms | ✅ On target |
| Document Processing | <30ms | 215ms | 🔴 Needs optimization |
| Classification | <5ms | 1-3ms | ✅ Excellent |
| Entity Extraction | <10ms | 5-8ms | ✅ Good |
| Normalization | <8ms | 6-10ms | ✅ Good |  
| Semantic Analysis | <5ms | 2-4ms | ✅ Excellent |

## Implementation Details

### Core Classes

#### CleanFusionPipeline
Main pipeline orchestrator that:
- Loads processor configurations
- Executes phases in sequence
- Handles sidecar A/B testing
- Collects performance metrics

#### PipelinePhase  
Represents a single phase:
- Wraps processor implementations
- Provides timing and error handling
- Supports multiple processor interfaces

#### ProcessorFactory
Creates processors by name:
- ServiceProcessorWrapper
- FusionProcessorWrapper  
- Custom processor implementations

### Configuration Structure

```yaml
pipeline:
  # Main document processing phase
  document_processing:
    processor: "service_processor"
    sidecar_test: null  # or "fusion_pipeline" for A/B testing
    target_time_ms: 30
    
  # Future configurable phases
  pdf_conversion:
    enabled: true
    processor: "docling_extractor"
    
  classification:
    enabled: true
    processor: "embedded"
```

## Adding New Processors

### 1. Create Processor Wrapper

```python
from pipeline.processors import AbstractProcessor, ProcessorResult

class MyCustomProcessor(AbstractProcessor):
    def process(self, input_data, metadata=None):
        # Your implementation here
        return ProcessorResult(data=results, success=True, timing_ms=processing_time)
```

### 2. Register with Factory

```python
from pipeline.processors import ProcessorFactory

ProcessorFactory.register('my_processor', MyCustomProcessor)
```

### 3. Configure in config.yaml

```yaml
pipeline:
  document_processing:
    processor: "my_processor"
```

## Performance Optimization Guidelines

### Rule #12: FLPC Pattern Matching
- **NEVER** use Python `re` module
- **ALWAYS** use FLPC (Fast Lexical Pattern Compiler)  
- **Performance impact**: 40x degradation with Python regex

### Optimization Strategies
1. **Eliminate Python regex** (Rule #12 compliance)
2. **Use Aho-Corasick** for keyword matching
3. **Minimize I/O operations** 
4. **Optimize worker counts** (sweet spot: 8 CPU workers)
5. **Cache pattern compilations**

### Performance Debugging

When processing is slow:

1. **Check for regex violations**:
   ```bash
   grep -r "import re" pipeline/
   grep -r "re\." pipeline/
   ```

2. **Monitor phase timing**:
   ```bash
   python fusion_cli.py --file test.pdf -v
   # Look for phases >30ms
   ```

3. **Enable A/B testing** to compare processors

## Migration Guide

### From Legacy to Clean Pipeline

Old approach:
```python
from pipeline.service_processor import ServiceProcessor
processor = ServiceProcessor(config, workers)
results = processor.process_files_service(files, output_dir)
```

New clean approach:
```python  
from fusion_cli import CleanFusionPipeline
pipeline = CleanFusionPipeline(config)
results, metadata = pipeline.process(files, {'output_dir': output_dir})
```

Benefits:
- Standardized interface
- Performance monitoring
- A/B testing capability
- Easier maintenance and testing

## Future Enhancements

1. **Separate Phase Processors** - Currently phases 3-6 are embedded in document processing
2. **Custom Phase Ordering** - Configure phase sequence via config
3. **Parallel Phase Execution** - Run independent phases concurrently
4. **Real-time Performance Dashboard** - Web interface for monitoring
5. **Auto-scaling Workers** - Dynamic worker allocation based on load