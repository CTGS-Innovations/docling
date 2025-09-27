#!/usr/bin/env python3
"""
Negative Number Detection Test
==============================

GOAL: Test why -20°F is not being detected as single measurement entity
REASON: User requirement to detect negative numbers correctly
PROBLEM: FLPC should detect "-20°F" not just "20°F"

Pattern: (?i)\b-?\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)\b
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fusion.flpc_engine import FLPCEngine
import yaml
from pathlib import Path
import re

def test_negative_detection():
    """Test negative number detection in measurements"""
    print("🔍 NEGATIVE NUMBER DETECTION TEST")
    print("=" * 50)
    print("Testing FLPC measurement pattern for negative numbers")
    print()
    
    # Load FLPC engine
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    flpc_engine = FLPCEngine(config)
    
    # Test cases with negative numbers
    test_cases = [
        "-20°F",
        "-29°C", 
        "Temperature range -20°F to 120°F",
        "-37 inches",
        "Growth projection: 10-15% range",
        "20°F",  # Positive control
        "Temperature is -20°F today"
    ]
    
    print("📊 FLPC DETECTION TEST:")
    print("-" * 30)
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i}: \"{text}\"")
        
        try:
            results = flpc_engine.extract_entities(text)
            measurements = results.get('entities', {}).get('MEASUREMENT', [])
            
            print(f"  📏 MEASUREMENT entities: {measurements}")
            
            # Check if negative numbers are properly detected
            if any('-' in m for m in measurements):
                print(f"  ✅ Negative number detected properly")
            elif measurements and '-' in text:
                print(f"  ⚠️  Detected measurements but missed negative sign")
            elif not measurements and any(unit in text for unit in ['°F', '°C', 'inches', '%']):
                print(f"  ❌ Failed to detect measurement entirely")
            else:
                print(f"  ℹ️  No measurement expected or found")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            
        print()
    
    # Test the pattern directly with regex
    print("📊 DIRECT REGEX TEST:")
    print("-" * 30)
    
    measurement_pattern = r'(?i)\b-?\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|pounds?|oz|ounces?|ml|l|liters?|gal|gallons?|ft|feet|foot|inches?|inch|meters?|metre|m|cm|mm|millimeters?|kilometers?|km|decibels?|db|minutes?|min|hours?|hr|°[CF]|degrees?)\b'
    compiled = re.compile(measurement_pattern)
    
    regex_test_cases = ["-20°F", "-29°C", "-37 inches", "20°F"]
    
    for text in regex_test_cases:
        matches = compiled.findall(text)
        print(f"\"{text}\" → Regex matches: {matches}")
    
    print(f"\n🎯 DIAGNOSIS:")
    print("If regex works but FLPC doesn't, issue is in FLPC compilation/execution")
    print("If regex fails too, issue is in pattern design")

if __name__ == "__main__":
    print("# GOAL: Test negative number detection in measurements")
    print("# REASON: -20°F should be detected as single entity") 
    print("# PROBLEM: FLPC may not be detecting negative numbers properly")
    print()
    
    test_negative_detection()
    
    print("\n🔧 Next: Fix negative number detection based on test results")