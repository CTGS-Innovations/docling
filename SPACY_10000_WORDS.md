I couldn’t find any credible published information about **“SpaceyNear”** — I suspect perhaps you meant **spaCy-NER**, or some other NER engine? If “SpaceyNear” is correct then it might be new / proprietary / not well documented. If you meant **spaCy**, I can share what is known; if not, I can try digging more if you can confirm.

If you meant **spaCy’s Named Entity Recognition**, here are some numbers and how speed is reported, plus what influences “tokens per second” performance:

---

### What is known for spaCy

From spaCy’s “Facts & Figures” documentation (for version \~3.x): ([spaCy][1])

* They report **words per second (WPS)** for end-to-end pipelines on raw text.

* Example speeds (on CPU) for spaCy models:

  | Pipeline                              | CPU WPS                         |
  | ------------------------------------- | ------------------------------- |
  | `en_core_web_lg`                      | \~10,014 words/sec ([spaCy][1]) |
  | `en_core_web_trf` (transformer based) | \~684 words/sec ([spaCy][1])    |

* Accuracy / quality is also reported (but that’s separate). ([spaCy][1])

---

### What determines tokens (or words) per second

“Tokens per second” (or “words per second”) depends heavily on:

* The model size / architecture (lighter / non-transformer ≈ faster; transformer or large deep model ≈ slower).
* Whether GPU or CPU is used.
* The complexity of the input (length, formatting, need for lots of context).
* Tokenization strategy (subword vs word vs character); sometimes multiple subtokens per word.
* Whether batching is used, or streaming one document at a time.

---

### Do we have anything like spaCy’s tokens/sec?

Yes — spaCy reports **words per second**. If you assume each word is roughly one token (or a fixed multiple depending on tokenizer), you can use that as a proxy for tokens/sec. For example, spaCy’s \~10,000 words/sec for its large non-transformer model implies similar tokens/sec (maybe a bit higher or lower depending). ([spaCy][1])

---

If you confirm whether you meant **spaCy-NER** or a specific “SpaceyNear”, I can try to find more precise TPS (tokens per second) numbers for *that* tool (or approximate based on benchmarks). Do you want me to check that?

[1]: https://spacy.io/usage/facts-figures?utm_source=chatgpt.com "Facts & Figures · spaCy Usage Documentation"
