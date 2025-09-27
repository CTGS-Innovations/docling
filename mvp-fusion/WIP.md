# WIP: Range Detection Post-Processing Enhancement
## Work in Progress - Product Requirements Document

### 🎯 **PROJECT OBJECTIVE**
Implement post-processing range normalization to fix inconsistent range detection while preserving all working functionality.

### 🔍 **PROBLEM STATEMENT**
**Current Issue:** Range detection inconsistency in entity extraction
- **Evidence:** `30-37 inches` missed while `76-94 cm` detected as range entities
- **Root Cause:** Individual measurement entities not being consolidated into ranges
- **Impact:** Incomplete range extraction affecting measurement analysis
- **Location:** `/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md`

### 📋 **CONFIRMED STRATEGY (User-Specified)**
1. **PRESERVE** existing DATE/TIME/MONEY/MEASUREMENT detection patterns (NO MODIFICATIONS)
2. **ADD** post-processing normalization to detect ranges from already-detected entities  
3. **MAINTAIN** processing order: DATE → TIME → MONEY → MEASUREMENT → Range Normalization
4. **USE** span analysis to link related entities (30 + - + 37 + inches → 30-37 inches)
5. **DO NOT** modify working FLPC patterns in `config/pattern_sets.yaml`

### 🚫 **CONSTRAINTS & PROHIBITIONS**
- **NEVER** modify existing working DATE/TIME/MONEY patterns
- **NEVER** break existing entity categorization (dates as dates, times as times, etc.)
- **NEVER** change FLPC pattern detection logic
- **NO** wide→narrow pattern precedence approaches
- **NO** universal detection pattern replacements

### 🏗️ **TECHNICAL APPROACH**
**Architecture:** Post-Processing Normalization (Industry Standard)
- **Phase 1:** Standard entity detection (existing working system)
- **Phase 2:** Span-based range consolidation in normalization phase
- **Method:** Analyze detected entity spans for range patterns
- **Logic:** EntityA + Connector + EntityB + Unit → Range Entity

### 📂 **FILES TO MODIFY**
1. **Revert Changes:**
   - `config/pattern_sets.yaml` → Restore original working patterns
   - `pipeline/legacy/service_processor.py` → Restore original entity processing

2. **New Implementation:**
   - Create post-processing range normalization in normalization phase
   - Add span analysis logic to identify: Number + Connector + Number + Unit patterns
   - Consolidate detected entities into range entities

### 🔧 **IMPLEMENTATION STEPS**
1. **REVERT:** Remove all broken universal patterns and span-based changes
2. **RESTORE:** Original working DATE/TIME/MONEY/MEASUREMENT detection
3. **CREATE:** Test file in `throwaway_tests/` to validate approach
4. **IMPLEMENT:** Post-processing range normalization in service processor normalization phase
5. **VALIDATE:** Test with problematic cases (30-37 inches, 76-94 cm)

### ✅ **SUCCESS CRITERIA**
- **Both** `30-37 inches` AND `76-94 cm` detected as range entities
- **All** existing DATE/TIME/MONEY entities still properly categorized  
- **No** fragmentation of dates into individual numbers
- **Proper** entity tagging: `January 1, 2024` stays as single DATE entity
- **Range consolidation** works for all measurement types

### 🧪 **TEST CASES**
**Primary Test:** `"Handrail height 30-37 inches (76-94 cm)"`
- Expected: 2 range entities detected
- Expected: Individual measurements removed/consolidated
- Expected: No individual 30, 37, 76, 94 number entities

**Validation Test:** DATE/TIME/MONEY still working
- Dates remain as complete date entities
- Money amounts properly categorized as MONEY
- Times properly categorized as TIME

### 📊 **CURRENT STATUS**
- **Problem:** Range detection inconsistency identified
- **Strategy:** Post-processing approach confirmed and approved
- **Decision Framework:** Applied and documented in `CLAUDE_DECISION_FRAMEWORK.md`
- **Next Action:** Revert broken changes and implement correct post-processing approach

### 🎯 **SOLUTION ARCHITECT NOTES**
**This WIP represents the ONLY approved approach:**
- Post-processing normalization is the confirmed strategy
- All working functionality must be preserved
- No pattern modifications allowed
- Span-based consolidation in normalization phase only
- Decision Framework (Rule #17) was applied to confirm this approach

**Context Carryover:** When resuming work, follow this WIP exactly. Do not deviate from post-processing approach or modify working detection patterns.