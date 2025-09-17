# Founder's Journey Semantic Knowledge Extraction Framework

A comprehensive system for extracting structured, actionable intelligence from hundreds of thousands of websites to power the complete **Founder's Journey** - giving entrepreneurs everything they need to make informed market entry decisions.

## Core Philosophy: Full-Stack Founder Intelligence

Scout extracts semantic facts across **12 critical decision areas** that determine startup success or failure. While others use generic AI summarization, we extract structured, comparable facts that provide founders with intelligence advantages over incumbents.

## The Founder's Journey: From Idea to Exit Strategy

Every market entry decision requires intelligence across these interconnected areas:
- **Market & Capital Flows** → Is there opportunity and funding?
- **Competition & Users** → Who are we displacing and why will they switch?
- **Talent & Regulation** → Can we build and operate legally?
- **Growth & Exit** → How do we scale and where does this lead?

---

## 🟢 1. The 12 Founder's Journey Fact Categories

### **🔵 Market Intelligence Cluster**

**1. Market Opportunity**
- Market size, CAGR, geographic breakdown
- Adjacent and emerging markets (white spaces, blue oceans)
- Macroeconomic indicators affecting the space

**2. Capital Flows & Investment**
- VC/PE funding patterns and thesis evolution
- Corporate venture activity and strategic investments
- Government grants, contracts, and incentive programs

**3. Financial Signals & Economics**
- Exit multiples (M&A, IPO valuations)
- Gross margin benchmarks and unit economics
- Typical burn rates and runway requirements

### **🟠 Competitive & User Cluster**

**4. Competitive Landscape**
- Market leaders, challengers, and positioning
- Feature differentiation matrices
- M&A activity and partnership strategies

**5. User Pain Points & Behavior**
- Explicit pain points (forums, support tickets)
- Latent needs (workarounds, job postings, patent gaps)
- Cultural and behavioral shifts driving demand

**6. Customer Acquisition & Growth**
- Dominant acquisition channels and CAC benchmarks
- Viral mechanics and network effects evidence
- Partnership and reseller ecosystem dynamics

### **🟢 Operational & Scaling Cluster**

**7. Technical Innovation & Infrastructure**
- Popular frameworks, stacks, and development patterns
- Patent clusters and emerging IP areas
- Infrastructure dependencies and supply chain factors

**8. Talent & Human Capital**
- Availability and cost of skilled workers
- Communities of practice and talent hubs
- Regulatory/licensing requirements

**9. Regulatory & Policy Intelligence**
- Current and emerging regulations
- Enforcement patterns and compliance costs
- Government incentives and trade restrictions

### **🟡 Growth & Exit Cluster**

**10. Ecosystem Analysis**
- Key players, suppliers, and integrators
- Industry standards and certification requirements
- Distribution channels and market access

**11. Scaling Pathways**
- Proven growth models in the vertical
- Platform and partnership opportunities
- Geographic expansion patterns

**12. Exit Landscape**
- Active acquirers and their acquisition criteria
- IPO readiness benchmarks and public comparables
- Strategic buyer maps and consolidation trends

---

## 🟢 2. Universal Founder's Journey JSON Schema

Every website extraction, regardless of vertical, produces this standardized structure:

```json
{
  "document_id": "web_healthcare_crm_001",
  "domain_detected": "healthcare_technology",
  "url": "https://example-healthtech.com",
  "extraction_date": "2024-01-15",
  
  "founder_intelligence": {
    
    "market_opportunity": [
      {
        "fact_id": "market_001",
        "type": "MarketSize",
        "market": "Healthcare CRM",
        "size": "$4.2B",
        "growth_rate": "12.5% CAGR",
        "timeframe": "2024-2029",
        "source": "About page market stats",
        "confidence": 0.7
      }
    ],
    
    "capital_flows": [
      {
        "fact_id": "funding_001", 
        "type": "InvestmentActivity",
        "investor": "Andreessen Horowitz",
        "amount": "$50M Series B",
        "focus_area": "Healthcare workflow automation",
        "date": "2024-01-10",
        "source": "Press release",
        "confidence": 0.95
      }
    ],
    
    "user_pain_points": [
      {
        "fact_id": "pain_001",
        "type": "ExplicitPainPoint", 
        "pain_point": "Manual patient data entry takes 40% of staff time",
        "affected_users": "Healthcare administrators",
        "frequency": "Daily workflow issue",
        "source": "Customer testimonial",
        "confidence": 0.85
      }
    ],
    
    "competitive_landscape": [
      {
        "fact_id": "comp_001",
        "type": "CompetitivePosition",
        "company": "Salesforce Health Cloud",
        "market_position": "Market leader",
        "key_differentiator": "Integration with existing Salesforce ecosystem", 
        "market_share": "23%",
        "source": "Competitive comparison page",
        "confidence": 0.8
      }
    ],
    
    "talent_signals": [
      {
        "fact_id": "talent_001",
        "type": "TalentDemand",
        "role": "Healthcare Software Engineers",
        "salary_range": "$120K-180K",
        "availability": "High demand, limited supply",
        "location": "San Francisco Bay Area",
        "source": "Careers page",
        "confidence": 0.75
      }
    ]
    
    // ... Additional categories
  },
  
  "entity_map": {
    "organizations": [...],
    "persons": [...],
    "products": [...],
    "technologies": [...]
  },
  
  "relationships": [
    {
      "subject": "Andreessen Horowitz",
      "predicate": "invested_in", 
      "object": "Healthcare CRM Company",
      "context": "Series B funding"
    }
  ]
}
```

---

## 🟢 3. Web-Scale Extraction Patterns for Founder's Journey

### **High-Value Fact Patterns Across Hundreds of Thousands of Websites**

| Founder Category | Fact Pattern | Website Sources | Extraction Signal |
|------------------|--------------|-----------------|-------------------|
| **Market Opportunity** | Market size claims | Company about pages, investor decks | `"$X billion market"`, `"Growing at X% CAGR"` |
| **Capital Flows** | Funding announcements | Press releases, TechCrunch, company blogs | `"raises $X Series Y"`, `"led by [Investor]"` |
| **Pain Points** | User frustration signals | Support forums, Reddit, job postings | `"biggest challenge"`, `"spending too much time on"` |
| **Competitive Position** | Market positioning claims | Landing pages, comparison pages | `"leading provider"`, `"unlike [Competitor]"` |
| **Technical Innovation** | Technology stack mentions | Engineering blogs, job postings, GitHub | Framework names, language preferences |
| **Talent Signals** | Hiring patterns | Careers pages, LinkedIn jobs | Role requirements, salary ranges, team size |
| **Customer Acquisition** | Growth claims | Case studies, testimonials | `"increased by X%"`, `"saved $X"`, CAC metrics |
| **Exit Activity** | M&A announcements | Business news, SEC filings | `"acquires"`, `"merger"`, valuation multiples |

### **Source Quality Weighting**

**Tier 1 (Confidence 0.9+)**: SEC filings, official press releases, company investor pages
**Tier 2 (Confidence 0.7-0.9)**: Reputable business news, company blogs, customer case studies  
**Tier 3 (Confidence 0.5-0.7)**: Social media, forums, third-party articles
**Tier 4 (Confidence <0.5)**: Marketing copy, unverified claims, user-generated content

---

## 🟢 4. Scout's Competitive Intelligence Advantage

### **The Knowledge Extraction Edge**

While competitors use generic AI for web summarization, Scout extracts **structured, queryable intelligence** that enables:

**Cross-Market Analysis**:
- "Show me all SaaS companies in healthcare claiming >40% efficiency gains"
- "Which fintech startups got Series A funding in Q4 2024?"
- "What are the top 3 pain points mentioned across 1000+ customer testimonials?"

**Trend Detection at Scale**:
- Emerging technology adoption patterns across industries
- Capital flow shifts and investment thesis evolution  
- Regulatory changes impacting market opportunities

**Competitive Positioning Intelligence**:
- Feature gap analysis across market leaders
- Pricing model evolution and market positioning shifts
- Partnership and acquisition pattern recognition

### **Web-Scale Implementation Requirements**

**🟢 Core Pattern Recognition (Linear Performance)**:
- Aho-Corasick multi-pattern matching for entity normalization
- FLPC Rust regex for structured fact extraction
- Single-pass architecture across all 12 Founder categories

**🟡 Source Authority Classification**:
- Domain authority scoring and source type detection
- Cross-source fact validation and confidence weighting
- Temporal fact tracking for trend analysis

**🔴 Critical Gap: Relationship Extraction**:
- Predicate vocabulary for business relationships
- Semantic pattern matching for "Company A acquires Company B"
- Context understanding for conditional facts

---

## 🟢 5. Universal Output Template

Every document, regardless of domain, produces this standardized JSON structure:

```json
{
  "document_id": "doc_123",
  "domain_detected": "regulatory_compliance",
  "entities": {
    "persons": [
      {
        "id": "person_001",
        "canonical_name": "John Smith",
        "aliases": ["J. Smith", "Smith, John"],
        "role": "Safety Director",
        "source": "Page 2"
      }
    ],
    "organizations": [
      {
        "id": "org_osha", 
        "canonical_name": "Occupational Safety and Health Administration",
        "aliases": ["OSHA", "the Agency"],
        "type": "regulatory_agency",
        "source": "Page 1"
      }
    ],
    
    // Domain-specific entities (conditional)
    "standards": [...],      // Only if regulatory domain
    "equipment": [...],      // Only if equipment-focused
    "products": [...],       // Only if commercial domain
    "treatments": [...]      // Only if healthcare domain
  },
  
  "relationships": [
    {
      "subject": "org_osha",
      "predicate": "issues", 
      "object": "std_1926_1050",
      "source": "Page 3"
    }
  ],
  
  "facts": [
    {
      "id": "fact_001",
      "type": "Requirement",
      "subject": "Employers", 
      "predicate": "must_provide",
      "object": "Stairway or ladder at worker access points",
      "condition": "Break in elevation ≥ 19 inches",
      "source": "Page 3",
      "confidence": 0.95
    }
  ]
}
```

---

## 🟢 6. Comparative Analysis Across Domains

The power of this approach: **same extraction framework, comparable outputs across completely different domains**.

### **Web Content vs. Regulatory Document**

**Website Analysis:**
```json
{
  "domain_detected": "commercial_web",
  "facts": [
    {
      "type": "Impact", 
      "subject": "Our software",
      "predicate": "increases",
      "object": "productivity by 40%",
      "source": "Homepage hero section",
      "confidence": 0.7  // Lower confidence for marketing claims
    }
  ]
}
```

**OSHA Document:**
```json
{
  "domain_detected": "regulatory_compliance", 
  "facts": [
    {
      "type": "Impact",
      "subject": "Safety training", 
      "predicate": "reduces", 
      "object": "workplace accidents by 40%",
      "source": "Page 15, Study Citation",
      "confidence": 0.95  // Higher confidence for regulatory data
    }
  ]
}
```

### **Cross-Domain Comparison Benefits**
- **Fact Verification**: Compare claims across authoritative vs. marketing sources
- **Knowledge Synthesis**: Link regulatory requirements to business claims  
- **Source Quality**: Weight facts by domain authority and provenance
- **Pattern Recognition**: Identify universal vs. domain-specific insights


Here’s a reusable Markdown section you can drop into your docs — focused on **Normalization 2**, the step that makes entities comparable across files and domains:

---

## 🔑 Normalization 2: Entity → Canonical Form

Once raw entities and spans are extracted, the **second normalization step** (“Normalization 2”) ensures they become **comparable, reusable, and linkable** across documents and domains. Without this, entities stay siloed and facts cannot be aggregated.

### 🎯 Goals

* **Resolve surface forms**: map variants (*OSHA*, *Occupational Safety and Health Administration*, *the Agency*) to one canonical ID.
* **Anchor to external knowledge**: connect entities to stable identifiers (e.g., Wikidata QID, ISO code, SEC CIK, ICD-10).
* **Standardize values**: normalize units, dates, numbers, and formats (e.g., *\$4*, *4 dollars*, *USD 4.00* → `4.0 USD`).

### 🛠️ Process

1. **Deduplication**

   * Collapse aliases and spelling variants.
   * Example: *“Dept. of Labor”* → *“Department of Labor”*.

2. **Canonical Mapping**

   * Assign each entity a canonical form (`canonical_name`) and a persistent ID (`entity_id`).
   * Example:

     ```yaml
     raw: "OSHA"
     canonical_name: "Occupational Safety and Health Administration"
     entity_id: "Q192334"   # Wikidata ID
     ```

3. **Value Normalization**

   * Dates → ISO 8601 (`1991-03-15`)
   * Measurements → SI + alt units (`10 in` → `25.4 cm`)
   * Money → numeric + currency code (`$4` → `4.0 USD`)

4. **Cross-Document Linking**

   * Entities with the same `entity_id` are treated as the same real-world thing, even if phrased differently across files.
   * Enables comparison (e.g., OSHA citation counts across reports).

### 📊 Example

From OSHA stairways report:

```yaml
- type: RegulationCitation
  raw: "29 CFR 1926.1050"
  canonical_name: "29 CFR Part 1926.1050"
  entity_id: "CFR:1926.1050"
  domain: safety_compliance
```

### ⚡ Why It Matters

* Without Normalization 2, you have *strings*.
* With Normalization 2, you have **knowledge objects** you can compare, aggregate, and query globally.

---

Do you want me to also sketch the **universal YAML template** for Normalization 2 fields (`raw`, `canonical_name`, `entity_id`, `normalized_value`, `domain`), so you can bake it into your pipeline definition?

---

## 🚀 Performance Architecture: Nonlinear Algorithms for Linear Cost

The semantic enhancement layer leverages **nonlinear algorithms** that maintain O(n) performance regardless of pattern complexity - making fact extraction performance-friendly at scale.

### 🔧 Core Performance Engines

**Aho-Corasick Multi-Pattern Matching:**
- **Complexity**: O(n + m + z) - linear with text size, NOT pattern count
- **Capability**: Search 1000+ canonical mappings as fast as 10 mappings
- **Use Case**: Entity normalization, alias resolution, canonical form mapping
- **Performance**: One pass through text finds all entity variants simultaneously

**FLPC Rust Regex Engine:**
- **Complexity**: O(n) linear time with text length
- **Capability**: Multiple complex fact patterns processed in parallel
- **Use Case**: Structured fact extraction (RegulationCitation, Requirements, FinancialImpact)
- **Performance**: Adding more extraction patterns doesn't degrade speed

### 🎯 Implementation Strategy

```python
# Canonical Normalization - Aho-Corasick O(1) lookup
canonical_map = {
    "OSHA": "Occupational Safety and Health Administration",
    "EPA": "Environmental Protection Agency", 
    "DOL": "Department of Labor",
    "29 CFR": "Code of Federal Regulations Title 29",
    # ... 1000+ mappings processed simultaneously
}

# Fact Pattern Recognition - FLPC Rust Regex
fact_patterns = {
    'RegulationCitation': r'(\w+)\s+(\d+\s+CFR\s+[\d\.]+)',
    'Requirement': r'(must|shall|required)\s+(.+?)(?=\.|,)',
    'FinancialImpact': r'\$[\d,]+(?:\.\d{2})?.*?(?:save|cost|impact)',
    'MeasurementRequirement': r'(\d+(?:\.\d+)?)\s*(inches?|feet?|meters?)',
    # ... All patterns processed in single pass
}
```

### ⚡ Performance Advantage

**Single-Pass Architecture:**
1. **ONE** text traversal with ALL patterns active
2. **Simultaneous** entity recognition + canonicalization + fact extraction
3. **Post-processing** match assembly into structured facts
4. **No multiple passes** - no exponential scaling

**Key Insight:** Semantic intelligence comes "for free" because both Aho-Corasick and FLPC are designed for massive pattern sets with linear performance. Adding 1000 fact patterns costs the same as adding 10.

### 📊 Scaling Characteristics

- **Text Length**: Linear O(n) - 10KB processes as fast as 1KB per character
- **Pattern Count**: Constant O(1) - 1000 patterns ≈ 10 patterns  
- **Fact Complexity**: No penalty - complex structured facts cost same as simple entities
- **Domain Count**: Additive only - 20 domains scale independently

**Result**: Rich semantic extraction with entity-level performance costs.
