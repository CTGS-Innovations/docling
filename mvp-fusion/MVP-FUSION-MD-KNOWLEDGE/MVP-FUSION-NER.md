Here’s a **micro PRD** you can hand off to your coding/AI agent to implement a normalized measurement extraction pipeline. It’s concise but covers all the measurement categories with examples.

---

## Micro PRD: Normalized Measurement Extraction

### Problem Statement

Current NER extraction detects measurements but lacks normalization. Units are inconsistent (inches, feet, miles, percent, etc.), making downstream reasoning and aggregation difficult.

### Goal

Design a measurement extraction schema that:

1. Captures **raw text** as found.
2. Classifies into **semantic type** (length, weight, volume, etc.).
3. Normalizes to a **canonical unit system** for consistency.
4. Preserves **span offsets** for traceability.

### Functional Requirements

* Extract `value`, `unit`, `text`, `type`, and `span`.
* Add `normalized` field with `{value, unit}` in base units.
* Support at least the following measurement types:

  * **Length** → normalize to **meters**

    * Example: `"5 miles"` → `value: 5, unit: mi` → `normalized: {8046.72, m}`
  * **Weight** → normalize to **kilograms**

    * Example: `"250 pounds"` → `value: 250, unit: lb` → `normalized: {113.4, kg}`
  * **Volume** → normalize to **liters** or **m³**

    * Example: `"2 gallons"` → `value: 2, unit: gal` → `normalized: {7.57, L}`
  * **Temperature** → normalize to **Celsius**

    * Example: `"98.6 °F"` → `value: 98.6, unit: °F` → `normalized: {37, °C}`
  * **Angle** → normalize to **degrees** (or radians if preferred)

    * Example: `"75.5°"` → `value: 75.5, unit: deg` → `normalized: {1.318, rad}`
  * **Percentage** → normalize to **ratio**

    * Example: `"20 percent"` → `value: 20, unit: percent` → `normalized: {0.2, ratio}`
  * **Time** → normalize to **seconds**

    * Example: `"3 hours"` → `value: 3, unit: hr` → `normalized: {10800, s}`
  * **Speed** → normalize to **m/s**

    * Example: `"60 mph"` → `value: 60, unit: mph` → `normalized: {26.82, m/s}`
  * **Area** → normalize to **m²**

    * Example: `"500 sq ft"` → `value: 500, unit: ft²` → `normalized: {46.45, m²}`
  * **Currency** → normalize to **ISO 4217 codes**

    * Example: `"$100"` → `value: 100, unit: USD` → `normalized: {100, USD}`
  * **Count / Unitless** → leave as raw number with type `count`

    * Example: `"3 units"` → `value: 3, unit: unit` → `normalized: {3, count}`

### Non-Functional Requirements

* Must not lose fidelity: raw text and span must always be preserved.
* Schema must be compact and human-readable (YAML/JSON).
* Normalization rules stored in a canonical unit map for easy extension.

---

Would you like me to also generate that **canonical unit map** as a ready-to-drop-in YAML/JSON file (e.g., `mi → m`, `lb → kg`), so your agent can just load and apply it?
yes.