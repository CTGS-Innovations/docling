#!/usr/bin/env python3
"""Debug tagger to check BI patterns."""

import importlib.util
from pathlib import Path

# Import mvp-hyper-tagger
spec_tagger = importlib.util.spec_from_file_location("mvp_hyper_tagger", "mvp-hyper-tagger.py")
mvp_hyper_tagger = importlib.util.module_from_spec(spec_tagger)
spec_tagger.loader.exec_module(mvp_hyper_tagger)

MVPHyperTagger = mvp_hyper_tagger.MVPHyperTagger

# Test content with clear business intelligence elements
test_content = """
Acme Corp, a technology company founded by CEO John Smith, announced a $50 million Series B funding round. 
Contact: info@acmecorp.com or call (555) 123-4567.
Located in San Francisco, California.

The company struggles with manual data processing workflows that are time-consuming and expensive.
The market for automated workflow solutions is worth $2.5 billion and growing rapidly.
Their breakthrough approach to AI automation represents a novel solution.
Competitors like TechFlow Inc. have established market positions.
"""

# Initialize tagger and test
tagger = MVPHyperTagger(cache_enabled=False)
result = tagger.tag_document(Path("test.md"), test_content)

print("=== TAGGER DEBUG RESULTS ===")
print(f"Document Types: {result.document_types}")
print(f"Universal Entities: {result.universal_entities}")
print(f"Pain Points: {result.pain_points}")
print(f"Market Opportunities: {result.market_opportunities}")
print(f"Innovation Signals: {result.innovation_signals}")
print(f"Competitive Intelligence: {result.competitive_intelligence}")
print(f"Processing Time: {result.processing_time}s")