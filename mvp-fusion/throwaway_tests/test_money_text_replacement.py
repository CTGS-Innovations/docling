#!/usr/bin/env python3
"""
GOAL: Debug money text replacement span mismatch
REASON: $1.2 million shows as ||$1.2 million||mon010||||.2 million (duplicated text)
PROBLEM: Text replacement not using complete FLPC match spans
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_money_text_replacement():
    """Test money text replacement to find span mismatch"""
    print("🧪 TESTING MONEY TEXT REPLACEMENT SPANS")
    print("=" * 50)
    
    # Test cases showing the problem
    test_cases = [
        ("Training allocation: **$1.2 million**", "$1.2 million", "Should replace complete entity"),
        ("Legal reserves: **$1.5 million**", "$1.5 million", "Should replace complete entity"),
        ("Simple case: **$500,000**", "$500,000", "Should work fine (no magnitude)"),
    ]
    
    print(f"📄 TEST CASES:")
    for i, (text, expected, description) in enumerate(test_cases, 1):
        print(f"   {i}. {text}")
        print(f"      Expected: Complete replacement of '{expected}'")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING ENTITY EXTRACTION AND NORMALIZATION:")
        print("-" * 55)
        
        for i, (test_text, expected_money, description) in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {description}")
            print(f"    Input: '{test_text}'")
            
            # Step 1: Check FLPC detection
            if processor.flpc_engine:
                flpc_results = processor.flpc_engine.extract_entities(test_text, 'complete')
                flpc_entities = flpc_results.get('entities', {})
                money_matches = flpc_entities.get('MONEY', [])
                
                print(f"    FLPC Detection: {len(money_matches)} matches")
                for j, match in enumerate(money_matches, 1):
                    print(f"      {j}. '{match}'")
            
            # Step 2: Check service processor extraction
            entities = processor._extract_universal_entities(test_text)
            money_entities = entities.get('money', [])
            
            print(f"    Service Processor: {len(money_entities)} entities")
            for j, money in enumerate(money_entities, 1):
                text = money.get('text', '')
                value = money.get('value', '')
                span = money.get('span', {})
                print(f"      {j}. text: '{text}', span: {span}")
            
            # Step 3: Check normalization
            if money_entities:
                from knowledge.extractors.entity_normalizer import EntityNormalizer
                normalizer = EntityNormalizer()
                
                normalized = normalizer._canonicalize_money_entities(money_entities)
                
                print(f"    Normalization: {len(normalized)} normalized")
                for j, norm in enumerate(normalized, 1):
                    canonical = norm.normalized
                    entity_id = norm.id
                    print(f"      {j}. canonical: '{canonical}', id: '{entity_id}'")
            
            # Step 4: Check what text replacement would do
            print(f"    Expected replacement: '{expected_money}' -> '||{expected_money}||id||'")
        
        print(f"\n🎯 SPAN ANALYSIS:")
        print("-" * 25)
        print("The issue is likely that:")
        print("1. FLPC detects '$1.2 million' as one entity")
        print("2. But text replacement only replaces '$1.2' part")
        print("3. Leaving '.2 million' as leftover text")
        print("4. This suggests span information mismatch")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_money_text_replacement()