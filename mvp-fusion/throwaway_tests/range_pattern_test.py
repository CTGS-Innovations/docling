#!/usr/bin/env python3
"""
Range Pattern Direct Test
=========================

GOAL: Test the range regex pattern directly to see why it's not matching
REASON: FLPC showing 0 range entities for obvious range patterns
PROBLEM: Need to validate regex pattern against test cases

Pattern from config:
(?i)(?:-?\d+(?:\.\d+)?%\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?%|-?\d+(?:\.\d+)?°[CF]\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?°[CF]|\b\d+(?:\.\d+)?\s*(?:to|-|through)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)|\b\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?|%))
"""

import re

def test_range_pattern():
    """Test range regex pattern directly"""
    print("🔍 RANGE PATTERN DIRECT TEST")
    print("=" * 50)
    print("Testing regex pattern against failing cases")
    print()
    
    # The exact pattern from config
    range_pattern = r'(?i)(?:-?\d+(?:\.\d+)?%\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?%|-?\d+(?:\.\d+)?°[CF]\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?°[CF]|\b\d+(?:\.\d+)?\s*(?:to|-|through)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)|\b\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?|%))'
    
    # Test cases that should match
    test_cases = [
        "10-15%",
        "-20°F to 120°F", 
        "30-37 inches",
        "10% to 15%",
        "20°F - 120°F",
        "-29°C to 49°C",
        "between 10% and 15%"  # This might not match - no 'between' in pattern
    ]
    
    compiled_pattern = re.compile(range_pattern)
    
    print("📊 REGEX PATTERN TEST RESULTS:")
    print("-" * 40)
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i}: \"{text}\"")
        
        matches = compiled_pattern.findall(text)
        
        if matches:
            print(f"  ✅ MATCHED: {matches}")
        else:
            print(f"  ❌ NO MATCH")
            
            # Try to understand why
            print(f"    🔍 Debugging:")
            
            # Test individual pattern components
            percent_range = re.search(r'-?\d+(?:\.\d+)?%\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?%', text, re.IGNORECASE)
            temp_range = re.search(r'-?\d+(?:\.\d+)?°[CF]\s*(?:to|-|through)\s*-?\d+(?:\.\d+)?°[CF]', text, re.IGNORECASE)
            unit_range = re.search(r'\b\d+(?:\.\d+)?\s*(?:to|-|through)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)', text, re.IGNORECASE)
            hyphen_range = re.search(r'\b\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?|%)', text, re.IGNORECASE)
            
            if percent_range:
                print(f"    - Percent range component: MATCHED")
            if temp_range:
                print(f"    - Temperature range component: MATCHED")
            if unit_range:
                print(f"    - Unit range component: MATCHED")
            if hyphen_range:
                print(f"    - Hyphen range component: MATCHED")
            if not any([percent_range, temp_range, unit_range, hyphen_range]):
                print(f"    - No component patterns matched")
        
        print()
    
    print("🎯 PATTERN ANALYSIS:")
    print("-" * 20)
    print("The pattern has 4 main components:")
    print("1. Percent ranges: -?\\d+(?:\\.\\d+)?%\\s*(?:to|-|through)\\s*-?\\d+(?:\\.\\d+)?%")
    print("2. Temperature ranges: -?\\d+(?:\\.\\d+)?°[CF]\\s*(?:to|-|through)\\s*-?\\d+(?:\\.\\d+)?°[CF]") 
    print("3. Unit ranges with 'to': \\b\\d+(?:\\.\\d+)?\\s*(?:to|-|through)\\s*\\d+(?:\\.\\d+)?\\s*[units]")
    print("4. Hyphen ranges: \\b\\d+(?:\\.\\d+)?\\s*-\\s*\\d+(?:\\.\\d+)?\\s*[units]")

if __name__ == "__main__":
    print("# GOAL: Test range regex pattern directly")
    print("# REASON: FLPC returning 0 range entities for obvious ranges")
    print("# PROBLEM: Need to debug regex pattern matching")
    print()
    
    test_range_pattern()
    
    print("\n🔧 Next: Fix pattern based on test results")