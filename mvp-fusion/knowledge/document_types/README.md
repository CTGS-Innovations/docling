# Document Type Classification Patterns

## Purpose

Document type classification determines **WHAT KIND** of document is being processed. This determines the appropriate processing pipeline and extraction patterns within Scout's MVP development platform.

## Document Type Architecture

### 211+ Document Types Across 9 Verticals

#### Startup/Venture Ecosystem (16 types)
Investment, legal, and product development documents
- `pitch_deck`, `term_sheet`, `business_plan`, `cap_table`, `mvp_spec`, etc.

#### Social Media & Forum Intelligence (15 types)  
Platform content and community discussions
- `reddit_post`, `twitter_thread`, `pain_point_discussion`, `product_review`, etc.

#### Enterprise B2B (22 types)
Sales, technical, and operational business documents
- `sales_proposal`, `api_documentation`, `security_assessment`, `contract`, etc.

#### Healthcare (25 types)
Clinical, administrative, and research documents
- `medical_record`, `clinical_note`, `lab_report`, `hipaa_document`, etc.

#### Fintech (20 types)
Banking, trading, and financial services documents
- `loan_application`, `credit_report`, `investment_prospectus`, `audit_report`, etc.

#### Legal (25 types)
Contracts, litigation, and intellectual property documents
- `contract`, `nda`, `patent_application`, `legal_memo`, `court_filing`, etc.

#### E-commerce/Retail (23 types)
Product, sales, and customer experience documents
- `product_listing`, `customer_review`, `inventory_report`, `sales_receipt`, etc.

#### Manufacturing (25 types)
Production, safety, and quality management documents
- `work_order`, `safety_procedure`, `quality_control`, `maintenance_log`, etc.

#### Education (25 types)
Academic, training, and assessment documents
- `lesson_plan`, `transcript`, `assignment`, `training_material`, etc.

## YAML Structure Standards

### File Format
```yaml
# Document Type Category: Description
# Purpose for Scout's processing pipeline

document_type_name:
  weight: 2.5  # Type importance (1.0-4.0)
  keywords:
    "exact phrase": 4.0    # Definitive type identifier
    "common pattern": 3.0  # Strong type indicator
    "related term": 2.0    # Supporting evidence
    "context clue": 1.5    # Weak indicator
  entities:  # Optional: specific entity patterns
    entity_category: ["value1", "value2", "value3"]
```

### Weight Guidelines

#### Document Type Weight
- **3.0-4.0**: Mission-critical document types for Scout platform
- **2.0-2.9**: Important business documents 
- **1.5-1.9**: Supporting document types
- **1.0-1.4**: General/reference documents

#### Keyword Weight  
- **4.0**: Definitive document identifiers ("pitch deck", "medical record")
- **3.0-3.5**: Strong type indicators (document structure, format clues)
- **2.0-2.9**: Moderate indicators (professional terminology)
- **1.5-1.9**: Supporting context (general business terms)
- **1.0-1.4**: Weak signals (very general language)

## Pattern Design Principles

### 1. Document Structure Focus
- Target **document format indicators** (headers, sections, structure)
- Include **process-specific language** (application, report, analysis)
- Capture **purpose indicators** (proposal, assessment, review)

### 2. Business Process Alignment
- Map to **actual business workflows** Scout needs to understand
- Include **industry-standard document types** across all verticals
- Cover **informal document types** (posts, discussions, feedback)

### 3. Processing Pipeline Optimization
- Each document type should trigger **specific extraction logic**
- Group related types for **shared processing patterns**
- Enable **routing to appropriate analysis modules**

### 4. Scalability Structure
- **Modular organization** by business vertical
- **Consistent naming conventions** across files
- **Balanced coverage** of high/low volume document types

## Example Patterns

### Startup Document Types
```yaml
pitch_deck:
  weight: 3.0
  keywords:
    "pitch deck": 4.0
    "investor presentation": 3.5
    "funding round": 3.0
    "series a": 3.0
    "traction slide": 2.5
    "market size": 2.5
  entities:
    funding_stages: ["pre-seed", "seed", "series a", "series b"]
    investor_types: ["angel", "vc", "strategic"]

mvp_spec:
  weight: 3.0
  keywords:
    "mvp": 4.0
    "minimum viable product": 4.0
    "product spec": 3.0
    "user stories": 2.5
    "acceptance criteria": 2.5
```

### Pain Point Document Types
```yaml
pain_point_discussion:
  weight: 3.0
  keywords:
    "frustrated": 3.0
    "annoying": 2.5
    "hate that": 2.5
    "wish there was": 3.0
    "someone should build": 3.5
    "why doesn't": 3.0
    "pain point": 4.0
    "biggest problem": 3.0

customer_feedback:
  weight: 2.5
  keywords:
    "feedback": 3.0
    "experience": 2.0
    "customer service": 2.5
    "complaint": 2.5
    "issue": 2.0
    "problem": 2.0
    "disappointed": 2.0
```

## Document Type Categories

### High-Value Types for Scout (Weight 3.0-4.0)
Focus on documents with maximum entrepreneurial intelligence:
- **Investment documents**: pitch_deck, term_sheet, investor_update
- **Pain point sources**: pain_point_discussion, customer_feedback, product_review
- **Innovation indicators**: research_paper, patent_application, whitepaper
- **Market intelligence**: competitive_analysis, market_research, industry_report

### Standard Business Types (Weight 2.0-2.9)
Common document types across verticals:
- **Contracts and agreements**: service_agreement, employment_agreement
- **Technical documentation**: api_documentation, system_documentation  
- **Financial documents**: financial_statement, audit_report, invoice
- **Operational documents**: project_plan, status_report, meeting_minutes

### Supporting Types (Weight 1.0-1.9)
General reference and administrative documents:
- **Training materials**: manual, brochure, training_material
- **Communications**: email_campaign, newsletter, press_release
- **Administrative**: enrollment_form, attendance_record, policy_document

## Expansion Guidelines

### Adding New Document Types

1. **Business Process Analysis**: Identify document types crucial for MVP development
2. **Vertical Coverage**: Ensure comprehensive coverage within each SaaS domain
3. **Pattern Collection**: Gather real-world examples and terminology
4. **Weight Calibration**: Test classification accuracy with sample content
5. **Processing Integration**: Define extraction logic for new document types

### Document Type Validation

1. **Sample Testing**: Test with 5+ representative documents per type
2. **Precision Check**: Ensure >80% correct classification 
3. **Distinctiveness**: Verify minimal overlap with existing types
4. **Business Value**: Confirm relevance to Scout's MVP development goals
5. **Processing Logic**: Define specific intelligence extraction for each type

### Naming Conventions

- **File names**: `{vertical_name}.yaml` (lowercase, underscores)
- **Document types**: `{descriptive_name}` (lowercase, underscores)  
- **Consistency**: Use parallel structure across verticals

## Integration with Scout Platform

### Processing Pipeline Routing
```python
# Document type determines processing approach
if doc_type == "pitch_deck":
    extract_investment_intelligence(document)
elif doc_type == "pain_point_discussion":
    extract_mvp_opportunities(document)
elif doc_type == "patent_application":
    extract_innovation_intelligence(document)
```

### Intelligence Extraction Mapping

#### Entrepreneurial Intelligence Types
- **pitch_deck** → Investment trends, market validation, competitive landscape
- **pain_point_discussion** → MVP opportunities, user needs, market gaps
- **patent_application** → Innovation trends, technological opportunities
- **competitive_analysis** → Market positioning, feature gaps, pricing intelligence

#### Operational Intelligence Types  
- **financial_statement** → Market health, growth patterns, business models
- **api_documentation** → Integration opportunities, technical capabilities
- **customer_review** → Product feedback, user satisfaction, improvement areas
- **regulatory_document** → Compliance requirements, market constraints

## Performance Optimization

### Aho-Corasick Integration
- **Pattern density**: Optimize for 15-25 keywords per document type
- **Weight distribution**: Balance precision vs. recall
- **Memory efficiency**: Share patterns across related document types

### Classification Efficiency
- **High-frequency patterns**: Prioritize common document type indicators
- **Distinctive markers**: Focus on unique identifying characteristics
- **Context sensitivity**: Include document structure and format clues

## Quality Assurance

### Testing Requirements
- **Cross-vertical testing**: Ensure types don't overlap across domains
- **Confidence scoring**: Monitor classification confidence levels
- **False positive analysis**: Check for misclassification patterns
- **Performance monitoring**: Track processing time impact

### Maintenance Guidelines
- **Quarterly reviews**: Update patterns based on new document types
- **Performance tuning**: Optimize weights based on classification results
- **Coverage expansion**: Add document types for emerging business processes
- **Pattern refinement**: Remove ineffective or redundant patterns

## Future Enhancements

### Emerging Document Types
- **AI-generated content**: AI reports, automated analysis, bot communications
- **Blockchain documents**: Smart contracts, token documentation, DeFi protocols
- **Remote work**: Virtual collaboration docs, distributed team communications
- **Sustainability**: ESG reports, carbon tracking, sustainability metrics

### Advanced Features
- **Dynamic typing**: Learn new document types from classification patterns
- **Hierarchical types**: Support sub-types and document variants
- **Context-aware typing**: Consider source, author, and distribution context
- **Multi-modal support**: Handle documents with mixed content types

---

**Remember**: Document type classification drives Scout's intelligence extraction pipeline. Precise typing enables targeted entrepreneurial intelligence extraction for MVP development across all SaaS verticals.