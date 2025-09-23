# MVP-Fusion Pipeline Enhancement Plan
## From Working Legacy to Modular Pipeline Architecture

### 🎯 Primary Goal
Transform the existing working legacy system into a modular pipeline architecture that maintains **identical performance and output** by wrapping existing code into isolated stages. This is **NOT a rewrite** - we are preserving all current working logic exactly as-is, just organizing it into stages.

**Core Principle: Same Code = Same Performance**
- Wrap existing working functions into stage interfaces
- No optimization, no changes to core logic
- Identical imports, dependencies, and processing flows
- Same performance baseline guaranteed

---

## 📋 Current State Assessment

### ✅ What Works Today
- **Legacy System**: `service_processor` + `fusion_pipeline` delivering solid results
- **Performance**: ~2,878ms total processing time across 5 files
- **Complete Output Pipeline**:
  - ✅ **Markdown files with YAML frontmatter** (single `.md` file per document)
  - ✅ **Semantic knowledge JSON** (single `.json` file per document)
  - ✅ Entity extraction (person, org, location, money, dates) in YAML frontmatter
  - ✅ Normalized entities in YAML frontmatter
  - ✅ Classification data in YAML frontmatter
  - ✅ Semantic facts/rules/relationships in JSON file

### 🎯 Target Architecture
Wrap existing working code into **7 isolated pipeline stages** with identical input/output at each stage. **No `use_orchestrated` toggle** - the orchestrated pipeline becomes the default and only implementation.

**Implementation Philosophy:**
- **Copy, don't rewrite**: Extract existing logic into stage wrappers
- **Same functions, new organization**: Preserve all current working code
- **Zero functional changes**: Only interface wrapping, no logic modifications

---

## 🏗️ Pipeline Stage Design

### Stage Interface Standard
```python
class StageInterface(ABC):
    def process(self, input_data: Any, metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """
        Args:
            input_data: Output from previous stage (or file paths for stage 1)
            metadata: Processing context and configuration
            
        Returns:
            Tuple of (stage_output, timing_ms)
        """
        pass
```

### 7-Stage Pipeline Architecture

#### Stage 1: PDF Conversion
- **Input**: List of file paths
- **Output**: List of `InMemoryDocument` objects with raw content
- **Legacy Code**: PDF extraction logic from `service_processor.py:100-150`
- **Responsibility**: Convert PDFs/documents to processable text format

#### Stage 2: Document Processing  
- **Input**: List of `InMemoryDocument` objects
- **Output**: List of `InMemoryDocument` with processed content and metadata
- **Legacy Code**: Core processing from `service_processor.py:200-400`
- **Responsibility**: Text processing, markdown generation, basic metadata

#### Stage 3: Classification
- **Input**: List of processed `InMemoryDocument` objects
- **Output**: Same documents with classification metadata added
- **Legacy Code**: Aho-Corasick classification from `fusion_pipeline.py:150-200`
- **Responsibility**: Document type classification, domain identification

#### Stage 4: Entity Extraction
- **Input**: Classified documents
- **Output**: Documents with raw entity extraction data
- **Legacy Code**: Entity extraction from `service_processor.py:400-600`
- **Responsibility**: Extract persons, organizations, locations, money, dates

#### Stage 5: Normalization
- **Input**: Documents with raw entities
- **Output**: Documents with normalized entity data
- **Legacy Code**: Entity normalization from `EntityNormalizer`
- **Responsibility**: Canonicalize and standardize extracted entities

#### Stage 6: Semantic Analysis
- **Input**: Documents with normalized entities
- **Output**: Documents with semantic facts, rules, relationships
- **Legacy Code**: Semantic extraction from `SemanticFactExtractor`
- **Responsibility**: Generate semantic JSON with facts/rules/relationships

#### Stage 7: File Writing
- **Input**: Fully processed documents
- **Output**: Written files and processing report
- **Legacy Code**: File writing logic from `service_processor.py:800-900`
- **Responsibility**: Write **2 files per document**:
  - `document.md` - Markdown content with YAML frontmatter
  - `document.json` - Semantic knowledge JSON

---

## 🔄 Implementation Strategy

### Phase 1: Create Wrapper Pipeline (Week 1)
**Goal**: Identical performance and output through wrapped stages

1. **Extract Stage Logic - Copy Existing Code Exactly**
   - **Copy/paste existing working functions** into 7 stage classes
   - **Maintain every import, dependency, and logic flow**
   - **Zero modifications** to core processing logic
   - **Same performance guaranteed** because it's the same code

2. **Pipeline Orchestrator**
   - Sequential stage execution: 1→2→3→4→5→6→7
   - **Use existing timing measurement** from legacy system
   - **Preserve existing error handling** and logging

3. **Configuration Integration**
   ```yaml
   pipeline:
     # No use_orchestrated toggle - this IS the system
     stages:
       stage_1_pdf_conversion: { enabled: true }
       stage_2_document_processing: { enabled: true }
       stage_3_classification: { enabled: true }
       stage_4_entity_extraction: { enabled: true }
       stage_5_normalization: { enabled: true }
       stage_6_semantic_analysis: { enabled: true }
       stage_7_file_writing: { enabled: true }
   ```

### Phase 2: Validation Testing (Week 1)
**Goal**: Prove identical output to legacy system

1. **Baseline Comparison**
   ```bash
   # Test command (no parameters - uses config defaults)
   python fusion_cli.py
   
   # Expected: Same 5 files → Same 10 output files (5 .md + 5 .json)
   # Same performance: ~2,878ms total processing time
   ```

2. **Output Validation**
   - Compare **markdown files with YAML frontmatter** byte-for-byte
   - Validate **entity extraction counts** in YAML frontmatter match exactly  
   - Verify **semantic JSON structure** identical
   - Confirm **classification data** in YAML frontmatter matches
   - Confirm performance within 5% of baseline

3. **Success Criteria - Validation Command: `python fusion_cli.py`**
   - ✅ Same 5 files processed successfully
   - ✅ **2 files per document**: `document.md` + `document.json`
   - ✅ **Raw entity extraction** visible in YAML frontmatter
   - ✅ **Normalized entity extraction** visible in YAML frontmatter  
   - ✅ **Completed semantic JSON** file generated
   - ✅ Same entity counts in YAML frontmatter (person, org, location, money, dates)
   - ✅ Performance: 2,500-3,200ms (within 10% of 2,878ms baseline)

**How to Know When Done:**
Run `python fusion_cli.py` and verify:
1. **Raw entities** appear in markdown YAML frontmatter
2. **Normalized entities** appear in markdown YAML frontmatter
3. **Semantic JSON** files are generated and complete
4. Same performance as baseline (~2,878ms)

### Phase 3: Sidecar Framework (Future)
**Goal**: Enable A/B testing and optimization

1. **Sidecar Interface**
   ```yaml
   pipeline:
     stages:
       stage_2_document_processing:
         processor: "legacy_wrapper"
         sidecar_test: "optimized_processor"  # Future optimization
   ```

2. **A/B Testing Framework**
   - Run primary processor for production output
   - Run sidecar processor for performance comparison
   - Log timing and output differences

---

## 📊 Validation Plan

### Test Environment
- **Files**: 5 files from `/home/corey/projects/docling/cli/data_complex`
- **Command**: `python fusion_cli.py` with default settings
- **Expected Output**: All current outputs maintained

### Success Metrics

| Metric | Legacy Baseline | Pipeline Target | Status |
|--------|----------------|-----------------|---------|
| Total Processing Time | ~2,878ms | 2,500-3,200ms | 🎯 |
| **Markdown Files Generated** | **5** | **5** | 🎯 |
| **JSON Files Generated** | **5** | **5** | 🎯 |
| Entity Extraction Count | [Current counts] | Identical | 🎯 |
| YAML Frontmatter Structure | [Current structure] | Identical | 🎯 |
| Memory Usage | [Current usage] | Within 10% | 🎯 |

### Output File Validation
```bash
# Generated files should match current output (2 files per document):
output/
├── document1.md           # Markdown with YAML frontmatter
├── document1.json         # Semantic knowledge JSON  
├── document2.md           # Markdown with YAML frontmatter
├── document2.json         # Semantic knowledge JSON
└── ...                    # etc.
```

### YAML Frontmatter Structure (in .md files)
```yaml
---
conversion:
  tool: orchestrated_pipeline
  timestamp: '2025-09-23T18:52:24'
  page_count: 1
  source_file: /path/to/source.pdf
processing:
  stage: extracted
  processed_at: 1758653544.523506
  word_count: 364966
classification:
  primary_domain: general
  primary_document_type: document
  raw_entities:
    global_entities: {...}
    domain_entities: {...}
entity_insights:
  has_financial_data: false
  total_entities_found: 0
normalization:
  canonical_entities: []
  entity_reduction_percent: 0.0
---
```

### Semantic JSON Structure (.json files)
```json
{
  "semantic_facts": {...},
  "normalized_entities": {...},
  "semantic_summary": {
    "total_facts": 0,
    "fact_types": {},
    "extraction_engine": "FLPC + Classification Parallel Processing"
  }
}
```

---

## 🚀 Implementation Tasks

### Week 1: Core Pipeline Implementation

#### Day 1-2: Stage Extraction
- [ ] Extract PDF conversion logic → `Stage1_PdfConversion`
- [ ] Extract document processing → `Stage2_DocumentProcessing`  
- [ ] Extract classification logic → `Stage3_Classification`
- [ ] Extract entity extraction → `Stage4_EntityExtraction`

#### Day 3-4: Remaining Stages
- [ ] Extract normalization logic → `Stage5_Normalization`
- [ ] Extract semantic analysis → `Stage6_SemanticAnalysis`
- [ ] Extract file writing logic → `Stage7_FileWriting`

#### Day 5: Pipeline Orchestrator
- [ ] Create `WrappedLegacyPipeline` class
- [ ] Implement sequential stage execution
- [ ] Add timing and logging
- [ ] Integration with `fusion_cli.py`

#### Day 6-7: Testing & Validation
- [ ] Run baseline legacy system tests
- [ ] Run new pipeline system tests  
- [ ] Compare outputs byte-for-byte
- [ ] Performance validation
- [ ] Fix any discrepancies

---

## 🎯 Key Success Principles

### 1. **Zero Functional Changes**
- Copy existing working code exactly
- Maintain all imports, dependencies, logic flows
- Only change: wrap in stage interface

### 2. **Identical Output Guarantee**
- Same input files → same output files
- Byte-for-byte markdown comparison
- Identical entity extraction results
- Same semantic JSON structure

### 3. **Performance Baseline Maintenance**
- Target: Within 10% of current 2,878ms
- No performance degradation from wrapping
- Measure each stage individually

### 4. **Future-Ready Architecture**
- Clean stage interfaces for sidecar testing
- Configuration-driven stage selection
- A/B testing framework ready

---

## 🔧 Technical Implementation Notes

### Import Strategy
```python
# Reuse all existing imports and logic
from pipeline.legacy.service_processor import ServiceProcessor
from pipeline.legacy.fusion_pipeline import FusionPipeline
from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
# ... all current working imports
```

### Stage Implementation Pattern
```python
class Stage2_DocumentProcessing(StageInterface):
    def __init__(self, config):
        super().__init__(config)
        # Copy/paste existing working logic - NO CHANGES
        self.service_processor = ServiceProcessor(config)
        
    def process(self, input_docs, metadata):
        start_time = time.perf_counter()
        
        # EXACT copy of existing working logic
        # Same functions, same imports, same everything
        result = self.service_processor.process_documents(input_docs)
        
        timing_ms = (time.perf_counter() - start_time) * 1000
        return result, timing_ms
```

**Critical Implementation Rules:**
1. **Copy, don't rewrite**: Use existing functions as-is
2. **Same imports**: All existing dependencies preserved
3. **Same logic flows**: No algorithmic changes
4. **Same error handling**: Preserve existing try/catch blocks
5. **Same logging**: Keep existing log statements

### Configuration Integration
- **Remove `use_orchestrated` toggle completely**
- **Orchestrated pipeline becomes the default system**
- **`python fusion_cli.py` always uses orchestrated pipeline**
- **No legacy fallback needed once validation complete**

---

## 📈 Expected Outcomes

### Immediate (Week 1)
- ✅ Working pipeline architecture with 7 isolated stages
- ✅ Identical output to legacy system
- ✅ Performance within 10% of baseline
- ✅ Configuration-driven stage execution

### Future Capabilities Enabled
- 🚀 Individual stage optimization through sidecars
- 🧪 A/B testing of different implementations
- 📊 Per-stage performance monitoring
- 🔧 Easy addition of new processing stages

### Risk Mitigation
- Legacy system remains available as fallback
- Gradual migration approach reduces risk
- Comprehensive validation before production use
- Easy rollback if issues discovered

---

**This plan transforms the working legacy system into a modular pipeline architecture while maintaining 100% compatibility and enabling future optimization through the sidecar pattern.**