#!/usr/bin/env python3
"""
FLPC Pattern Compilation Test
=============================

GOAL: Check if FLPC is properly compiling and using the RANGE pattern
REASON: Regex works fine but FLPC returns 0 range entities
PROBLEM: Pattern compilation, loading, or execution issue in FLPC

Debug Steps:
1. Check pattern loading from config
2. Check pattern compilation 
3. Check pattern execution order
4. Check pattern selection logic
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fusion.flpc_engine import FLPCEngine
import yaml
from pathlib import Path

def test_flpc_compilation():
    """Test FLPC pattern compilation and execution"""
    print("🔍 FLPC PATTERN COMPILATION TEST")
    print("=" * 50)
    print("Testing FLPC pattern loading and compilation")
    print()
    
    # Load config and create engine
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("📊 STEP 1: FLPC Engine Initialization")
    print("-" * 30)
    try:
        flpc_engine = FLPCEngine(config)
        print("✅ FLPC engine created successfully")
    except Exception as e:
        print(f"❌ FLPC engine creation failed: {e}")
        return
    
    print(f"✅ Pattern sets loaded: {list(flpc_engine.pattern_sets.keys())}")
    
    # Check pattern availability
    print("\n📊 STEP 2: Pattern Availability Check")
    print("-" * 30)
    available_patterns = flpc_engine.get_available_patterns()
    for category, patterns in available_patterns.items():
        print(f"📋 {category}: {patterns}")
        
    # Check if RANGE pattern exists
    universal_patterns = flpc_engine.pattern_sets.get('universal_entities', {})
    if 'range' in universal_patterns:
        print("✅ RANGE pattern found in universal_entities")
        range_info = universal_patterns['range']
        print(f"  - Compiled: {hasattr(range_info.get('compiled'), '__call__') if range_info.get('compiled') else 'No'}")
        print(f"  - Description: {range_info.get('description', 'None')}")
        print(f"  - Priority: {range_info.get('priority', 'None')}")
    else:
        print("❌ RANGE pattern NOT found in universal_entities")
        print(f"Available patterns: {list(universal_patterns.keys())}")
    
    # Test pattern selection
    print("\n📊 STEP 3: Pattern Selection Test")
    print("-" * 30)
    
    # Test default pattern set
    default_patterns = flpc_engine._select_patterns("default")
    print(f"Default pattern set: {list(default_patterns.keys())}")
    
    # Test complete pattern set  
    complete_patterns = flpc_engine._select_patterns("complete")
    print(f"Complete pattern set: {list(complete_patterns.keys())}")
    
    # Test extraction with range text
    print("\n📊 STEP 4: Range Extraction Test")
    print("-" * 30)
    
    test_text = "Temperature range -20°F to 120°F and growth 10-15%"
    print(f"Test text: \"{test_text}\"")
    
    try:
        results = flpc_engine.extract_entities(test_text, "complete")
        print(f"✅ Extraction successful")
        print(f"📊 Results: {results.get('entities', {})}")
        
        # Check which patterns were executed
        metadata = results.get('metadata', {})
        print(f"📋 Patterns executed: {metadata.get('patterns_executed', 'Unknown')}")
        print(f"📋 Processing time: {metadata.get('processing_time_ms', 'Unknown')}ms")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
    
    print("\n🎯 DIAGNOSIS:")
    print("-" * 15)
    if 'range' not in universal_patterns:
        print("❌ CRITICAL: RANGE pattern missing from pattern compilation")
    elif 'range' not in complete_patterns:
        print("❌ CRITICAL: RANGE pattern excluded from pattern selection")
    else:
        print("✅ RANGE pattern properly loaded and selected")
        print("🔧 Issue likely in pattern execution or precedence")

if __name__ == "__main__":
    print("# GOAL: Debug FLPC pattern compilation and execution")
    print("# REASON: Regex works but FLPC returns 0 range entities")
    print("# PROBLEM: Pattern loading, compilation, or execution issue")
    print()
    
    test_flpc_compilation()
    
    print("\n🔧 Next: Fix FLPC pattern issue based on diagnosis")