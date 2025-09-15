Nice! Hitting \~1,800 pages/s with pyahocorasick means your hot loop is healthy. With **\~15,000 entities across 740 docs (\~20.3 entities/doc on average)**, here’s what you should expect from a pure Aho-Corasick (gazetteer) pass—and how to sanity-check it.

# What AC (gazetteer) *does* give you

* **Exact string hits** from your term list, very fast, with start/end offsets.
* **No context or disambiguation**: every surface match is treated as “the entity,” even if it’s part of a company name, a URL, a code sample, etc.
* **Overlaps and nesting**: shorter terms inside longer ones will both match unless you suppress them (e.g., “York” inside “New York”).
* **Case behavior as configured**: case-sensitive by default; you may get misses on casing variants unless you normalized inputs.

# What those numbers typically look like

* **Entity density** (\~20/doc) is reasonable for Markdown corpora with lists, tables, and headings. Expect higher density in TOCs, glossaries, vendor lists, and footers.
* **Heavy head, long tail**: a few very frequent entities (brands, countries, months) dominate; many singletons appear once.
* **Section skew**: most hits cluster in headers, bullet lists, and tables. Narrative paragraphs yield fewer raw gazetteer matches.

# Common artifacts you’ll see (and should handle next)

1. **Over-tagging in code/URLs**
   Entities firing inside code fences, link URLs, or paths.
   *Mitigation:* suppress matching in code blocks and URLs, or downweight those zones.

2. **Substring/partial hits**
   “York” firing inside “New York,” “Ann” inside “Ann Arbor.”
   *Mitigation:* longest-match-wins or require word-boundary rules for certain lists.

3. **Ambiguous tokens**
   “May” (month vs. verb), “General,” “Office,” “Apple” (fruit vs. org).
   *Mitigation:* domain-specific stoplists, section-based biasing (e.g., “Team” vs “Vendors”), and proximity cues (emails, titles, legal suffixes).

4. **Casing/diacritics variants**
   Misses on “São Paulo” vs “Sao Paulo,” “ACME” vs “Acme.”
   *Mitigation:* case/diacritic-insensitive normalization on both text and dictionary (store canonical form separately).

5. **Plural/inflectional variants**
   “Laboratories” vs “Laboratory,” “Universities” vs “University.”
   *Mitigation:* add morphological variants to your gazetteer or lemmatize dictionary terms offline.

# Quick QA checks (no code, just what to look at)

* **Top-50 entities by frequency**: eyeball precision; if junk appears here, fix dictionary or add anti-rules—this cleans a huge fraction fast.
* **Per-section hit map**: verify most hits are in sane zones (headers, lists, tables) and not code/links.
* **Overlap rate**: % of matches that are substrings of a longer match; high numbers signal a need for longest-match policy.
* **Doc coverage**: % of docs with ≥1 entity; if low, your dictionaries are too narrow or casing/variants need work.
* **Source mix**: if you have multiple gazetteers (orgs, places, units), check each one’s precision separately.

# What to add next (still CPU-light) to get “spaCy-like” utility

* **Longest-match-wins resolution** for overlapping spans, with type priority (e.g., prefer GPE “New York” over a bare ORG hit “York Labs” only when context warrants).
* **Section-aware rules** for Markdown: “Team/People/Contributors” boost PERSON-like spans; “Vendors/Partners/Companies” boost ORG; suppress in code fences and link URLs.
* **Pattern entities** using a SIMD/linear-time regex engine (RE2 or Hyperscan/Vectorscan) for MONEY, DATE, CARDINAL, QUANTITY, emails, URLs, IDs—this fills out your “core 7” reliably at high speed.
* **Light normalizers on candidates only**: `dateparser` for DATE strings that regex flagged, small unit lists for QUANTITY, ISO currency codes for MONEY.
* **Micro-classifier (scoring rules) for PERSON vs ORG**: honorifics, name lists, legal suffixes, email/domain agreement, title cues—cheap signals that dramatically cut ORG junk.

# A quick read on whether your 15k entities are “good”

* If ≥80% of your **top-50** look correct after a glance, you’re in great shape; fix the 5–10 noisy tokens and you’ll clean most noise.
* If **overlap rate** is >10–15%, implement longest-match and word-boundary policies.
* If **many hits** come from **code/links**, add zone suppression—precision will jump immediately.
* If **GPE and ORG** are muddled, add the legal-suffix list and a small countries/cities gazetteer; that usually separates them.

If you want, tell me your rough **gazetteer contents** (names, orgs, geos, units, currencies) and typical **page size**. I’ll translate your current results into a short “expectation sheet” with target precision for each bucket and a prioritized punch list to turn this into clean PERSON/ORG/GPE/MONEY/DATE/CARDINAL/QUANTITY output at the same speed.
