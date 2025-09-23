Got it — you’re designing a **layered knowledge pipeline**: start with “cheap” classification and structural parsing, then refine with heavier semantic passes. That’s a solid approach. Here’s a hierarchy you can adopt that balances **speed, accuracy, and scalability** (CPU-friendly at first, with room for heavier semantic passes if needed).

---

## 📚 Suggested Hierarchy for Document → Knowledge

### **Layer 0: File & Metadata Extraction**

* File type, size, encoding, page count, date.
* Extract metadata (title, author, publisher, standard tags).
* Quick checksum / hash for deduplication.

*Goal:* Fast fingerprinting. Helps cache & avoid duplicate work.

---

### **Layer 1: Structure & Layout**

* **Regex / Echohor pass** for:

  * Page breaks, headers, footers.
  * Tables of contents, numbered lists.
  * Sections & headings (important for context windows later).
* Markdown/JSON tree structure: Document → Sections → Paragraphs → Sentences.

*Goal:* Normalize everything to a predictable topology so later layers don’t fight layout noise.

---

### **Layer 2: Domain & Type Classification**

* Domain detection (technical, construction, safety, etc.) — what you already have.
* Document type (report, standard, guide, etc.).
* Confidence scoring to route into **specialized sub-pipelines** (e.g., compliance docs get extra reg-entity scan).

*Goal:* Route to the right extractor family before deep entity pass.

---

### **Layer 3: Shallow Entity Recognition (Fast Patterns)**

* Regex/dictionary/Aho-Corasick for **universal entities**:

  * Dates, monetary values, measurements (ft, psi, dB), codes/IDs, contact info.
  * Common standard IDs (ISO, OSHA, ASTM).
* CPU-optimized libraries (like pyahocorasick, FlashText).
* Fast 1000+ pages/sec baseline.

*Goal:* Harvest low-hanging fruit quickly.

---

### **Layer 4: Deep Named Entity Recognition**

* Domain-tuned NER:

  * People, organizations, locations (generic).
  * Domain-specific: chemicals, equipment types, safety codes, materials.
* Can use **lightweight CPU models** (e.g., DistilBERT-NER) or hybrid rules+ML.
* Include **entity linking** (map to Wikidata/OSHA/CFR reference IDs).

*Goal:* Semantic anchors for knowledge graphing.

---

### **Layer 5: Relations & Events**

* Relation extraction: “Company X complies with Regulation Y,” “Chemical Z exceeds limit.”
* Event detection: “Inspection failed,” “Accident occurred.”
* Graph edges: Entity → Relation → Entity.

*Goal:* Move from isolated entities to connected knowledge.

---

### **Layer 6: Higher-Order Semantics**

* Summarization (per section, per doc).
* Topic modeling (LDA or embedding clustering).
* Argument/claim extraction (statements vs. evidence).
* Compliance/safety “flags” (align text against rulebooks).

*Goal:* Transform content into **usable semantic knowledge objects**.

---

### **Layer 7: Knowledge Graph / Index Integration**

* Store structured data:

  * Entity nodes (with types, spans, confidence).
  * Relationships (causal, compliance, temporal).
  * Semantic embeddings (for search).
* Link across docs → cross-document entity graph.

*Goal:* Global reasoning & cross-corpus retrieval.

---

## ⚡ Pipeline Benefits

* **Early layers (0–3):** cheap, CPU-friendly, high throughput.
* **Later layers (4–6):** deeper semantics, heavier but selective (only on routed docs).
* **Final layer (7):** persistent knowledge base for RAG, QA, analytics.

---

👉 Since you’re already doing Regex + Echohor for Layer 1, the biggest *next leverage point* is **Layer 3 shallow entities**, because it gives you a lot of semantic hooks without ML overhead. Then you can selectively escalate to Layer 4 NER only where the doc class demands it.

Do you want me to sketch this as a **Mermaid flowchart with subgraphs** (Pipeline Layers → Outputs → Next Layer) so you can visualize how it fits into your MVP Fusion pipeline?
