#!/usr/bin/env python3
"""
Debug script to test semantic extraction and see what's happening
"""

import sys
sys.path.append('.')

from knowledge.extractors.standalone_intelligent_extractor import StandaloneIntelligentExtractor

def test_semantic_extraction():
    # Initialize the extractor
    extractor = StandaloneIntelligentExtractor()
    
    # Test with some sample content that should produce facts
    test_content = """---
conversion:
  engine: mvp-fusion-highspeed
  page_count: 15
  source_file: 3124-stairways-and-ladders.pdf
  format: PDF
domain_classification:
  domains:
    safety_compliance: 14.1
    federal_agencies: 3.1
---

# OSHA Safety Requirements

OSHA regulation 29 CFR 1926.95 requires all construction workers to wear personal protective equipment (PPE) including hard hats, safety glasses, and steel-toed boots when working on construction sites above 6 feet.

Workers must inspect ladders before each use to ensure they are in good condition. Damaged ladders must be removed from service immediately.

The Department of Labor established that fall protection is required for workers at heights exceeding 6 feet. This regulation applies to all construction activities.

Safety training must be conducted annually for all employees working with ladders and stairways. Training records must be maintained for a minimum of 3 years.
"""
    
    print("🔍 Testing semantic extraction...")
    print(f"📄 Content length: {len(test_content)} characters")
    
    # Extract facts
    try:
        results = extractor.extract_semantic_facts(test_content)
        
        print(f"\n📊 Extraction results:")
        print(f"   Facts: {len(results.get('facts', []))}")
        print(f"   Rules: {len(results.get('rules', []))}")
        print(f"   Relationships: {len(results.get('relationships', []))}")
        
        if results.get('facts'):
            print(f"\n📋 Facts found:")
            for i, fact in enumerate(results['facts'][:3], 1):
                print(f"   {i}. {fact}")
                
        if results.get('rules'):
            print(f"\n📜 Rules found:")
            for i, rule in enumerate(results['rules'][:3], 1):
                print(f"   {i}. {rule}")
                
        return results
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_semantic_extraction()