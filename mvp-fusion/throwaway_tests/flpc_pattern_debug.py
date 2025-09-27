#!/usr/bin/env python3
"""
Debug FLPC pattern loading and test specific problematic cases
============================================================

GOAL: Verify FLPC engine is loading the updated measurement pattern correctly
REASON: Some measurements like "15 minutes" and "-20°F to 120°F" still not being extracted
PROBLEM: Need to confirm the pattern is being loaded and applied correctly
"""

import sys
sys.path.append('/home/corey/projects/docling/mvp-fusion')

from fusion.flpc_engine import FLPCEngine
import yaml
from pathlib import Path

def test_flpc_measurement_extraction():
    """Test FLPC engine directly with problematic measurement cases"""
    
    print("🔍 Testing FLPC Engine Measurement Pattern")
    print("=" * 60)
    
    # Load config like the pipeline does
    config_dir = Path("/home/corey/projects/docling/mvp-fusion/config")
    with open(config_dir / "config.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    print("🚀 Initializing FLPC Engine...")
    try:
        flpc_engine = FLPCEngine(config)
        print("✅ FLPC Engine initialized successfully")
    except Exception as e:
        print(f"❌ FLPC Engine initialization failed: {e}")
        return
    
    # Check if measurement pattern is loaded
    if 'universal_entities' in flpc_engine.raw_patterns:
        measurement_pattern = flpc_engine.raw_patterns['universal_entities'].get('measurement', {})
        print(f"\n📋 Loaded measurement pattern:")
        print(f"   Pattern: {measurement_pattern.get('pattern', 'NOT FOUND')}")
        print(f"   Description: {measurement_pattern.get('description', 'NOT FOUND')}")
    else:
        print("❌ No universal_entities patterns found")
        return
    
    # Test problematic cases
    test_cases = [
        "15 minutes maximum",
        "90 decibels for 8 hours", 
        "-20°F to 120°F",
        "-29°C to 49°C",
        "22 inches",
        "30-37 inches",
        "500 feet"
    ]
    
    print(f"\n🧪 Testing Extraction Results:")
    print("-" * 60)
    
    for test_text in test_cases:
        print(f"\nTesting: '{test_text}'")
        try:
            # Extract entities using FLPC engine
            results = flpc_engine.extract_entities(test_text)
            
            if results:
                print(f"   ✅ Extracted: {results}")
            else:
                print(f"   ❌ No entities extracted")
                
        except Exception as e:
            print(f"   ❌ Error during extraction: {e}")
    
    # Get FLPC engine metrics
    print(f"\n📊 FLPC Engine Metrics:")
    print(f"   Chars processed: {flpc_engine.metrics['chars_processed']:,}")
    print(f"   Processing time: {flpc_engine.metrics['processing_time']:.3f}s")
    print(f"   Patterns executed: {flpc_engine.metrics['patterns_executed']}")
    print(f"   Entities extracted: {flpc_engine.metrics['entities_extracted']}")

def test_direct_pattern_matching():
    """Test the pattern directly with regex to isolate the issue"""
    
    print(f"\n\n🧪 Direct Pattern Testing")
    print("=" * 60)
    
    # Load the actual pattern from config
    config_file = Path("/home/corey/projects/docling/mvp-fusion/config/pattern_sets.yaml")
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    measurement_pattern = config['flpc_regex_patterns']['universal_entities']['measurement']['pattern']
    print(f"Pattern from config: {measurement_pattern}")
    
    import re
    pattern = re.compile(measurement_pattern)
    
    test_cases = [
        "15 minutes maximum",
        "90 decibels", 
        "-20°F to 120°F",
        "-29°C to 49°C",
        "22 inches",
        "30-37 inches"
    ]
    
    print(f"\n🔍 Direct Regex Results:")
    for test_text in test_cases:
        matches = pattern.findall(test_text)
        if matches:
            print(f"   ✅ '{test_text}' -> {matches}")
        else:
            print(f"   ❌ '{test_text}' -> NO MATCH")

if __name__ == "__main__":
    test_flpc_measurement_extraction()
    test_direct_pattern_matching()