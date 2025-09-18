# Entity Extraction Debugging Session Notes
*Session Date: 2025-09-18*

## Where We Were

### Major Issues Identified and Fixed
1. **✅ Pipeline Stage Configuration Bug** - CLI `--file` and `--directory` weren't running all 4 stages (convert → classify → enrich → extract)
2. **✅ Empty Fact Data Pollution** - Hundreds of empty semantic facts with no content polluting JSON output
3. **✅ Location Misclassification** - People names appearing as cities ("Bin Wang" as city), technical terms as locations
4. **✅ Useless Name Regurgitation** - People sections with just names, no roles/organizations/context
5. **✅ Sentence Boundary Context** - Context extraction using character windows instead of complete sentences
6. **✅ Dual Pipeline Validation Gap** - Validation applied to enrichment flow but not classification flow

### Root Architecture Problem Discovered
**Two Separate Data Flows** with inconsistent validation:
- **Enrichment Flow** (had validation) → JSON semantic facts  
- **Classification Flow** (no validation) → Markdown YAML

## Current Problem: Role Extraction Failure

### The Mary Johnson Case Study
**Text**: `"Mary Johnson, Director of Engineering, will present at conference..."`

**Current Output** (broken):
```yaml
people:
  - name: Mary Johnson
    role: director  # Missing "of Engineering" part
```

**Expected Output**:
```yaml
people:
  - name: Mary Johnson
    role: "Director of Engineering"
    organization: "Global Dynamics Corporation"
    context: "Mary Johnson, Director of Engineering, will present at conference..."
```

### Root Cause: Missing Transitional Connectors
Role extraction patterns are **word-boundary focused** and miss **multi-word phrases with prepositions**:

**Missing Connectors:**
- "Director **of** Engineering"  
- "VP **of** Operations"
- "works **at** TechCorp"
- "reports **to** manager"
- "Chief **Medical** Officer"

## What We Were About to Fix

### Two-Span Strategy Implementation
We identified need for **different span strategies** for different purposes:

1. **Context Spans** (±200 chars, sentence boundaries)
   - Purpose: Human-readable context
   - Current: ✅ Working (fixed earlier)

2. **Connector Spans** (±20-50 words, word boundaries) 
   - Purpose: Extract structured relationships
   - Current: ❌ **THIS IS WHAT NEEDS TO BE FIXED**

### Next Steps (Priority Order)

#### 1. Fix Role Extraction Patterns
**File**: `/knowledge/extractors/comprehensive_entity_extractor.py`
**Method**: `_extract_role_from_context()`

**Current Broken Patterns**:
```python
r'(?:director|manager|supervisor)'  # Only finds "director"
```

**Needs to Become**:
```python
r'(?:director|manager|supervisor)(?:\s+of\s+\w+)?'  # Finds "director of engineering"
```

#### 2. Add Universal Transitional Connector Detection
**Apply to ALL entity types** (not just people):
- PERSON: "Mary Johnson" + "Director of" + "Engineering"
- ORG: "TechCorp" + "acquired" + "StartupInc"  
- LOCATION: "San Francisco" + "headquarters of" + "TechCorp"

#### 3. Implement Connector Span Strategy
Create new method for relationship detection:
```python
def _extract_entity_relationships(self, entity, text):
    # Use tight connector spans (±20-50 words)
    # Look for transitional words that link entities
    # Build structured relationships
```

#### 4. Test Pipeline with Mary Johnson Case
Verify that after fixes:
- Role extraction captures "Director of Engineering" (not just "director")
- Organization extraction finds "Global Dynamics Corporation"
- Temporal relationships captured ("from 2020-2023")

## Files Modified This Session
- `/pipeline/fusion_pipeline.py` - Added domain entity validation
- `/knowledge/extractors/comprehensive_entity_extractor.py` - Added quality gates and context validation
- `/knowledge/extractors/semantic_fact_extractor.py` - Fixed empty fact filtering
- `/knowledge/corpus/geographic_data.py` - Improved location classification
- `/fusion_cli.py` - Fixed CLI to use full pipeline instead of extractor-only

## Technical Debt to Address
- Multiple role extraction methods (need to consolidate)
- Inconsistent validation across different code paths
- Hard-coded entity lists that should use centralized reference data

## Success Metrics for Next Session
- Mary Johnson shows complete role: "Director of Engineering"
- No people names appearing in locations section
- No empty facts in JSON output
- All entities have meaningful context or get filtered out

---
*Resume here: Focus on fixing transitional connector patterns in role extraction*