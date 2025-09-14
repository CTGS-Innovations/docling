# FutureState Architecture Plan
## Enhanced MVP Hyper Pipeline with Universal Entity Classification

---

## Executive Summary

**Vision**: Transform the MVP Hyper Pipeline from a three-tier system to a clean four-stage flow: **MARKDOWN → CLASSIFICATION → ENRICHMENT → SEMANTIC FACT EXTRACTION**

**Key Enhancement**: Integrate universal entity extraction (people, places, organizations, structural patterns) into the CLASSIFICATION phase using spaCy NLP and optimized regex patterns, creating a "semantic roadmap" that accelerates downstream processing.

**Performance Goal**: Maintain 1000+ pages/sec in classification while providing 3-5x performance boost to enrichment and semantic phases through pre-identified high-value content areas.

---

## Current State Analysis

### What's Working Well ✅
- **Fast document classification**: Document types & domains with confidence percentages (2000+ pages/sec)
- **Keyword extraction**: Frequency-based method extracting relevant terms  
- **Topic identification**: Higher-level themes (system architecture, implementation, performance)
- **Basic entity extraction**: Simple pattern matching for organizations, acronyms, emails, dates
- **Pipeline orchestration**: Clean step-by-step processing with performance monitoring

### Current Output Example
```yaml
document_types: [safety: 50%, financial: 38%, general: 12%]
domains: [safety: 50%, finance: 25%, general: 25%]
keywords: body, location, paragraph, document, doclaynet, annotation, layout, text, pages, page
entities: IBM, Annotated Dataset, bpf@zurich.ibm.com, 0/22/08, Large Human
topics: system architecture, implementation, performance, testing
```

### Performance Baseline
- **Classification**: 2000+ pages/sec (current tagger)
- **Enrichment**: 1500+ pages/sec (domain-specific enhancement)
- **Semantic Extraction**: 300+ pages/sec (fact extraction)

### Issues to Address
- **Flat entity list**: No differentiation between people, organizations, locations
- **Limited structural awareness**: Missing requirements, conditionals, measurements
- **Scattered processing**: Multiple passes over content instead of intelligent targeting
- **Terminology confusion**: "Conversion/Extraction" vs desired "Markdown/Semantic Fact Extraction"

---

## Future State Architecture

### Enhanced Pipeline Flow

```
INPUT DOCUMENT
      ↓
  MARKDOWN CONVERSION (mvp-hyper-core.py)
  • Convert to markdown format
  • Target: 700+ pages/sec
      ↓
  ENHANCED CLASSIFICATION (mvp-hyper-classification-enhanced.py) 
  • Document types & domains
  • Universal entity extraction (spaCy NLP)
  • Structural pattern identification 
  • Authority/citation detection
  • Target: 1200-1500 pages/sec
      ↓
  ENRICHMENT (mvp-hyper-tagger.py - enhanced)
  • Domain-specific deep extraction
  • Targeted processing using classification roadmap
  • Target: 2000+ pages/sec (boosted by pre-identification)
      ↓
  SEMANTIC FACT EXTRACTION (mvp-hyper-semantic.py)
  • Structured fact extraction
  • Relationship building
  • JSON output generation
  • Target: 500+ pages/sec (boosted by pre-identification)
```

### Enhanced Classification Components

#### 1. Universal Entity Extraction (spaCy NLP)
```python
# Entities to extract using spaCy NER-only pipeline
SPACY_ENTITIES = {
    'PERSON': 'Individual names',
    'ORG': 'Organizations and companies', 
    'GPE': 'Geopolitical entities (places)',
    'MONEY': 'Monetary values',
    'DATE': 'Date and time references',
    'CARDINAL': 'Numbers and quantities',
    'QUANTITY': 'Measurements with units'
}
```

#### 2. Structural Pattern Extraction (Fast Regex)
```python
UNIVERSAL_PATTERNS = {
    'requirements': r'\b(must|shall|required to|should|will|cannot|may not)\s+([^.!?]{15,100})',
    'conditionals': r'\b(if|when|unless|provided that|in case)\s+([^,]{10,60})', 
    'measurements': r'(\d+(?:\.\d+)?)\s*(percent|%|dollars?|\$|hours?|days?|years?|times?)',
    'headers': r'^#{1,6}\s+(.+)$',
    'lists': r'^\s*[-*•]\s+(.+)$',
    'authorities': r'\b(CFR|USC|ISO|ANSI|NFPA|OSHA)\s+\d+(?:[-.]?\d+)*',
    'references': r'\b(?:see|refer to|according to|pursuant to)\s+([^.]{10,50})'
}
```

#### 3. Enhanced Output Format
```yaml
---
# Existing fast classification
document_types: [safety: 50%, financial: 38%, general: 12%]
domains: [safety: 50%, finance: 25%, general: 25%]
keywords: body, location, paragraph, document, doclaynet, annotation
topics: system architecture, implementation, performance, testing

# Enhanced universal entities
universal_entities:
  persons: [John Smith, Dr. Johnson, Large Human]
  organizations: [IBM, OSHA, Department of Labor]
  locations: [California, New York, Washington]
  emails: [contact@company.com, bpf@zurich.ibm.com]
  dates: [2023-01-15, 0/22/08]
  money: [$1.2 million, $500,000]

# Structural intelligence 
structural_patterns:
  requirements: ["must comply with safety standards", "shall provide adequate protection"]
  conditionals: ["if the employee is exposed", "when working at height"]
  measurements: ["50 percent", "8 hours", "30 days"]
  authorities: ["OSHA 1926.95", "CFR 1910.132", "ISO 9001"]
  
# Performance metadata
classification_stats:
  processing_time: 0.024s
  entities_found: 15
  patterns_matched: 8
  confidence: 0.87
---
```

---

## Performance Specifications

### Target Performance by Phase

| Phase | Current | Enhanced | Target | Strategy |
|-------|---------|----------|---------|----------|
| Markdown | 700+ pages/sec | - | 700+ pages/sec | No change |
| Classification | 2000+ pages/sec | 1200-1500 pages/sec | 1000+ pages/sec | spaCy NLP + optimized regex |
| Enrichment | 1500+ pages/sec | 2000+ pages/sec | 1500+ pages/sec | Targeted by classification |
| Semantic | 300+ pages/sec | 500+ pages/sec | 300+ pages/sec | Pre-identified spans |

### Performance Optimization Strategies

#### Classification Phase
- **spaCy NLP optimization**: NER-only pipeline with disabled parser/tagger/lemmatizer
- **Pre-compiled regex patterns**: All patterns compiled at initialization
- **Content chunking**: Process in 10KB chunks for memory efficiency
- **Early filtering**: Skip very short documents (< 100 words)

#### Enrichment Phase Boost
- **Targeted processing**: Focus on pre-identified entity spans
- **Pattern prioritization**: Process high-confidence structural patterns first
- **Domain routing**: Route to specialized processors based on classification

#### Semantic Phase Boost  
- **High-value span processing**: Focus on pre-identified requirements, conditionals, authorities
- **Entity relationship shortcuts**: Use pre-classified entity types
- **Fact validation acceleration**: Pre-identified authority sources

### Fallback Strategy
If enhanced classification drops below 1000 pages/sec:
- **Hybrid mode**: Use enhanced extraction only on documents < 5KB
- **Sampling mode**: Extract entities from first 2KB of content only
- **Graceful degradation**: Fall back to existing simple entity extraction

---

## File Architecture & Implementation Strategy

### Minimal File Changes Approach

#### New Files to Create
```
mvp-hyper/
├── FutureState.md                           # This architecture document
├── mvp-hyper-classification-enhanced.py     # New enhanced classifier
└── test-enhanced-classification.py          # Performance testing script
```

#### Files to Modify (Minimally)
```
mvp-hyper/
├── mvp-hyper-pipeline-clean.py             # Update step_classification() method
└── mvp-hyper-pipeline-clean-config.yaml    # Add enhanced classification config
```

#### Files to Keep Unchanged (Backwards Compatibility)
```
mvp-hyper/
├── mvp-hyper-core.py                       # Markdown conversion (no changes)
├── mvp-hyper-tagger.py                     # Existing tagger (fallback)
├── mvp-hyper-semantic.py                   # Semantic extraction (enhanced by classification)
└── config.yaml                             # Existing config (preserved)
```

### Integration Strategy

#### Phase 1: Enhanced Classifier Creation
```python
# mvp-hyper-classification-enhanced.py
class EnhancedMVPClassifier:
    def __init__(self, enable_spacy=True, enable_structural=True):
        # Initialize spaCy NLP (NER-only)
        self.nlp = spacy.load("en_core_web_sm")
        self.nlp.disable_pipes(["parser", "tagger", "lemmatizer"])
        
        # Pre-compile regex patterns
        self.structural_patterns = self._compile_patterns()
        
        # Initialize existing tagger for fallback
        self.fallback_tagger = MVPHyperTagger()
    
    def classify_document(self, file_path, content):
        # 1. Run existing fast classification
        base_classification = self._get_base_classification(content)
        
        # 2. Add spaCy universal entities  
        universal_entities = self._extract_spacy_entities(content)
        
        # 3. Add structural patterns
        structural_patterns = self._extract_structural_patterns(content)
        
        # 4. Combine and return enhanced metadata
        return self._combine_results(base_classification, universal_entities, structural_patterns)
```

#### Phase 2: Pipeline Integration
```python
# mvp-hyper-pipeline-clean.py (step_classification method update)
def step_classification(self, input_path: str, output_path: str) -> bool:
    """Step 2: Enhanced classification with universal entity extraction."""
    
    try:
        # Try enhanced classifier first
        enhanced_classifier = EnhancedMVPClassifier()
        return self._run_enhanced_classification(enhanced_classifier, input_path, output_path)
    except Exception as e:
        print(f"⚠️  Enhanced classification failed: {e}")
        print("🔄 Falling back to standard classification...")
        # Fallback to existing tagger
        return self._run_standard_classification(input_path, output_path)
```

#### Phase 3: Configuration Enhancement
```yaml
# mvp-hyper-pipeline-clean-config.yaml
pipeline:
  classification:
    enhanced_mode: true
    spacy_model: "en_core_web_sm" 
    enable_structural_patterns: true
    performance_target: 1000  # pages/sec minimum
    fallback_on_failure: true
    
  performance_targets:
    markdown: 700
    classification: 1000  # Reduced from 2000 for enhanced features
    enrichment: 1500     # Expected boost from pre-identification
    semantic: 300        # Expected boost from pre-identification
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- ✅ Create FutureState.md architecture document
- 🔄 Implement mvp-hyper-classification-enhanced.py
- 🔄 Create test-enhanced-classification.py for benchmarking
- 🔄 Basic spaCy NLP integration with entity extraction

### Phase 2: Enhancement (Week 2)  
- 🔄 Add structural pattern extraction (requirements, conditionals, measurements)
- 🔄 Add authority/citation pattern detection
- 🔄 Implement enhanced output format
- 🔄 Performance optimization and tuning

### Phase 3: Integration (Week 3)
- 🔄 Update mvp-hyper-pipeline-clean.py with enhanced classification
- 🔄 Add fallback mechanism for backwards compatibility
- 🔄 Update configuration files
- 🔄 End-to-end testing and performance validation

### Phase 4: Validation (Week 4)
- 🔄 Comprehensive performance benchmarking
- 🔄 Compare enhanced vs standard classification outputs
- 🔄 Validate enrichment and semantic phase improvements
- 🔄 Documentation and deployment preparation

---

## Success Criteria

### Performance Benchmarks
- ✅ **Classification**: Maintain 1000+ pages/sec with enhanced features
- ✅ **Overall Pipeline**: Net performance improvement despite slower classification
- ✅ **Memory Usage**: No significant increase in memory footprint
- ✅ **Accuracy**: Improved entity classification and structural awareness

### Quality Improvements
- ✅ **Structured Entities**: Clear separation of persons, organizations, locations
- ✅ **Semantic Roadmap**: Pre-identified high-value content areas for downstream processing
- ✅ **Universal Patterns**: Non-domain specific structural intelligence
- ✅ **Authority Recognition**: Automatic detection of standards, regulations, citations

### Architectural Goals
- ✅ **Minimal Disruption**: Maximum 3 files modified, existing system preserved
- ✅ **Clean Separation**: Enhanced features in dedicated, properly-named components
- ✅ **Backwards Compatibility**: Graceful fallback to existing functionality
- ✅ **Maintainability**: Well-documented, testable, modular code

---

## Risk Mitigation

### Performance Risks
- **Risk**: Enhanced classification too slow
- **Mitigation**: Hybrid processing mode, content sampling, fallback system

### Integration Risks  
- **Risk**: Breaking existing pipeline
- **Mitigation**: Minimal file changes, comprehensive fallback mechanism

### Quality Risks
- **Risk**: Reduced accuracy with faster processing
- **Mitigation**: Extensive testing, confidence scoring, validation against current outputs

---
