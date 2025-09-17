# Entity Extraction Patterns

## Purpose

Entity extraction identifies **specific data points** within classified documents. This provides granular intelligence for Scout's MVP development platform, extracting actionable insights from domain-classified content.

## Entity Architecture

### Universal Entities (Layer 4)
Core entities applicable across all domains and document types:
- **People**: founders, investors, executives, customers
- **Organizations**: companies, startups, investors, competitors  
- **Financial**: funding amounts, revenue figures, valuations, costs
- **Geographic**: markets, regions, countries, cities
- **Temporal**: dates, timelines, milestones, deadlines
- **Technology**: platforms, APIs, frameworks, tools

### Domain-Specific Entities (Layer 5)
Specialized entities for deep domain intelligence:
- **Healthcare**: medical conditions, treatments, medications, providers
- **Legal**: case numbers, court systems, legal precedents, regulations
- **Financial**: securities, account types, transaction IDs, market indices
- **Manufacturing**: part numbers, safety codes, equipment models, processes

## YAML Structure Standards

### File Format
```yaml
# Entity Category: Description
# Purpose for Scout's intelligence extraction

entity_category:
  weight: 2.0  # Extraction priority (1.0-4.0)
  patterns:
    - pattern: "regex_pattern"     # Regex for structured data
      weight: 3.0                  # Pattern confidence
      examples: ["example1", "example2"]
  keywords:
    "exact phrase": 3.5           # Keyword-based extraction
    "identifier": 3.0             # Identity markers
    "context_clue": 2.0           # Supporting context
  extraction_rules:
    format: "expected_format"      # Output format specification
    validation: "validation_rule"  # Data validation logic
    context_required: true        # Requires surrounding context
```

### Weight Guidelines

#### Entity Category Weight
- **3.5-4.0**: Critical for MVP development (funding amounts, pain points)
- **2.5-3.4**: Important for market intelligence (companies, technologies)
- **1.5-2.4**: Supporting context (dates, locations, people)
- **1.0-1.4**: General reference information

#### Pattern/Keyword Weight
- **4.0**: Definitive entity identifiers (structured data, exact formats)
- **3.0-3.5**: Strong indicators (formal terminology, standard patterns)
- **2.0-2.9**: Moderate confidence (contextual clues, variations)
- **1.5-1.9**: Supporting evidence (related terms, informal language)

## Entity Categories

### Financial Entities
```yaml
funding_amounts:
  weight: 4.0
  patterns:
    - pattern: "\\$([0-9]+(?:\\.[0-9]+)?(?:[MBK])?)"
      weight: 4.0
      examples: ["$2.5M", "$50K", "$1.2B"]
    - pattern: "([0-9]+(?:\\.[0-9]+)?) million"
      weight: 3.5
      examples: ["2.5 million", "15.7 million"]
  keywords:
    "funding": 3.0
    "investment": 3.0
    "round": 2.5
    "valuation": 3.5
  extraction_rules:
    format: "numeric_with_scale"
    validation: "positive_number"
    context_required: true

company_valuations:
  weight: 3.5
  patterns:
    - pattern: "valued at \\$([0-9]+(?:\\.[0-9]+)?[MBK]?)"
      weight: 4.0
      examples: ["valued at $50M", "valued at $1.2B"]
  keywords:
    "valuation": 4.0
    "worth": 2.5
    "valued at": 3.5
```

### Technology Entities
```yaml
technology_stack:
  weight: 3.0
  keywords:
    "react": 3.0
    "python": 3.0
    "aws": 3.5
    "kubernetes": 3.0
    "api": 2.5
    "microservices": 3.0
  extraction_rules:
    format: "technology_list"
    context_required: false

software_platforms:
  weight: 2.5
  keywords:
    "salesforce": 3.5
    "hubspot": 3.0
    "slack": 3.0
    "notion": 2.5
    "figma": 2.5
```

### Pain Point Entities
```yaml
user_frustrations:
  weight: 4.0
  keywords:
    "frustrated with": 3.5
    "hate": 3.0
    "annoying": 3.0
    "broken": 3.5
    "doesn't work": 3.5
    "slow": 2.5
    "expensive": 2.5
  extraction_rules:
    format: "frustration_statement"
    context_required: true
    
unmet_needs:
  weight: 4.0
  keywords:
    "wish there was": 4.0
    "need a tool": 3.5
    "looking for": 3.0
    "should exist": 3.5
    "missing": 3.0
  extraction_rules:
    format: "need_statement"
    context_required: true
```

### Market Intelligence Entities
```yaml
competitors:
  weight: 3.0
  patterns:
    - pattern: "competitor[s]?:?\\s+([A-Z][a-zA-Z\\s&]+)"
      weight: 3.5
      examples: ["Competitors: Slack & Microsoft Teams"]
  keywords:
    "competitor": 3.5
    "alternative": 2.5
    "similar to": 2.5
    "vs": 2.0

market_size:
  weight: 3.5
  patterns:
    - pattern: "market size.{0,20}\\$([0-9]+(?:\\.[0-9]+)?[MBK]?)"
      weight: 4.0
      examples: ["market size of $50B", "market size: $2.5M"]
  keywords:
    "tam": 3.5
    "total addressable market": 4.0
    "market opportunity": 3.0
```

## Domain-Specific Entity Files

### Healthcare Entities (`healthcare_entities.yaml`)
```yaml
medical_conditions:
  weight: 3.0
  keywords:
    "diabetes": 3.5
    "hypertension": 3.5
    "covid-19": 3.5
    "diagnosis": 3.0

medications:
  weight: 3.0
  patterns:
    - pattern: "([A-Z][a-z]+(?:in|ol|ide|ine))\\s+(?:[0-9]+mg)"
      weight: 3.5
      examples: ["Aspirin 81mg", "Lisinopril 10mg"]
```

### Legal Entities (`legal_entities.yaml`)
```yaml
case_numbers:
  weight: 3.5
  patterns:
    - pattern: "Case No\\.\\s+([0-9-A-Z]+)"
      weight: 4.0
      examples: ["Case No. 2023-CV-1234"]

legal_precedents:
  weight: 3.0
  patterns:
    - pattern: "([A-Z][a-z]+\\s+v\\.\\s+[A-Z][a-z]+)"
      weight: 3.5
      examples: ["Smith v. Jones", "Apple v. Samsung"]
```

## Extraction Pipeline Integration

### Layer 4: Universal Entity Extraction
```python
def extract_universal_entities(content, domain, doc_type):
    """Extract entities applicable across all domains"""
    entities = {}
    
    # Financial entities for investment intelligence
    if any(term in content.lower() for term in ['funding', 'investment', 'revenue']):
        entities['financial'] = extract_financial_entities(content)
    
    # Technology entities for competitive intelligence  
    if any(term in content.lower() for term in ['api', 'platform', 'software']):
        entities['technology'] = extract_technology_entities(content)
        
    # Pain point entities for MVP opportunities
    if domain == 'pain_points':
        entities['frustrations'] = extract_frustration_entities(content)
        
    return entities
```

### Layer 5: Deep Domain Entity Extraction
```python
def extract_domain_entities(content, domain, doc_type):
    """Extract domain-specific entities conditionally"""
    
    if domain == 'healthcare' and doc_type in ['medical_record', 'clinical_note']:
        return extract_medical_entities(content)
    elif domain == 'legal' and doc_type in ['contract', 'legal_memo']:
        return extract_legal_entities(content)
    elif domain == 'capital_markets' and doc_type == 'pitch_deck':
        return extract_investment_entities(content)
    
    return {}
```

## Extraction Rules and Validation

### Format Specifications
- **numeric_with_scale**: `{"value": 2.5, "scale": "M", "raw": "$2.5M"}`
- **technology_list**: `["React", "Node.js", "AWS", "PostgreSQL"]`
- **frustration_statement**: `{"text": "frustrated with slow loading", "intensity": "high"}`
- **company_reference**: `{"name": "Salesforce", "domain": "enterprise", "context": "competitor"}`

### Validation Rules
- **positive_number**: Ensure financial values are positive
- **known_technology**: Validate against technology database
- **company_exists**: Cross-reference against company database
- **date_format**: Ensure dates are properly formatted

### Context Requirements
- **context_required: true**: Entity needs surrounding context for accuracy
- **context_required: false**: Entity can be extracted in isolation
- **minimum_context**: Minimum number of surrounding words needed

## Performance Optimization

### Extraction Efficiency
- **Conditional extraction**: Only extract domain-relevant entities
- **Pattern caching**: Cache compiled regex patterns
- **Batch processing**: Process multiple entities in single pass
- **Early termination**: Stop extraction when confidence threshold met

### Memory Management
- **Lazy loading**: Load entity patterns on demand
- **Pattern sharing**: Share common patterns across domains
- **Result caching**: Cache extraction results for duplicate content

## Quality Assurance

### Validation Process
1. **Pattern testing**: Test regex patterns with diverse content samples
2. **Precision measurement**: Track extraction accuracy rates
3. **Recall analysis**: Ensure comprehensive entity coverage
4. **Performance monitoring**: Monitor extraction time impact

### False Positive Handling
- **Context validation**: Verify entities make sense in context
- **Cross-reference checking**: Validate against known entity databases
- **Confidence thresholding**: Only extract high-confidence entities
- **Human validation**: Sample review of extracted entities

## Integration with Scout Platform

### MVP Opportunity Pipeline
```python
# Pain point entities feed MVP development
pain_entities = extract_entities(content, 'pain_points', 'pain_point_discussion')
for frustration in pain_entities['frustrations']:
    opportunity = {
        'problem': frustration['text'],
        'intensity': frustration['intensity'], 
        'domain': classify_problem_domain(frustration),
        'mvp_potential': score_mvp_potential(frustration)
    }
    add_to_opportunity_pipeline(opportunity)
```

### Competitive Intelligence
```python
# Technology and competitor entities inform market analysis
tech_entities = extract_entities(content, 'enterprise', 'api_documentation')
competitive_landscape = {
    'technologies': tech_entities['technology_stack'],
    'competitors': tech_entities['competitors'],
    'market_position': analyze_competitive_position(tech_entities)
}
```

## Future Enhancements

### Advanced Entity Types
- **Sentiment entities**: Emotional indicators, opinion strength
- **Relationship entities**: Company partnerships, dependencies, integrations
- **Temporal entities**: Project timelines, milestone sequences, deadlines
- **Geographic entities**: Market regions, expansion plans, location strategies

### Machine Learning Integration
- **Named entity recognition**: Use ML models for complex entity extraction
- **Entity linking**: Connect extracted entities to knowledge graphs
- **Context understanding**: Use transformers for context-aware extraction
- **Continuous learning**: Improve extraction based on validation feedback

---

**Remember**: Entity extraction provides the granular intelligence that powers Scout's MVP development decisions. Precise entity identification enables targeted opportunity discovery and competitive analysis across all SaaS verticals.