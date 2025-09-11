# Product Requirements Document (PRD): Enhanced Formula Detection in Docling

## 1. Executive Summary

**Problem Statement**: Docling's current formula detection system suffers from incomplete formula extraction, often detecting only partial formulas (left-hand side, right-hand side, or individual variables) instead of complete mathematical expressions. This occurs both for standalone formulas and formulas embedded within paragraphs.

**Solution**: Implement a multi-layered approach to improve formula detection accuracy through enhanced layout detection, intelligent region merging, and adaptive confidence thresholds.

## 2. Current State Analysis

### 2.1 Existing Architecture
- **Layout Detection**: Vision-based models (EGRET, HERON) identify formula regions
- **Formula Processing**: CodeFormula model (`ds4sd/CodeFormulaV2`) extracts LaTeX from detected regions
- **Confidence Threshold**: Fixed 0.5 threshold for formula detection
- **Two-Stage Process**: Layout detection → Formula enrichment

### 2.2 Identified Issues
1. **Fragmented Detection**: Layout model splits complex formulas into multiple regions
2. **Incomplete Bounding Boxes**: Detected regions don't encompass full formulas
3. **Embedded Formula Problems**: Formulas within paragraphs aren't properly isolated
4. **Fixed Thresholds**: One-size-fits-all confidence settings don't adapt to document types

## 3. Product Requirements

### 3.1 Functional Requirements

#### FR-1: Enhanced Layout Detection
- **FR-1.1**: Support for multiple layout model configurations with different accuracy/speed tradeoffs
- **FR-1.2**: Adaptive confidence thresholds based on document type and formula complexity
- **FR-1.3**: Higher resolution image processing (2x scale) for improved detection accuracy

#### FR-2: Intelligent Region Merging
- **FR-2.1**: Automatic detection and merging of fragmented formula regions
- **FR-2.2**: Spatial proximity analysis to group related formula components
- **FR-2.3**: Context-aware merging that considers formula structure and mathematical notation

#### FR-3: Advanced Formula Processing
- **FR-3.1**: VLM pipeline integration for sophisticated formula understanding
- **FR-3.2**: Multi-pass formula detection for complex mathematical expressions
- **FR-3.3**: Support for inline and display formula detection modes

#### FR-4: Quality Assurance
- **FR-4.1**: Formula completeness validation
- **FR-4.2**: LaTeX syntax verification for extracted formulas
- **FR-4.3**: Confidence scoring for formula extraction quality

### 3.2 Non-Functional Requirements

#### NFR-1: Performance
- **NFR-1.1**: Processing time increase should not exceed 50% of current baseline
- **NFR-1.2**: Memory usage should remain within 2x of current requirements
- **NFR-1.3**: Support for batch processing of multiple documents

#### NFR-2: Accuracy
- **NFR-2.1**: Achieve 90%+ complete formula detection rate (vs. current ~70%)
- **NFR-2.2**: Reduce false positive rate to <5%
- **NFR-2.3**: Maintain 95%+ accuracy for standalone formulas

#### NFR-3: Compatibility
- **NFR-3.1**: Backward compatibility with existing Docling API
- **NFR-3.2**: Support for all current document formats (PDF, Word, HTML, etc.)
- **NFR-3.3**: Integration with existing enrichment pipeline

## 4. Technical Implementation Plan

### 4.1 Phase 1: Layout Model Enhancement (Weeks 1-2)

#### 4.1.1 Configuration Updates
```python
# Enhanced pipeline configuration
pipeline_options = PdfPipelineOptions()
pipeline_options.layout_options.model_spec = DOCLING_LAYOUT_EGRET_LARGE  # More accurate model
pipeline_options.images_scale = 2.0  # Higher resolution
pipeline_options.do_formula_enrichment = True
```

#### 4.1.2 Adaptive Confidence Thresholds
```python
# Dynamic confidence thresholds based on document characteristics
FORMULA_CONFIDENCE_THRESHOLDS = {
    "academic_papers": 0.4,      # Lower threshold for dense mathematical content
    "technical_docs": 0.45,      # Medium threshold for mixed content
    "general_docs": 0.6,         # Higher threshold for cleaner detection
}
```

### 4.2 Phase 2: Region Merging Implementation (Weeks 3-4)

#### 4.2.1 Spatial Analysis Engine
```python
class FormulaRegionMerger:
    def __init__(self, merge_threshold: float = 0.1):
        self.merge_threshold = merge_threshold
    
    def merge_fragmented_formulas(self, clusters: List[Cluster]) -> List[Cluster]:
        """Merge formula clusters that are spatially related"""
        formula_clusters = [c for c in clusters if c.label == DocItemLabel.FORMULA]
        merged_clusters = self._spatial_grouping(formula_clusters)
        return merged_clusters
    
    def _spatial_grouping(self, clusters: List[Cluster]) -> List[Cluster]:
        """Group clusters based on spatial proximity and mathematical context"""
        # Implementation details for spatial analysis
```

#### 4.2.2 Context-Aware Merging
- Analyze mathematical notation patterns
- Consider formula structure (operators, brackets, etc.)
- Implement semantic understanding of formula components

### 4.3 Phase 3: VLM Pipeline Integration (Weeks 5-6)

#### 4.3.1 VLM Configuration
```python
# VLM pipeline for advanced formula detection
vlm_options = VlmPipelineOptions()
vlm_options.vlm_options = InlineVlmOptions(
    response_format=ResponseFormat.DOCTAGS,
    model_type=VlmModelType.SMOLDOCLING_TRANSFORMERS,
)
vlm_options.generate_picture_images = True
vlm_options.images_scale = 2.0
```

#### 4.3.2 Multi-Pass Detection
- First pass: Standard layout detection
- Second pass: VLM-based refinement for complex formulas
- Third pass: Validation and quality assurance

### 4.4 Phase 4: Quality Assurance (Weeks 7-8)

#### 4.4.1 Formula Validation
```python
class FormulaValidator:
    def validate_completeness(self, formula_text: str) -> bool:
        """Check if formula appears complete"""
        # Check for balanced brackets, operators, etc.
    
    def validate_latex_syntax(self, latex_text: str) -> bool:
        """Validate LaTeX syntax correctness"""
        # Basic LaTeX syntax validation
```

#### 4.4.2 Confidence Scoring
- Implement confidence scoring for formula extraction quality
- Provide feedback mechanism for continuous improvement

## 5. Success Metrics

### 5.1 Primary Metrics
- **Complete Formula Detection Rate**: Target 90%+ (current ~70%)
- **False Positive Rate**: Target <5% (current ~15%)
- **Processing Time**: Maintain within 150% of baseline

### 5.2 Secondary Metrics
- **User Satisfaction**: Formula extraction quality ratings
- **API Adoption**: Usage of enhanced formula detection features
- **Error Reduction**: Decrease in manual formula correction needs

## 6. Implementation Timeline

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1 | 2 weeks | Enhanced layout configuration, adaptive thresholds |
| Phase 2 | 2 weeks | Region merging engine, spatial analysis |
| Phase 3 | 2 weeks | VLM integration, multi-pass detection |
| Phase 4 | 2 weeks | Quality assurance, validation system |
| **Total** | **8 weeks** | **Complete enhanced formula detection system** |

## 7. Risk Assessment

### 7.1 Technical Risks
- **Risk**: VLM model performance degradation
- **Mitigation**: Fallback to standard pipeline, performance monitoring

### 7.2 Performance Risks
- **Risk**: Increased processing time
- **Mitigation**: Optimized batch processing, caching mechanisms

### 7.3 Compatibility Risks
- **Risk**: Breaking changes to existing API
- **Mitigation**: Backward compatibility layer, gradual migration

## 8. Future Enhancements

### 8.1 Advanced Features
- Machine learning-based formula type classification
- Support for handwritten mathematical notation
- Integration with mathematical knowledge bases

### 8.2 Performance Optimizations
- GPU acceleration for VLM processing
- Distributed processing for large document batches
- Caching mechanisms for repeated formula patterns

---

**Document Version**: 1.0  
**Last Updated**: [Current Date]  
**Owner**: Docling Development Team  
**Stakeholders**: Users requiring accurate mathematical formula extraction