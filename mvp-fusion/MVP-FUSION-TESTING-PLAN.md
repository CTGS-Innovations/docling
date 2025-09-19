# MVP-Fusion Testing Plan: Entity Normalization Phase

## Overview
Testing plan for implementing the new **Normalization Phase** in the MVP-Fusion pipeline. This phase sits between the Enrichment and Extraction stages to canonicalize entities and create clean, AI-ready document representations.

## Pipeline Enhancement

### Current Flow:
```
convert � classify � enrich � extract
```

### Enhanced Flow:
```
convert � classify � enrich � normalize � extract
```

## Normalization Phase Objectives

### 1. Entity Canonicalization
Transform duplicate entity mentions into canonical forms with unique tracking IDs.

**Example Input (Raw Entities):**
```yaml
entities:
  person:
    - text: "John Smith"
      span: {start: 100, end: 110}
    - text: "Mr. Smith"  
      span: {start: 220, end: 230}
    - text: "John A. Smith"
      span: {start: 600, end: 612}
```

**Example Output (Normalized):**
```yaml
normalized_entities:
  - id: p001
    type: PERSON
    normalized:
      canonical: "John Smith"
      count: 3
    mentions:
      - text: "John Smith"
        span: {start: 100, end: 110}
      - text: "Mr. Smith"
        span: {start: 220, end: 230}
      - text: "John A. Smith"
        span: {start: 600, end: 612}
```

### 2. Global Text Replacement
Replace all entity mentions with canonical form + ID using Aho-Corasick for performance.

**Format:** `||canonical||id||`

**Original Text:**
```markdown
Mr. Smith met with John A. Smith to discuss the $2.5M budget. Later, John Smith called OSHA.
```

**Normalized Text:**
```markdown
||John Smith||p001|| met with ||John Smith||p001|| to discuss the ||$2,500,000||mon001|| budget. Later, ||John Smith||p001|| called ||Occupational Safety and Health Administration||org001||.
```

## Core 8 Entity Types - Professional Normalization Strategy

### 1. PERSON
**Normalization Strategy:** Remove titles, standardize format, use longest variant as canonical

**Professional Example:**
```yaml
- id: p001
  type: PERSON
  normalized: "John Smith"
  aliases: ["Mr. Smith", "John A. Smith", "Dr. Smith"]
  count: 3
  mentions:
    - text: "Mr. John A. Smith"
      span: {start: 100, end: 115}
    - text: "Mr. Smith"
      span: {start: 230, end: 239}
    - text: "Dr. Smith"
      span: {start: 420, end: 430}
```

**Techniques:**
- **Title removal:** `regex.sub(r'^(Dr|Prof|Mr|Mrs|Ms)\.\s*', '', name)`
- **Fuzzy matching:** Use rapidfuzz for name similarity (85% threshold)
- **Corpus lookup:** Match against 429K first names, 99K last names

### 2. ORGANIZATION
**Normalization Strategy:** Expand acronyms, use formal legal names, follow SEC standards

**Professional Example:**
```yaml
- id: org001
  type: ORG
  normalized: "Environmental Protection Agency"
  aliases: ["EPA", "E.P.A."]
  count: 3
  mentions:
    - text: "EPA"
      span: {start: 300, end: 303}
    - text: "Environmental Protection Agency"
      span: {start: 600, end: 631}
    - text: "E.P.A."
      span: {start: 820, end: 826}
```

**Techniques:**
- **Acronym expansion:** First letter matching + fuzzy similarity
- **Aho-Corasick:** Exact matching for known acronyms (EPA, FDA, OSHA)
- **SEC database:** Use EDGAR company listings for canonical names

### 3. LOCATION
**Normalization Strategy:** USPS standardization, expand abbreviations, add geographic context

**Professional Example:**
```yaml
- id: loc001
  type: LOCATION
  normalized: "New York City, NY"
  aliases: ["NYC", "New York", "Manhattan"]
  count: 3
  mentions:
    - text: "NYC"
      span: {start: 100, end: 103}
    - text: "New York City"
      span: {start: 200, end: 213}
    - text: "Manhattan"
      span: {start: 300, end: 309}
```

**Techniques:**
- **USPS database:** Standard address formats
- **Geographic corpus:** Major cities, states, landmarks
- **Context resolution:** "Springfield" + surrounding text → "Springfield, IL"

### 4. GPE (Geopolitical Entity)
**Normalization Strategy:** ISO 3166 country codes, official government names

**Professional Example:**
```yaml
- id: gpe001
  type: GPE
  normalized: "United States"
  iso_alpha2: "US"
  iso_alpha3: "USA"
  aliases: ["U.S.", "USA", "United States of America"]
  count: 4
  mentions:
    - text: "U.S."
      span: {start: 100, end: 104}
    - text: "USA"
      span: {start: 200, end: 203}
    - text: "United States of America"
      span: {start: 300, end: 325}
    - text: "United States"
      span: {start: 400, end: 412}
```

**Techniques:**
- **ISO 3166 codes:** Standard country/territory identifiers
- **Fuzzy matching:** Handle spelling variations
- **Official names:** Use UN/government databases

### 5. DATE
**Normalization Strategy:** ISO 8601 format, resolve relative dates

**Professional Example:**
```yaml
- id: d001
  type: DATE
  normalized: "2024-03-20"
  format: "ISO8601"
  aliases: ["March 20, 2024", "20/03/2024"]
  count: 3
  mentions:
    - text: "March 20, 2024"
      span: {start: 50, end: 64}
    - text: "20/03/2024"
      span: {start: 120, end: 130}
    - text: "2024-03-20"
      span: {start: 200, end: 210}
```

**Techniques:**
- **dateutil.parser:** Flexible date parsing
- **ISO 8601:** Standard YYYY-MM-DD format
- **Relative resolution:** "today", "next week" → actual dates

### 6. TIME
**Normalization Strategy:** 24-hour ISO format, timezone handling

**Professional Example:**
```yaml
- id: t001
  type: TIME
  normalized: "09:00:00"
  timezone: "UTC-5"
  aliases: ["9:00 AM", "09:00", "0900h"]
  count: 3
  mentions:
    - text: "9:00 AM"
      span: {start: 500, end: 507}
    - text: "09:00"
      span: {start: 600, end: 605}
    - text: "0900h"
      span: {start: 700, end: 705}
```

**Techniques:**
- **24-hour format:** HH:MM:SS standard
- **Timezone inference:** Context + document metadata
- **Keyword resolution:** "noon" → "12:00:00"

### 7. MONEY
**Normalization Strategy:** ISO 4217 currency codes, numeric storage

**Professional Example:**
```yaml
- id: mon001
  type: MONEY
  normalized: 2500000
  currency: "USD"
  display: "$2,500,000"
  aliases: ["two point five million dollars", "$2.5M", "2,500,000 USD"]
  count: 3
  mentions:
    - text: "two point five million dollars"
      span: {start: 100, end: 130}
    - text: "$2.5M"
      span: {start: 140, end: 145}
    - text: "2,500,000 USD"
      span: {start: 160, end: 172}
```

**Techniques:**
- **Regex patterns:** Handle numeric variations and multipliers
- **Currency detection:** Symbol/text → ISO 4217 codes
- **Number words:** "two million" → 2000000

### 4. LOCATION
**Normalization Strategy:** Authoritative geographic IDs, alias tables, fuzzy matching for variants

**Professional Example:**
```yaml
- id: loc001
  type: LOCATION
  normalized: "New York City"
  geonames_id: 5128581
  iso: "US-NY"
  aliases: ["NYC", "New York", "Manhattan"]
  count: 3
  mentions:
    - text: "NYC"
      span: {start: 100, end: 103}
    - text: "New York City"
      span: {start: 200, end: 213}
    - text: "Manhattan"
      span: {start: 300, end: 309}
```

**Techniques:**
- **GeoNames database:** Authoritative geographic IDs and canonical names
- **Alias tables:** Pre-built mappings for common variants (NYC → New York City)
- **Fuzzy matching:** Levenshtein + token similarity for typos and variations

### 5. GPE (Geopolitical Entity)
**Normalization Strategy:** ISO 3166 country codes, official government names, fuzzy matching

**Professional Example:**
```yaml
- id: gpe001
  type: GPE
  normalized: "United States"
  iso_alpha2: "US"
  iso_alpha3: "USA"
  aliases: ["U.S.", "USA", "United States of America"]
  count: 4
  mentions:
    - text: "U.S."
      span: {start: 100, end: 104}
    - text: "USA"
      span: {start: 200, end: 203}
    - text: "United States of America"
      span: {start: 300, end: 325}
    - text: "United States"
      span: {start: 400, end: 412}
```

**Techniques:**
- **ISO 3166 codes:** Standard country/territory identifiers (US, USA)
- **Official names:** Use UN/government databases for canonical forms
- **Fuzzy matching:** Handle spelling variations and informal names

### 6. DATE
**Normalization Strategy:** ISO 8601 format, resolve relative dates

**Professional Example:**
```yaml
- id: d001
  type: DATE
  normalized: "2024-03-20"
  format: "ISO8601"
  aliases: ["March 20, 2024", "20/03/2024"]
  count: 3
  mentions:
    - text: "March 20, 2024"
      span: {start: 50, end: 64}
    - text: "20/03/2024"
      span: {start: 120, end: 130}
    - text: "2024-03-20"
      span: {start: 200, end: 210}
```

**Techniques:**
- **dateutil.parser:** Flexible date parsing for multiple formats
- **ISO 8601:** Standard YYYY-MM-DD canonical format
- **Relative resolution:** "today", "next week" → actual dates

### 7. TIME
**Normalization Strategy:** 24-hour ISO format, timezone handling

**Professional Example:**
```yaml
- id: t001
  type: TIME
  normalized: "09:00:00"
  timezone: "UTC-5"
  aliases: ["9:00 AM", "09:00", "0900h"]
  count: 3
  mentions:
    - text: "9:00 AM"
      span: {start: 500, end: 507}
    - text: "09:00"
      span: {start: 600, end: 605}
    - text: "0900h"
      span: {start: 700, end: 705}
```

**Techniques:**
- **24-hour format:** HH:MM:SS standard for consistency
- **Timezone inference:** Context + document metadata for timezone detection
- **Keyword resolution:** "noon", "midnight" → standardized times

### 8. MEASUREMENT
**Normalization Strategy:** SI units, metric conversion, categorize by measurement type

**Professional Example:**
```yaml
- id: meas001
  type: MEASUREMENT
  normalized: 1.83
  unit: "m"
  canonical: "6 ft"
  category: "length"
  aliases: ["6 feet", "six ft", "1.83 meters"]
  count: 3
  mentions:
    - text: "6 feet"
      span: {start: 100, end: 106}
    - text: "six ft"
      span: {start: 200, end: 206}
    - text: "1.83 meters"
      span: {start: 300, end: 311}
```

**Techniques:**
- **SI conversion:** Store in standard metric units (meters, kilograms, etc.)
- **Category classification:** Length, weight, volume, temperature, percentage, technical
- **Unit normalization:** "ft" → "feet", expand abbreviations

## Unified Fact Set - Complete Document Example

**Final YAML Output (All Core 8 Together):**
```yaml
normalized_entities:
  - id: p001
    type: PERSON
    normalized: "John Smith"
    aliases: ["Mr. Smith", "Dr. Smith"]
    count: 3
    mentions:
      - text: "Mr. John Smith"
        span: {start: 10, end: 23}
      - text: "Dr. Smith"
        span: {start: 150, end: 159}
      - text: "Mr. Smith"
        span: {start: 300, end: 309}

  - id: org001
    type: ORG
    normalized: "Environmental Protection Agency"
    aliases: ["EPA"]
    count: 2
    mentions:
      - text: "EPA"
        span: {start: 45, end: 48}
      - text: "Environmental Protection Agency"
        span: {start: 200, end: 231}

  - id: loc001
    type: LOCATION
    normalized: "New York City, NY"
    aliases: ["NYC"]
    count: 1
    mentions:
      - text: "NYC"
        span: {start: 75, end: 78}

  - id: gpe001
    type: GPE
    normalized: "United States"
    iso_alpha2: "US"
    aliases: ["U.S."]
    count: 1
    mentions:
      - text: "U.S."
        span: {start: 120, end: 124}

  - id: d001
    type: DATE
    normalized: "2024-03-20"
    format: "ISO8601"
    aliases: ["March 20, 2024"]
    count: 1
    mentions:
      - text: "March 20, 2024"
        span: {start: 180, end: 194}

  - id: t001
    type: TIME
    normalized: "14:30:00"
    timezone: "UTC-5"
    aliases: ["2:30 PM"]
    count: 1
    mentions:
      - text: "2:30 PM"
        span: {start: 220, end: 227}

  - id: mon001
    type: MONEY
    normalized: 2500000
    currency: "USD"
    display: "$2,500,000"
    aliases: ["$2.5M"]
    count: 1
    mentions:
      - text: "$2.5M"
        span: {start: 250, end: 255}

  - id: meas001
    type: MEASUREMENT
    normalized: 1.83
    unit: "m"
    canonical: "6 feet"
    category: "length"
    aliases: ["6 ft"]
    count: 1
    mentions:
      - text: "6 ft"
        span: {start: 280, end: 285}
```

## Professional Strategy Benefits

✅ **Canonical Standards:** ISO formats for all entity types
✅ **Complete Preservation:** All raw mentions with exact spans maintained  
✅ **Cross-Document Linking:** Stable IDs enable entity tracking across documents
✅ **AI-Ready:** Clean normalized values for computation and analysis
✅ **Audit Trail:** Full aliases and mention history for transparency
✅ **Industry Compliance:** Follows established standards (ISO, SEC, USPS, etc.)

## Aho-Corasick vs Regex Decision Matrix

| Entity Type | AC Suitable | Regex Required | Fuzzy Needed |
|-------------|-------------|----------------|--------------|
| PERSON      | Partial ✓   | Titles ✓       | Names ✓      |
| ORG         | Acronyms ✓  | Patterns ✓     | Variations ✓ |
| LOCATION    | Known ✓     | Addresses ✓    | Variations ✓ |
| GPE         | Exact ✓     | No ❌          | Variations ✓ |
| DATE        | Keywords ✓  | Formats ✓      | No ❌        |
| TIME        | Keywords ✓  | Formats ✓      | No ❌        |
| MONEY       | Symbols ✓   | Numbers ✓      | No ❌        |
| MEASUREMENT | Units ✓     | Numbers ✓      | No ❌        |

## Hybrid Architecture Recommendation

**Stage 1: Aho-Corasick** (Fast exact matching)
- Known entities, acronyms, keywords
- Pattern prefixes and suffixes

**Stage 2: Regex** (Flexible pattern matching)  
- Numeric patterns, date/time formats
- Complex structural patterns

**Stage 3: Fuzzy Matching** (Similarity matching)
- Person name variations
- Organization name variations
- Location name variations

This hybrid approach maximizes Aho-Corasick's speed for exact matches while leveraging regex and fuzzy matching where AC limitations require it.

## Testing Strategy

### Phase 1: Entity Resolution Testing
- [ ] Test person name matching (nicknames, titles, initials)
- [ ] Test organization acronym expansion
- [ ] Test money amount standardization
- [ ] Test date format normalization
- [ ] Validate unique ID generation (no collisions)

### Phase 2: Canonical Form Testing
- [ ] Verify canonical name quality across all entity types
- [ ] Test fuzzy matching for similar entities
- [ ] Validate count accuracy in mentions
- [ ] Test span preservation in normalization

### Phase 3: Global Replacement Testing
- [ ] Test Aho-Corasick performance on entity substitution
- [ ] Verify `||canonical||id||` format implementation
- [ ] Test document readability after normalization
- [ ] Validate AI knowledge extraction on normalized text

### Phase 4: Pipeline Integration Testing
- [ ] Test normalization phase insertion between enrich and extract
- [ ] Verify memory efficiency (in-RAM processing)
- [ ] Test configuration flag for raw entities output
- [ ] Validate semantic analysis enhancement

## Performance Requirements

### Memory Efficiency
- Process normalization entirely in RAM
- No intermediate file I/O
- CloudFlare Workers compatible (1GB limit)

### Speed Targets
- Normalization phase: <50ms per document
- Entity resolution: O(n) linear complexity
- Global replacement: Aho-Corasick linear scan

### Quality Metrics
- Entity deduplication accuracy: >95%
- Canonical form consistency: >98%
- Span preservation: 100%
- ID uniqueness: 100% (zero collisions)

## Implementation Notes

### Configuration Options
```yaml
normalization:
  enabled: true
  output_format: "canonical_with_id"  # ||canonical||id||
  include_raw_entities: false         # Debug flag
  fuzzy_matching_threshold: 0.85      # Person name similarity
  canonical_preference: "longest"     # For name variants
```

### Error Handling
- Graceful degradation if normalization fails
- Preserve original entities as fallback
- Log normalization statistics for monitoring

## Success Criteria
1. **Clean YAML Output:** Single normalized_entities section with canonical structure
2. **AI-Ready Text:** Documents with consistent entity representations
3. **Performance:** No significant pipeline slowdown (<10% overhead)
4. **Accuracy:** High-quality canonical forms with comprehensive span tracking
5. **Scalability:** Handles documents with hundreds of entities efficiently