#!/usr/bin/env python3
"""
GOAL: Test whether sophisticated disambiguation would filter false positive orgs
REASON: Document shows noise like "we move", "e fund", "r bar" as organizations
PROBLEM: Need to verify if POS/scoring system would eliminate these properly
"""

import sys
import os

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_disambiguation_effectiveness():
    """Test whether current disambiguation would filter false positive org entities"""
    
    # Test cases from actual document showing false positives
    test_cases = [
        {
            "text": "we move",
            "context": "As we move into 2025, we're seeing a standout year",
            "should_be_org": False,
            "reason": "Pronoun + verb phrase, not organization"
        },
        {
            "text": "e fund", 
            "context": "investment focus is startups, early-stage and emerging companies. The financing is provided by venture capital firms or funds, e fund",
            "should_be_org": False,
            "reason": "Partial word fragment, not real organization"
        },
        {
            "text": "r bar",
            "context": "some context with r bar in it",
            "should_be_org": False, 
            "reason": "Partial word fragment, nonsensical"
        },
        {
            "text": "real estate",
            "context": "focused on technology, healthcare, financial services, innovation, renewable energy, e-commerce, and real estate",
            "should_be_org": False,
            "reason": "Generic industry term, not specific organization"
        },
        {
            "text": "the way",
            "context": "Revolutionize the way you evaluate investments",
            "should_be_org": False,
            "reason": "Common phrase, not organization"
        },
        # Compare with legitimate organizations that should pass
        {
            "text": "Google",
            "context": "Google announced new AI features today",
            "should_be_org": True,
            "reason": "Known major corporation, capitalized, proper context"
        },
        {
            "text": "Tiger Global",
            "context": "Tiger Global is a venture capital fund",
            "should_be_org": True,
            "reason": "Known VC firm, proper capitalization, business context"
        }
    ]
    
    print("🧪 TESTING DISAMBIGUATION EFFECTIVENESS")
    print("=" * 50)
    
    try:
        # Test organization extraction quality controls from config
        from config.config import load_config
        config = load_config()
        
        org_config = config.get('corpus', {}).get('organization_extraction', {})
        print(f"Organization extraction mode: {org_config.get('mode', 'not configured')}")
        print(f"Reject single words: {org_config.get('reject_single_words', False)}")
        print(f"Reject common words: {org_config.get('reject_common_words', False)}")
        print(f"Confidence threshold: {org_config.get('thresholds', {}).get('confidence', 'not set')}")
        
        # Test blacklist patterns
        blacklist = org_config.get('blacklist_patterns', [])
        print(f"Blacklist patterns: {len(blacklist)} patterns configured")
        
        for pattern in blacklist:
            print(f"  - {pattern}")
            
    except Exception as e:
        print(f"⚠️ Could not load config: {e}")
    
    print("\n" + "=" * 50)
    print("TESTING INDIVIDUAL CASES:")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        text = case["text"]
        context = case["context"]
        should_be_org = case["should_be_org"]
        reason = case["reason"]
        
        print(f"\n{i}. Testing: '{text}'")
        print(f"   Context: ...{context}...")
        print(f"   Expected: {'✅ ORG' if should_be_org else '❌ NOT ORG'}")
        print(f"   Reason: {reason}")
        
        # Check against known quality controls
        issues = []
        
        # Check capitalization
        if not text[0].isupper() and len(text.split()) == 1:
            issues.append("not capitalized (single word)")
            
        # Check for common word patterns
        common_words = ['the', 'a', 'an', 'of', 'and', 'we', 'you', 'they', 'move', 'way']
        if any(word in text.lower() for word in common_words):
            issues.append("contains common words")
            
        # Check length
        if len(text) < 3:
            issues.append("too short")
            
        # Check for partial fragments
        if len(text.split()) == 2 and len(text) < 6:
            issues.append("likely partial fragment")
            
        # Check for obvious non-org patterns
        if text.lower().startswith(('we ', 'the ', 'and ')):
            issues.append("starts with article/pronoun")
            
        if issues:
            print(f"   ⚠️ Quality issues found: {', '.join(issues)}")
            predicted_result = "Would be FILTERED OUT"
        else:
            predicted_result = "Would PASS filters"
            
        print(f"   🔍 Prediction: {predicted_result}")
        
        # Check if prediction matches expectation
        should_filter = not should_be_org
        would_filter = len(issues) > 0
        
        if should_filter == would_filter:
            print(f"   ✅ CORRECT: Filter prediction matches expectation")
        else:
            print(f"   ❌ INCORRECT: Filter prediction doesn't match expectation")

if __name__ == "__main__":
    test_disambiguation_effectiveness()