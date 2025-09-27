#!/usr/bin/env python3
"""
Test measurement pattern issues from safety document
===================================================

GOAL: Identify why 70%+ of measurements are missing from section 9.4
REASON: Current pattern isn't capturing common measurements like "22 inches", "90 decibels"
PROBLEM: Pattern may be missing units or have spacing issues
"""

import re

def test_current_measurement_pattern():
    """Test current measurement pattern against real safety measurements"""
    
    # Current pattern from pattern_sets.yaml
    current_pattern = r'(?i)(?:\b\d+(?:\.\d+)?\s*(?:to|-)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?))|(?:\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?))'
    
    # Real measurements from section 9.4 that should be extracted
    missing_measurements = [
        "22 inches",
        "30-37 inches", 
        "76-94 cm",
        "30 inches",
        "76 cm",
        "9.5 inches",
        "24 cm", 
        "20 inches",
        "51 cm",
        "18 inches",
        "46 cm",
        "10 feet",
        "3 meters",
        "5 feet", 
        "1.5 meters",
        "90 decibels",
        "500 feet",
        "152 meters",
        "15 minutes",
        "15 feet",
        "4.6 meters",
        "-20°F to 120°F",
        "-29°C to 49°C"
    ]
    
    # Measurements that are being extracted
    working_measurements = [
        "1.8288",  # No unit - decimal only
        "1.07",    # No unit - decimal only  
        "0.1016",  # No unit - decimal only
        "250.0",   # No unit - being captured as money
        "28 G",    # Working
        "15 L",    # Working
        "5m"       # Working
    ]
    
    print("🧪 Testing Current Measurement Pattern")
    print("=" * 60)
    print(f"Pattern: {current_pattern}")
    print()
    
    pattern = re.compile(current_pattern)
    
    print("❌ MISSING measurements (should match but don't):")
    missing_count = 0
    for measurement in missing_measurements:
        matches = pattern.findall(measurement)
        if not matches:
            missing_count += 1
            print(f"   ❌ '{measurement}' -> NO MATCH")
        else:
            print(f"   ✅ '{measurement}' -> {matches}")
    
    print(f"\n✅ WORKING measurements:")
    working_count = 0
    for measurement in working_measurements:
        matches = pattern.findall(measurement)
        if matches:
            working_count += 1
            print(f"   ✅ '{measurement}' -> {matches}")
        else:
            print(f"   ❌ '{measurement}' -> NO MATCH")
    
    total_tested = len(missing_measurements) + len(working_measurements)
    success_rate = ((working_count) / total_tested) * 100
    missing_rate = (missing_count / len(missing_measurements)) * 100
    
    print(f"\n📊 RESULTS:")
    print(f"   Missing: {missing_count}/{len(missing_measurements)} ({missing_rate:.1f}%)")
    print(f"   Working: {working_count}/{len(working_measurements)}")
    print(f"   Overall success rate: {success_rate:.1f}%")
    
    if missing_rate > 50:
        print(f"   🔴 **CRITICAL**: {missing_rate:.1f}% of expected measurements are missing!")

def analyze_pattern_issues():
    """Analyze what's wrong with the current pattern"""
    
    print(f"\n🔍 PATTERN ANALYSIS")
    print("=" * 60)
    
    # Current pattern broken down
    current_pattern = r'(?i)(?:\b\d+(?:\.\d+)?\s*(?:to|-)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?))|(?:\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?))'
    
    print("🔴 **IDENTIFIED ISSUES:**")
    print("1. Missing units:")
    print("   - 'inch' (only has 'inches?')")
    print("   - 'decibels' / 'db'")  
    print("   - 'minutes' / 'min'")
    print("   - 'hours' / 'hr'")
    print("   - Temperature ranges: '°F to °C'")
    print()
    print("2. Spacing issues:")
    print("   - Pattern requires \\s* but some have different spacing")
    print("   - Negative numbers: '-20°F' not handled")
    print()
    print("3. Range format issues:")
    print("   - '30-37 inches' should be captured as single entity")
    print("   - Temperature ranges like '-20°F to 120°F' not handled")

def propose_improved_measurement_pattern():
    """Propose improved measurement pattern"""
    
    print(f"\n🔧 PROPOSED IMPROVED PATTERN")
    print("=" * 60)
    
    # Comprehensive measurement pattern 
    improved_pattern = r'''(?i)(?:
        # Temperature ranges: -20°F to 120°F, -29°C to 49°C
        -?\d+(?:\.\d+)?°[CF]\s*(?:to|-)\s*-?\d+(?:\.\d+)?°[CF]
        |
        # Measurement ranges: 30-37 inches, 76-94 cm
        \b\d+(?:\.\d+)?\s*(?:to|-)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)
        |
        # Single measurements: 22 inches, 90 decibels, 15 minutes
        \b-?\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)
    )'''
    
    # Clean pattern (remove comments and whitespace)
    clean_pattern = r'(?i)(?:-?\d+(?:\.\d+)?°[CF]\s*(?:to|-)\s*-?\d+(?:\.\d+)?°[CF]|\b\d+(?:\.\d+)?\s*(?:to|-)\s*\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)|\b-?\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?))'
    
    print(f"Improved pattern:")
    print(f"{clean_pattern}")
    print()
    print("🎯 **IMPROVEMENTS:**")
    print("1. Added missing units: decibels, minutes, hours, inch, pounds")
    print("2. Added negative number support: -20°F")
    print("3. Fixed temperature ranges: -20°F to 120°F")
    print("4. Better range handling: 30-37 inches as single entity")
    print("5. More unit variations: metre, foot, db, min, hr")
    
    return clean_pattern

if __name__ == "__main__":
    test_current_measurement_pattern()
    analyze_pattern_issues()
    improved = propose_improved_measurement_pattern()
    
    print(f"\n🧪 Testing Improved Pattern")
    print("=" * 60)
    
    # Quick test of improved pattern
    test_cases = ["22 inches", "30-37 inches", "90 decibels", "-20°F to 120°F", "15 minutes"]
    improved_regex = re.compile(improved)
    
    for test in test_cases:
        matches = improved_regex.findall(test)
        if matches:
            print(f"   ✅ '{test}' -> {matches}")
        else:
            print(f"   ❌ '{test}' -> NO MATCH")