#!/usr/bin/env python3
"""
GOAL: Debug why "30" is still not detected in "30-37 inches"
REASON: Pattern changes captured prefixes but still miss first number
PROBLEM: Need to find exact pattern that captures both "30 inches" and "37 inches"
"""

import re

def debug_boundary_patterns():
    """Test different approaches to detect both numbers in ranges"""
    print("🔍 DEBUGGING BOUNDARY PATTERNS")
    print("=" * 50)
    
    test_text = "30-37 inches"
    
    # Test different pattern approaches
    patterns = [
        (r'(?i)(?:^|[\s\-])\d+(?:\.\d+)?\s*(?:inches?)', "Current (with prefix capture)"),
        (r'(?i)(?<=^|[\s\-])\d+(?:\.\d+)?\s*(?:inches?)', "Lookbehind (may not work)"),
        (r'(?i)(?:(?<=^)|(?<=\s)|(?<=\-))\d+(?:\.\d+)?\s*(?:inches?)', "Multiple lookbehinds"),
        (r'(?i)\d+(?:\.\d+)?\s*(?:inches?)', "No boundaries (simple)"),
        (r'(?i)(?:\d+\s*(?:inches?))', "Grouped capture"),
    ]
    
    print(f"Testing text: '{test_text}'")
    print("-" * 30)
    
    for pattern, description in patterns:
        print(f"✅ {description}")
        print(f"   Pattern: {pattern}")
        try:
            matches = re.findall(pattern, test_text)
            print(f"   Matches: {matches}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
    
    # Test the core issue: why isn't "30" detected?
    print("🎯 CORE ISSUE ANALYSIS:")
    print("-" * 30)
    
    # Break down the text character by character around "30"
    text = "30-37 inches"
    print(f"Text breakdown: '{text}'")
    print("Position: 0123456789...")
    print()
    
    # Test if simple digit detection works
    digit_pattern = r'\d+'
    digit_matches = re.findall(digit_pattern, text)
    print(f"All digits: {digit_matches}")
    
    # Test if the issue is the unit matching
    number_unit_pattern = r'\d+\s*inches?'
    nu_matches = re.findall(number_unit_pattern, text)
    print(f"Number + unit: {nu_matches}")
    
    # Test the specific positioning
    print("\nPosition analysis:")
    print(f"'30' at position 0-1")
    print(f"'-' at position 2") 
    print(f"'37' at position 3-4")
    print(f"' inches' at position 5-11")
    
    # The key insight: "30" doesn't have "inches" directly after it
    # We need to detect "30" near "inches" via proximity
    print("\n💡 KEY INSIGHT:")
    print("'30' doesn't have 'inches' directly after it - only '37 inches' does")
    print("We need proximity-based detection using range indicators")

if __name__ == "__main__":
    debug_boundary_patterns()