# Corpus Expansion Strategy for Founder Intelligence
## 1GB Memory-Optimized Entity Recognition at Scale

### Overview
Strategic corpus expansion to support high-accuracy entity disambiguation across 12 founder intelligence domains while maintaining CloudFlare Workers compatibility (128MB) and edge deployment constraints (1GB RAM limit).

---

## Memory Allocation Strategy

### Base Foundation (92MB Total)

| Category | Count | Memory | Aho-Corasick | Total |
|----------|-------|--------|--------------|-------|
| **First Names** | 100K | ~1MB | ~5MB | ~6MB |
| **Last Names** | 100K | ~1MB | ~5MB | ~6MB |
| **Organizations** | 100K | ~2MB | ~8MB | ~10MB |
| **Working Memory** | - | - | - | ~20MB |
| **Safety Buffer** | - | - | - | ~50MB |
| **TOTAL BASE** | **300K** | **~4MB** | **~18MB** | **~92MB** |

### Domain-Specific Vocabularies (908MB Available)

| Domain | Entities | Memory | Priority Sources |
|--------|----------|--------|------------------|
| **Market Intelligence** | 50K | ~50MB | Industry reports, market research, category taxonomies |
| **Capital Flows** | 30K | ~30MB | Crunchbase, PitchBook, investment terminology |
| **Competitive Landscape** | 40K | ~40MB | Product databases, feature lists, competitive analysis |
| **Technical Innovation** | 60K | ~60MB | GitHub, Stack Overflow, tech documentation |
| **Talent Signals** | 25K | ~25MB | LinkedIn job titles, skills databases, certifications |
| **Regulatory Landscape** | 20K | ~20MB | Legal databases, compliance frameworks, regulations |
| **Exit Landscape** | 15K | ~15MB | M&A databases, IPO filings, exit terminology |
| **Scaling Pathways** | 30K | ~30MB | Growth metrics, KPI terminology, scaling frameworks |
| **Partnership Ecosystem** | 25K | ~25MB | Integration platforms, partnership types, API directories |
| **Product Development** | 40K | ~40MB | Product Hunt, feature databases, development terminology |
| **Operational Excellence** | 20K | ~20MB | Operations frameworks, efficiency metrics, process terms |
| **User Pain Points** | 15K | ~15MB | UX terminology, customer feedback, pain point categories |

**TOTAL EXPANDED: 1.67M entities in ~1GB RAM**

---

## Data Source Priority Matrix

### Tier 1: Manually Curated (Highest Quality)
- **Fortune 500 companies** - Immediate download
- **S&P 500 listings** - SEC filings, public data
- **Major VC firms** - Crunchbase verified data
- **Top universities** - Academic rankings, QS/Times
- **Government agencies** - Official directories

### Tier 2: High-Quality Datasets (NER Verified)
- **CoNLL-2003** - Gold standard person/org names (35K entities, 100MB)
- **WikiANN English** - Wikipedia-sourced entities (200K entities, 500MB)
- **OntoNotes 5.0** - Multi-genre annotated entities (1M+ entities, 2GB)

### Tier 3: Domain-Specific APIs/Databases
- **Crunchbase API** - Startups, funding, investors
- **GitHub API** - Tech companies, projects, technologies
- **LinkedIn API** - Job titles, skills, company data
- **SEC Edgar** - Public company filings
- **Patent databases** - Innovation terminology

### Tier 4: Web Scraping (Quality Filtered)
- **AngelList** - Startup ecosystem
- **Product Hunt** - Product names, features
- **Stack Overflow** - Technical terminology
- **TechCrunch** - Company mentions, funding news
- **Industry associations** - Domain-specific terminology

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
- [x] Implement 100K/100K/100K base corpus
- [ ] Download and process CoNLL-2003 + WikiANN
- [ ] Manual curation of Fortune 500 + major VCs
- [ ] Memory optimization and testing

### Phase 2: Domain Expansion (Week 2-3)
- [ ] **Market Intelligence**: Industry taxonomies, market categories
- [ ] **Capital Flows**: Investment terminology, funding round types
- [ ] **Technical Innovation**: Programming languages, frameworks, APIs
- [ ] **Competitive Landscape**: Product names, feature terminology

### Phase 3: Advanced Domains (Week 4-5)
- [ ] **Talent Signals**: Job titles, skills, certifications
- [ ] **Regulatory**: Compliance frameworks, legal terminology
- [ ] **Operations**: Efficiency metrics, process terminology
- [ ] **User Experience**: Pain points, UX terminology

### Phase 4: Optimization (Week 6)
- [ ] Performance tuning for CloudFlare Workers
- [ ] Memory compression techniques
- [ ] Quality scoring and filtering
- [ ] Edge deployment testing

---

## Technical Implementation Scripts

### Script 1: Foundation Builder
```python
# /knowledge/corpus/foundation_builder.py
# Downloads and processes Tier 1 + Tier 2 datasets
# Outputs: 100K first names, 100K last names, 100K organizations
```

### Script 2: Domain Expander
```python
# /knowledge/corpus/domain_expander.py  
# Processes domain-specific APIs and datasets
# Outputs: Domain-specific entity vocabularies
```

### Script 3: Quality Scorer
```python
# /knowledge/corpus/quality_scorer.py
# Ranks entities by frequency, sources, validation
# Filters to priority entities within memory limits
```

### Script 4: Corpus Optimizer
```python
# /knowledge/corpus/corpus_optimizer.py
# Optimizes Aho-Corasick performance and memory usage
# Generates deployment-ready corpus files
```

---

## Quality Assurance Framework

### Frequency-Based Filtering
- Require 2+ mentions across different sources
- Prioritize entities from multiple datasets
- Weight by source reliability (manual > verified > scraped)

### Length and Format Validation
- First names: 2-20 characters, alphabetic only
- Last names: 2-30 characters, allow hyphens/apostrophes  
- Organizations: 2-100 characters, allow common punctuation
- Domain terms: 2-50 characters, technical notation allowed

### Deduplication Strategy
- Normalize case, spacing, punctuation
- Detect and merge variants (IBM = International Business Machines)
- Track aliases for entity disambiguation
- Cross-reference against existing corpus

### Performance Benchmarks
- **Target**: 90%+ coverage of founder intelligence entities
- **Speed**: >100K entities/second disambiguation rate
- **Memory**: <1GB total corpus size
- **Accuracy**: >95% precision on manual test set

---

## Data Sources by Domain

### Market Intelligence (50K entities)
**Priority Sources:**
- **Industry taxonomies**: NAICS codes, SIC codes, industry classifications
- **Market research**: CB Insights categories, PitchBook sectors
- **Investment databases**: Market size terminology, TAM/SAM/SOM
- **Business terminology**: Market dynamics, competitive forces

**Scripts to Build:**
- Market category scraper (CB Insights, PitchBook)
- Industry taxonomy processor (NAICS/SIC)
- Investment terminology extractor

### Capital Flows (30K entities)
**Priority Sources:**
- **Crunchbase API**: Funding rounds, investment types, investor categories
- **PitchBook**: PE/VC terminology, deal structures
- **SEC filings**: Investment terminology, financial instruments
- **Investment news**: TechCrunch, VentureBeat funding announcements

**Scripts to Build:**
- Crunchbase investment terminology extractor
- SEC filing financial term processor
- Funding news terminology scraper

### Technical Innovation (60K entities)
**Priority Sources:**
- **GitHub API**: Programming languages, frameworks, libraries
- **Stack Overflow**: Technology discussions, tool mentions
- **Documentation sites**: API names, technical specifications
- **Developer surveys**: Technology adoption, tool popularity

**Scripts to Build:**
- GitHub technology stack analyzer
- Stack Overflow terminology extractor
- Documentation scraper for technical terms

### Competitive Landscape (40K entities)
**Priority Sources:**
- **Product Hunt**: Product names, feature descriptions
- **G2/Capterra**: Software categories, feature comparisons
- **Company websites**: Product portfolios, feature lists
- **Review sites**: Competitive analysis terminology

**Scripts to Build:**
- Product database scraper (Product Hunt, G2)
- Feature terminology extractor
- Competitive analysis term processor

### Talent Signals (25K entities)
**Priority Sources:**
- **LinkedIn API**: Job titles, skills, company roles
- **Job boards**: Indeed, Glassdoor role descriptions
- **Certification bodies**: Technical certifications, professional designations
- **University programs**: Degree types, specializations

**Scripts to Build:**
- LinkedIn job title/skills scraper
- Certification database processor
- Academic program terminology extractor

### Regulatory Landscape (20K entities)
**Priority Sources:**
- **Legal databases**: Westlaw, LexisNexis regulatory terminology
- **Government sites**: SEC, FDA, EPA compliance frameworks
- **Industry standards**: ISO, ANSI, industry-specific regulations
- **Compliance vendors**: RegTech terminology, frameworks

**Scripts to Build:**
- Regulatory database scraper
- Compliance framework processor
- Legal terminology extractor

### Exit Landscape (15K entities)
**Priority Sources:**
- **M&A databases**: Deal terminology, transaction types
- **IPO filings**: Public offering terminology, market categories
- **Private equity**: Exit strategy terminology, deal structures
- **Financial news**: Exit terminology from news sources

**Scripts to Build:**
- M&A terminology processor
- IPO filing term extractor
- Exit strategy terminology scraper

### Scaling Pathways (30K entities)
**Priority Sources:**
- **Growth frameworks**: OKRs, KPIs, scaling methodologies
- **Business literature**: Scaling terminology, growth metrics
- **Consultant frameworks**: McKinsey, BCG scaling approaches
- **SaaS metrics**: ARR, MRR, growth terminology

**Scripts to Build:**
- Growth metrics database processor
- Business framework terminology extractor
- SaaS metrics terminology scraper

### Partnership Ecosystem (25K entities)
**Priority Sources:**
- **API directories**: RapidAPI, ProgrammableWeb integration types
- **Platform partnerships**: App stores, marketplace categories
- **Integration platforms**: Zapier, MuleSoft connector types
- **Business partnerships**: Channel types, partner categories

**Scripts to Build:**
- API directory scraper
- Integration platform terminology processor
- Partnership type classifier

### Product Development (40K entities)
**Priority Sources:**
- **Feature databases**: Product Hunt, ProductBoard feature types
- **Development methodologies**: Agile, DevOps terminology
- **Product management**: Roadmap terminology, development stages
- **User research**: UX terminology, research methodologies

**Scripts to Build:**
- Product feature terminology extractor
- Development methodology processor
- Product management term scraper

### Operational Excellence (20K entities)
**Priority Sources:**
- **Operations frameworks**: Lean, Six Sigma, operational metrics
- **Business process**: BPM terminology, efficiency metrics
- **Quality standards**: Quality management terminology
- **Operational tools**: Operations software, process terminology

**Scripts to Build:**
- Operations framework processor
- Business process terminology extractor
- Quality standards terminology scraper

### User Pain Points (15K entities)
**Priority Sources:**
- **UX research**: Pain point categories, user experience terminology
- **Customer feedback**: Support ticket categories, common issues
- **Review analysis**: User complaint terminology, friction points
- **UX methodologies**: User research terminology, pain point frameworks

**Scripts to Build:**
- UX terminology processor
- Customer feedback analyzer
- Pain point category extractor

---

## Next Steps

1. **Immediate (This Week)**:
   - Implement foundation builder script
   - Download and process CoNLL-2003 + WikiANN datasets
   - Create 100K/100K/100K base corpus

2. **Short Term (Next 2 Weeks)**:
   - Build domain-specific scrapers for top 4 domains
   - Implement quality scoring and ranking system
   - Test memory usage and performance benchmarks

3. **Medium Term (Next Month)**:
   - Complete all 12 domain vocabularies
   - Optimize for CloudFlare Workers deployment
   - Build automated corpus update pipelines

4. **Long Term (Ongoing)**:
   - Continuous corpus improvement based on usage data
   - Expand to international markets and languages
   - Integration with real-time data sources