#!/usr/bin/env python3
"""
GOAL: Test range indicator detection and fix measurement pattern word boundaries
REASON: Need to verify range_indicator pattern works and fix "30-37 inches" detection
PROBLEM: Only detecting "-37 inches" instead of both "30" and "37 inches"
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_range_indicators():
    """Test range indicator pattern and measurement boundary issues"""
    print("🔍 TESTING RANGE INDICATORS AND BOUNDARIES")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test cases with different range indicators
    test_cases = [
        "Handrail height 30-37 inches (76-94 cm)",
        "Distance between 6 to 10 feet", 
        "Temperature range from -20°F through 120°F",
        "Weight between 50 and 75 pounds",
        "Duration 15-30 minutes maximum",
        "Simple: 30 inches and 37 inches"
    ]
    
    print("📋 TESTING RANGE INDICATOR DETECTION:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case}")
        
        # Test with FLPC
        flpc_results = flpc_engine.extract_entities(test_case, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        # Show range indicators
        range_indicators = flpc_entities.get('RANGE_INDICATOR', [])
        if range_indicators:
            print(f"   🎯 RANGE_INDICATOR: {range_indicators}")
        else:
            print(f"   ❌ No range indicators detected")
        
        # Show measurements
        measurement_detected = False
        for entity_type in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE']:
            entities = flpc_entities.get(entity_type, [])
            if entities:
                measurement_detected = True
                print(f"   ✅ {entity_type}: {entities}")
        
        if not measurement_detected:
            print(f"   ❌ No measurements detected")
    
    # Test the specific word boundary issue
    print(f"\n🎯 TESTING WORD BOUNDARY FIXES:")
    print("-" * 40)
    
    import re
    
    # Current pattern (problematic)
    current_pattern = r'(?i)\b\d+(?:\.\d+)?\s*(?:inches?|feet|ft)'
    
    # Proposed fixes
    fixed_patterns = [
        r'(?i)(?<=\s|^|\-)\d+(?:\.\d+)?\s*(?:inches?|feet|ft)',  # Lookbehind with hyphen
        r'(?i)(?:\s|^|\-)(\d+(?:\.\d+)?)\s*(?:inches?|feet|ft)',  # Group capture with hyphen
        r'(?i)\d+(?:\.\d+)?\s*(?:inches?|feet|ft)',  # Simple without word boundary
    ]
    
    test_text = "30-37 inches"
    
    print(f"Testing text: '{test_text}'")
    print()
    
    print(f"Current pattern: {current_pattern}")
    matches = re.findall(current_pattern, test_text)
    print(f"Matches: {matches}")
    print()
    
    for i, pattern in enumerate(fixed_patterns, 1):
        print(f"Fix {i}: {pattern}")
        try:
            matches = re.findall(pattern, test_text)
            print(f"Matches: {matches}")
        except Exception as e:
            print(f"Error: {e}")
        print()

if __name__ == "__main__":
    test_range_indicators()