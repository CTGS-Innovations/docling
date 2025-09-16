# MVP-Fusion Testing & Performance Plan
**Step-by-Step Development with Performance Validation**

---

## Development Methodology

### **Step-by-Step Iteration Process**
```
Implement → Test → Validate → Gate Decision → Next Step
```

**Development Commands:**
- `python fusion_cli.py --convert-only`   ✅ (Step 1 Complete)
- `python fusion_cli.py --classify-only`  🔄 (Step 2 In Progress)  
- `python fusion_cli.py --enrich-only`    ⏭️ (Step 3 Pending)
- `python fusion_cli.py --extract-only`   ⏭️ (Step 4 Pending)

### **Gate Criteria for Each Step:**
- **Functionality**: Stage works correctly and completely
- **Performance**: Meets timing budgets (<50ms for classify/enrich)
- **Quality**: Output matches or exceeds MVP Hyper baseline
- **Integration**: Reads previous stage outputs correctly

---

## Testing Infrastructure

### **Development Testing (Fast Iteration)**
**Location**: `/home/corey/projects/docling/cli/data_complex/`
- **Files**: 3 test PDFs (Complex1, Complex2, 3124-stairways-and-ladders)
- **Purpose**: Rapid development iteration and feature validation
- **Output**: `/home/corey/projects/docling/output/fusion/`

### **Performance Testing (Reality Check)**  
**Location**: `/home/corey/projects/docling/cli/data_osha/`
- **Files**: Hundreds of real-world OSHA documents
- **Variety**: Different sizes, shapes, complexity levels
- **Purpose**: Performance threshold validation at scale
- **Critical**: Uses source PDFs (not pre-converted markdown)

---

## Performance Budgets

### **Per-File Processing Budget**
```
🚀 CONVERSION: ~X ms per page (scales with document size)
📋 CLASSIFICATION: <50ms per file (flat cost, any size)  
🔍 ENRICHMENT: <50ms per file (flat cost, any size)
📄 EXTRACTION: TBD ms per file (flat cost, any size)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YAML OVERHEAD: <100ms per file (independent of file size)
```

### **Performance Validation Requirements**
- **Development**: 3 files meeting timing budgets
- **Stress Test**: Hundreds of OSHA documents meeting same budgets
- **Source**: Must test complete pipeline starting from PDF files
- **Measurement**: Per-stage timing breakdown required

---

## Development Stages

### **✅ Step 1: Conversion (Complete)**
**Status**: Working with basic YAML frontmatter
```yaml
---
conversion:
  description: "High-Speed Document Conversion & Analysis"
  yaml_engine: "mvp-fusion-yaml-v1" 
  yaml_schema_version: "1.0"
  # ... file metadata
---
```

### **🔄 Step 2: Classification (In Progress)**
**Requirement**: Add classification section to existing YAML
**Target**: Match MVP Hyper classification quality
```yaml
classification:
  description: "Document Classification & Type Detection"
  document_types: '["safety", "compliance"]'
  universal_entities_found: 243
  money: '["$4", "$250"]'
  phone: '["(404) 562-2300"]'
  regulation: '["29 CFR 1926.1050"]'
  # ... entity extraction results
```
**Performance**: <50ms per file
**Input**: Existing markdown files from Step 1
**Output**: Enhanced markdown with conversion + classification YAML

### **⏭️ Step 3: Enrichment (Pending)**
**Requirement**: Add enrichment section to existing YAML  
**Target**: Domain-specific entity extraction
```yaml
enrichment:
  description: "Domain-Specific Enrichment & Entity Extraction"
  domains_processed: '["safety", "compliance"]'
  total_entities: 42
  # ... domain-specific results
```
**Performance**: <50ms per file
**Input**: Markdown files from Step 2
**Output**: Enhanced markdown with conversion + classification + enrichment YAML

### **⏭️ Step 4: Extraction (Pending)**
**Requirement**: Generate semantic rules JSON files
**Target**: Knowledge extraction matching MVP Hyper
**Performance**: TBD ms per file  
**Input**: Markdown files from Step 3
**Output**: Enhanced markdown + separate `.semantic.json` files

---

## Performance Testing Protocol

### **Development Cycle Testing**
1. **Implement** stage functionality
2. **Test** on 3-file development set  
3. **Validate** timing and quality
4. **Gate decision**: Pass/fail before next stage

### **Performance Validation Testing**
1. **Complete pipeline** working on development set
2. **Run OSHA corpus** (hundreds of PDFs)
3. **Measure** per-stage timing breakdown
4. **Validate** all budgets maintained at scale
5. **Stress test** memory and resource usage

### **Success Criteria**
- **Functionality**: All stages work end-to-end
- **Performance**: <100ms YAML overhead per file maintained on OSHA corpus
- **Quality**: Entity extraction matching or exceeding MVP Hyper
- **Scalability**: Performance holds across document variety
- **Service-ready**: Single-file processing optimized

---

## Baseline Comparisons

### **MVP Hyper Baseline (3 Test Files)**
- `3124-stairways-and-ladders.md`: 38KB output, rich classification
- `Complex1.md`: 59KB output, 243 entities found
- `Complex2.md`: 56KB output, comprehensive metadata
- `.semantic.json`: ~350-470 bytes per file

### **MVP Fusion Targets**
- **Quality**: Match or exceed MVP Hyper entity extraction
- **Performance**: Beat MVP Hyper pipeline timing  
- **Completeness**: Full YAML + semantic JSON output
- **Service Architecture**: Optimized for single-file processing

---

## Risk Management

### **Performance Risks**
- **Classification timing**: Ensure <50ms budget maintained
- **Memory usage**: Monitor for leaks during large batch processing
- **Quality regression**: Maintain entity extraction accuracy

### **Development Risks**  
- **Integration issues**: Each stage must read previous stage correctly
- **YAML complexity**: Progressive YAML building without file re-reading
- **Service compatibility**: Maintain single-file processing focus

### **Mitigation Strategies**
- **Step-by-step validation**: No advancement until current stage solid
- **Continuous benchmarking**: Regular OSHA corpus performance checks  
- **Quality gates**: Automated comparison with MVP Hyper baselines

---

**This testing plan ensures we build a production-ready MVP-Fusion system that exceeds MVP Hyper performance while maintaining quality and service architecture principles.**