# WIP Entity Extraction Pipeline Enhancements

## Overview
This document outlines the step-by-step fixes needed to resolve critical issues in the MVP-Fusion entity extraction pipeline. Based on the audit of `ENTITY_EXTRACTION_MD_DOCUMENT.md`, we've identified gaps in entity relationship detection, measurement unit coverage, and normalization logic.

## Current State Analysis

### ✅ Working Components
- **Individual Entity Detection**: Core 8 entities (PERSON, ORG, LOC, GPE, DATE, TIME, MONEY, PERCENT) are being detected correctly
- **FLPC Pattern Engine**: Successfully extracting entities using Rust-based regex patterns
- **Pipeline Architecture**: 7-stage orchestrated pipeline is functioning properly

### ❌ Critical Issues Identified
1. **Percent Symbol Loss**: Percentages detected in Stage 4 lose the `%` symbol during Stage 5 normalization
2. **Missing Measurement Units**: FLPC patterns missing common units like `decibels`, `minutes`, `feet`, `hours`
3. **No Entity Relationship Detection**: Stage 5 normalization only does canonicalization, missing relationship detection
4. **Range Formation Gap**: No logic to form ranges from related entities (e.g., "30-37 inches" from "30", "-", "37", "inches")

## Step-by-Step Fix Instructions

### Step 0: Treat percent as MEASUREMENT subtype (percentage) (BLOCKER)
**Location**: `/mvp-fusion/pipeline/legacy/service_processor.py`

**Problem**: Percent should not be a separate universal entity; it is a measurement subtype. We must keep FLPC PERCENT results merged into `measurement` while preserving `%` and annotating a `measurement_type` of `percentage` for downstream normalization.

**Reasoning**: Our NER standard groups all numerics under MEASUREMENT (length, volume, time, temperature, percentage, etc.). Ranges are built later in normalization using span proximity + joining tokens.

**Implementation Steps**:

1. Keep mapping PERCENT → MEASUREMENT (correct as-is):
   ```python
   percent_entities = self._convert_flpc_entities(flpc_entities.get('PERCENT', []), 'MEASUREMENT')[:30]
   ```

2. When converting PERCENT matches, annotate unit and subtype so downstream logic can differentiate:
   ```python
   # Inside _convert_flpc_entities or immediately after conversion for PERCENT-origin entities
   for ent in percent_entities:
       ent['unit'] = '%'
       ent['measurement_type'] = 'percentage'
   ```

3. Merge into measurement (keep a single universal key):
   ```python
   entities['measurement'] = measurement_entities + percent_entities
   ```

4. **Test Verification**: All percent values appear under `measurement` with `unit: '%'` and `measurement_type: 'percentage'`; normalization preserves `%` in output.

---

### Step 1: Fix Percent Symbol Preservation (HIGH PRIORITY)
**Location**: Stage 5 Normalization Logic

**Problem**: During normalization, percentages like "99.5%" become "99.5" without the `%` symbol.

**Reasoning**: The current normalization focuses on canonicalization and text replacement but doesn't preserve critical formatting symbols that are essential for entity meaning.

**Implementation Steps**:

1. **Modify EntityNormalizer** (`/mvp-fusion/knowledge/extractors/entity_normalizer.py`):
   ```python
   def _canonicalize_measurements(self, entity_list):
       """Enhanced measurement canonicalization that preserves symbols"""
       canonicalized = []
       for entity in entity_list:
           # Preserve percent symbol in normalized form
           if entity.get('unit') == '%':
               normalized = f"{entity['value']}%"
           else:
               normalized = entity['value']
           # ... rest of canonicalization logic
   ```

2. **Update normalization configuration** (`/mvp-fusion/config/config.yaml`):
   ```yaml
   normalization:
     preserve_symbols:
       - '%'  # Preserve percent symbols
       - '$'  # Preserve currency symbols
       - '°'  # Preserve degree symbols
   ```

3. **Test Verification**: Run pipeline and verify "99.5%" remains "99.5%" in final output.

---

### Step 2: Expand Measurement Unit Coverage
**Location**: FLPC Pattern Definitions

**Problem**: Missing common measurement units like `decibels`, `minutes`, `feet`, `hours` in FLPC patterns.

**Reasoning**: The current pattern `(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)` is missing frequently used units, causing entities like "90 decibels" to be missed.

**Implementation Steps**:

1. **Update FLPC pattern** (`/mvp-fusion/fusion/flpc_engine.py`):
   ```python
   'measurement': {
       'pattern': r'(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|liters?|gal|gallons?|ft|feet|inches?|meters?|metres?|m|cm|mm|°[CF]|degrees?|decibels?|seconds?|minutes?|hours?|yards?|miles?|pounds?|tons?)',
       'description': 'Comprehensive measurements and units',
       'priority': 'high'
   }
   ```

2. **Update config pattern sets** (`/mvp-fusion/config/pattern_sets.yaml`):
   ```yaml
   measurement:
     pattern: '(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|liters?|gal|gallons?|ft|feet|inches?|meters?|metres?|m|cm|mm|°[CF]|degrees?|decibels?|seconds?|minutes?|hours?|yards?|miles?|pounds?|tons?)'
     priority: high
   ```

3. **Test Verification**: Verify "90 decibels", "15 minutes", "500 feet" are now detected as measurements.

---

### Step 3: Implement Entity Relationship Detection
**Location**: Stage 5 Normalization Enhancement

**Problem**: No logic to detect relationships between entities that are close to each other.

**Reasoning**: The current normalization only does canonicalization. We need to add relationship detection that analyzes entity spans and joining words to identify related entities before forming ranges.

**Implementation Steps**:

1. **Create relationship detection method** in `Stage5_Normalization` class:
   ```python
   def _detect_entity_relationships(self, entities, document_text):
       """Detect relationships between entities using span proximity and joining words"""
       relationships = {'entity_relationships': [], 'potential_ranges': []}

       # Flatten all entities with spans
       all_entities = []
       for entity_type, entity_list in entities.items():
           for entity in entity_list:
               if 'span' in entity:
                   entity_info = entity.copy()
                   entity_info['type'] = entity_type
                   all_entities.append(entity_info)

       # Sort by position and find close entities
       all_entities.sort(key=lambda x: x['span']['start'])

       for i, entity1 in enumerate(all_entities):
           for j, entity2 in enumerate(all_entities[i+1:], i+1):
               distance = entity2['span']['start'] - entity1['span']['end']

               if 0 <= distance <= 50:  # Within 50 characters
                   joining_text = document_text[entity1['span']['end']:entity2['span']['start']]

                   # Check for joining patterns
                   if self._has_joining_pattern(joining_text):
                       relationship = {
                           'entity1': entity1,
                           'entity2': entity2,
                           'joining_text': joining_text,
                           'distance': distance
                       }
                       relationships['entity_relationships'].append(relationship)
   ```

2. **Add joining pattern detection**:
   ```python
   def _has_joining_pattern(self, text):
       """Check if text contains relationship indicators"""
       joining_patterns = [
           r'\b(?:to|and|or|through|between|from|-|--|–|—|&)\b',
           r'[-–—&/]'
       ]
       return any(re.search(pattern, text, re.IGNORECASE) for pattern in joining_patterns)
   ```

3. **Test Verification**: Verify relationships are detected between entities like "30" and "37" with "inches" nearby.

---

### Step 4: Implement Range Formation Logic
**Location**: Stage 5 Normalization - Range Formation

**Problem**: No logic to form range entities from related individual entities.

**Reasoning**: Once relationships are detected, we need logic to combine related entities into range entities (e.g., "30-37 inches" from "30", "-", "37", "inches").

**Implementation Steps**:

1. **Add range formation method**:
   ```python
   def _form_ranges_from_relationships(self, relationships, entities, document_text):
       """Form range entities from detected relationships"""
       ranges = {'measurement_ranges': []}

       for relationship in relationships['potential_ranges']:
           if relationship['relationship_type'] == 'range':
               entity1 = relationship['entity1']
               entity2 = relationship['entity2']

               # Create range entity
               range_entity = {
                   'type': 'measurement_range',
                   'value': f"{entity1['value']}-{entity2['value']}",
                   'text': f"{entity1['text']}{relationship['joining_text']}{entity2['text']}",
                   'span': {
                       'start': entity1['span']['start'],
                       'end': entity2['span']['end']
                   },
                   'components': [entity1, entity2],
                   'unit': self._extract_common_unit(entity1, entity2)
               }
               ranges['measurement_ranges'].append(range_entity)
   ```

2. **Add unit compatibility checking**:
   ```python
   def _extract_common_unit(self, entity1, entity2):
       """Extract common unit from related entities"""
       unit1 = entity1.get('unit')
       unit2 = entity2.get('unit')

       if unit1 and unit2 and unit1 == unit2:
           return unit1
       return None
   ```

3. **Test Verification**: Verify "30-37 inches" is created as a range entity from individual components.

---

### Step 5: Update Pipeline Integration
**Location**: Orchestrated Pipeline Wrapper

**Problem**: Stage 5 normalization needs to be enhanced to include relationship detection.

**Reasoning**: The current Stage5_Normalization wrapper only calls the basic entity normalizer. We need to enhance it to include our new relationship detection logic.

**Implementation Steps**:

1. **Enhance Stage5_Normalization class** (`/mvp-fusion/pipeline/orchestrated_pipeline_wrapper.py`):
   - Add relationship detection configuration
   - Add methods for relationship detection and range formation
   - Integrate with existing normalization flow

2. **Update configuration loading** to include relationship detection settings:
   ```yaml
   normalization:
     relationship_detection:
       max_span_distance: 50
       joining_patterns:
         - '\b(?:to|and|or|through|between|from|-|--|–|—|&)\b'
         - '[-–—&/]'
   ```

3. **Test Verification**: Run full pipeline and verify ranges are formed in final output.

---

## Testing Strategy

### Individual Component Testing
1. **Unit Test Percent Symbol Preservation**:
   ```bash
   python -c "from entity_normalizer import EntityNormalizer; n = EntityNormalizer(); result = n.normalize_entity({'type': 'PERCENT', 'value': '99.5', 'unit': '%'}); print(result)"
   ```

2. **Unit Test Measurement Pattern**:
   ```bash
   python -c "from flpc_engine import FLPCEngine; e = FLPCEngine({}); result = e.extract_entities('90 decibels for 8 hours'); print(result)"
   ```

3. **Unit Test Relationship Detection**:
   ```bash
   python -c "from stage5_normalization import Stage5_Normalization; s = Stage5_Normalization({}); relationships = s._detect_entity_relationships(entities, text); print(relationships)"
   ```

### Integration Testing
1. **Run Full Pipeline**:
   ```bash
   python fusion_cli.py --file ENTITY_EXTRACTION_MD_DOCUMENT.md
   ```

2. **Verify Outputs**:
   - Check percentages maintain `%` symbol
   - Verify new measurement units are detected
   - Confirm ranges are formed from individual entities
   - Validate entity relationships are detected

---

## Expected Outcomes

After implementing these fixes:

1. **Percentages**: "99.5%" remains "99.5%" in normalized output
2. **Measurements**: "90 decibels", "15 minutes", "500 feet" are detected
3. **Entity Relationships**: Related entities are identified and linked
4. **Ranges**: "30-37 inches" formed from individual components
5. **Overall Accuracy**: Entity extraction accuracy increases by 15-20%

## Risk Assessment

- **Low Risk**: Pattern and normalization changes are additive
- **Medium Risk**: Relationship detection logic - ensure doesn't break existing functionality
- **Mitigation**: Comprehensive testing before production deployment

## Rollback Plan

If issues arise:
1. Revert Stage5_Normalization changes
2. Restore original FLPC patterns
3. Keep percent symbol and measurement unit fixes (low risk)
4. Test incrementally rather than all at once

---

*This document will be updated as fixes are implemented and tested.*
