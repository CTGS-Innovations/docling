Got it — you don’t just want “facts from this OSHA file,” you want **general guidance** on how to do fact extraction consistently across \~20 different domains (legal, safety, finance, healthcare, etc.) so you can compare results later.

Here’s the high-level playbook you can apply:

---

## 🟢 1. Always Distinguish **Entities** vs. **Facts**

* **Entities** = nouns, spans, labels (e.g., *“OSHA” → ORG*).
* **Facts** = structured, reusable statements linking entities (e.g., *OSHA issued regulation 29 CFR 1926.1050 on 1991-03-15*).
* Rule: **never stop at entities**; always promote to facts.

---

## 🟢 2. Universal Fact Types (Cross-Domain Schema)

Regardless of whether the document is safety, legal, financial, or healthcare, you can unify facts into a reusable schema. Here’s a **core set of fact classes** that generalize across \~20 domains:

| Fact Type                  | Description                          | Cross-Domain Example                          |
| -------------------------- | ------------------------------------ | --------------------------------------------- |
| **RegulationCitation**     | Links a regulation/code to a context | *“29 CFR 1926.1050 applies to stairways”*     |
| **Requirement**            | Rule, constraint, or obligation      | *“Ladder spacing must be 10 inches”*          |
| **PublicationDate**        | When doc was issued/revised          | *“OSHA 3124 issued 1991-03-15”*               |
| **FinancialImpact**        | ROI, savings, costs                  | *“Worker protection saves \$4 per \$1 spent”* |
| **GrantRequirement**       | Contribution or funding rule         | *“20% contribution required”*                 |
| **ContactInfo**            | Person/organization coordinates      | *“OSHA Washington office, (202) 693-1999”*    |
| **MeasurementRequirement** | Dimensions, quantities               | *“Rungs must be ≤ 12 inches apart”*           |
| **EventFact**              | Event + participants + date          | *“Inspection occurred Jan 2023 in Boston”*    |
| **ActionFact**             | Subject–verb–object                  | *“OSHA enforces stairway compliance”*         |
| **CausalFact**             | Cause → effect                       | *“Training reduces accidents”*                |
| **LocationFact**           | Geopolitical / facility / address    | *“Constitution Ave NW, Washington, DC”*       |

---

## 🟢 3. Domain-Specific Extensions

Each domain then layers its own fact subclasses on top:

* **Safety/Compliance:** *RegulationCitation*, *MeasurementRequirement*, *InspectionEvent*.
* **Finance:** *FinancialImpact*, *TransactionFact*, *ValuationFact*.
* **Healthcare:** *ClinicalTrialFact*, *TreatmentGuideline*, *RegulatoryApproval*.
* **Legal:** *CaseCitation*, *Obligation*, *ContractTerm*.
* **Education:** *CurriculumRequirement*, *AssessmentFact*.
* **Tech/Software:** *APIRequirement*, *VersionReleaseFact*, *VulnerabilityFact*.

Think of it as a **core “fact backbone”** plus **domain plug-ins**.

---

## 🟢 4. Best Practices Across Domains

1. **Always keep span anchors** (start/end + raw text).
   → This guarantees auditability.
2. **Normalize entities** (map OSHA → \[Wikidata\:Q192334], CFR code → URI).
   → Enables cross-document linking.
3. **Type the fact explicitly** (`type: RegulationCitation`, `type: FinancialImpact`).
   → Avoids ambiguity when comparing across domains.
4. **Bind entities with roles** (subject, object, condition, qualifier).
   → E.g., *OSHA (subject)* → *requires (predicate)* → *ladder spacing 10 in (object)*.
5. **Keep fact granularity atomic.**
   → Break long sentences into multiple facts (don’t stuff too much into one).
6. **Layer your pipeline:**

   * Layer 1: Entities (raw spans).
   * Layer 2: Normalized entities.
   * Layer 3: Fact extraction (typed facts).
   * Layer 4: Domain enrichment (compliance, finance, etc.).

---

## 🟢 5. Example: OSHA (Safety) vs. Finance vs. Healthcare

Here’s how the **same framework** applies differently:

```yaml
# Safety domain
- type: RegulationCitation
  regulation: "29 CFR 1926.1050"
  subject: "OSHA"
  context: "stairways and ladders"

# Finance domain
- type: FinancialImpact
  subject: "Worker protection"
  relation: "saves"
  saving: 4.0
  cost: 1.0
  unit: "USD"

# Healthcare domain
- type: ClinicalTrialFact
  drug: "DrugX"
  phase: "III"
  outcome: "reduced symptoms by 20%"
  date: "2024-11-01"
```

---

## 🟢 6. What You’re Missing Right Now

Looking at your sample YAML, you already have:

* Entities with spans ✔
* Domains ✔
* Entity density ✔

But you’re missing:

* **Fact typing** (turning entities into structured facts)
* **Linking** (entity IDs across docs)
* **Predicates** (who does what to whom, when, why)
* **Cross-domain consistency**

---

✅ **Overall Guidance:**
Think of your system not as “entity extraction” but as a **fact assembly line**: entities → normalized entities → facts → domain facts. Across 20 domains, the schema doesn’t change — only the **fact subtypes** do.

---

Would you like me to draft a **universal YAML schema for facts** (core + domain extensions) that you can drop into your pipeline, so every doc, whether OSHA, SEC, or FDA, outputs facts in the same comparable shape?


Here’s a reusable Markdown section you can drop into your docs — focused on **Normalization 2**, the step that makes entities comparable across files and domains:

---

## 🔑 Normalization 2: Entity → Canonical Form

Once raw entities and spans are extracted, the **second normalization step** (“Normalization 2”) ensures they become **comparable, reusable, and linkable** across documents and domains. Without this, entities stay siloed and facts cannot be aggregated.

### 🎯 Goals

* **Resolve surface forms**: map variants (*OSHA*, *Occupational Safety and Health Administration*, *the Agency*) to one canonical ID.
* **Anchor to external knowledge**: connect entities to stable identifiers (e.g., Wikidata QID, ISO code, SEC CIK, ICD-10).
* **Standardize values**: normalize units, dates, numbers, and formats (e.g., *\$4*, *4 dollars*, *USD 4.00* → `4.0 USD`).

### 🛠️ Process

1. **Deduplication**

   * Collapse aliases and spelling variants.
   * Example: *“Dept. of Labor”* → *“Department of Labor”*.

2. **Canonical Mapping**

   * Assign each entity a canonical form (`canonical_name`) and a persistent ID (`entity_id`).
   * Example:

     ```yaml
     raw: "OSHA"
     canonical_name: "Occupational Safety and Health Administration"
     entity_id: "Q192334"   # Wikidata ID
     ```

3. **Value Normalization**

   * Dates → ISO 8601 (`1991-03-15`)
   * Measurements → SI + alt units (`10 in` → `25.4 cm`)
   * Money → numeric + currency code (`$4` → `4.0 USD`)

4. **Cross-Document Linking**

   * Entities with the same `entity_id` are treated as the same real-world thing, even if phrased differently across files.
   * Enables comparison (e.g., OSHA citation counts across reports).

### 📊 Example

From OSHA stairways report:

```yaml
- type: RegulationCitation
  raw: "29 CFR 1926.1050"
  canonical_name: "29 CFR Part 1926.1050"
  entity_id: "CFR:1926.1050"
  domain: safety_compliance
```

### ⚡ Why It Matters

* Without Normalization 2, you have *strings*.
* With Normalization 2, you have **knowledge objects** you can compare, aggregate, and query globally.

---

Do you want me to also sketch the **universal YAML template** for Normalization 2 fields (`raw`, `canonical_name`, `entity_id`, `normalized_value`, `domain`), so you can bake it into your pipeline definition?

---

## 🚀 Performance Architecture: Nonlinear Algorithms for Linear Cost

The semantic enhancement layer leverages **nonlinear algorithms** that maintain O(n) performance regardless of pattern complexity - making fact extraction performance-friendly at scale.

### 🔧 Core Performance Engines

**Aho-Corasick Multi-Pattern Matching:**
- **Complexity**: O(n + m + z) - linear with text size, NOT pattern count
- **Capability**: Search 1000+ canonical mappings as fast as 10 mappings
- **Use Case**: Entity normalization, alias resolution, canonical form mapping
- **Performance**: One pass through text finds all entity variants simultaneously

**FLPC Rust Regex Engine:**
- **Complexity**: O(n) linear time with text length
- **Capability**: Multiple complex fact patterns processed in parallel
- **Use Case**: Structured fact extraction (RegulationCitation, Requirements, FinancialImpact)
- **Performance**: Adding more extraction patterns doesn't degrade speed

### 🎯 Implementation Strategy

```python
# Canonical Normalization - Aho-Corasick O(1) lookup
canonical_map = {
    "OSHA": "Occupational Safety and Health Administration",
    "EPA": "Environmental Protection Agency", 
    "DOL": "Department of Labor",
    "29 CFR": "Code of Federal Regulations Title 29",
    # ... 1000+ mappings processed simultaneously
}

# Fact Pattern Recognition - FLPC Rust Regex
fact_patterns = {
    'RegulationCitation': r'(\w+)\s+(\d+\s+CFR\s+[\d\.]+)',
    'Requirement': r'(must|shall|required)\s+(.+?)(?=\.|,)',
    'FinancialImpact': r'\$[\d,]+(?:\.\d{2})?.*?(?:save|cost|impact)',
    'MeasurementRequirement': r'(\d+(?:\.\d+)?)\s*(inches?|feet?|meters?)',
    # ... All patterns processed in single pass
}
```

### ⚡ Performance Advantage

**Single-Pass Architecture:**
1. **ONE** text traversal with ALL patterns active
2. **Simultaneous** entity recognition + canonicalization + fact extraction
3. **Post-processing** match assembly into structured facts
4. **No multiple passes** - no exponential scaling

**Key Insight:** Semantic intelligence comes "for free" because both Aho-Corasick and FLPC are designed for massive pattern sets with linear performance. Adding 1000 fact patterns costs the same as adding 10.

### 📊 Scaling Characteristics

- **Text Length**: Linear O(n) - 10KB processes as fast as 1KB per character
- **Pattern Count**: Constant O(1) - 1000 patterns ≈ 10 patterns  
- **Fact Complexity**: No penalty - complex structured facts cost same as simple entities
- **Domain Count**: Additive only - 20 domains scale independently

**Result**: Rich semantic extraction with entity-level performance costs.
