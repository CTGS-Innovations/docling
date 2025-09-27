#!/usr/bin/env python3
"""
GOAL: Test range detection methods without full pipeline dependencies
REASON: Avoid import errors while testing core range logic
PROBLEM: ServiceProcessor has dependencies that prevent standalone testing

Direct test of range detection logic extracted from implementation
"""

def _fallback_range_detection(text: str):
    """
    Fallback range detection using simple string analysis.
    Copied from service_processor.py implementation
    """
    range_entities = []
    
    # Look for measurement ranges like "30-37 inches", "76-94 cm"
    measurement_units = ['inches', 'inch', 'cm', 'mm', 'meters', 'metres', 'feet', 'ft', 'yards', 'miles']
    
    # Split text into words for analysis
    words = text.split()
    print(f"Debug: Words = {words}")
    
    for i in range(len(words) - 1):  # Need at least 2 words: number-number unit
        word1 = words[i]
        word2 = words[i + 1] if i + 1 < len(words) else ""
        
        # Clean word1 and word2 of punctuation 
        word1_clean = word1.strip('().,;:!?')
        word2_clean = word2.strip('().,;:!?').lower()
        
        # Check for pattern: number-number unit (including within parentheses)
        if '-' in word1_clean and word2_clean in measurement_units:
            # Try to extract numbers from word1_clean
            parts = word1_clean.split('-')
            if len(parts) == 2:
                try:
                    start_num = float(parts[0])
                    end_num = float(parts[1])
                    
                    # Create range entity  
                    full_text = f"{word1_clean} {word2_clean}"
                    
                    # Find position in original text (approximate)
                    start_pos = text.find(full_text)
                    if start_pos >= 0:
                        range_entity = {
                            'value': full_text,
                            'text': full_text,
                            'type': 'measurement_range',
                            'span': {
                                'start': start_pos,
                                'end': start_pos + len(full_text)
                            },
                            'range_components': {
                                'start_value': str(start_num),
                                'end_value': str(end_num),
                                'unit': word2_clean
                            },
                            'confidence': 'medium',
                            'detection_method': 'fallback_string_analysis'
                        }
                        range_entities.append(range_entity)
                
                except ValueError:
                    # Not valid numbers, skip
                    continue
    
    return range_entities

def test_range_detection():
    """Test the range detection methods directly"""
    print("🟡 **WAITING**: Testing range detection logic...")
    
    # Test the primary case from WIP.md
    test_text = "Handrail height 30-37 inches (76-94 cm) installed January 1, 2024 for $1,500"
    
    print(f"Test text: {test_text}")
    print()
    
    # Test the range detection method directly
    ranges = _fallback_range_detection(test_text)
    
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
    print("🟢 **SUCCESS**: Starting isolated range method test")
    print("=" * 60)
    
    # Test range detection
    ranges = test_range_detection()
    print()
    
    # Validate success criteria
    success = validate_success_criteria(ranges)
    print()
    
    # Final result
    if success:
        print("🟢 **SUCCESS**: Range detection logic working!")
        print("✅ Implementation meets WIP.md criteria")
    else:
        print("🔴 **BLOCKED**: Range detection logic needs adjustment")

if __name__ == "__main__":
    main()