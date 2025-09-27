#!/usr/bin/env python3
"""
GOAL: Debug why "37 inches" is not detected in "**30-37 inches**"
REASON: Need to understand exact character analysis and pattern matching
PROBLEM: Expected FLPC to detect "37 inches" but it's not happening
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_37_inches_detection():
    """Debug character-by-character why 37 inches isn't detected"""
    print("🔍 DEBUGGING '37 inches' DETECTION IN '**30-37 inches**'")
    print("=" * 60)
    
    # Exact test case
    test_text = "**30-37 inches**"
    
    print(f"📄 TEST TEXT: '{test_text}'")
    print(f"   Length: {len(test_text)} characters")
    print(f"   Character breakdown:")
    for i, char in enumerate(test_text):
        print(f"   [{i:2d}] '{char}' (ord: {ord(char)})")
    
    # Find where "37 inches" should be
    target_start = test_text.find("37")
    target_end = test_text.find("inches") + len("inches")
    expected_text = test_text[target_start:target_end]
    
    print(f"\n🎯 EXPECTED DETECTION:")
    print(f"   Target: '37 inches'")
    print(f"   Found at: [{target_start}-{target_end}]") 
    print(f"   Actual text: '{expected_text}'")
    
    # Analyze pattern requirements
    print(f"\n🔍 PATTERN ANALYSIS:")
    print(f"   Pattern: (?i)(?:^|[^\\w])\\d+(?:\\.\\d+)?\\s*\\b(?:inches?)\\b")
    print(f"   Requirements:")
    print(f"   1. (?:^|[^\\w]) - Start of string OR non-word character before number")
    print(f"   2. \\d+ - One or more digits")
    print(f"   3. (?:\\.\\d+)? - Optional decimal part")
    print(f"   4. \\s* - Optional whitespace")
    print(f"   5. \\b(?:inches?)\\b - Word 'inch' or 'inches' with word boundaries")
    
    # Check character before "37"
    char_before_37 = test_text[target_start - 1] if target_start > 0 else "START"
    print(f"\n📝 CHARACTER ANALYSIS:")
    print(f"   Character before '37': '{char_before_37}' (ord: {ord(char_before_37) if char_before_37 != 'START' else 'N/A'})")
    print(f"   Is '{char_before_37}' a non-word character? {not char_before_37.isalnum() and char_before_37 != '_' if char_before_37 != 'START' else 'N/A'}")
    
    # Check if "-" qualifies as [^\w]
    hyphen_is_nonword = not '-'.isalnum() and '-' != '_'
    print(f"   Is '-' a non-word character? {hyphen_is_nonword}")
    
    # Initialize ServiceProcessor to test actual pattern
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🧪 TESTING ACTUAL FLPC PATTERN:")
        print("-" * 40)
        
        # Test with FLPC directly
        flpc_results = processor.flpc_engine.extract_entities(test_text, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        # Check all measurement types
        all_measurements = []
        for measurement_type in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
            measurements = flpc_entities.get(measurement_type, [])
            all_measurements.extend(measurements)
        
        print(f"   Raw FLPC measurements found: {len(all_measurements)}")
        
        for i, measurement in enumerate(all_measurements, 1):
            text = measurement.get('text', 'N/A')
            start = measurement.get('start', 0)
            end = measurement.get('end', 0)
            actual_text = test_text[start:end] if start < len(test_text) and end <= len(test_text) else "INVALID"
            
            print(f"   {i}. FLPC detected: '{text}' at [{start}-{end}] | Actual: '{actual_text}'")
        
        # Test different variations to isolate the issue
        print(f"\n🔬 TESTING PATTERN VARIATIONS:")
        print("-" * 40)
        
        test_variations = [
            "37 inches",          # Clean case
            " 37 inches",         # With space
            "-37 inches",         # With hyphen
            "0-37 inches",        # With preceding digit
            "30-37 inches",       # Full case
            "**37 inches**",      # With markdown
            "*30-37 inches*",     # Single asterisk
        ]
        
        for variation in test_variations:
            entities = processor._extract_universal_entities(variation)
            measurements = entities.get('measurement', [])
            
            print(f"   '{variation}' → {len(measurements)} measurements")
            for measurement in measurements:
                text = measurement.get('text', 'N/A')
                span = measurement.get('span', {})
                print(f"      - '{text}' [{span.get('start')}-{span.get('end')}]")
        
        # Manual regex test
        print(f"\n🔧 MANUAL REGEX TEST:")
        print("-" * 40)
        
        import re
        
        # Test our exact pattern
        pattern = r'(?i)(?:^|[^\w])\d+(?:\.\d+)?\s*\b(?:inches?)\b'
        
        matches = list(re.finditer(pattern, test_text))
        print(f"   Manual regex matches: {len(matches)}")
        
        for i, match in enumerate(matches, 1):
            matched_text = match.group()
            start = match.start()
            end = match.end()
            print(f"   {i}. Manual match: '{matched_text}' at [{start}-{end}]")
        
        # Test simplified patterns
        simplified_patterns = [
            r'\d+\s*inches?',                    # Just number + inches
            r'(?:^|[^\w])\d+',                   # Just the prefix part
            r'\d+(?:\.\d+)?\s*\binches?\b',      # Number + word boundary inches
        ]
        
        for pattern_name, simple_pattern in zip(['Number+Inches', 'Prefix+Number', 'Number+WB+Inches'], simplified_patterns):
            matches = list(re.finditer(simple_pattern, test_text, re.IGNORECASE))
            print(f"   {pattern_name}: {len(matches)} matches")
            for match in matches:
                print(f"      - '{match.group()}' at [{match.start()}-{match.end()}]")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Debug failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_37_inches_detection()