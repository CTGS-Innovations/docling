#!/usr/bin/env python3
"""
Test FLPC patterns for money, percentage, and measurement ranges
================================================================

GOAL: Test if FLPC patterns correctly handle:
- Money ranges: "60 to 70 billion", "$10M to $20M" 
- Percentage ranges: "60% to 70%", "15-20%"
- Complex money: "$25.91 billion", "$55.7B"
- Simple percentages: "5%", "12.5%"

REASON: User reported that percentages and money ranges aren't being extracted correctly
PROBLEM: Current FLPC patterns are too simple and don't handle ranges or complex formats
"""

import re
from typing import List, Dict, Any

def test_current_patterns():
    """Test current FLPC patterns against real examples"""
    
    # Current patterns from pattern_sets.yaml
    current_patterns = {
        'money': r'(?i)\$[\d,]+(?:\.?\d{0,2})?(?:\s*(?:million|billion|thousand|M|B|K))?|[\d,]+(?:\.?\d{0,2})?\s*(?:dollars?|USD|EUR|GBP|pounds?|euros?)',
        'percent': r'\b\d{1,3}(?:\.\d{1,2})?%',
        'measurement': r'(?i)\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)',
        'range': r'(?i)\b\d+\s*-\s*\d+\b|\b\d+\s*to\s*\d+\b'
    }
    
    # Test cases from real venture capital document
    test_cases = [
        # Money values that should work
        "$58.51",
        "$55.7B", 
        "$52.3B",
        "$21 billion",
        "$25B",
        
        # Money ranges that currently fail
        "60 to 70 billion dollars",
        "$10M to $20M",
        "$1.5 billion to $2.3 billion",
        "between $500K and $1M",
        
        # Percentage values 
        "5%",
        "12.5%",
        "85%",
        
        # Percentage ranges that currently fail
        "60% to 70%",
        "15-20%",
        "between 5% and 10%",
        "5% - 15%",
        
        # Measurements
        "28 G",
        "15 L", 
        "5m",
        
        # Measurement ranges that currently fail
        "10-15 kg",
        "5 to 10 feet",
        "between 100g and 200g"
    ]
    
    print("🧪 Testing Current FLPC Patterns")
    print("=" * 60)
    
    for pattern_name, pattern_str in current_patterns.items():
        print(f"\n📊 {pattern_name.upper()} Pattern:")
        print(f"   Pattern: {pattern_str}")
        
        pattern = re.compile(pattern_str)
        matches_found = 0
        
        for test_case in test_cases:
            matches = pattern.findall(test_case)
            if matches:
                matches_found += 1
                print(f"   ✅ '{test_case}' -> {matches}")
            else:
                # Check if this test case should match this pattern type
                should_match = False
                if pattern_name == 'money' and ('$' in test_case or 'billion' in test_case or 'dollars' in test_case):
                    should_match = True
                elif pattern_name == 'percent' and '%' in test_case:
                    should_match = True
                elif pattern_name == 'measurement' and any(unit in test_case.lower() for unit in ['g', 'l', 'm', 'kg', 'feet']):
                    should_match = True
                elif pattern_name == 'range' and ('to' in test_case or '-' in test_case):
                    should_match = True
                    
                if should_match:
                    print(f"   ❌ '{test_case}' -> NO MATCH (should match)")
        
        print(f"   📈 Total matches: {matches_found}/{len(test_cases)}")

def propose_improved_patterns():
    """Propose improved patterns that handle ranges and complex formats"""
    
    print("\n\n🔧 PROPOSED IMPROVED PATTERNS")
    print("=" * 60)
    
    improved_patterns = {
        'money': {
            'pattern': r'(?i)(?:\$[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?|\$[\d,]+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?\s*(?:million|billion|thousand|M|B|K)?\s*(?:dollars?|USD))|(?:\$[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?\s*(?:to|-)\s*\$?[\d,]+(?:\.\d{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?)|(?:\d+(?:\.\d{1,2})?\s*(?:to|-)\s*\d+(?:\.\d{1,2})?\s*(?:million|billion|thousand)?\s*dollars?)',
            'description': 'Money amounts including ranges: $1M, $10-20M, 60 to 70 billion dollars',
            'examples': ['$58.51', '$55.7B', '$10M to $20M', '60 to 70 billion dollars']
        },
        
        'percent': {
            'pattern': r'(?i)\b\d{1,3}(?:\.\d{1,2})?%(?:\s*(?:to|-)\s*\d{1,3}(?:\.\d{1,2})?%)?|\b\d{1,3}(?:\.\d{1,2})?%?\s*(?:to|-)\s*\d{1,3}(?:\.\d{1,2})?%',
            'description': 'Percentage values including ranges: 5%, 60% to 70%, 15-20%',
            'examples': ['5%', '12.5%', '60% to 70%', '15-20%']
        },
        
        'measurement': {
            'pattern': r'(?i)\b\d+(?:\.\d+)?(?:\s*(?:to|-)\s*\d+(?:\.\d+)?)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)',
            'description': 'Measurements including ranges: 28G, 10-15 kg, 5 to 10 feet',
            'examples': ['28 G', '15 L', '10-15 kg', '5 to 10 feet']
        }
    }
    
    for pattern_name, pattern_info in improved_patterns.items():
        print(f"\n🎯 {pattern_name.upper()} (Improved):")
        print(f"   Pattern: {pattern_info['pattern']}")
        print(f"   Description: {pattern_info['description']}")
        print(f"   Examples: {', '.join(pattern_info['examples'])}")

if __name__ == "__main__":
    test_current_patterns()
    propose_improved_patterns()