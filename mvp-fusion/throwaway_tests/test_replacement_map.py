#!/usr/bin/env python3
"""
GOAL: Debug replacement map contents for money entities
REASON: Check what keys are in replacement_map vs what text we're trying to replace
PROBLEM: Text replacement seems to miss complete money entities
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_replacement_map():
    """Test what's actually in the replacement map"""
    print("🧪 TESTING REPLACEMENT MAP CONTENTS")
    print("=" * 45)
    
    # Test the exact problematic text from Section 7
    test_text = """
### 7.1 Budget Items (10 amounts)
1. Safety equipment budget: **$500,000**
2. Training allocation: **$1.2 million**
3. Compliance software: **$250,000**
"""
    
    print(f"📄 TEST TEXT:")
    print(test_text)
    print("=" * 45)
    
    # Initialize ServiceProcessor and EntityNormalizer
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    from knowledge.extractors.entity_normalizer import EntityNormalizer
    
    processor = ServiceProcessor(config)
    normalizer = EntityNormalizer()
    
    try:
        print(f"🔍 STEP 1: ENTITY EXTRACTION")
        print("-" * 35)
        
        # Extract entities
        entities = processor._extract_universal_entities(test_text)
        money_entities = entities.get('money', [])
        
        print(f"Money entities found: {len(money_entities)}")
        for i, money in enumerate(money_entities, 1):
            text = money.get('text', '')
            value = money.get('value', '')
            span = money.get('span', {})
            print(f"  {i}. text: '{text}', value: '{value}', span: {span}")
        
        print(f"\n🔍 STEP 2: NORMALIZATION")
        print("-" * 30)
        
        # Normalize entities (this builds the replacement map)
        all_entities = {'money': money_entities}
        result = normalizer.normalize_entities_phase(all_entities, test_text)
        
        print(f"Normalized entities: {len(result.normalized_entities)}")
        for entity in result.normalized_entities:
            print(f"  - id: {entity.id}, normalized: '{entity.normalized}'")
            print(f"    mentions: {[m['text'] for m in entity.mentions]}")
        
        print(f"\n🔍 STEP 3: WHAT SHOULD BE IN REPLACEMENT MAP")
        print("-" * 45)
        
        # Show what should be in replacement map
        for entity in result.normalized_entities:
            for mention in entity.mentions:
                original_text = mention['text']
                print(f"  Key: '{original_text}' -> Value: ('{entity.normalized}', '{entity.id}')")
        
        print(f"\n🔍 STEP 4: TEXT REPLACEMENT TEST")
        print("-" * 40)
        
        # Check what's actually in the document that needs replacing
        import re
        money_pattern = r'\*\*\$[^*]+\*\*'
        matches = re.findall(money_pattern, test_text)
        
        print(f"Money patterns in document: {len(matches)}")
        for i, match in enumerate(matches, 1):
            print(f"  {i}. Found in document: '{match}'")
            
            # Check if this would be found by replacement map
            clean_match = match.replace('**', '')  # Remove markdown
            print(f"      Clean version: '{clean_match}'")
            
            # Check if any entity text matches this
            found_match = False
            for entity in result.normalized_entities:
                for mention in entity.mentions:
                    if clean_match in mention['text'] or mention['text'] in clean_match:
                        found_match = True
                        print(f"      ✅ Would be replaced by entity: '{mention['text']}'")
                        break
                if found_match:
                    break
            
            if not found_match:
                print(f"      ❌ NO MATCHING ENTITY FOUND!")
        
        print(f"\n📊 FINAL RESULT:")
        print("-" * 20)
        print(f"Normalized text preview:")
        print(result.normalized_text[:300] + "..." if len(result.normalized_text) > 300 else result.normalized_text)
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_replacement_map()