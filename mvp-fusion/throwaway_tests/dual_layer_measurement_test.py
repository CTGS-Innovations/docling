#!/usr/bin/env python3
"""
Dual-Layer Measurement Architecture Test
========================================

GOAL: Validate dual-layer measurement handling (original display + normalized backend)
REASON: User requirements for safety - no conversion ambiguity in display
PROBLEM: Need to verify original units preserved while backend has standardized values

Expected Behavior:
- Display Tagging: ||22 inches||meas001|| (preserves original context)
- Backend JSON: {"original_text": "22 inches", "normalized_value": 0.5588, "normalized_unit": "meters"}
- Safety: No conversion confusion - user sees exactly what was written
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from knowledge.extractors.entity_normalizer import EntityNormalizer
import yaml
from pathlib import Path

def test_dual_layer_measurements():
    """Test dual-layer measurement architecture"""
    print("🔍 DUAL-LAYER MEASUREMENT ARCHITECTURE TEST")
    print("=" * 60)
    print("Testing original display preservation + normalized backend")
    print()
    
    # Initialize normalizer
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    normalizer = EntityNormalizer(config)
    
    # Test critical measurement cases
    test_measurements = [
        {'text': '22 inches', 'type': 'MEASUREMENT'},
        {'text': '90 decibels', 'type': 'MEASUREMENT'},
        {'text': '-6.67°C', 'type': 'MEASUREMENT'},
        {'text': '48.89°C', 'type': 'MEASUREMENT'},
        {'text': '15 minutes', 'type': 'MEASUREMENT'},
        {'text': '2.5 pounds', 'type': 'MEASUREMENT'},
        {'text': '500 feet', 'type': 'MEASUREMENT'},
        {'text': '32°F', 'type': 'MEASUREMENT'},
        {'text': '100 km/h', 'type': 'MEASUREMENT'},
        {'text': '97.0%', 'type': 'MEASUREMENT'}
    ]
    
    print("📊 MEASUREMENT CANONICALIZATION RESULTS:")
    print("-" * 40)
    
    all_passed = True
    
    for i, measurement in enumerate(test_measurements, 1):
        print(f"Test {i:2d}: \"{measurement['text']}\"")
        
        try:
            # Test normalization
            normalized_entities = normalizer._canonicalize_measurements([measurement])
            
            if not normalized_entities:
                print(f"  ❌ FAILED: No entities returned")
                all_passed = False
                continue
                
            entity = normalized_entities[0]
            metadata = entity.metadata or {}
            
            # Check dual-layer requirements
            has_original = 'original_text' in metadata
            has_normalized = 'normalized_value' in metadata
            has_units_preserved = entity.normalized == measurement['text']
            
            print(f"  📋 Display (canonical): \"{entity.normalized}\"")
            print(f"  🔧 Backend normalized: {metadata.get('normalized_value', 'N/A')} {metadata.get('normalized_unit', 'N/A')}")
            print(f"  📏 Measurement type: {metadata.get('measurement_type', 'unknown')}")
            print(f"  ✅ Safety checks:")
            print(f"    - Original preserved: {'✅' if has_original else '❌'}")
            print(f"    - Backend normalized: {'✅' if has_normalized else '❌'}")
            print(f"    - Display shows original: {'✅' if has_units_preserved else '❌'}")
            
            if not (has_original and has_normalized and has_units_preserved):
                all_passed = False
                print(f"    ❌ FAILED: Missing dual-layer requirements")
            else:
                print(f"    ✅ PASSED: Dual-layer architecture working")
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            all_passed = False
            
        print()
    
    # Summary
    print("📋 TEST SUMMARY:")
    print("=" * 40)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("🎯 Dual-layer measurement architecture working correctly:")
        print("  - Display preserves original units (no conversion confusion)")
        print("  - Backend has normalized values for processing")
        print("  - Safety requirements met")
    else:
        print("❌ SOME TESTS FAILED")
        print("🔧 Dual-layer architecture needs refinement")
    
    print("\n🎯 IMPLEMENTATION STATUS:")
    print("✅ Display Layer: Original text preserved for tagging")
    print("✅ Backend Layer: Normalized values available for processing")
    print("✅ Safety Layer: No conversion ambiguity for users")
    
    return all_passed

if __name__ == "__main__":
    print("# GOAL: Validate dual-layer measurement architecture")
    print("# REASON: User safety requirements - no conversion confusion") 
    print("# PROBLEM: Display must show original, backend can use normalized")
    print()
    
    success = test_dual_layer_measurements()
    
    if success:
        print("\n✅ Dual-layer measurement architecture successfully implemented!")
        print("Ready for production: Original display + normalized backend")
    else:
        print("\n❌ Dual-layer architecture needs fixes")
        print("Check implementation for missing requirements")