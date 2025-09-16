# MVP-Fusion: High-Performance Document Processing

**Ground-up rewrite optimized for extreme speed while maintaining MVP-Hyper output quality.**

## 🎯 Performance Targets
- **Conservative**: 4,000+ pages/sec (20x improvement)
- **Aggressive**: 10,000+ pages/sec (50x improvement)  
- **Extreme**: 50,000+ pages/sec (250x improvement)

## 🚀 Key Features

### **Same Output Quality as MVP-Hyper**
- Rich Markdown with metadata headers
- High-quality semantic JSON with facts and rules
- 100% format compatibility for drop-in replacement

### **Extreme Performance Optimizations**
- **Fusion Engine**: Aho-Corasick (50M chars/sec) + FLPC Rust (69M chars/sec)
- **Smart Routing**: Content analysis for optimal engine selection
- **Zero-Copy Operations**: Memory-mapped I/O and string views
- **Parallel Processing**: Multi-core batch processing
- **JSON Sidecars**: No YAML parsing overhead

## 📦 Installation

### Basic Installation
```bash
cd mvp-fusion
pip install -r requirements.txt
```

### High-Performance Installation (Recommended)
```bash
# Install high-performance regex engines
pip install flpc pyahocorasick

# Verify installation
python test_fusion.py
```

## 🔧 Usage

### Command Line Interface

#### Process Single File
```bash
python fusion_cli.py --file document.pdf
```

#### Process Directory
```bash
python fusion_cli.py --directory ~/documents/ --batch-size 32
```

#### Performance Test
```bash
python fusion_cli.py --performance-test --verbose
```

#### Advanced Options
```bash
python fusion_cli.py --directory ~/docs/ \
    --config custom_config.yaml \
    --workers 16 \
    --batch-size 64 \
    --export-metrics metrics.json
```

### Python API

```python
from pipeline.fusion_pipeline import FusionPipeline

# Initialize pipeline
pipeline = FusionPipeline()

# Process single document
result = pipeline.process_document("document.txt", content)

# Check results
if result['status'] == 'success':
    print(f"Pages/sec: {result['processing_metadata']['pages_per_sec']}")
    print(f"Outputs: {result['output_paths']}")
```

## 📊 Performance Comparison

| Engine | Speed (chars/sec) | Speedup vs Python re |
|--------|-------------------|----------------------|
| Python re (baseline) | 4.6M | 1.0x |
| **FLPC (Rust)** | **69M** | **14.9x** |
| **Aho-Corasick** | **50M** | **10.9x** |
| **MVP-Fusion** | **Target: 10,000+ pages/sec** | **50x pipeline** |

## 🏗️ Architecture

### Fusion Engine
```
┌─────────────────────────────────────────────────┐
│                FUSION ENGINE                    │
├─────────────────┬─────────────────┬─────────────┤
│   AC Automaton  │   FLPC Regex    │  Smart Router│
│   (Keywords)    │   (Patterns)    │  (Analysis)  │
├─────────────────┼─────────────────┼─────────────┤
│ • 50M+ chars/s  │ • 69M chars/s   │ • Content    │
│ • O(n) lookup   │ • Rust speed    │   analysis   │
│ • Domain terms  │ • Complex regex │ • Engine     │
│                 │                 │   selection  │
└─────────────────┴─────────────────┴─────────────┘
```

### Pipeline Strategy
1. **Content Analysis** → Smart engine routing
2. **Parallel Processing** → Multi-document batches  
3. **Zero-Copy Operations** → Memory efficiency
4. **Progressive Enhancement** → In-place metadata
5. **Compatible Output** → Same format as MVP-Hyper

## 🧪 Testing

### Quick Test
```bash
python test_fusion.py
```

### Full Performance Test
```bash
python fusion_cli.py --performance-test
```

### Expected Output
```
🎯 MVP-FUSION PERFORMANCE SUMMARY
====================================
📄 Documents processed: 185
🚀 Pages per second: 8,247.3
⏱️ Average time per doc: 0.121ms
🔧 Engine Performance:
   AC selections: 45%
   FLPC selections: 40% 
   Hybrid selections: 15%
```

## 📁 Output Format (Same as MVP-Hyper)

### Enhanced Markdown
```markdown
---
title: "document_name"
source_file: "document.txt"  
processing_engine: "mvp-fusion-hybrid"
pages_per_sec: 8247.30

# Classification
primary_domain: "safety"
confidence: 0.856

# Extracted Entities
## Money
- $2,500
- $500

## Organizations  
- OSHA
- EPA
---

# Document content with metadata...
```

### Semantic JSON
```json
{
  "document_metadata": {
    "processing_engine": "mvp-fusion-hybrid",
    "performance_metrics": {
      "pages_per_sec": 8247.30,
      "chars_per_sec": 420150
    }
  },
  "classification": {
    "primary_domain": "safety",
    "entities_by_type": { "MONEY": {"count": 2, "items": ["$2,500", "$500"]} }
  },
  "semantic_extraction": {
    "facts": [...],
    "rules_and_regulations": [...], 
    "key_relationships": [...]
  }
}
```

## ⚙️ Configuration

Edit `config/fusion_config.yaml` for performance tuning:

```yaml
performance:
  mode: "extreme"              # balanced | aggressive | extreme
  target_pages_per_sec: 10000  # Performance target
  batch_size: 32               # Documents per batch
  max_workers: 16              # CPU cores to use

fusion_engine:
  engines:
    aho_corasick: 
      enabled: true             # 50M+ chars/sec keywords
    flpc_rust:
      enabled: true             # 69M chars/sec regex
  routing:
    smart_routing: true         # Content-based engine selection
    keyword_threshold: 0.8      # 80% keywords → AC
    complexity_threshold: 0.3   # 30% complex → FLPC
```

## 🔍 Troubleshooting

### Performance Issues
```bash
# Check engine status
python -c "
from fusion.fusion_engine import FusionEngine
engine = FusionEngine()
print(engine.get_engine_status())
"

# Install high-performance engines
pip install flpc pyahocorasick
```

### Memory Issues
```bash
# Reduce batch size
python fusion_cli.py --batch-size 8 --workers 4
```

### Debug Mode
```bash
python fusion_cli.py --verbose --export-metrics debug.json
```

## 📈 Performance Tips

1. **Install FLPC and Aho-Corasick** for maximum speed
2. **Use batch processing** for multiple documents
3. **Tune worker count** to match CPU cores
4. **Enable smart routing** for optimal engine selection
5. **Use SSD storage** for I/O intensive operations

## 🤝 Compatibility

- **100% MVP-Hyper Output Compatible**
- **Python 3.8+** 
- **Linux/macOS/Windows**
- **Drop-in Replacement** for MVP-Hyper workflows

---

**Ready to process at light speed! 🚀**