#!/usr/bin/env python3
"""
GOAL: Debug why specific measurements are missed (decibels, minutes, inches in ranges)
REASON: We detect most measurements but miss "90 decibels", "15 minutes", "30-37 inches"
PROBLEM: Need to find which patterns aren't matching these specific cases
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_missing_measurements():
    """Test specific missed measurements against our split patterns"""
    print("🔍 DEBUGGING MISSING MEASUREMENTS")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test cases that should be detected but aren't
    test_cases = [
        "Handrail height 30-37 inches (76-94 cm)",
        "Noise exposure limit 90 decibels for 8 hours", 
        "Response time 15 minutes maximum",
        "Temperature range -20°F to 120°F (-29°C to 49°C)",
        "Simple test: 30 inches and 37 inches",
        "Simple test: 90 decibels",
        "Simple test: 15 minutes"
    ]
    
    print("📋 TESTING SPECIFIC MISSED CASES:")
    print("-" * 30)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case}")
        
        # Test with FLPC
        flpc_results = flpc_engine.extract_entities(test_case, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        # Show what FLPC detected
        detected = False
        for entity_type, entities in flpc_entities.items():
            if 'MEASUREMENT' in entity_type and entities:
                detected = True
                print(f"   ✅ {entity_type}: {entities}")
        
        if not detected:
            print(f"   ❌ No measurements detected")
    
    # Test our patterns individually
    print(f"\n📋 TESTING INDIVIDUAL PATTERNS:")
    print("-" * 30)
    
    import re
    
    # Test pattern definitions from our config
    patterns = {
        'MEASUREMENT_LENGTH': r'(?i)\b-?\d+(?:\.\d+)?\s*(?:feet|ft|inches?|inch|cm|mm|meters?|metres?|m|km|mi|yd|yards?)',
        'MEASUREMENT_SOUND': r'(?i)\b-?\d+(?:\.\d+)?\s*(?:decibels?|dB)',
        'MEASUREMENT_TIME': r'(?i)\b-?\d+(?:\.\d+)?\s*(?:minutes?|mins?|seconds?|secs?|hours?|hrs?|days?|weeks?|months?|years?)',
        'MEASUREMENT_TEMPERATURE': r'(?i)\b-?\d+(?:\.\d+)?\s*(?:degrees?|degC|degF|°C|°F)'
    }
    
    problem_texts = [
        "30-37 inches",
        "90 decibels", 
        "15 minutes",
        "-20°F to 120°F"
    ]
    
    for text in problem_texts:
        print(f"\n🔍 Testing: '{text}'")
        for pattern_name, pattern in patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                print(f"   ✅ {pattern_name}: {matches}")
            else:
                print(f"   ❌ {pattern_name}: no match")
    
    print(f"\n📊 ANALYSIS:")
    print("- If individual patterns match but FLPC doesn't detect: FLPC compilation issue")
    print("- If patterns don't match: pattern needs adjustment")
    print("- Range patterns like '30-37 inches' need individual '30' and '37' detection")

if __name__ == "__main__":
    debug_missing_measurements()