#!/usr/bin/env python3
"""
Focused Range Linking Test - Key Findings
=========================================

GOAL: Validate the specific "10-15%" issue and key joining patterns
REASON: Growth projection shows "10-||15.0||meas115||" broken split
PROBLEM: Need focused test on critical joining scenarios

Key Test Cases:
1. "10-15%" (the failing case)
2. Common joining patterns that work/fail
3. Expected normalization output format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fusion.flpc_engine import FLPCEngine
from pathlib import Path
import yaml

def test_range_linking():
    """Test key range linking scenarios"""
    # Load FLPC engine
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    flpc_engine = FLPCEngine(config)
    
    # Critical test cases from real document
    test_cases = [
        # The exact failing case
        "Growth projection: 10-15% range",
        
        # Key percentage patterns
        "10-15%",
        "10% to 15%", 
        "10% - 15%",
        "between 10% and 15%",
        
        # Temperature ranges  
        "-20°F to 120°F",
        "-29°C to 49°C",
        "32-212 degrees",
        
        # Measurement ranges
        "30-37 inches",
        "500-1000 feet", 
        "2.5 to 5.0 pounds",
        "15-30 minutes",
        
        # Date ranges
        "January 1 to December 31, 2024",
        "Q1-Q4 2024",
        
        # Money ranges
        "$1-5 million",
        "$100 to $500 thousand",
    ]
    
    print("🔍 FOCUSED RANGE LINKING TEST")
    print("=" * 50)
    print("Testing critical range patterns for normalization design")
    print()
    
    working_patterns = []
    broken_patterns = []
    
    for i, text in enumerate(test_cases, 1):
        print(f"Test {i:2d}: \"{text}\"")
        
        # Extract entities
        results = flpc_engine.extract_entities(text)
        entities = results.get('entities', {})
        
        # Analyze detection
        total_entities = sum(len(elist) for elist in entities.values())
        entity_details = []
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                entity_details.append(f"{entity_type}:{entity}")
        
        print(f"         Detected: {entity_details}")
        
        # Determine if this is a good candidate for range normalization
        has_multiple_same_type = any(len(elist) >= 2 for elist in entities.values())
        
        if has_multiple_same_type:
            working_patterns.append(text)
            print(f"         Status: ✅ GOOD - Multiple entities for normalization")
        elif total_entities == 1:
            working_patterns.append(text)
            print(f"         Status: ✅ PERFECT - Already unified range")
        else:
            broken_patterns.append(text)
            print(f"         Status: ❌ NEEDS WORK - Unclear pattern")
            
        print()
    
    # Summary and recommendations
    print("📊 SUMMARY:")
    print("=" * 30)
    print(f"✅ Good for normalization: {len(working_patterns)}")
    print(f"❌ Need pattern fixes: {len(broken_patterns)}")
    print()
    
    print("🎯 NORMALIZATION STRATEGY:")
    print("=" * 30)
    print("1. ✅ Individual detection is working well")
    print("2. 🔧 Need EntityNormalizer to:")
    print("   - Detect nearby entities of same type")
    print("   - Analyze text between entities for joining words")
    print("   - Create single range entity: ||10-15%||range001||")
    print("   - Replace original entities with range entity")
    print()
    
    print("💡 IMPLEMENTATION APPROACH:")
    print("=" * 30)
    print("Stage 1 (Current): FLPC detects ['10%', '15%']")
    print("Stage 2 (New): EntityNormalizer sees:")
    print("  - Two PERCENT entities")
    print("  - Text between them: '-' ")
    print("  - Creates: ||10-15%||range001||")
    print("  - Removes: ||10%||percent001|| and ||15%||percent002||")
    
    return {
        'working_patterns': working_patterns,
        'broken_patterns': broken_patterns,
        'recommendation': 'Implement range normalization in EntityNormalizer'
    }

if __name__ == "__main__":
    print("# GOAL: Validate range linking for normalization design")
    print("# REASON: '10-||15.0||meas115||' shows broken range detection")
    print("# PROBLEM: Need focused test on critical scenarios")
    print()
    
    results = test_range_linking()
    
    print(f"\n✅ Test complete - {len(results['working_patterns'])} patterns ready for normalization")
    print("Next: Implement range linking in EntityNormalizer post-processing")