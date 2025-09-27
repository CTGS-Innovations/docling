#!/usr/bin/env python3
"""
GOAL: Test range-aware measurement patterns
REASON: Verify "30-37 inches" and "-20°F to 120°F" are detected as complete ranges
PROBLEM: Need to confirm new range patterns work correctly
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_range_patterns():
    """Test the range-aware measurement patterns"""
    print("🧪 TESTING RANGE-AWARE MEASUREMENT PATTERNS")
    print("=" * 55)
    
    # Test cases with ranges
    test_cases = [
        ("Handrail height **30-37 inches** (76-94 cm)", "30-37 inches", "Range length measurement"),
        ("Temperature range **-20°F to 120°F** (-29°C to 49°C)", "-20°F to 120°F", "Range temperature measurement"),
        ("Single measurement **42 inches** (107 cm)", "42 inches", "Single length measurement"),
        ("Single temperature **72°F** (22°C)", "72°F", "Single temperature measurement"),
    ]
    
    print(f"📄 TEST CASES:")
    for i, (text, expected, description) in enumerate(test_cases, 1):
        print(f"   {i}. {text}")
        print(f"      Expected: '{expected}' - {description}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING RANGE PATTERN DETECTION:")
        print("-" * 50)
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, (test_text, expected_measurement, description) in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {description}")
            print(f"    Text: '{test_text}'")
            print(f"    Expected: '{expected_measurement}'")
            
            # Test FLPC extraction directly
            if processor.flpc_engine:
                flpc_results = processor.flpc_engine.extract_entities(test_text, 'complete')
                flpc_entities = flpc_results.get('entities', {})
                
                # Check all measurement types
                all_measurements = []
                for measurement_type in ['MEASUREMENT_LENGTH', 'MEASUREMENT_LENGTH_RANGE', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_TEMPERATURE_RANGE']:
                    matches = flpc_entities.get(measurement_type, [])
                    for match in matches:
                        all_measurements.append((match, measurement_type))
                
                print(f"    FLPC Results: {len(all_measurements)} measurements")
                for match, mtype in all_measurements:
                    print(f"      - '{match}' ({mtype})")
                
                # Check if expected measurement found
                found_expected = False
                for match, mtype in all_measurements:
                    if expected_measurement.lower() in match.lower() or match.lower() in expected_measurement.lower():
                        found_expected = True
                        print(f"    ✅ SUCCESS: Found expected measurement '{match}'")
                        success_count += 1
                        break
                
                if not found_expected:
                    print(f"    ❌ FAILED: Expected '{expected_measurement}' not found")
            else:
                print(f"    🔴 ERROR: FLPC engine not available")
        
        # Summary
        print(f"\n📊 RANGE PATTERN SUMMARY:")
        print("-" * 40)
        print(f"Successful detections: {success_count}/{total_tests}")
        print(f"Success rate: {(success_count/total_tests*100):.1f}%")
        
        if success_count == total_tests:
            print(f"🟢 **SUCCESS**: All range patterns working correctly!")
        elif success_count >= total_tests * 0.7:
            print(f"🟡 **GOOD**: Most range patterns working")
        else:
            print(f"🔴 **NEEDS WORK**: Range patterns need improvement")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_range_patterns()