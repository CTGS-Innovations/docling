#!/usr/bin/env python3
"""
GOAL: Test URL pattern fix for consecutive markdown links
REASON: Pattern was detecting all URLs as one entity instead of three separate ones  
PROBLEM: Pattern allowed parentheses so didn't stop at markdown link boundaries
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_url_pattern_fix():
    """Test that URL pattern correctly separates consecutive markdown links"""
    
    # Test case with consecutive markdown links
    test_text = """CEO & Founder of DealRoom[](https://www.linkedin.com/in/kisonpatel/)[](https://twitter.com/KisonPatel)[](https://kisonpatel.com/)The VC investment levels"""
    
    print("🧪 TESTING URL PATTERN FIX")
    print("=" * 45)
    print(f"Input text: {test_text}")
    print("-" * 40)
    
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    
    processor = ServiceProcessor(config)
    
    # Extract entities using the fixed pattern
    entities = processor._extract_universal_entities(test_text)
    
    # Check URL entities
    url_entities = entities.get('url', [])
    print(f"URL entities found: {len(url_entities)}")
    
    for i, url in enumerate(url_entities, 1):
        text = url.get('text', '')
        print(f"  {i}. {repr(text)}")
    
    # Expected: 3 separate URLs
    expected_urls = [
        "https://www.linkedin.com/in/kisonpatel/",
        "https://twitter.com/KisonPatel", 
        "https://kisonpatel.com/"
    ]
    
    print(f"\nExpected: {len(expected_urls)} separate URLs")
    for i, expected in enumerate(expected_urls, 1):
        print(f"  {i}. {expected}")
    
    if len(url_entities) == 3:
        print("\n✅ SUCCESS: Found 3 separate URL entities!")
    elif len(url_entities) == 1:
        print("\n❌ ISSUE: Still detecting as 1 combined entity")
    else:
        print(f"\n⚠️  UNEXPECTED: Found {len(url_entities)} entities")

if __name__ == "__main__":
    test_url_pattern_fix()