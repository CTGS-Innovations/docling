#!/usr/bin/env python3
"""
GOAL: Test range deduplication in service processor
REASON: Verify "30-37 inches" is chosen over "37 inches" after deduplication
PROBLEM: Need to test complete service processor path with deduplication
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_range_deduplication():
    """Test the range deduplication logic in service processor"""
    print("🧪 TESTING RANGE DEDUPLICATION IN SERVICE PROCESSOR")
    print("=" * 60)
    
    # Test cases with ranges that should be deduplicated
    test_cases = [
        ("Handrail height **30-37 inches** (76-94 cm)", "30-37 inches", "Should prefer range over individual"),
        ("Temperature range **-20°F to 120°F** (-29°C to 49°C)", "-20°F to 120°F", "Should prefer complete range"),
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
        print(f"\n🔍 TESTING SERVICE PROCESSOR WITH DEDUPLICATION:")
        print("-" * 50)
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, (test_text, expected_measurement, description) in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {description}")
            print(f"    Text: '{test_text}'")
            print(f"    Expected: '{expected_measurement}'")
            
            # Use complete service processor extraction
            entities = processor._extract_universal_entities(test_text)
            measurements = entities.get('measurement', [])
            
            print(f"    Service Processor Results: {len(measurements)} measurements")
            for j, measurement in enumerate(measurements, 1):
                text = measurement.get('text', '')
                mtype = measurement.get('type', '')
                print(f"      {j}. '{text}' ({mtype})")
            
            # Check if expected range measurement found
            found_expected = False
            found_partial = False
            
            for measurement in measurements:
                text = measurement.get('text', '')
                
                # Check for exact or close match
                if expected_measurement.lower() in text.lower() or text.lower() in expected_measurement.lower():
                    # Check if it's the complete range or just partial
                    if len(text) >= len(expected_measurement) * 0.8:  # At least 80% of expected length
                        found_expected = True
                        print(f"    ✅ SUCCESS: Found complete range '{text}'")
                        success_count += 1
                        break
                    else:
                        found_partial = True
                        print(f"    🟡 PARTIAL: Found partial match '{text}'")
            
            if not found_expected:
                if found_partial:
                    print(f"    ❌ FAILED: Only found partial matches, not complete range")
                else:
                    print(f"    ❌ FAILED: Expected range '{expected_measurement}' not found")
        
        # Summary
        print(f"\n📊 RANGE DEDUPLICATION SUMMARY:")
        print("-" * 40)
        print(f"Successful range detections: {success_count}/{total_tests}")
        print(f"Success rate: {(success_count/total_tests*100):.1f}%")
        
        if success_count == total_tests:
            print(f"🟢 **SUCCESS**: Range deduplication working perfectly!")
        elif success_count >= total_tests * 0.5:
            print(f"🟡 **PARTIAL**: Some range deduplication working")
        else:
            print(f"🔴 **FAILED**: Range deduplication needs improvement")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_range_deduplication()