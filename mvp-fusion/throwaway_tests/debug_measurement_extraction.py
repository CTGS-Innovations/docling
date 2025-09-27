#!/usr/bin/env python3
"""
GOAL: Debug if FLPC is extracting measurements and why logging doesn't show MEASUREMENT count
REASON: Logs show DATE/MONEY/TIME but missing MEASUREMENT counts  
PROBLEM: Fix applied but logs still show old format without MEASUREMENT
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_flpc_measurement_extraction():
    """Test direct FLPC measurement extraction"""
    print("🔍 TESTING DIRECT FLPC MEASUREMENT EXTRACTION")
    print("=" * 50)
    
    try:
        # Load config
        with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Initialize FLPC engine
        from fusion.flpc_engine import FLPCEngine
        flpc_engine = FLPCEngine(config)
        print("✅ FLPC engine initialized")
        
        # Test text with measurements from 9.4 section
        test_text = """
Fall protection required above 6 feet (1.8 meters) in construction
Guardrails must be 42 inches (107 cm) high
Toe boards minimum 4 inches (10 cm) high
Safety nets within 30 feet (9.1 meters)
Handrail height 30-37 inches (76-94 cm)
Storage height limit 15 feet (4.6 meters)
"""
        
        print(f"📝 Test text length: {len(test_text)} characters")
        
        # Extract entities using FLPC
        flpc_results = flpc_engine.extract_entities(test_text)
        flpc_entities = flpc_results.get('entities', {})
        
        print("\n📊 FLPC RAW RESULTS:")
        for entity_type, entity_list in flpc_entities.items():
            print(f"   {entity_type}: {len(entity_list)} entities")
            if entity_list and len(entity_list) <= 10:  # Show up to 10 entities
                for i, entity in enumerate(entity_list[:10]):
                    print(f"      {i+1}. {entity}")
        
        # Test measurement extraction specifically
        measurements = flpc_entities.get('MEASUREMENT', [])
        print(f"\n🎯 MEASUREMENT ENTITIES: {len(measurements)}")
        for i, meas in enumerate(measurements[:20]):
            print(f"   {i+1:2d}. {meas}")
        
        print(f"\n✅ Test complete - FLPC found {len(measurements)} measurements")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_flpc_measurement_extraction()