#!/usr/bin/env python3
"""
GOAL: Test range_indicator pattern directly with FLPC engine
REASON: Range indicators show empty in output despite pattern being included
PROBLEM: Need to verify if FLPC is compiling and matching range_indicator pattern
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_range_indicator_direct():
    """Test range_indicator pattern directly with FLPC"""
    print("🔍 TESTING RANGE INDICATOR PATTERN DIRECTLY")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test cases that should trigger range indicators
    test_cases = [
        "30-37 inches",           # Hyphen
        "6 to 10 feet",          # "to"
        "between 50 and 75",     # "between" and "and"
        "from -20°F through 120°F", # "through"
        "range 15-30 minutes",   # Hyphen in context
        "-",                     # Just hyphen
        "to",                    # Just "to"
        "between",               # Just "between"
        "and",                   # Just "and"
        "through"                # Just "through"
    ]
    
    print("📋 TESTING RANGE INDICATOR DETECTION:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: '{test_case}'")
        
        # Test with FLPC
        flpc_results = flpc_engine.extract_entities(test_case, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        # Show range indicators specifically
        range_indicators = flpc_entities.get('RANGE_INDICATOR', [])
        if range_indicators:
            print(f"   ✅ RANGE_INDICATOR: {range_indicators}")
        else:
            print(f"   ❌ No range indicators detected")
            
        # Also show what else was detected
        other_entities = {k: v for k, v in flpc_entities.items() if k != 'RANGE_INDICATOR' and v}
        if other_entities:
            print(f"   ℹ️  Other entities: {other_entities}")
    
    # Test the pattern itself
    print(f"\n🎯 PATTERN ANALYSIS:")
    print("-" * 30)
    
    import re
    
    # The range indicator pattern from config
    pattern = r'(?i)\b(?:to|through|between|and)\b|[-–—]'
    
    for test_case in test_cases:
        matches = re.findall(pattern, test_case)
        print(f"'{test_case}' -> {matches}")

if __name__ == "__main__":
    test_range_indicator_direct()