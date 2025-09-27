#!/usr/bin/env python3
"""
GOAL: Debug if FLPC recognizes our new split measurement pattern names
REASON: Context7 research shows large alternations cause compilation issues - test our split approach
PROBLEM: FLPC may not recognize MEASUREMENT_LENGTH, MEASUREMENT_WEIGHT etc. vs single MEASUREMENT
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_flpc_pattern_recognition():
    """Test if FLPC recognizes our split measurement patterns"""
    print("🔍 TESTING FLPC PATTERN RECOGNITION")
    print("=" * 50)
    
    try:
        # Load config
        with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize FLPC engine
        from fusion.flpc_engine import FLPCEngine
        flpc_engine = FLPCEngine(config)
        print("✅ FLPC engine initialized")
        
        # Test text with various measurement types
        test_text = """
Length: 6 feet, 42 inches, 107 cm, 30 meters
Weight: 250 pounds, 113 kg, 5 oz
Time: 15 minutes, 2 hours, 30 seconds  
Temperature: 120°F, -20°C, 25 degrees
Sound: 90 decibels, 85 dB
"""
        
        print(f"📝 Test text length: {len(test_text)} characters")
        
        # Extract entities using FLPC
        flpc_results = flpc_engine.extract_entities(test_text, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        print(f"\n📊 FLPC RAW RESULTS ({len(flpc_entities)} entity types):")
        for entity_type, entity_list in flpc_entities.items():
            count = len(entity_list) if entity_list else 0
            print(f"   {entity_type}: {count} entities")
            if entity_list and count <= 10:  # Show entities for small lists
                for i, entity in enumerate(entity_list[:10]):
                    print(f"      {i+1}. {entity}")
        
        # Check specifically for our split measurement patterns
        measurement_types = [
            'MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 
            'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND', 'MEASUREMENT'
        ]
        
        print(f"\n🎯 MEASUREMENT PATTERN ANALYSIS:")
        total_measurements = 0
        for mtype in measurement_types:
            count = len(flpc_entities.get(mtype, []))
            total_measurements += count
            status = "✅" if count > 0 else "❌"
            print(f"   {status} {mtype}: {count} entities")
            
            if count > 0:
                entities = flpc_entities.get(mtype, [])[:5]  # Show first 5
                for i, entity in enumerate(entities):
                    print(f"      {i+1}. {entity}")
        
        print(f"\n📊 TOTAL MEASUREMENTS DETECTED: {total_measurements}")
        
        # Determine the issue
        if total_measurements == 0:
            print("\n🔴 ISSUE: No measurements detected at all")
            print("   - Pattern compilation may have failed")
            print("   - Pattern names may not match FLPC expectations")
        elif total_measurements < 10:
            print(f"\n🟡 ISSUE: Only {total_measurements} measurements detected (expected ~15)")
            print("   - Some patterns may not be working")
        else:
            print(f"\n🟢 SUCCESS: {total_measurements} measurements detected")
            print("   - Split pattern approach is working")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flpc_pattern_recognition()