Example Extraction (from one paragraph)
Raw text input:

H.R. 1234, introduced on January 15, 2025, by Rep. Maria Smith (D-CA) and Sen. John Lee (R-TX), appropriates $500,000,000 to the Department of Energy for clean energy research in FY2026. The bill was reported by the House Committee on Appropriations and passed the House with a vote of 312–118 on February 10, 2025.

Structured facts (JSON):

[
  {
    "bill_id": "HR1234-118",
    "predicate": "introduced_on",
    "value": "2025-01-15",
    "sponsors": [
      {"person_id": "S001234", "name": "Rep. Maria Smith", "party": "D", "state": "CA"},
      {"person_id": "L009876", "name": "Sen. John Lee", "party": "R", "state": "TX"}
    ]
  },
  {
    "bill_id": "HR1234-118",
    "predicate": "appropriates_to",
    "object_id": "DOE",
    "amount_usd": 500000000,
    "fiscal_year": 2026,
    "purpose": "clean energy research"
  },
  {
    "bill_id": "HR1234-118",
    "predicate": "reported_by",
    "object_id": "H-APPR"
  },
  {
    "bill_id": "HR1234-118",
    "predicate": "passed_in",
    "object_id": "US-House",
    "vote": {"yea": 312, "nay": 118},
    "date": "2025-02-10"
  }
]
Popular Tools for Cheap Extraction
Regex & Pattern Matching: built-in Python re, FlashText for ultra-fast keyword scanning.
Named Entity Recognition (NER):
spaCy → fast, extensible, offline.
Stanza → good accuracy, slower than spaCy.
Flair → powerful embeddings, slower throughput.
Gazetteer/Dictionaries:
RapidFuzz → fuzzy matching.
FlashText → keyword dictionaries at scale.
Dependency Parsing / Part-of-Speech (POS):
spaCy (small/medium models).
Stanza (accurate but slower).
Speed Estimates (rough, typical hardware)
Method	Pages/sec*	Chunks/sec**	Notes
Regex (Python re)	2000–5000	10,000+	CPU only, scales linearly
FlashText (dictionary scan)	5000–20,000	50,000+	Extremely fast keyword lookup
RapidFuzz (fuzzy match)	200–500	1000+	Slower but flexible
spaCy small (NER + POS)	30–100	200–600	Multi-core batching speeds this up
Stanza (NER + POS)	10–30	80–200	Higher accuracy, slower throughput
Flair embeddings	5–15	50–100	More accurate contextual NER
Hybrid (Regex + spaCy NER)	50–200	300–800	Best cost/coverage balance



Here’s a **Product Requirements Document (PRD)** written in plain Markdown that captures exactly what you asked for: a **local, CPU-based, cost-effective knowledge extraction system** using regex, NLP, dictionaries, and graphs — no external LLMs.

---

```markdown
# PRD: Local, CPU-Based Knowledge Extraction System

## 1. Executive Summary
We need a system to extract structured knowledge (facts, entities, relationships) from large volumes of raw text (PDFs, web pages, transcripts, bill texts).  
The goal is **cost-effective, local-only processing** that runs on commodity CPUs with RAM, without relying on cloud LLMs.  
We will use **cheap-first techniques** — regex, dictionaries, lightweight NLP, and graph reconciliation — to achieve scalable fact extraction and verification.

---

## 2. Goals
- Extract entities (people, organizations, bills, committees, dates, money amounts, votes).  
- Extract relationships between entities (e.g., appropriates_to, sponsored_by, passed_in).  
- Store results in a structured schema (documents → chunks → candidate_facts → facts).  
- Preserve provenance (every fact linked back to original text span and source).  
- Run entirely offline, CPU-only, using open-source libraries.  
- Be cost-effective: millions of pages processed per day on commodity hardware.

---

## 3. Non-Goals
- No cloud APIs or external LLM usage.  
- No GPU acceleration (optional future).  
- No complex ML model training pipelines (only use pre-trained light NLP libs).  
- No end-user dashboard included (this PRD stops at structured fact store).

---

## 4. Requirements

### 4.1 Input Sources
- PDF documents (laws, regulations, reports).  
- HTML web pages (bill trackers, press releases).  
- TXT/Docx documents (meeting notes, transcripts).  
- Metadata: source URL, crawl time, domain.

### 4.2 Processing Pipeline
1. **Document ingestion**  
   - Parse raw files into text.  
   - Tools: Apache Tika, pdfminer.six, BeautifulSoup.  
   - Performance: 10–100 pages/sec (I/O bound).

2. **Chunking**  
   - Split text into chunks (by pages, sections, or tokens).  
   - Tools: custom Python splitter, LangChain splitters.  
   - Performance: 1,000+ chunks/sec.

3. **Cheap-first extraction**  
   - Regex + finite state machines: bill IDs, dollar amounts, dates, votes.  
   - Dictionary/gazetteer lookup: agencies, committees, legislators.  
   - Named Entity Recognition (NER): people, organizations, money, dates.  
   - Part-of-Speech (POS) tagging + dependency parsing: connect “who did what to whom.”  
   - Tools: Python regex, FlashText, RapidFuzz, spaCy small, Stanza.  
   - Performance:  
     - Regex: 2,000–5,000 pages/sec  
     - FlashText: 50,000+ matches/sec  
     - spaCy small: 30–100 pages/sec

4. **Candidate facts**  
   - Store raw proposed facts with provenance: subject, predicate, object, value.  
   - Example: `{bill=HR1234} --appropriates_to--> {DOE}, $500M, FY2026`.

5. **Verification**  
   - Run cheap checks on candidate facts:  
     - Numeric parsing (money, votes).  
     - Date parsing.  
     - Cross-check entity IDs against gazetteers.  
   - Tools: Python `dateutil`, regex validators, RapidFuzz.  
   - Performance: 5,000+ checks/sec (CPU cheap).

6. **Reconciliation**  
   - Group candidate facts describing the same real-world fact.  
   - Merge duplicates, resolve conflicts, assign confidence.  
   - Tools: SQL GROUP BY, Dedupe/Splink (record linkage).  
   - Performance: 100k+ facts/sec with indexes.

7. **Fact store (graph/relational)**  
   - Final fused facts with provenance links.  
   - Store in Postgres or Neo4j.  
   - Schema: documents, chunks, candidate_facts, facts, fact_support, entities, gazetteers, taxonomies.

---

## 5. Technical Design

### 5.1 Data Model
- **documents**: one row per ingested source.  
- **chunks**: segmented text for extraction.  
- **candidate_facts**: raw extractions.  
- **verification_results**: pass/fail cheap checks.  
- **reconciliation_groups**: align same real-world facts.  
- **facts**: fused truths with confidence.  
- **fact_support**: evidence linking facts back to documents.  
- **entities/entity_alias**: canonical IDs with alias mappings.  
- **gazetteers**: curated lists for fast lookups.  
- **taxonomies**: tags for thematic grouping.

### 5.2 Processing Stack
- **Language:** Python 3.11  
- **Libraries:**  
  - Parsing: Apache Tika, pdfminer.six, BeautifulSoup  
  - Regex: Python `re`  
  - Dictionaries: FlashText, RapidFuzz  
  - NLP: spaCy (small models), Stanza  
  - Storage: PostgreSQL or DuckDB  
- **Execution model:** batch jobs, parallelized by documents/chunks  
- **Deployment:** Linux servers or local workstation, CPU-only

---

## 6. Performance Targets
- **Ingestion:** 50k–100k documents/day on 16-core CPU, 64GB RAM.  
- **Extraction:** regex/dictionary processing at 2,000–20,000 pages/sec; NLP at 30–100 pages/sec.  
- **Verification:** near-free; 5,000+ checks/sec.  
- **Reconciliation:** 100k+ facts/sec with proper indexes.  
- **Storage:** millions of facts and evidences manageable in Postgres with partitioning.

---

## 7. Risks & Mitigations
- **Ambiguity in entity names (e.g., DOE = Energy vs Education).**  
  *Mitigation:* Gazetteers + context rules.  
- **Cross-sentence relationships may be missed.**  
  *Mitigation:* Simple co-reference resolution or sentence merging heuristics.  
- **Accuracy lower than LLM-based extraction.**  
  *Mitigation:* Cheap-first covers 80–90%; ambiguous cases can be flagged for later review.  
- **Scaling to 100M+ documents.**  
  *Mitigation:* Use distributed Postgres (Citus) or graph DB for horizontal scale.

---

## 8. Deliverables
- Working ETL pipeline (documents → facts).  
- Postgres schema + indexes.  
- Extraction modules: regex, gazetteer, spaCy/Stanza wrappers.  
- Verification + reconciliation logic.  
- Documentation + scripts to run end-to-end locally.  

---

## 9. Success Criteria
- **Coverage:** 80% of bill/regulation facts extracted with regex + NLP.  
- **Speed:** Process 100k+ documents/day on CPU hardware.  
- **Cost:** Zero cloud inference cost; commodity server only.  
- **Provenance:** Every fact linked to at least one evidence span.  
```

---

✅ This PRD sets a **clear local-first design**: regex + dictionaries for speed, lightweight NLP for semantics, graph/relational reconciliation for structure.
Would you like me to also create a **“Cheap vs Moderate vs Heavy” methods comparison table** inside this PRD, so you can decide when to stop at regex and when to escalate to NLP or graph reasoning?
