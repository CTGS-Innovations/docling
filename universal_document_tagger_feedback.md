Great start. You’ve got a clean surface API, sensible dataclasses, and pragmatic fallbacks. Here are the most important fixes and upgrades, ordered by impact.

# Critical bugs

1. YAKE tuple order is reversed
   `yake.extract_keywords()` returns `(keyword, score)`, but your loop unpacks `(score, keyword)`. That makes your YAKE path silently fail.

```python
# Fix
for keyword, score in yake_keywords:
    if is_high_quality_keyword(keyword, text):
        filtered_keywords.append(keyword.lower())
```

2. You destroy emails/URLs before trying to extract them
   `_preprocess_text()` strips `@` and `:/`, then `_extract_entities()` looks for emails/URLs. It will never find them. Keep two text streams: raw for regex entities, normalized for NLP.

```python
# In tag_document:
raw_text = text_content
clean_text = self._preprocess_text(raw_text)

entities = self._extract_entities(raw_text)  # use raw, not cleaned
# Everything else can use clean_text
```

3. Topic fallback can never work
   You lowercase in `_preprocess_text()`, then `_extract_topics()` fallback searches for `\b[A-Z][a-z]+ [A-Z][a-z]+\b`. It will return nothing on lowercased text. Use raw text or remove the capitalization heuristic.

```python
topics = self._extract_topics(raw_text)  # or drop the capitalized-phrase fallback
```

4. Confidence scaling is inconsistent and near-meaningless
   You compute `score = matches / word_count`, then do `min(0.9, score * 100)` and apply a geometric decay. On realistic corpora, confidences don’t reflect probabilities. Either:

* keep them as calibrated probabilities via sigmoid or softmax over class scores, or
* present uncalibrated scores but **don’t** label them “confidence.”

Minimal fix:

```python
# After computing raw scores dict (per class):
vals = list(scores.values())
if sum(vals) > 0:
    total = sum(vals)
    norm = {k: v/total for k, v in scores.items()}
else:
    norm = {k: 0.0 for k in scores}
# Use softmax if you want sharper separation:
# import math
# norm = {k: math.exp(v)/sum(math.exp(x) for x in vals) for k,v in scores.items()}
```

5. Substring counting creates false matches and O(n\*m) cost
   `text.count(indicator)` counts substrings, so `"api"` matches “capita”, and you’re repeatedly scanning the whole string. Tokenize once and count tokens with boundaries or use regex `\b`.

```python
# Pre-tokenize once
tokens = re.findall(r"\b\w[\w\-]*\b", text)  # keep hyphenated terms
freq = collections.Counter(tokens)

# Match per-token indicators
score = sum(freq[ind] for ind in indicators if ind in freq)
```

6. YAML string escaping is unsafe
   Your f-string nested quote replacement is fragile. Use a small helper that quotes as needed.

```python
def _yaml_value(self, value):
    if isinstance(value, str):
        if any(c in value for c in ['"', "'", ':', '#', '\n']):
            return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'
        return value
    ...
```

# High-value improvements

7. Replace the huge static stoplist with adaptive filters
   Your `common_words` set is massive and brittle. Prefer:

* **POS gating**: keep `NOUN`, `PROPN`, maybe `ADJ`.
* **Document-frequency gates** across your corpus: drop tokens with DF > 0.85 and DF < 2.
* **Entropy/dispersion**: remove tokens that are uniformly distributed.
  Keep a **small** static list only for tokenizer leaks.

8. Fix keyword quality checks

* Your frequency check: `text.lower().count(word_clean) / len(text.split())` mixes *substring hits* with *token denominator*. Swap to token counts, see #5.
* Allow multi-word phrases via PMI/collocations so “machine learning” survives even if “machine” is common.

Minimal refactor:

```python
def _extract_keywords(self, text, max_keywords=25):
    tokens = re.findall(r"\b\w[\w\-]*\b", text.lower())
    # Optional: lemmatize first if spaCy available
    # POS filter if spaCy available
    # Build DF across corpus if you have one; otherwise within-doc heuristics + YAKE/TextRank
```

9. spaCy labels and features

* `TECH` isn’t a default spaCy label, so your entity filter may drop useful entities. Consider a whitelist like `{'ORG','PRODUCT','GPE','LOC','PERSON','WORK_OF_ART','EVENT','LAW','NORP'}`.
* `doc.noun_chunks` requires the parser; `en_core_web_sm` has it, but it’s slower. If speed matters, switch to a faster pipeline or `spacy.load("en_core_web_sm", disable=["ner","lemmatizer"])` for features you don’t use in that step.

10. “Topic modeling” isn’t topic modeling
    Right now it’s “frequent noun phrases.” If you really want topics:

* **YAKE/KeyBERT** per doc for salient phrases, or
* **BERTopic** or LDA at corpus level. For online/lightweight, start with KeyBERT + MMR.

11. Language detection
    Your heuristic gives many false positives. Use a tiny, robust detector (e.g., `lingua-language-detector`, `langdetect`, or fastText). Keep it optional.

12. File-type hints
    A `.xlsx` isn’t necessarily a “spreadsheet” conceptually. Keep the hint but lower its prior so content can override it. Example: assign a prior score (not 0.8 confidence) and combine with text evidence.

13. Performance

* Avoid repeated `.split()` and `.count()`. Tokenize once.
* Slice limits are good, but 5,000 chars may be too short for long PDFs; consider sampling head + middle + tail windows to reduce bias.

14. Better metadata times
    Use timezone-aware timestamps and include the source hash for traceability.

```python
"extraction_timestamp": datetime.now(datetime.timezone.utc).isoformat(),
"content_sha1": hashlib.sha1(text_content.encode("utf-8")).hexdigest(),
```

# Drop-in patches

**A) Dual-text handling (raw vs cleaned)**

```python
def tag_document(...):
    start = time.time()
    raw_text = text_content or ""
    clean_text = self._preprocess_text(raw_text)

    document_types = self._classify_document_type(clean_text, file_path)
    domains       = self._classify_domain(clean_text, file_path)
    keywords      = self._extract_keywords(clean_text)
    entities      = self._extract_entities(raw_text)      # raw!
    topics        = self._extract_topics(raw_text)        # raw or better method
    ...
```

**B) Token-aware indicator scoring**

```python
def _score_indicators(self, text, indicators):
    tokens = re.findall(r"\b\w[\w\-]*\b", text)
    freq = collections.Counter(tokens)
    return sum(freq[ind] for ind in indicators)
```

Use `_score_indicators` in both classifiers, then normalize with softmax or sum-normalization.

**C) Fix YAKE path**

```python
if YAKE_AVAILABLE:
    kw_extractor = yake.KeywordExtractor(lan="en", n=3, dedupLim=0.7, top=max_keywords*2)
    for keyword, score in kw_extractor.extract_keywords(text):
        if is_high_quality_keyword(keyword, text):
            filtered_keywords.append(keyword.lower())
```

**D) spaCy entity filter**

```python
ENT_KEEP = {"ORG","PRODUCT","GPE","LOC","PERSON","WORK_OF_ART","EVENT","LAW","NORP"}
for ent in doc.ents:
    if ent.label_ in ENT_KEEP and is_high_quality_keyword(ent.text, text):
        keywords.add(ent.text.lower())
```

# Nice-to-haves

* Add **KeyBERT+MMR** as another unsupervised keyword option.
* Add **BM25** weighting for keyword scoring if you keep a corpus index.
* Normalize confidences to `[0,1]` and round to, say, 3 decimals everywhere.
* Expand phone/URL regexes if you need international support.

# Summary

Fix the YAKE tuple bug, stop destroying emails/URLs before extraction, make classification token-aware with calibrated confidences, and replace the giant static stoplist with POS+DF/entropy gates. Those four changes will noticeably improve accuracy and robustness without blowing up complexity.
