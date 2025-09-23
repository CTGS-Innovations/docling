# spaCy Testing Framework for MVP-Fusion

## Directory Structure

### `focused_entity_extraction/` - **CURRENT WORKING FOLDER**
**Purpose**: Testing spaCy's core strengths (PERSON, ORG, GPE, LOC extraction)
**Focus**: Pure entity detection without semantics or relationships

**Files**:
- `focused_entity_extraction.py` - Main test script for PERSON/ORG/GPE/LOC extraction
- `test_document.md` - Clean markdown test document (12,873 characters)
- `spacy_focused_entities.yaml/json` - spaCy extraction results (92 entities)
- `ac_baseline_entities.yaml/json` - AC automaton baseline (failed to load)
- `entity_quality_comparison.yaml/json` - Quality analysis and comparison

**Key Results**:
- PERSON: 96.0% detection accuracy (24/25 entities found)
- ORG: 70.0% detection accuracy (21/30 entities found)  
- GPE: 62.5% detection accuracy (5/8 entities found)
- LOC: 0.0% detection accuracy (0/19 entities found)
- Performance: 308ms for 92 entities

### `comprehensive_analysis/` - **ARCHIVED**
**Purpose**: Complete spaCy capability testing (all features)
**Focus**: Full spectrum analysis including semantics, relationships, and rules

**Files**:
- `complete_spacy_analysis_TMP.py` - Comprehensive test script
- `complete_results.json` - Full extraction results (16MB)
- `raw_entities.yaml/json` - Raw entity extraction
- `normalized_entities.yaml/json` - Normalized entities
- `linguistics.yaml/json` - Linguistic analysis
- `relationships.yaml/json` - Relationship extraction (15MB)
- `semantic_rules.yaml/json` - Semantic rule extraction
- `performance.yaml/json` - Performance metrics
- `analysis_report.md` - Summary report

### `archived_tests/` - **UTILITIES**
**Purpose**: Supporting utilities and experimental code

**Files**:
- `format_converter_TMP.py` - Convert spaCy output to MVP-Fusion format
- `run_spacy_analysis.sh` - Shell script runner

## Testing Methodology

### Focused Entity Extraction (Current)
1. **Optimized spaCy Configuration**:
   ```python
   spacy.require_cpu()
   nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
   ```

2. **Target Entity Types**: PERSON, ORG, GPE, LOC only
3. **No Semantics**: Pure entity detection without relationships
4. **Quality Validation**: Ground truth comparison with expected entities
5. **Format Consistency**: MVP-Fusion compatible span notation

### Key Findings
- **spaCy excels at PERSON detection** (96% accuracy)
- **Strong ORG detection** (70% accuracy) 
- **Weak LOC detection** (0% accuracy)
- **Potential hybrid approach**: spaCy for PERSON/ORG + AC for LOC

## Recommendations
1. **Integrate spaCy for PERSON extraction** - 96% accuracy justifies implementation
2. **Consider spaCy for ORG extraction** - 70% accuracy could supplement AC
3. **Avoid spaCy for LOC extraction** - 0% accuracy, use AC automaton instead
4. **Focus on core strengths** - Don't use spaCy for semantic analysis or relationships

## Usage
```bash
cd /home/corey/projects/docling/mvp-fusion
source .venv-clean/bin/activate
python spacy_testing/focused_entity_extraction/focused_entity_extraction.py
```