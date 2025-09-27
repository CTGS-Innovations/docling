#!/usr/bin/env python3
"""
GOAL: Test exact text from file to find where range indicators are lost
REASON: FLPC detects range indicators but final output shows empty array
PROBLEM: Range indicators lost between FLPC detection and pipeline output
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_exact_file_text():
    """Test the exact text from our test file with FLPC"""
    print("🔍 TESTING EXACT FILE TEXT WITH FLPC")
    print("=" * 50)
    
    # Read exact text from test file
    with open('/home/corey/projects/docling/mvp-fusion/throwaway_tests/range_test_input.txt', 'r') as f:
        file_text = f.read()
    
    print("📋 FILE TEXT:")
    print("-" * 20)
    print(repr(file_text))  # Show exact content with escapes
    print()
    print(file_text)
    print()
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    print("🔄 FLPC DETECTION ON EXACT FILE TEXT:")
    print("-" * 40)
    
    # Test with FLPC using exact file text
    flpc_results = flpc_engine.extract_entities(file_text, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    
    # Show range indicators
    range_indicators = flpc_entities.get('RANGE_INDICATOR', [])
    print(f"RANGE_INDICATOR count: {len(range_indicators)}")
    if range_indicators:
        print(f"✅ RANGE_INDICATOR detected: {range_indicators}")
        for i, indicator in enumerate(range_indicators, 1):
            print(f"   {i}. '{indicator}'")
    else:
        print(f"❌ No range indicators detected from file text")
    
    print()
    
    # Show measurements for comparison
    measurement_types = ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']
    measurement_total = 0
    for mtype in measurement_types:
        entities = flpc_entities.get(mtype, [])
        if entities:
            measurement_total += len(entities)
            print(f"✅ {mtype}: {len(entities)} entities")
            for i, entity in enumerate(entities[:3], 1):  # Show first 3
                print(f"   {i}. '{entity}'")
    
    print(f"\n📊 SUMMARY:")
    print(f"Range indicators: {len(range_indicators)}")
    print(f"Measurements: {measurement_total}")
    
    # Check for line ending issues
    print(f"\n🔍 TEXT ANALYSIS:")
    print(f"Text length: {len(file_text)} chars")
    print(f"Line endings: {repr(file_text.splitlines())}")
    
    # Look for specific range patterns manually
    print(f"\n🎯 MANUAL RANGE SEARCH:")
    if '-' in file_text:
        print(f"✅ Contains hyphen '-'")
    if 'to' in file_text:
        print(f"✅ Contains 'to'")
    if 'between' in file_text:
        print(f"✅ Contains 'between'")
    if 'through' in file_text:
        print(f"✅ Contains 'through'")
    if 'and' in file_text:
        print(f"✅ Contains 'and'")

if __name__ == "__main__":
    test_exact_file_text()