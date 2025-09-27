#!/usr/bin/env python3
"""
GOAL: Test that measurements preserve original units in tags
REASON: Verify "37 inches" appears as ||37 inches||meas074|| not ||0.9398||meas074||
PROBLEM: Need to confirm preserve-original architecture works end-to-end
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_preserve_original_units():
    """Test that original units are preserved in final tagging"""
    print("🧪 TESTING PRESERVE-ORIGINAL UNITS IN TAGS")
    print("=" * 55)
    
    # Test cases that should preserve original units
    test_cases = [
        ("**37 inches**", "37 inches", "Should preserve inches not convert to meters"),
        ("Height: 6 feet", "6 feet", "Should preserve feet not convert to meters"), 
        ("Weight: 150 pounds", "150 pounds", "Should preserve pounds not convert to kg"),
        ("Temperature: 72°F", "72°F", "Should preserve Fahrenheit not convert to Celsius"),
        ("Growth: 15%", "15%", "Should preserve percentage as-is"),
        ("Distance: 5 kilometers", "5 kilometers", "Should preserve kilometers as-is"),
    ]
    
    print(f"📄 TEST CASES:")
    for i, (text, expected, description) in enumerate(test_cases, 1):
        print(f"   {i}. {text} - {description}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING PRESERVE-ORIGINAL ARCHITECTURE:")
        print("-" * 50)
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, (test_text, expected_in_tag, description) in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {test_text}")
            print(f"    Expected in tag: '{expected_in_tag}'")
            
            # Extract entities
            entities = processor._extract_universal_entities(test_text)
            measurements = entities.get('measurement', [])
            
            print(f"    Measurements detected: {len(measurements)}")
            
            found_preserved = False
            for measurement in measurements:
                text = measurement.get('text', 'N/A')
                span = measurement.get('span', {})
                range_info = measurement.get('range_indicator', {})
                
                print(f"      Found measurement: '{text}'")
                
                # Check if original units are preserved
                if expected_in_tag.lower() in text.lower():
                    found_preserved = True
                    print(f"      ✅ SUCCESS: Original units preserved")
                    success_count += 1
                    break
                else:
                    print(f"      ❌ ISSUE: Expected '{expected_in_tag}' in measurement")
            
            if not found_preserved and measurements:
                print(f"      🔴 FAILED: Original units not preserved")
            elif not measurements:
                print(f"      🔴 FAILED: No measurements detected")
        
        # Now test the full pipeline with text replacement
        print(f"\n🎯 TESTING FULL PIPELINE WITH TEXT REPLACEMENT:")
        print("-" * 50)
        
        test_document = """
# Test Document

## Measurements Section
- Handrail height **30-37 inches** (76-94 cm)
- Weight capacity: 150 pounds
- Temperature range: 68-72°F
- Success rate: 85%
- Distance: 2.5 kilometers
        """.strip()
        
        print(f"Processing test document...")
        
        # Process through complete pipeline
        result = processor.process_document(test_document)
        
        # Check if tagged content preserves original units
        tagged_content = result.get('tagged_content', '')
        
        print(f"\n📋 TAGGED CONTENT ANALYSIS:")
        print("-" * 30)
        
        # Look for measurement tags
        import re
        tag_pattern = r'\|\|([^|]+)\|\|(meas\d+)\|\|'
        tag_matches = list(re.finditer(tag_pattern, tagged_content))
        
        print(f"Measurement tags found: {len(tag_matches)}")
        
        preserved_count = 0
        converted_count = 0
        
        for match in tag_matches:
            tag_content = match.group(1)
            tag_id = match.group(2)
            
            print(f"  Tag: ||{tag_content}||{tag_id}||")
            
            # Check if this preserves original units
            if any(unit in tag_content.lower() for unit in ['inches', 'feet', 'pounds', '%', 'kilometers', '°f']):
                preserved_count += 1
                print(f"    ✅ PRESERVED: Original units maintained")
            elif any(indicator in tag_content.lower() for indicator in ['meters', 'kg', '°c', 'celsius']):
                converted_count += 1
                print(f"    ❌ CONVERTED: Units were converted (harmful)")
            else:
                print(f"    ❓ UNCLEAR: Could not determine unit preservation")
        
        # Summary
        print(f"\n📊 PRESERVE-ORIGINAL SUMMARY:")
        print("-" * 40)
        print(f"Individual detection tests: {success_count}/{total_tests} passed")
        print(f"Tag preservation: {preserved_count} preserved, {converted_count} converted")
        
        if success_count == total_tests and converted_count == 0:
            print(f"🟢 **SUCCESS**: 100% preserve-original architecture working!")
        elif success_count >= total_tests * 0.8 and converted_count == 0:
            print(f"🟡 **GOOD**: Most measurements preserved correctly")
        else:
            print(f"🔴 **NEEDS WORK**: Still converting units in tags (harmful)")
        
        # Show sample of tagged content
        print(f"\n📄 SAMPLE TAGGED CONTENT:")
        print("-" * 30)
        print(tagged_content[:500] + "..." if len(tagged_content) > 500 else tagged_content)
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_preserve_original_units()