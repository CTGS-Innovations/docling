# MVP-Fusion Cleanup & Refactor Plan

## 🚨 Current State: MESSY
- **59 temporary/test files** out of 71 total (83% junk!)
- **Unclear directory structure**
- **Hard to maintain and understand**

## 🎯 Target State: CLEAN
- **Clean pipeline design within fusion_cli.py**
- **Organized directory structure**
- **Easy to maintain and enhance**

---

## Phase 1: Remove Temporary Files (59 files)

### Files to DELETE:
```bash
# TMP files (experimental code)
debug_pipeline_flow_TMP.py
debug_document_processing_TMP.py
utils/flpc_entity_extractor_TMP.py
debug_full_document_persons_TMP.py
debug_real_text_TMP.py
debug_tagging_TMP.py
debug_real_pipeline_gpe_TMP.py
test_pdf_conversion_speed_TMP.py
find_overhead_bottleneck_TMP.py

# Test files (no longer needed)
test_direct_integration.py
test_processors.py
test_processors_simple.py
test_architecture.py
debug_service_processor.py

# Log files
debug_workers.log
final_test.log
debug_test.log
debug.log

# Temporary output directories
test_output_persons_fixed/
test_async_streaming/
test_io_timing/
test_output_fixed/

# Temporary config files
config/full_test.yaml
test_normalization_TMP.txt

# Processor testing (replaced by clean pipeline)
processors/
```

### Files to KEEP:
```bash
# Core pipeline files
fusion_cli.py                    # Main CLI (to be refactored)
pipeline/service_processor.py    # Current processor (to be wrapped)
pipeline/fusion_pipeline.py      # Alternative processor
pipeline/in_memory_document.py   # Document handling

# Configuration
config/config.yaml              # Main configuration
config/processors.yaml          # Clean processor config

# Utilities
utils/logging_config.py         # Logging
utils/phase_manager.py          # Phase timing
utils/global_spacy_manager.py   # Component management
utils/person_entity_extractor.py # Person extraction

# Knowledge base
knowledge/                      # Entity corpora and extractors
normalization/                  # Entity normalization
extraction/                     # Document extraction

# Documentation
README.md
CLAUDE.md
```

---

## Phase 2: Clean Pipeline Design in fusion_cli.py

### Current Problems:
- Hardcoded pipeline phases
- No clean separation of concerns
- Hard to A/B test different processors
- Maintenance nightmare

### Target Architecture:
```python
# Clean pipeline within fusion_cli.py
class FusionPipeline:
    def __init__(self, config):
        self.phases = [
            Phase("pdf_conversion", ConversionProcessor(config)),
            Phase("document_processing", DocumentProcessor(config)),  # Configurable!
            Phase("classification", ClassificationProcessor(config)),
            Phase("entity_extraction", EntityProcessor(config)),
            Phase("normalization", NormalizationProcessor(config)),
            Phase("semantic_analysis", SemanticProcessor(config))
        ]
    
    def process(self, input_data):
        for phase in self.phases:
            input_data = phase.execute(input_data)
        return input_data

# Sidecar A/B testing via config
document_processing:
  processor: "service_processor"  # or "flpc_optimized"
  sidecar_test: "flpc_optimized"  # Optional A/B test
```

### Benefits:
- Same entry point: `python fusion_cli.py`
- Same performance (1-2ms overhead)
- Clean phase separation
- A/B testing via config
- Easy to maintain and enhance

---

## Phase 3: Clean Directory Structure

```
mvp-fusion/
├── fusion_cli.py              # MAIN ENTRY POINT
├── config/
│   ├── config.yaml            # Main configuration
│   └── pipeline.yaml          # Pipeline processor config
├── pipeline/
│   ├── __init__.py            # Pipeline framework
│   ├── phases.py              # Phase definitions
│   ├── processors.py          # Processor implementations
│   └── legacy/                # Existing processors (wrapped)
│       ├── service_processor.py
│       └── fusion_pipeline.py
├── utils/                     # Utilities
├── knowledge/                 # Entity knowledge
├── normalization/             # Entity normalization
├── extraction/               # Document extraction
└── docs/                     # Documentation
    ├── README.md
    └── PIPELINE_DESIGN.md
```

---

## Implementation Steps:

1. **CLEANUP**: Remove 59 temporary files
2. **REFACTOR**: Implement clean pipeline in fusion_cli.py  
3. **WRAP**: Existing processors as configurable components
4. **TEST**: Same performance, cleaner architecture
5. **INTEGRATE**: A/B testing capabilities

Expected timeline: 2-3 hours for complete cleanup and refactor.