# MVP-Fusion Architecture Patterns

## Pipeline Architecture Overview

### Core Concepts

**PIPELINE**: Common orchestrator that executes stages in sequence
**STAGES**: Isolated, independent processing units (also called "services")  
**SIDECAR**: Alternative implementation of any stage/service

### Pipeline Design Principles

1. **Sequential Processing**: Pipeline calls stages 1→2→3→4→5→6→7 in order
2. **Isolated Stages**: Each stage is completely separate with no cross-stage code
3. **Performance Isolation**: Each stage's timing can be measured independently
4. **Interface Consistency**: All stages accept same input type, produce same output type
5. **Interchangeable Implementation**: Any stage can be replaced with enhanced version

### Seven Pipeline Stages

1. **PDF Conversion Stage**: Convert documents to processable format
2. **Document Processing Stage**: Core document processing and transformation
3. **Classification Stage**: Document type and content classification
4. **Entity Extraction Stage**: Extract entities (people, organizations, locations, etc.)
5. **Normalization Stage**: Standardize and canonicalize extracted entities
6. **Semantic Analysis Stage**: Extract facts, rules, and relationships
7. **File Writing Stage**: Write processed results to output files

## Pipeline Sidecar Pattern

### Definition

In MVP-Fusion, a **"sidecar"** is an **alternative implementation** of a pipeline stage/service that follows these principles:

- **Same Interface**: Takes identical inputs and produces identical outputs as the original stage
- **Different Implementation**: Uses optimized algorithms, different libraries, or performance enhancements
- **Swappable via Configuration**: Can be switched without modifying pipeline code
- **A/B Testable**: Runs alongside primary stage for performance comparison
- **Promotes to Primary**: Can replace primary stage when proven better

### Purpose

1. **Isolated Optimization**: Improve individual pipeline phases without touching other code
2. **Zero Waste Development**: No pipeline modifications, no auxiliary code changes
3. **Clean Performance Testing**: Direct comparison between service implementations
4. **Risk-Free Deployment**: Test in production safely alongside current service
5. **Maintainable Architecture**: Each service is contained and independently optimizable

## Implementation Strategy

### Phase 1: Establish Clean Pipeline Architecture
**GOAL**: Get system working with isolated stages (no enhancements)

1. **Create Common Pipeline Orchestrator**: Single component that calls stages in sequence
2. **Extract 7 Isolated Stages**: Each stage is separate with clear input/output interfaces
3. **Verify Performance Baseline**: Ensure performance is similar to current system
4. **Confirm Stage Sequence**: All stages work in proper order

### Phase 2: Apply Sidecar Optimizations
**GOAL**: Replace stages with enhanced versions once baseline is established

1. **Keep Stages 1,3,4,5,6,7 Original**: No changes to other stages
2. **Replace Stage 2 with Sidecar**: Apply OptimizedDocProcessor as stage 2 enhancement
3. **Measure Isolated Performance**: Verify optimization impact on just that stage
4. **Repeat for Other Stages**: Apply pattern to any stage needing optimization

### Implementation Pattern

#### Configuration Structure
```yaml
pipeline:
  stages:
    stage_1_pdf_conversion:
      processor: "pdf_conversion_service"
      target_time_ms: 100
    stage_2_document_processing:
      processor: "document_processing_service"    # Primary stage
      sidecar_test: "optimized_doc_processor"     # Enhanced version
      target_time_ms: 30
    stage_3_classification:
      processor: "classification_service"
      target_time_ms: 50
    # ... stages 4-7
```

#### Stage Interface Requirements
All stages (primary and sidecar) must implement:

```python
class StageInterface:
    def __init__(self, config: Dict[str, Any]):
        """Initialize with configuration"""
        pass
    
    def process(self, input_data: Any, metadata: Dict[str, Any]) -> Tuple[Any, float]:
        """
        Process stage input and return output.
        
        Args:
            input_data: Output from previous stage (or initial input for stage 1)
            metadata: Processing metadata and context
            
        Returns:
            Tuple of (stage_output, timing_ms)
        """
        pass
```

#### A/B Testing Flow
```
Input Files → Primary Service (real work) → Output Files
     ↓
     └→ Sidecar Service (performance test) → Comparison Data
```

### Example: Document Processing Sidecar

#### Problem
- Primary service: `service_processor` taking 2,874ms
- Target: <30ms processing time
- Need: Faster implementation without breaking pipeline

#### Solution
```yaml
pipeline:
  document_processing:
    processor: "service_processor"           # Current slow service
    sidecar_test: "optimized_doc_processor"  # Fast alternative
    target_time_ms: 30
```

#### Results
- **Primary**: 2,874ms (production output)
- **Sidecar**: 6.83ms (421x faster)
- **Decision**: Promote sidecar to primary when ready

#### Promotion
```yaml
pipeline:
  document_processing:
    processor: "optimized_doc_processor"     # Promoted to primary
    sidecar_test: null                       # No more testing needed
```

### Benefits Achieved

1. **Performance**: 421x speedup demonstrated
2. **Safety**: Production continues working during testing
3. **Isolation**: Zero changes to pipeline architecture
4. **Clarity**: Clear comparison metrics for decision making
5. **Simplicity**: Single config change to deploy optimization

### Anti-Patterns to Avoid

❌ **Modifying Pipeline Code**: Never change pipeline architecture for service optimization
❌ **Breaking Interfaces**: Sidecar must have identical input/output interface
❌ **Complex Integration**: Keep service swapping simple - config-only changes
❌ **Auxiliary Code Changes**: Optimization should be contained within the service
❌ **Industry Definitions**: Don't confuse with "sidecar containers" - this is different

### Pattern Extensions

This pattern applies to any pipeline phase:
- **PDF Conversion**: Test different extraction engines
- **Classification**: Compare ML models
- **Entity Extraction**: Test different NLP approaches
- **Normalization**: Compare text processing algorithms

Each phase can have sidecars for independent optimization without affecting the overall pipeline.

---

**This pattern enables continuous performance improvement with minimal risk and maximum clarity.**