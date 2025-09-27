#!/usr/bin/env python3
"""
GOAL: Test lookbehind achieves true clean separation  
REASON: Verify "37 inches" detected cleanly without hyphen prefix
PROBLEM: Previous pattern included punctuation in match
"""

import sys
import os
import yaml
import re

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_lookbehind_separation():
    """Test that lookbehind gives us clean entity detection"""
    print("🧪 TESTING LOOKBEHIND CLEAN SEPARATION")
    print("=" * 50)
    
    # Test the key case
    test_text = "**30-37 inches**"
    
    print(f"📄 TEST: '{test_text}'")
    
    # Test the new lookbehind pattern manually
    new_pattern = r'(?i)(?<=^|[^\w])\d+(?:\.\d+)?\s*\b(?:inches?)\b'
    
    print(f"New pattern: {new_pattern}")
    
    matches = list(re.finditer(new_pattern, test_text))
    print(f"Manual regex matches: {len(matches)}")
    
    for i, match in enumerate(matches, 1):
        matched_text = match.group()
        start = match.start()
        end = match.end()
        print(f"  {i}. '{matched_text}' at [{start}-{end}]")
        
        # Check if this is clean (no leading punctuation)
        if matched_text.strip().startswith(('0','1','2','3','4','5','6','7','8','9')):
            print(f"      ✅ CLEAN: Starts with digit")
        else:
            print(f"      ❌ DIRTY: Starts with '{matched_text[0]}'")
    
    # Initialize ServiceProcessor to test with FLPC
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING WITH UPDATED FLPC PATTERNS:")
        print("-" * 40)
        
        entities = processor._extract_universal_entities(test_text)
        measurements = entities.get('measurement', [])
        range_indicators = entities.get('range_indicator', [])
        
        print(f"Measurements detected: {len(measurements)}")
        print(f"Range indicators detected: {len(range_indicators)}")
        
        for i, measurement in enumerate(measurements, 1):
            text = measurement.get('text', 'N/A')
            span = measurement.get('span', {})
            range_info = measurement.get('range_indicator', {})
            
            print(f"  {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
            print(f"     Range detected: {range_info.get('detected', False)}")
            
            # Check if this is clean
            if text.strip() and text.strip()[0].isdigit():
                print(f"     ✅ CLEAN: Starts with digit")
            else:
                print(f"     ❌ DIRTY: Starts with '{text.strip()[0] if text.strip() else 'EMPTY'}'")
        
        for i, indicator in enumerate(range_indicators, 1):
            text = indicator.get('text', 'N/A')
            span = indicator.get('span', {})
            print(f"  Range {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
        
        # Test multiple cases
        print(f"\n🔍 TESTING MULTIPLE CASES:")
        print("-" * 40)
        
        test_cases = [
            "**30-37 inches**",
            "(42 inches)",
            "Height: 6 feet",
            "*15 meters*",
            "Cost $100",
        ]
        
        clean_detections = 0
        total_detections = 0
        
        for test_case in test_cases:
            print(f"\n  Testing: '{test_case}'")
            entities = processor._extract_universal_entities(test_case)
            measurements = entities.get('measurement', [])
            
            for measurement in measurements:
                text = measurement.get('text', 'N/A')
                total_detections += 1
                
                if text.strip() and text.strip()[0].isdigit():
                    clean_detections += 1
                    print(f"    ✅ CLEAN: '{text}'")
                else:
                    print(f"    ❌ DIRTY: '{text}'")
        
        print(f"\n📊 CLEAN SEPARATION SUMMARY:")
        print("-" * 40)
        print(f"Total detections: {total_detections}")
        print(f"Clean detections: {clean_detections}")
        print(f"Clean percentage: {(clean_detections/total_detections*100):.1f}%" if total_detections > 0 else "No detections")
        
        if total_detections > 0 and clean_detections == total_detections:
            print(f"🟢 **SUCCESS**: 100% clean separation achieved!")
        elif clean_detections > total_detections * 0.8:
            print(f"🟡 **GOOD**: Mostly clean separation")
        else:
            print(f"🔴 **FAILED**: Still have dirty detections")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Lookbehind test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lookbehind_separation()