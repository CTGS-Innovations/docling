#!/usr/bin/env python3
"""
GOAL: Test why "30" in "30-37 inches" isn't being detected
REASON: Need to understand regex word boundary issues with ranges
PROBLEM: "30-37 inches" should detect both "30 inches" and "37 inches"
"""

import re

def test_range_patterns():
    """Test different regex patterns for range detection"""
    print("🔍 TESTING RANGE PATTERN DETECTION")
    print("=" * 50)
    
    text = "30-37 inches"
    
    patterns = [
        (r'\b\d+(?:\.\d+)?\s*(?:inches?)', "Current pattern (with word boundary)"),
        (r'(?<!\d)\d+(?:\.\d+)?\s*(?:inches?)', "Negative lookbehind (no digit before)"),
        (r'(?:^|\s|-)(\d+(?:\.\d+)?)\s*(?:inches?)', "Start/space/hyphen before number"),
        (r'\d+(?:\.\d+)?\s*(?:inches?)', "Simple pattern (no boundaries)"),
        (r'(?:\b|-)(\d+(?:\.\d+)?)\s*(?:inches?)', "Word boundary OR hyphen"),
    ]
    
    print(f"Testing text: '{text}'")
    print("-" * 30)
    
    for pattern, description in patterns:
        matches = re.findall(pattern, text)
        print(f"✅ {description}")
        print(f"   Pattern: {pattern}")
        print(f"   Matches: {matches}")
        print()
    
    # Test the complete range detection
    print("🎯 COMPLETE RANGE DETECTION TEST:")
    print("-" * 30)
    
    test_cases = [
        "30-37 inches",
        "height 30-37 inches and width", 
        "between 6-10 feet",
        "range of 15-20 meters"
    ]
    
    # Best pattern based on tests above
    best_pattern = r'(?:\b|-)(\d+(?:\.\d+)?)\s*(?:inches?|feet|ft|meters?|metres?|cm|mm)'
    
    for case in test_cases:
        matches = re.findall(best_pattern, case)
        print(f"Text: '{case}'")
        print(f"Detected: {matches}")
        print()

if __name__ == "__main__":
    test_range_patterns()