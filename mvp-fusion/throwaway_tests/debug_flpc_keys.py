#!/usr/bin/env python3
"""
GOAL: Check exact keys FLPC uses for entities vs what ServiceProcessor expects
REASON: Range indicators detected by FLPC but ServiceProcessor gets empty list
PROBLEM: Likely key mismatch between FLPC output and ServiceProcessor lookup
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_flpc_keys():
    """Debug exact FLPC entity keys vs ServiceProcessor expectations"""
    print("🔍 DEBUGGING FLPC ENTITY KEYS")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    test_text = "Height 30-37 inches between 50 and 75 pounds"
    
    print(f"📋 TEST TEXT: '{test_text}'")
    print("-" * 40)
    
    # Get FLPC results
    flpc_results = flpc_engine.extract_entities(test_text, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    
    print("🔍 ALL FLPC ENTITY KEYS:")
    print("-" * 30)
    
    for key, value in flpc_entities.items():
        print(f"  '{key}': {len(value)} entities")
        if len(value) > 0:
            print(f"    Content: {value}")
    
    # Check specific keys that ServiceProcessor looks for
    print(f"\n🎯 SERVICE PROCESSOR KEY LOOKUP:")
    print("-" * 30)
    
    sp_keys_to_check = [
        'RANGE_INDICATOR',
        'range_indicator', 
        'RANGE_INDICATORS',
        'range_indicators',
        'MEASUREMENT_RANGE_INDICATOR',
        'RANGE'
    ]
    
    for key in sp_keys_to_check:
        value = flpc_entities.get(key, [])
        print(f"  flpc_entities.get('{key}'): {value}")
    
    # Show what ServiceProcessor is specifically looking for
    print(f"\n📋 SERVICEPROCESSOR LOGIC:")
    print("-" * 30)
    print("ServiceProcessor calls:")
    print("  flpc_entities.get('RANGE_INDICATOR', [])")
    
    actual_value = flpc_entities.get('RANGE_INDICATOR', [])
    print(f"  Result: {actual_value}")
    print(f"  Length: {len(actual_value)}")
    
    if len(actual_value) == 0:
        print("  🔴 THIS IS WHY RANGE INDICATORS ARE EMPTY!")
        print("  ServiceProcessor is looking for wrong key name")
    else:
        print("  ✅ Key lookup should work")

if __name__ == "__main__":
    debug_flpc_keys()