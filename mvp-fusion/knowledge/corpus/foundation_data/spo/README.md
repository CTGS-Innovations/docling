# SPO Predicate Dictionary - AC Pattern Library

## Overview
This directory contains **Aho-Corasick (AC) pattern dictionaries** for high-performance Subject-Predicate-Object (SPO) fact extraction. Each file contains curated predicate patterns optimized for exact string matching with O(1) lookup performance.

## File Structure

### Core Predicate Categories
- **`state_predicates.txt`** - Being, existence, and state relationships (is, was, became, etc.)
- **`ownership_predicates.txt`** - Ownership, control, and possession relationships  
- **`location_predicates.txt`** - Spatial, geographic, and positioning relationships
- **`relationship_predicates.txt`** - Personal, social, and professional relationships
- **`business_predicates.txt`** - Commercial, corporate, and market relationships

### Specialized Categories  
- **`legal_regulatory_predicates.txt`** - Legal actions, compliance, and regulatory relationships
- **`obligations_compliance_predicates.txt`** - Mandatory, permissive, and restrictive relationships
- **`quantitative_performance_predicates.txt`** - Metrics, measurements, and performance relationships
- **`causality_conditions_predicates.txt`** - Causal, conditional, and dependency relationships

## Usage in AC Engine

```python
# Load all SPO predicate dictionaries
spo_predicates = {}
for category in ['state', 'ownership', 'location', 'relationship', 'business', 
                'legal_regulatory', 'obligations_compliance', 
                'quantitative_performance', 'causality_conditions']:
    with open(f'spo/{category}_predicates.txt', 'r') as f:
        spo_predicates[category] = [line.strip() for line in f 
                                   if line.strip() and not line.startswith('#')]

# Add to AC automaton
for category, predicates in spo_predicates.items():
    for predicate in predicates:
        ac_engine.add_pattern(predicate, pattern_type='predicate', category=category)
```

## Performance Characteristics

- **Lookup Speed**: O(1) per pattern using Aho-Corasick automaton
- **Memory Efficiency**: Shared state machine for all patterns
- **Coverage**: 90%+ of common predicate relationships
- **Scalability**: Linear O(n) with text length, constant with pattern count

## Pattern Guidelines

### Exact Matching Only
- All patterns are exact string matches (not regex)
- Case-sensitive matching for consistency
- No wildcards or variable substitution

### Multi-word Predicates
- Include common multi-word predicates: "works at", "based in", "married to"
- Maintain consistency in spacing and formatting
- Prioritize high-frequency combinations

### Coverage Strategy
- **90% AC Coverage**: Common, high-frequency exact patterns
- **10% FLPC Coverage**: Complex patterns requiring flexibility handled separately

## Integration with FLPC

While AC handles exact predicate matching, FLPC patterns complement this with:
- Flexible tense variations: `r'(is|was|are|were)\s+(the\s+)?([A-Z]+)\s+of'`
- Proximity-based relationships: `r'([A-Z][a-z]+)\s+.{0,20}\s+(founded|acquired)\s+([A-Z][a-z]+)'`
- Conditional patterns: `r'if\s+.+?,\s+then\s+([A-Z][a-z]+)\s+(will|must|should)'`

## Maintenance

### Adding New Predicates
1. Identify category based on semantic meaning
2. Add to appropriate `.txt` file
3. Follow existing format (one predicate per line)
4. Test AC performance impact

### Quality Standards
- **High Frequency**: Only include commonly used predicates
- **Exact Match**: Ensure exact string matching works in context
- **No Duplicates**: Avoid redundancy across categories
- **Clear Semantics**: Each predicate should have unambiguous meaning

## Performance Monitoring

Track the following metrics:
- **AC Hit Rate**: Percentage of predicates found via AC vs FLPC
- **Processing Speed**: Time per document for predicate extraction
- **Memory Usage**: AC automaton size with full predicate dictionary
- **Coverage**: Percentage of relationships detected

Target: **90%+ predicate detection via AC**, **<10% requiring FLPC processing**