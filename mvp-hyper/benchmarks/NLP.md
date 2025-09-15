Gotcha. If spaCy was \~16 pages/s for you, you’ll need **deterministic, compiled automata** and/or **native sidecars**. Here’s a tight menu of **CPU-only** options that can realistically push *hundreds to thousands of small Markdown pages per second* on one core, given sane page sizes.

# What to use (no ML, no GPU)

## A) Exact-term (gazetteer) matchers

* **pyahocorasick (C ext.)** – Classic Aho-Corasick trie; O(n) scan. Great for big termlists.
* **marisa-trie (C++ via Python)** – Minimal, memory-mapped static trie; tiny RAM footprint, fast lookups.
* **flashtext2** – Very light keyword extractor if you don’t need all offsets, faster than many regex cases.
* **spaCy EntityRuler / PhraseMatcher (rules-only)** – If you must keep spaCy objects but drop models; still slower than the three above.

**When it shines:** universal dictionaries, product catalogs, standards lists, ICD/ISO, orgs, etc.

## B) Pattern entities (emails, URLs, money, percents, IDs, citations)

* **Hyperscan / Vectorscan (Python bindings)** – Multi-regex engine using SIMD; compile once, scan at multi-GB/s per core. Best raw speed.
* **RE2 (pyre2)** – Linear-time, safe on untrusted input; slower than Hyperscan but still very fast and simple to deploy.

**When it shines:** everything you’d usually do with many regexes, plus Hearst-style patterns (“such as”, “including”, “X is a Y”).

## C) Tokenization / sentence windows (for lightweight relations)

* **BlingFire** – Finite-state tokenizer/sentencer; tiny and extremely fast.
* **Rule windows** – Co-occurrence within same sentence or ±N tokens, plus verb cues (must/shall/required to/owned by/etc.).

**When it shines:** you need just enough structure to place edges without a parser.

## D) Address/Date/Name normalizers (call only on candidates)

* **dateparser** – Broad date normalization, light if used sparingly.
* **probablepeople** – Western-style name/company splitter; use on likely name spans only.
* **libpostal/pypostal** – Accurate but heavy; avoid under a strict \~1 GB cap unless absolutely necessary.

# Sidecar binaries for “over-1000 pages/s” ambitions

If you’re open to subprocess sidecars (Rust/C++), these are **ridiculously fast** and still CPU-only:

* **ripgrep (rg)** – Rust, uses DFA/automata; supports fixed-string lists (`-F -f terms.txt`), word boundaries, JSON output. Perfect for massive gazetteers and many patterns.
* **ugrep** (with Hyperscan enabled) – C++/Hyperscan build; excels at huge multi-regex sets.
* **hyperscan tools** (e.g., hsbench/hsfilter) – Precompile a database of patterns and stream text through it.

**Why sidecars:** You bypass Python’s overhead for the hot loop; Python just orchestrates I/O and merges results.

# Relationship extraction (still CPU-light)

* **Windowed co-occurrence + typed cues:** within sentence/section, look for cue verbs and pattern anchors to propose edges like
  `ORG —[must_comply_with]→ AUTHORITY`, `PRODUCT —[belongs_to]→ ORG`, `DOC_ID —[references]→ STANDARD`.
* **Header anchoring for Markdown:** if a section header names an entity (e.g., `## Vendor Alpha`), bias edges to that node for entities found under it.
* **Hearst-style patterns:** “X such as A, B, and C” → `A,B,C is_a X`. Implement with your fast regex engine.

# What typically hits your target

* **Small Markdown pages (a few KB each):**

  * **ripgrep (fixed-strings) + BlingFire + RE2/Hyperscan** orchestration routinely processes *thousands* of pages/sec on a single modern core, I/O permitting.
* **Larger pages (tens of KB):**

  * Expect **hundreds to low-thousands** pages/sec with **Hyperscan** for patterns and **Aho-Corasick/marisa-trie** for dictionaries.

> Throughput ultimately scales with **bytes/sec** more than “pages/sec.” To stay within \~1 GB RAM, **pre-compile** pattern banks/tries once, **stream** files (no full in-RAM corpus), and **avoid per-page initialization**.

# Quick decision guide

* **Dictionary-heavy?** marisa-trie or pyahocorasick (Python) or ripgrep `-F` (sidecar).
* **Pattern-heavy?** Hyperscan/Vectorscan (best) or RE2 (simpler).
* **Need sentence windows?** BlingFire.
* **Strict 1 GB cap?** Prefer marisa-trie + RE2; avoid libpostal.
* **Max speed / minimal Python work?** ripgrep/ugrep sidecar + JSON → Python aggregator.

If you want, tell me your **entity domains** (e.g., orgs, standards, SKUs, addresses) and the **average page size** you're processing. I'll map that to an exact stack and estimate realistic MB/s and pages/s for your box, along with a minimal ops layout (precompiled DBs, buffers, and streaming).

---

# OUR BENCHMARK PLAN & TESTING STRATEGY

## Current Performance Baseline
- **Enhanced Regex**: 670 pages/sec (closest to target)
- **spaCy NER**: 15.5 pages/sec (too slow)
- **Stanford Stanza**: 51.6 pages/sec (too slow)
- **TARGET**: 1000+ pages/sec for real-time classification

## Our Entity Domains & Use Case
- **Documents**: OSHA safety standards, worker rights, compliance docs
- **Average page size**: ~3-5KB markdown pages
- **Total pages tested**: 81 pages across 10 documents
- **System**: 16 CPUs, 11.7GB RAM

### Entity Types We Need to Extract:
1. **OSHA Standards**: CFR 1926.95, OSHA 3162-01R, ISO 9001, ANSI Z87.1
2. **Organizations**: Department of Labor, OSHA, EPA, CDC, IBM
3. **Chemical Entities**: asbestos, benzene, lead, silica, formaldehyde
4. **Safety Requirements**: "must wear", "shall provide", "required to comply"
5. **Measurements**: "50 percent", "8 hours", "30 days", "$1.2 million"
6. **Person Titles**: "Dr. Johnson", "Director Smith", "Inspector Brown"
7. **Locations**: California, New York, Washington, Boston
8. **Contact Info**: emails, phone numbers
9. **Dates**: 2023-01-15, 03/15/2024
10. **Conditionals**: "if exposed", "when working", "unless protected"

## Libraries We're Benchmarking

### ✅ INSTALLED & READY TO TEST:

#### Priority 1: Exact-term Matchers (Gazetteers)
- **pyahocorasick v2.2.0** - Aho-Corasick trie for dictionary lookups
- **marisa-trie v1.3.1** - Memory-mapped static tries
- **flashtext v2.7** - Lightweight keyword extractor

#### Priority 2: Pattern Engines  
- **hyperscan v0.7.23** - SIMD-optimized multi-regex engine
- **RE2** - (need to install pyre2) Linear-time regex engine

#### Priority 3: Tokenization
- **blingfire v0.1.8** - Fast finite-state tokenizer

#### Priority 4: Sidecar Binaries
- **ripgrep (rg)** - Available system-wide
- **ugrep** - Need to install/compile

## Performance Assumptions & Predictions

| Library | Expected Pages/Sec | Memory Usage | Best For | Confidence |
|---------|-------------------|--------------|----------|------------|
| **pyahocorasick** | 1500-2000 | <100MB | OSHA standards, orgs | 🟢 HIGH |
| **hyperscan** | 2000-3000 | <200MB | All patterns combined | 🟢 HIGH |
| **marisa-trie** | 1200-1800 | <50MB | Memory-efficient lookups | 🟡 MED |
| **flashtext** | 1000-1500 | <100MB | Simple keyword extraction | 🟡 MED |
| **blingfire** | 2500+ | <100MB | Tokenization + windowing | 🟡 MED |
| **ripgrep sidecar** | 3000-5000 | <100MB | Ultimate performance | 🟢 HIGH |

### Why We Think These Will Work:
1. **No ML overhead** - Pure algorithmic approaches vs spaCy's neural networks
2. **Pre-compilation** - Build dictionaries/patterns once, scan thousands of times
3. **SIMD optimization** - Hardware acceleration for text processing
4. **Linear complexity** - O(n) scanning vs spaCy's complex model inference

## Benchmark Test Data

### What We're Actually Testing With:
- **Real OSHA documents**: 3162-screening-and-surveillance-a-guide-to-osha-standards.md
- **Worker rights booklets**: 3021-workers-rights-booklet-english.md
- **Safety alerts**: 4141-keep-workers-alive-during-diving-operations-osha-alert-english.md
- **Technical documents**: shib-03242004-suspension-traumaorthostatic-intolerance.md

### Sample Entity Extractions Expected:
```
OSHA Standards: ["OSHA 3162-01R", "CFR 1910.132", "ANSI Z87.1"]
Organizations: ["Occupational Safety and Health Administration", "Department of Labor", "CDC"]
Chemicals: ["asbestos", "benzene", "lead", "silica"]
Requirements: ["must comply with safety standards", "shall provide adequate protection"]
Measurements: ["50 percent", "8 hours", "30 days", "$500,000"]
Contacts: ["bpf@zurich.ibm.com", "(202) 693-1999"]
```

## Success Criteria

### 🎯 Must Achieve:
- **≥1000 pages/sec** processing speed
- **≥500 entities** extracted per test run
- **<500MB** memory usage
- **<1 second** setup time

### 🚀 Stretch Goals:
- **≥2000 pages/sec** for batch processing mode
- **Combined approach** (multiple libraries working together)
- **Real-time streaming** capability

## Testing Methodology

### Phase 1: Individual Library Tests
1. **pyahocorasick**: Test with OSHA standards dictionary (200+ terms)
2. **hyperscan**: Test with all regex patterns compiled together
3. **marisa-trie**: Test memory-efficient dictionary lookups
4. **flashtext**: Test simple keyword extraction

### Phase 2: Combined Approaches
- **Dictionary + Patterns**: pyahocorasick + hyperscan
- **Memory Optimized**: marisa-trie + flashtext
- **Maximum Speed**: ripgrep sidecar + JSON parsing

### Phase 3: Integration Testing
- Test with full 81-page document set
- Measure end-to-end pipeline performance
- Compare accuracy vs speed tradeoffs

## Next Steps
1. ✅ Install all libraries (COMPLETED)
2. 🔄 Create comprehensive benchmark script
3. 🔄 Run individual library tests
4. 🔄 Test combined approaches
5. 🔄 Analyze results and recommend final approach
