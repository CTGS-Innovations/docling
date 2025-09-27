#!/usr/bin/env python3
"""
GOAL: Test money entity parsing for comma and currency issues
REASON: Verify $14,502 detected as single entity with currency preserved
PROBLEM: Commas being treated as separate entities, currency symbols lost
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_money_parsing():
    """Test money parsing for comma and currency preservation"""
    print("🧪 TESTING MONEY ENTITY PARSING")
    print("=" * 40)
    
    # Test cases from Section 7
    test_cases = [
        ("Safety equipment budget: **$500,000**", "$500,000", "Dollar sign + comma formatting"),
        ("Maximum OSHA fine: **$14,502** per violation", "$14,502", "Dollar sign + comma formatting"),
        ("Serious violation: **$1,000** minimum", "$1,000", "Dollar sign + comma formatting"),
        ("Training allocation: **$1.2 million**", "$1.2 million", "Dollar sign + decimal + text"),
        ("Settlement: **£25,000** (British pounds)", "£25,000", "British pounds with comma"),
        ("Budget: **€100,000** (Euros)", "€100,000", "Euros with comma"),
    ]
    
    print(f"📄 TEST CASES:")
    for i, (text, expected, description) in enumerate(test_cases, 1):
        print(f"   {i}. {text}")
        print(f"      Expected: '{expected}' - {description}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING MONEY ENTITY DETECTION:")
        print("-" * 45)
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, (test_text, expected_money, description) in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {description}")
            print(f"    Text: '{test_text}'")
            print(f"    Expected: '{expected_money}'")
            
            # Test FLPC extraction directly first
            if processor.flpc_engine:
                flpc_results = processor.flpc_engine.extract_entities(test_text, 'complete')
                flpc_entities = flpc_results.get('entities', {})
                money_matches = flpc_entities.get('MONEY', [])
                
                print(f"    FLPC Raw Results: {len(money_matches)} money entities")
                for j, match in enumerate(money_matches, 1):
                    print(f"      {j}. '{match}'")
            
            # Test complete service processor extraction
            entities = processor._extract_universal_entities(test_text)
            money_entities = entities.get('money', [])
            
            print(f"    Service Processor Results: {len(money_entities)} money entities")
            for j, money in enumerate(money_entities, 1):
                text = money.get('text', '')
                value = money.get('value', '')
                print(f"      {j}. text: '{text}', value: '{value}'")
            
            # Check if expected money found
            found_expected = False
            for money in money_entities:
                text = money.get('text', '')
                value = money.get('value', '')
                
                # Check if expected money pattern found (text or value)
                if expected_money.lower() in text.lower() or expected_money.lower() in value.lower():
                    found_expected = True
                    print(f"    ✅ SUCCESS: Found expected money format")
                    success_count += 1
                    break
                # Also check for partial matches (numbers at least)
                expected_number = ''.join(c for c in expected_money if c.isdigit() or c == '.' or c == ',')
                text_number = ''.join(c for c in text if c.isdigit() or c == '.' or c == ',')
                if expected_number == text_number and expected_number:
                    print(f"    🟡 PARTIAL: Found number '{text_number}' but format differs")
            
            if not found_expected:
                print(f"    ❌ FAILED: Expected money '{expected_money}' not found")
        
        # Summary
        print(f"\n📊 MONEY PARSING SUMMARY:")
        print("-" * 35)
        print(f"Successful money detections: {success_count}/{total_tests}")
        print(f"Success rate: {(success_count/total_tests*100):.1f}%")
        
        if success_count == total_tests:
            print(f"🟢 **SUCCESS**: All money formats working correctly!")
        elif success_count >= total_tests * 0.7:
            print(f"🟡 **GOOD**: Most money formats working")
        else:
            print(f"🔴 **NEEDS WORK**: Money parsing needs improvement")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_money_parsing()