#!/usr/bin/env python3
"""
GOAL: Simple debug of why "37 inches" not detected in "**30-37 inches**"  
REASON: Need to test pattern matching step by step
PROBLEM: Pattern should match but doesn't
"""

import sys
import re

def debug_37_simple():
    """Simple pattern testing"""
    print("🔍 SIMPLE DEBUG: '37 inches' in '**30-37 inches**'")
    print("=" * 50)
    
    test_text = "**30-37 inches**"
    print(f"Text: '{test_text}'")
    print(f"Character positions:")
    for i, char in enumerate(test_text):
        print(f"  [{i:2d}] '{char}'")
    
    # Our current pattern
    pattern = r'(?i)(?:^|[^\w])\d+(?:\.\d+)?\s*\b(?:inches?)\b'
    
    print(f"\nPattern: {pattern}")
    print(f"Breaking down the match attempt:")
    
    # Find where "37" starts
    pos_37 = test_text.find("37")
    char_before = test_text[pos_37-1] if pos_37 > 0 else "START"
    
    print(f"  '37' starts at position {pos_37}")
    print(f"  Character before '37': '{char_before}' (ord: {ord(char_before)})")
    print(f"  Is '{char_before}' non-word? {not char_before.isalnum() and char_before != '_'}")
    
    # Test manual regex
    matches = list(re.finditer(pattern, test_text))
    print(f"\nRegex matches found: {len(matches)}")
    
    for i, match in enumerate(matches, 1):
        print(f"  {i}. '{match.group()}' at [{match.start()}-{match.end()}]")
    
    # Test simpler patterns progressively
    simple_patterns = [
        (r'37', "Just '37'"),
        (r'37\s*inches', "'37 inches'"),
        (r'\b37\s*inches\b', "'37 inches' with word boundaries"),
        (r'[^\w]37\s*inches', "Non-word + '37 inches'"),
        (r'(?:^|[^\w])37\s*inches', "Full prefix + '37 inches'"),
        (r'(?:^|[^\w])\d+\s*inches', "Full pattern without optional parts"),
        (r'(?i)(?:^|[^\w])\d+(?:\.\d+)?\s*\binches?\b', "Full current pattern"),
    ]
    
    print(f"\nTesting simpler patterns:")
    for pattern_test, description in simple_patterns:
        matches = list(re.finditer(pattern_test, test_text))
        print(f"  {description}: {len(matches)} matches")
        for match in matches:
            print(f"    - '{match.group()}' at [{match.start()}-{match.end()}]")
    
    # The key insight - let's check what SHOULD match
    print(f"\nChecking substring '37 inches':")
    substring = test_text[5:14]  # "37 inches"
    print(f"  Substring: '{substring}'")
    
    # Test the pattern against the substring
    substring_match = re.search(pattern, substring)
    print(f"  Pattern matches substring: {substring_match is not None}")
    
    # Test with context
    context = test_text[4:14]  # "-37 inches"
    print(f"  Context: '{context}'")
    context_match = re.search(pattern, context)
    print(f"  Pattern matches context: {context_match is not None}")
    if context_match:
        print(f"    Match: '{context_match.group()}'")

if __name__ == "__main__":
    debug_37_simple()