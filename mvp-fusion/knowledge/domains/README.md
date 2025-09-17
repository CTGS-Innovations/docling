# Domain Classification Patterns

## Purpose

Domain classification determines **WHAT** the document content is about. This routes intelligence to the appropriate SaaS vertical specialists and MVP development teams within Scout's platform.

## Domain Architecture

### 16-Domain Framework

#### Market Intelligence (1-9)
**Purpose**: Route to SaaS vertical specialists
- `healthcare.yaml` - Medical, clinical, pharmaceutical intelligence
- `fintech.yaml` - Banking, payments, financial services
- `legal.yaml` - Law, compliance, intellectual property
- `ecommerce.yaml` - Retail, marketplace, commerce
- `manufacturing.yaml` - Industrial, operations, safety
- `education.yaml` - Academic, training, learning platforms
- `social_media.yaml` - Platforms, content, engagement
- `startup_venture.yaml` - Company operations, business development
- `enterprise.yaml` - B2B SaaS, corporate solutions

#### Entrepreneurial Intelligence (10-12)
**Purpose**: Core opportunity discovery for MVP development
- `pain_points.yaml` - User frustrations, unmet needs, broken workflows
- `innovation.yaml` - Emerging trends, new technologies, market opportunities
- `capital_markets.yaml` - Complete funding ecosystem (VC, PE, angels, grants)

#### Strategic Intelligence (13-16)
**Purpose**: Market dynamics and competitive landscape analysis
- `competitive.yaml` - Existing solutions, pricing, feature gaps, market positioning
- `regulatory.yaml` - Domain-specific regulations affecting MVP viability
- `customer_acquisition.yaml` - Marketing channels, growth strategies, CAC analysis
- `mergers_acquisitions.yaml` - M&A activity, market consolidation, landscape shifts

## YAML Structure Standards

### File Format
```yaml
# Domain Name: Brief description
# Purpose statement for Scout platform

category_name:
  weight: 2.5  # Domain importance (1.0-4.0)
  keywords:
    "exact phrase": 4.0    # Highest confidence
    "common term": 3.0     # High confidence  
    "related word": 2.0    # Medium confidence
    "context clue": 1.5    # Lower confidence

another_category:
  weight: 2.0
  keywords:
    # More patterns...
```

### Weight Guidelines

#### Domain Weight (category level)
- **3.0-4.0**: Core domain concepts (definitive classification)
- **2.0-2.9**: Important domain areas (strong indicators)
- **1.5-1.9**: Supporting concepts (contextual clues)
- **1.0-1.4**: General terms (weak indicators)

#### Keyword Weight (individual terms)
- **4.0**: Definitive domain identifiers (technical jargon, specific processes)
- **3.0-3.5**: Strong domain indicators (common industry terms)
- **2.0-2.9**: Moderate indicators (broader professional terms)
- **1.5-1.9**: Contextual clues (general business terms)
- **1.0-1.4**: Weak signals (very general terms)

## Pattern Design Principles

### 1. Distinctive Patterns
- Each domain should have **unique identifier keywords**
- Avoid overlap with other domains where possible
- Use domain-specific jargon and technical terms

### 2. Comprehensive Coverage
- Include **formal terminology** (medical record, financial statement)
- Include **informal language** (pain points, user complaints)  
- Include **acronyms and abbreviations** (HIPAA, SEC, API)

### 3. Scalable Structure
- Organize keywords into logical categories
- Use consistent naming conventions
- Balance specificity with coverage

### 4. Performance Optimization
- Prioritize high-frequency, high-confidence terms
- Avoid overly broad terms that dilute precision
- Target 20-50 keywords per category for optimal performance

## Example Patterns

### Healthcare Domain
```yaml
# Healthcare - Medical, clinical, pharmaceutical intelligence
# Routes to healthcare SaaS specialists for medical MVP opportunities

clinical:
  weight: 3.0
  keywords:
    "medical record": 4.0
    "patient": 3.5
    "diagnosis": 3.5
    "clinical": 3.0
    "healthcare": 2.5

regulatory_medical:
  weight: 2.5
  keywords:
    "hipaa": 4.0
    "phi": 3.5
    "protected health information": 4.0
    "medical privacy": 3.0
```

### Pain Points Domain  
```yaml
# Pain Points - User frustrations and unmet needs
# Core entrepreneurial intelligence for MVP opportunity discovery

frustration:
  weight: 3.5
  keywords:
    "frustrated": 4.0
    "hate that": 3.5
    "drives me crazy": 4.0
    "can't stand": 3.0
    "annoying": 3.0

unmet_needs:
  weight: 4.0
  keywords:
    "wish there was": 4.0
    "someone should build": 4.0
    "why doesn't exist": 4.0
    "need a tool that": 3.5
    "looking for something": 3.0
```

## Expansion Guidelines

### Adding New Domains

1. **Market Research**: Identify emerging SaaS verticals with MVP potential
2. **Pattern Collection**: Gather domain-specific terminology and language patterns
3. **Category Design**: Organize into 3-7 logical categories per domain
4. **Weight Calibration**: Test with real content to optimize weights
5. **Integration Testing**: Ensure non-overlapping classification with existing domains

### Domain Validation Process

1. **Content Testing**: Test with 10+ representative documents
2. **Confidence Analysis**: Ensure >70% classification confidence
3. **Overlap Check**: Verify minimal overlap with existing domains  
4. **Performance Testing**: Confirm <50ms classification times
5. **Business Validation**: Confirm alignment with Scout's MVP strategy

### Naming Conventions

- **File names**: `{domain_name}.yaml` (lowercase, underscores)
- **Category names**: `{descriptive_name}` (lowercase, underscores)
- **Comments**: Include purpose and Scout platform context

## Integration with Scout Platform

### AI Agent Routing
```python
# Domain classification determines specialist routing
if domain == "healthcare":
    route_to_healthcare_mvp_team(document)
elif domain == "pain_points":
    route_to_opportunity_pipeline(document)
elif domain == "innovation":
    route_to_trend_analysis_team(document)
```

### MVP Development Pipeline
1. **Domain Classification** → Specialist Team Assignment
2. **Document Analysis** → Market Intelligence Extraction  
3. **Opportunity Scoring** → MVP Prioritization
4. **Development Routing** → MVP Implementation Team

## Performance Considerations

### Aho-Corasick Optimization
- **Linear scaling**: Performance scales linearly with pattern count
- **Memory efficiency**: Shared automaton across all domains
- **Fast matching**: Sub-millisecond pattern matching

### Pattern Efficiency
- **Keyword density**: 20-50 keywords per category optimal
- **Weight distribution**: Balance high/low weights for precision
- **Category balance**: 3-7 categories per domain ideal

## Quality Assurance

### Testing Requirements
- Test each domain with diverse content samples
- Validate classification confidence scores
- Check for false positives with other domains
- Monitor processing time impact

### Maintenance Guidelines
- Review patterns quarterly for emerging terminology
- Update weights based on classification performance
- Add new categories as markets evolve
- Remove outdated or ineffective patterns

---

**Remember**: Domain classification is the first intelligence filter for Scout's MVP development platform. Precise domain routing enables targeted entrepreneurial intelligence extraction across all SaaS verticals.