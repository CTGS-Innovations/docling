#!/usr/bin/env python3
"""
GOAL: Test post-processing range normalization implementation
REASON: Validate that 30-37 inches and 76-94 cm are detected as ranges
PROBLEM: Need to verify WIP.md success criteria are met

Test the exact implementation added to service_processor.py
"""

import sys
sys.path.append('/home/corey/projects/docling/mvp-fusion')

from pipeline.legacy.service_processor import ServiceProcessor
import yaml

def test_range_detection():
    """Test the range detection methods directly"""
    print("🟡 **WAITING**: Testing range detection implementation...")
    
    # Create ServiceProcessor instance
    config_path = '/home/corey/projects/docling/mvp-fusion/config/pattern_sets.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize processor (minimal setup)
    processor = ServiceProcessor(config)
    
    # Test the primary case from WIP.md
    test_text = "Handrail height 30-37 inches (76-94 cm) installed January 1, 2024 for $1,500"
    
    print(f"Test text: {test_text}")
    print()
    
    # Test the range detection method directly
    ranges = processor._detect_ranges_from_text(test_text)
    
    print(f"📊 Range detection results:")
    print(f"  Total ranges found: {len(ranges)}")
    
    for i, range_entity in enumerate(ranges, 1):
        print(f"  Range {i}:")
        print(f"    - Text: {range_entity['text']}")
        print(f"    - Type: {range_entity['type']}")
        print(f"    - Method: {range_entity['detection_method']}")
        print(f"    - Confidence: {range_entity['confidence']}")
        if 'range_components' in range_entity:
            components = range_entity['range_components']
            print(f"    - Components: {components['start_value']}-{components['end_value']} {components.get('unit', '')}")
    
    return ranges

def validate_success_criteria(ranges):
    """Validate against WIP.md success criteria"""
    print("🟡 **WAITING**: Validating against WIP.md success criteria...")
    
    # Success criteria from WIP.md:
    # - Both "30-37 inches" AND "76-94 cm" detected as range entities
    # - Expected: 2 range entities detected
    
    found_inches = False
    found_cm = False
    
    for range_entity in ranges:
        text = range_entity['text'].lower()
        if '30-37' in text and 'inches' in text:
            found_inches = True
            print("  ✅ Found 30-37 inches range")
        elif '76-94' in text and 'cm' in text:
            found_cm = True
            print("  ✅ Found 76-94 cm range")
    
    print(f"📊 **SUCCESS CRITERIA VALIDATION**:")
    print(f"  - 30-37 inches detected: {'✅ YES' if found_inches else '❌ NO'}")
    print(f"  - 76-94 cm detected: {'✅ YES' if found_cm else '❌ NO'}")
    print(f"  - Total ranges found: {len(ranges)} (expected: 2)")
    
    success = found_inches and found_cm and len(ranges) == 2
    return success

def main():
    """Main test function"""
    print("🟢 **SUCCESS**: Starting range implementation test")
    print("=" * 60)
    
    # Test range detection
    ranges = test_range_detection()
    print()
    
    # Validate success criteria
    success = validate_success_criteria(ranges)
    print()
    
    # Final result
    if success:
        print("🟢 **SUCCESS**: Range post-processing implementation working!")
        print("✅ Ready for full pipeline testing")
    else:
        print("🔴 **BLOCKED**: Range detection not meeting WIP.md criteria")
        print("❌ Implementation needs adjustment")

if __name__ == "__main__":
    main()