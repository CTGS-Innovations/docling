#!/usr/bin/env python3
"""
Debug Intelligent SPO Extractor

Test the intelligent extractor with simpler, focused content to identify
pattern matching issues and improve meaningful fact extraction.
"""

import sys
sys.path.append('.')

# Test content with clear safety requirements and measurements
test_content = """---
domain_classification:
  top_domains: ['safety_compliance']
  top_document_types: ['osha_report']
---

# Safety Compliance Requirements Document

## Section 1: Mandatory Safety Requirements

All employees must wear protective equipment when working in hazardous areas. The company shall provide safety training within 30 days of employment. Workers are required to comply with OSHA standards and maintain minimum distances from machinery.

## Section 2: Measurement Requirements

- Fall protection required above 6 feet (1.8 meters) in construction
- Guardrails must be 42 inches (1.07 meters) high  
- Noise exposure limit 90 decibels for 8 hours
- Weight capacity maximum 250 pounds (113 kg) per person
- Temperature range -20°F to 120°F (-29°C to 49°C)
- Visibility distance 500 feet (152 meters)
- Response time 15 minutes maximum
- Storage height limit 15 feet (4.5 meters)

## Section 3: Compliance Actions

The organization must implement safety protocols. Employees shall receive proper training. All equipment must meet ISO standards. Violations result in fines up to $50,000.

Any incident resulting in 3 or more injuries requires reporting within 8 hours. Inspections must be conducted monthly. Safety officers are required to maintain detailed records.
"""

def test_intelligent_extractor():
    """Test intelligent fact extractor with focused content"""
    print("DEBUGGING INTELLIGENT SPO EXTRACTOR")
    print("=" * 50)
    
    try:
        from knowledge.extractors.standalone_intelligent_extractor import StandaloneIntelligentExtractor
        
        print("✅ Creating standalone intelligent extractor...")
        extractor = StandaloneIntelligentExtractor()
        
        # Test individual components
        print("\n🔍 Testing domain context extraction...")
        yaml_content, markdown_content = extractor._parse_document_sections(test_content)
        domain_context = extractor._extract_domain_context(yaml_content)
        
        print(f"   YAML content length: {len(yaml_content)}")
        print(f"   Markdown content length: {len(markdown_content)}")
        print(f"   Domain context: {domain_context}")
        
        # Test relationship pattern matching
        print("\n🔍 Testing relationship patterns...")
        meaningful_facts = extractor._extract_meaningful_facts(markdown_content, domain_context)
        
        print(f"   Meaningful facts found: {len(meaningful_facts)}")
        for i, fact in enumerate(meaningful_facts[:5], 1):
            print(f"   {i}. Subject: {fact.subject}")
            print(f"      Predicate: {fact.predicate}")
            print(f"      Object: {fact.object}")
            print(f"      Confidence: {fact.confidence:.2f}")
            print(f"      Actionable: {fact.actionable}")
            print()
        
        # Test full extraction
        print("\n🔍 Testing full intelligent extraction...")
        intelligent_results = extractor.extract_semantic_facts(test_content)
        
        semantic_facts = intelligent_results.get('semantic_facts', {})
        semantic_summary = intelligent_results.get('semantic_summary', {})
        
        total_facts = semantic_summary.get('total_facts', 0)
        actionable_facts = semantic_summary.get('actionable_facts', 0)
        
        print(f"✅ Full extraction results:")
        print(f"   Total facts: {total_facts}")
        print(f"   Actionable facts: {actionable_facts}")
        print(f"   Domain: {semantic_summary.get('domain_context', 'unknown')}")
        
        # Show fact categories
        for category, facts in semantic_facts.items():
            if isinstance(facts, list) and len(facts) > 0:
                print(f"\n📊 {category}: {len(facts)} facts")
                for i, fact in enumerate(facts[:3], 1):
                    if isinstance(fact, dict):
                        subj = fact.get('subject', '')
                        pred = fact.get('predicate', '')
                        obj = fact.get('object', '')[:50] + '...' if len(fact.get('object', '')) > 50 else fact.get('object', '')
                        conf = fact.get('confidence', 0)
                        print(f"      {i}. {subj} -> {pred} -> {obj} (conf: {conf:.2f})")
        
        if total_facts == 0:
            print("\n❌ No facts extracted - debugging patterns...")
            
            # Test individual pattern categories
            for pattern_category in ['safety_requirements', 'measurement_relationships', 'compliance_requirements']:
                if pattern_category in extractor.relationship_patterns:
                    print(f"\n   Testing {pattern_category} patterns:")
                    patterns = extractor.relationship_patterns[pattern_category]
                    
                    for pattern in patterns[:2]:  # Test first 2 patterns
                        print(f"      Pattern: {pattern}")
                        
                        import re
                        try:
                            matches = list(re.finditer(pattern, markdown_content, re.IGNORECASE))
                            print(f"      Matches: {len(matches)}")
                            
                            for match in matches[:2]:
                                matched_text = match.group(0)[:80] + '...' if len(match.group(0)) > 80 else match.group(0)
                                print(f"         Match: {matched_text}")
                                
                        except Exception as e:
                            print(f"      Error: {e}")
        
        print(f"\n🟢 SUCCESS: Intelligent extractor debug complete!")
        
    except Exception as e:
        import traceback
        print(f"\n🔴 ERROR: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_intelligent_extractor()