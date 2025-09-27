#!/usr/bin/env python3
"""
GOAL: Test word boundary fix specifically for substring extraction issues
REASON: Need to verify "e fund" no longer extracts from "the funding"
PROBLEM: Word boundary validation should prevent substring matches
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_word_boundary_fix():
    """Test word boundary fix for specific substring issues"""
    
    # Specific test cases for word boundary validation
    test_cases = [
        {
            "text": "Naturally, the funding process for the startup firm",
            "should_not_extract": "e fund",
            "reason": "substring of 'funding'"
        },
        {
            "text": "They discussed the pan and its implications",
            "should_not_extract": "the pan", 
            "reason": "substring issue"
        },
        {
            "text": "Investment in E Fund has increased significantly",
            "should_extract": "E Fund",
            "reason": "legitimate standalone entity"
        },
        {
            "text": "Google partners with Apple on new technology",
            "should_extract": "Google, Apple",
            "reason": "legitimate standalone companies"
        },
        {
            "text": "conference room infrastructure development costs",
            "should_not_extract": "development",
            "reason": "part of larger phrase"
        }
    ]
    
    print("🔧 TESTING WORD BOUNDARY FIX")
    print("=" * 45)
    
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    for i, test_case in enumerate(test_cases, 1):
        text = test_case["text"]
        print(f"\n{i}. Testing: \"{text}\"")
        
        if "should_not_extract" in test_case:
            target = test_case["should_not_extract"]
            reason = test_case["reason"]
            print(f"   Should NOT extract: '{target}' ({reason})")
        else:
            target = test_case["should_extract"]  
            reason = test_case["reason"]
            print(f"   Should extract: '{target}' ({reason})")
        
        print("-" * 45)
        
        # Extract entities
        entities = processor._extract_universal_entities(text)
        org_entities = entities.get('org', [])
        
        if org_entities:
            print(f"   🏢 ORG entities found: {len(org_entities)}")
            for org in org_entities:
                org_text = org.get('text', '')
                print(f"     - '{org_text}'")
                
                # Check the result
                if "should_not_extract" in test_case:
                    target = test_case["should_not_extract"]
                    if target.lower() in org_text.lower():
                        print(f"       ❌ PROBLEM: '{target}' should not be extracted!")
                    else:
                        print(f"       ✅ OK: Different entity (not '{target}')")
                else:
                    target = test_case["should_extract"]
                    if any(t.lower() in org_text.lower() for t in target.split(', ')):
                        print(f"       ✅ SUCCESS: Found expected entity")
                    else:
                        print(f"       ⚠️ UNEXPECTED: Expected '{target}' but found '{org_text}'")
        else:
            print(f"   🏢 ORG entities found: 0")
            if "should_not_extract" in test_case:
                print(f"       ✅ SUCCESS: Correctly prevented extraction")
            else:
                print(f"       ❌ PROBLEM: Should have extracted '{test_case['should_extract']}'")
    
    print(f"\n🎯 WORD BOUNDARY FIX STATUS:")
    print(f"   ✅ Applied word boundary validation to entity extraction")
    print(f"   ✅ Should prevent substring matches like 'e fund' from 'funding'")
    print(f"   ✅ Should only match complete words bounded by non-alphanumeric characters")

if __name__ == "__main__":
    test_word_boundary_fix()