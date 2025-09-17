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

## 🟢 5. Founder's Journey Universal Output Examples

### **🔵 Market Intelligence Cluster Example**
*Source: TechCrunch article about AI SaaS funding*

```json
{
  "document_id": "web_techcrunch_ai_saas_001",
  "url": "https://techcrunch.com/ai-saas-funding-q4-2024",
  "domain_detected": "business_technology",
  
  "founder_intelligence": {
    "market_opportunity": [
      {
        "fact_id": "market_001",
        "type": "MarketSize", 
        "subject": "AI-powered SaaS market",
        "predicate": "valued_at",
        "object": "$28.1 billion",
        "timeframe": "2024",
        "growth_projection": "32% CAGR through 2029",
        "source": "Paragraph 2, Gartner report citation",
        "confidence": 0.85
      }
    ],
    "capital_flows": [
      {
        "fact_id": "funding_001",
        "type": "InvestmentRound",
        "subject": "Anthropic",
        "predicate": "raised", 
        "object": "$4 billion Series C",
        "investor": "Amazon",
        "date": "2024-11-15",
        "focus_area": "Enterprise AI safety",
        "source": "Headline and lead paragraph",
        "confidence": 0.95
      }
    ]
  }
}
```

### **🟠 Competitive & User Cluster Example** 
*Source: SaaS company comparison page*

```json
{
  "document_id": "web_g2_crm_comparison_001", 
  "url": "https://g2.com/categories/crm-software",
  "domain_detected": "software_comparison",
  
  "founder_intelligence": {
    "competitive_landscape": [
      {
        "fact_id": "comp_001",
        "type": "MarketPosition",
        "subject": "Salesforce",
        "predicate": "holds_market_share",
        "object": "19.8%",
        "market": "CRM software",
        "rank": "#1",
        "source": "Market share chart",
        "confidence": 0.80
      }
    ],
    "user_pain_points": [
      {
        "fact_id": "pain_001", 
        "type": "UserFriction",
        "subject": "Small business users",
        "predicate": "complain_about",
        "object": "Complex setup taking 3+ months",
        "frequency": "mentioned in 67% of reviews",
        "source": "Review summary section",
        "confidence": 0.75
      }
    ]
  }
}
```

### **🟢 Operational & Scaling Cluster Example**
*Source: Engineering blog about tech stack*

```json
{
  "document_id": "web_stripe_engineering_001",
  "url": "https://stripe.com/blog/engineering/scaling-apis", 
  "domain_detected": "engineering_technical",
  
  "founder_intelligence": {
    "technical_innovation": [
      {
        "fact_id": "tech_001",
        "type": "TechStackChoice",
        "subject": "Stripe API infrastructure", 
        "predicate": "built_with",
        "object": "Ruby on Rails + Go microservices",
        "performance_metric": "handles 10,000+ requests/second",
        "source": "Architecture diagram caption",
        "confidence": 0.90
      }
    ],
    "talent_signals": [
      {
        "fact_id": "talent_001",
        "type": "HiringPattern",
        "subject": "Stripe",
        "predicate": "hiring_for", 
        "object": "Senior Go Engineers",
        "salary_range": "$180K-250K base",
        "location": "Remote + SF",
        "urgency": "25 open positions",
        "source": "Careers page link in footer",
        "confidence": 0.85
      }
    ]
  }
}
```

### **🟡 Growth & Exit Cluster Example**
*Source: Business news acquisition announcement*

```json
{
  "document_id": "web_techcrunch_acquisition_001",
  "url": "https://techcrunch.com/adobe-figma-acquisition",
  "domain_detected": "business_news",
  
  "founder_intelligence": {
    "exit_landscape": [
      {
        "fact_id": "exit_001",
        "type": "AcquisitionEvent",
        "subject": "Adobe", 
        "predicate": "acquired",
        "object": "Figma",
        "valuation": "$20 billion",
        "multiple": "50x revenue",
        "strategic_rationale": "Design workflow consolidation",
        "date": "2024-01-15",
        "source": "Press release quote",
        "confidence": 0.95
      }
    ],
    "scaling_pathways": [
      {
        "fact_id": "scale_001",
        "type": "GrowthModel",
        "subject": "Figma",
        "predicate": "achieved_growth_via",
        "object": "Viral collaboration features",
        "metric": "10x user growth in 18 months", 
        "source": "CEO interview excerpt",
        "confidence": 0.80
      }
    ]
  }
}
```

---

## 🟢 6. Pattern Matching Implementation (Aho-Corasick + Rust Regex)

### **What's Achievable with Your Current Tech Stack**

**✅ High-Confidence Patterns (Aho-Corasick Multi-Pattern Matching)**:
```rust
// Market size extraction patterns
"$X billion market" | "$X.Y billion industry" | "market valued at $X"
"growing at X% CAGR" | "X% annual growth" | "projected to reach $X"

// Funding announcement patterns  
"raised $X Series [A-D]" | "closes $X funding round" | "$X investment led by"
"Series [A-D] of $X" | "secured $X from [Investor]"

// Competitive positioning patterns
"market leader in" | "leading provider of" | "#1 in [category]"
"holds X% market share" | "ranks #X in [market]"
```

**✅ Structured Fact Extraction (Rust Regex)**:
```rust
// Investment rounds
r"(?P<company>\w+)\s+raised\s+\$(?P<amount>[\d.]+\s*[BMK]?)\s+Series\s+(?P<round>[A-D])"

// Market metrics  
r"market\s+(?:valued|worth|size)\s+(?:of\s+)?\$(?P<amount>[\d.]+\s*[BMK]?)"

// Pain points
r"(?P<users>[\w\s]+)\s+(?:struggle|complain|frustrated)\s+(?:with|about)\s+(?P<pain>[\w\s]+)"

// Tech stack mentions
r"built\s+(?:with|using|on)\s+(?P<tech>[\w\s,+]+)"
```

### **Performance Advantage**
- **Single Pass**: All patterns processed simultaneously across hundreds of thousands of websites
- **Linear Scaling**: Adding 1000 patterns costs same as adding 10 patterns  
- **No AI Overhead**: Direct pattern matching without model inference costs

---

## 🟢 7. Organizational Implementation Roadmap

### **Phase 1: Foundation Patterns (Weeks 1-4)**
**Goal**: Get basic Founder's Journey facts extracting from 10,000 websites

**🔵 Market Intelligence Patterns**:
- Investment announcements (funding amounts, investors, dates)
- Market size claims (dollar amounts, growth rates)
- Company valuations (acquisition prices, IPO values)

**Implementation**:
1. Build Aho-Corasick dictionary for investor names, funding terminology
2. Create Rust regex patterns for dollar amounts and percentages
3. Test on TechCrunch, Business Insider, company press releases

### **Phase 2: Competitive Intelligence (Weeks 5-8)**  
**Goal**: Extract positioning and user feedback across 50,000 websites

**🟠 Competitive & User Patterns**:
- Market positioning claims ("leading", "first", "#1 in")
- User pain points (review sites, forums, support pages)
- Feature comparisons (vs. competitor language)

**Implementation**:
1. Expand Aho-Corasick for company names and positioning terms
2. Add regex patterns for review sentiment and complaint language
3. Test on G2, Capterra, Reddit, company comparison pages

### **Phase 3: Technical & Talent Intelligence (Weeks 9-12)**
**Goal**: Track innovation and hiring patterns across 100,000+ websites

**🟢 Operational Patterns**:
- Technology stack mentions (frameworks, languages, tools)
- Hiring patterns (job postings, salary ranges, team sizes)
- Partnership announcements (integrations, acquisitions)

**Implementation**:
1. Build tech terminology dictionary (React, Python, AWS, etc.)
2. Create patterns for job titles and salary formats
3. Test on engineering blogs, careers pages, LinkedIn

### **Phase 4: Growth & Exit Intelligence (Weeks 13-16)**
**Goal**: Complete Founder's Journey coverage across 200,000+ websites

**🟡 Growth & Exit Patterns**:
- Acquisition announcements (buyer, target, price, rationale)
- Growth metrics (user counts, revenue growth, market expansion)
- Exit multiples (revenue multiples, EBITDA multiples)

**Implementation**:
1. Add acquisition terminology and buyer company names
2. Create patterns for growth metrics and financial ratios
3. Test on business news, SEC filings, company earnings calls

### **Success Metrics by Phase**:
- **Phase 1**: 1,000 market facts/day from 10K websites
- **Phase 2**: 5,000 competitive facts/day from 50K websites  
- **Phase 3**: 10,000 operational facts/day from 100K websites
- **Phase 4**: 20,000+ complete founder profiles/day from 200K+ websites

## 🟢 8. Scout's Founder Intelligence Advantage

### **The Strategic Edge**

With this semantic extraction framework, Scout provides founders with **structured intelligence advantages**:

**Cross-Market Pattern Detection**:
- "Show me all AI startups that raised >$10M and claim 40%+ efficiency gains"
- "Which markets have the highest talent cost vs. funding availability ratios?"
- "What pain points appear across 5+ different industries?"

**Real-Time Market Intelligence**:
- Track funding velocity changes across sectors
- Monitor competitive positioning shifts and new market entrants
- Identify emerging technology adoption patterns before they become obvious

**Risk Assessment Capabilities**:
- Regulatory change impact analysis across affected markets
- Talent availability and cost trends in target geographies  
- Exit pathway health and buyer appetite by vertical

### **Competitive Moat**

While others use AI for summarization, Scout's **pattern-based semantic extraction** creates:
- **Queryable Knowledge Graphs**: Structured facts enable complex market analysis
- **Trend Detection**: Pattern changes signal market shifts before competitors notice
- **Source Authority Weighting**: Distinguish marketing claims from validated data
- **Cross-Domain Synthesis**: Connect regulatory, competitive, and financial intelligence

This isn't just better market research - it's **founder intelligence at scale**.

