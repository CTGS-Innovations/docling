#!/usr/bin/env python3
"""
Range Pattern Debug Test
========================

GOAL: Debug why FLPC range pattern isn't matching "10-15%" and "-20°F to 120°F"
REASON: User found broken range detection in production output
PROBLEM: Range pattern has highest priority but individual measurements winning

Expected:
- "10-15%" → RANGE entity (not individual measurements)
- "-20°F to 120°F" → RANGE entity (not separate measurements)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fusion.flpc_engine import FLPCEngine
import yaml
from pathlib import Path

def test_range_detection():
    """Test range pattern detection vs individual measurements"""
    print("🔍 RANGE PATTERN DEBUG TEST")
    print("=" * 50)
    print("Testing why range detection is failing")
    print()
    
    # Load FLPC engine
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    flpc_engine = FLPCEngine(config)
    
    # Test the exact failing cases
    test_cases = [
        "Growth projection: 10-15% range",
        "Temperature range -20°F to 120°F",
        "Temperature range (-29°C to 49°C)",
        "10-15%",
        "-20°F to 120°F",
        "30-37 inches",
        "between 10% and 15%",
        "from 20°F to 120°F"
    ]
    
    print("📊 RANGE VS INDIVIDUAL DETECTION:")
    print("-" * 40)
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i}: \"{text}\"")
        
        try:
            results = flpc_engine.extract_entities(text)
            entities = results.get('entities', {})
            
            ranges = entities.get('RANGE', [])
            measurements = entities.get('MEASUREMENT', [])
            percents = entities.get('PERCENT', [])
            
            print(f"  🎯 RANGE entities: {len(ranges)}")
            for r in ranges:
                print(f"    - \"{r}\"")
                
            print(f"  📏 MEASUREMENT entities: {len(measurements)}")
            for m in measurements:
                print(f"    - \"{m}\"")
                
            print(f"  📊 PERCENT entities: {len(percents)}")
            for p in percents:
                print(f"    - \"{p}\"")
            
            # Analyze the issue
            if ranges and not (measurements or percents):
                print(f"  ✅ CORRECT: Range detected properly")
            elif (measurements or percents) and not ranges:
                print(f"  ❌ BROKEN: Individual entities instead of range")
            elif ranges and (measurements or percents):
                print(f"  ⚠️  CONFLICT: Both range and individual entities detected")
            else:
                print(f"  ❓ UNCLEAR: No entities detected")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            
        print()
    
    print("🔧 PATTERN PRIORITY ANALYSIS:")
    print("-" * 30)
    print("Range pattern priority: highest")
    print("Measurement pattern priority: high") 
    print("Percent pattern priority: medium")
    print()
    print("🎯 EXPECTED BEHAVIOR:")
    print("Range pattern should match FIRST due to highest priority")
    print("Individual patterns should NOT match if range already matched")

if __name__ == "__main__":
    print("# GOAL: Debug range pattern vs individual measurement conflicts")
    print("# REASON: Production showing broken ranges like '10-||15%||'")
    print("# PROBLEM: Need to understand pattern precedence and matching")
    print()
    
    test_range_detection()
    
    print("\n🔧 Next step: Fix pattern precedence to ensure ranges match first")