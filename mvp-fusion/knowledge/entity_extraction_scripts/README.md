# Entity Extraction Scripts

This folder contains all working scripts used to build a 100K/100K/100K+ entity corpus for founder intelligence and NER disambiguation.

## Overview

We successfully built a corpus of:
- **100,000 first names** 
- **100,000 last names**
- **100,000+ organizations**

## Scripts

### 1. `scrape_all_categories.py`
**Purpose:** Scrapes all company categories from companiesmarketcap.com using a URL list  
**Data source:** companiesmarketcap.com (147 categories)  
**Output:** ~9,771 companies with rank, name, market cap, price, country  

**How to run:**
```bash
# Requires urllist.txt in same directory
python scrape_all_categories.py
```

**Output location:** `data/companies_all_categories/`
- `all_company_names_final.txt` - All company names (for corpus)
- `by_category/` - Separate files per industry category
- JSON and CSV files with full data

---

### 2. `extract_yelp_businesses.py`
**Purpose:** Extracts US businesses from Yelp Open Dataset  
**Data source:** HuggingFace dataset `yashraizada/yelp-open-dataset-business`  
**Output:** ~114,065 US business names  

**How to run:**
```bash
python extract_yelp_businesses.py
```

**Output location:** `data/yelp_businesses/`
- `yelp_us_businesses.txt` - Business names only
- `yelp_us_businesses_full.json` - Full business data

---

### 3. `entity_corpus_builder.py`
**Purpose:** Builds comprehensive first/last name corpus from ai4privacy dataset  
**Data source:** HuggingFace dataset `ai4privacy/pii-masking-300k`  
**Output:** 100K+ unique first and last names  

**How to run:**
```bash
python entity_corpus_builder.py
```

**Output location:** `data/entity_corpus/`
- `first_names_100k.txt` - Top 100K first names
- `last_names_100k.txt` - Top 100K last names
- Statistics and validation files

---

### 4. `extract_concatenated_orgs.py`
**Purpose:** Extracts organizations from 500K NER dataset with concatenated format  
**Data source:** HuggingFace dataset `adambuttrick/500K-ner-indexes-multiple-organizations`  
**Output:** ~24,491 US organizations  

**How to run:**
```bash
python extract_concatenated_orgs.py
```

**Output location:** `data/concatenated_orgs/`
- `us_organizations_cleaned.txt` - Cleaned organization names

---

### 5. `download_us_bulk_data.py`
**Purpose:** Downloads US organization data from multiple government/public sources  
**Data sources:** OpenData500, SEC, USAspending, etc.  
**Output:** ~1,035 companies from various US sources  

**How to run:**
```bash
python download_us_bulk_data.py
```

**Output location:** `data/us_orgs_bulk/`
- Multiple JSON/CSV files from different sources
- `combined_us_companies.txt` - All company names combined

---

### 6. `generate_domain_entities_working.py`
**Purpose:** Generates domain-specific companies using GPT-4o-mini API  
**Data source:** OpenAI API generation  
**Output:** Domain-specific company lists by year  

**How to run:**
```bash
# Requires OpenAI API key in script
python generate_domain_entities_working.py
```

**Configuration:** 
- Modify `DOMAINS` dict for different industries
- Modify `YEARS` list for different time periods
- Uses GPT-4o-mini (cost-effective model)

**Output location:** `data/test_working/`
- JSON files per domain and year

---

### 7. `urllist.txt`
**Purpose:** List of 147 category URLs from companiesmarketcap.com  
**Usage:** Input file for `scrape_all_categories.py`  

**Format:**
```
https://companiesmarketcap.com/tech/largest-tech-companies-by-market-cap/
https://companiesmarketcap.com/biotech/largest-companies-by-market-cap/
...
```

---

## Installation Requirements

```bash
pip install requests beautifulsoup4 pandas datasets openai
```

## Usage Order

To rebuild the complete entity corpus:

1. **Names corpus:**
   ```bash
   python entity_corpus_builder.py  # Extract 100K first/last names
   ```

2. **Organizations corpus:**
   ```bash
   python extract_yelp_businesses.py       # 114K businesses
   python scrape_all_categories.py         # 9.7K companies by category
   python extract_concatenated_orgs.py     # 24K organizations from NER
   python download_us_bulk_data.py         # 1K government sources
   ```

3. **Domain-specific (optional):**
   ```bash
   python generate_domain_entities_working.py  # Generate with GPT-4
   ```

## Output Statistics

| Script | Entity Type | Count | Quality |
|--------|------------|-------|---------|
| entity_corpus_builder.py | First Names | 100,000 | High - validated |
| entity_corpus_builder.py | Last Names | 100,000 | High - validated |
| extract_yelp_businesses.py | Organizations | 114,065 | High - real businesses |
| scrape_all_categories.py | Organizations | 9,771 | Very High - market data |
| extract_concatenated_orgs.py | Organizations | 24,491 | Medium - NER extracted |
| download_us_bulk_data.py | Organizations | 1,035 | High - government data |

**Total unique organizations available: 120,000+**

## Notes

- All scripts include rate limiting to be respectful to data sources
- Scripts save intermediate results for recovery from failures
- Output is deduplicated and cleaned
- Focus on US entities for consistency
- All outputs are UTF-8 encoded text files for easy integration

## Memory Constraints

These scripts are designed to work within:
- CloudFlare Workers: 128MB limit
- Local development: 1GB RAM
- Using streaming and chunking for large datasets