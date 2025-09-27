#!/usr/bin/env python3
"""
GOAL: Test word boundary fix and percentage measurement addition
REASON: Verify "37 inches" detected cleanly AND "15%" detected in ranges  
PROBLEM: Need both clean separation and percentage coverage
"""

import sys
import os
import yaml
import re

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_word_boundary_and_percentage():
    """Test clean word boundaries and percentage measurements"""
    print("🧪 TESTING WORD BOUNDARY + PERCENTAGE MEASUREMENTS")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        "**30-37 inches** (original problem)",
        "Growth projection: **10-15%** range",
        "Safety improvement: **25%** reduction", 
        "Market share: **45.5%** of industry",
        "Error rate: **0.5%** (half percent)",
        "Temperature: **20-25 degrees** celsius",
        "(42 inches) in parentheses",
    ]
    
    print(f"📄 TEST CASES:")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case}")
    
    # Test word boundary pattern manually
    print(f"\n🔍 MANUAL PATTERN TESTING:")
    print("-" * 40)
    
    # Test the simplified word boundary pattern
    length_pattern = r'(?i)\b\d+(?:\.\d+)?\s*(?:inches?|feet|cm|meters?)\b'
    percentage_pattern = r'(?i)\b\d+(?:\.\d+)?\s*%'
    
    test_text = "**30-37 inches** and **10-15%** range"
    
    length_matches = list(re.finditer(length_pattern, test_text))
    percent_matches = list(re.finditer(percentage_pattern, test_text))
    
    print(f"Test text: '{test_text}'")
    print(f"Length matches: {len(length_matches)}")
    for match in length_matches:
        print(f"  - '{match.group()}' at [{match.start()}-{match.end()}]")
    
    print(f"Percentage matches: {len(percent_matches)}")
    for match in percent_matches:
        print(f"  - '{match.group()}' at [{match.start()}-{match.end()}]")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING WITH UPDATED FLPC PATTERNS:")
        print("-" * 40)
        
        total_measurements = 0
        clean_measurements = 0
        percentage_measurements = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n  Test {i}: {test_case}")
            
            entities = processor._extract_universal_entities(test_case)
            measurements = entities.get('measurement', [])
            range_indicators = entities.get('range_indicator', [])
            
            print(f"    Measurements: {len(measurements)}")
            print(f"    Range indicators: {len(range_indicators)}")
            
            for measurement in measurements:
                text = measurement.get('text', 'N/A')
                span = measurement.get('span', {})
                range_info = measurement.get('range_indicator', {})
                
                total_measurements += 1
                
                # Check if clean (starts with digit)
                if text.strip() and text.strip()[0].isdigit():
                    clean_measurements += 1
                    print(f"      ✅ CLEAN: '{text}'")
                else:
                    print(f"      ❌ DIRTY: '{text}'")
                
                # Check if percentage
                if '%' in text:
                    percentage_measurements += 1
                    print(f"      📊 PERCENTAGE: '{text}'")
                
                # Check range flag
                if range_info.get('detected'):
                    indicator = range_info.get('indicator_text', 'N/A')
                    print(f"      🔗 RANGE: '{indicator}'")
        
        # Test specific critical cases
        print(f"\n🎯 CRITICAL CASE TESTING:")
        print("-" * 40)
        
        critical_tests = [
            ("**30-37 inches**", "Should detect '37 inches' cleanly"),
            ("**10-15%**", "Should detect '15%' as percentage"), 
        ]
        
        for test_text, expectation in critical_tests:
            print(f"\n  Testing: '{test_text}' ({expectation})")
            
            entities = processor._extract_universal_entities(test_text)
            measurements = entities.get('measurement', [])
            
            found_target = False
            for measurement in measurements:
                text = measurement.get('text', 'N/A')
                
                if '37' in text and 'inch' in text.lower():
                    found_target = True
                    if text.strip().startswith('37'):
                        print(f"    ✅ SUCCESS: Found clean '37 inches' as '{text}'")
                    else:
                        print(f"    ❌ DIRTY: Found '37 inches' as '{text}' (not clean)")
                
                elif '15' in text and '%' in text:
                    found_target = True
                    if text.strip().startswith('15'):
                        print(f"    ✅ SUCCESS: Found clean '15%' as '{text}'")
                    else:
                        print(f"    ❌ DIRTY: Found '15%' as '{text}' (not clean)")
            
            if not found_target:
                print(f"    ❌ MISSED: Target not found")
        
        # Summary
        print(f"\n📊 SUMMARY:")
        print("-" * 40)
        print(f"Total measurements detected: {total_measurements}")
        print(f"Clean measurements (start with digit): {clean_measurements}")
        print(f"Percentage measurements: {percentage_measurements}")
        print(f"Clean percentage: {(clean_measurements/total_measurements*100):.1f}%" if total_measurements > 0 else "No measurements")
        
        if total_measurements > 0:
            if clean_measurements == total_measurements:
                print(f"🟢 **SUCCESS**: 100% clean separation achieved!")
            elif clean_measurements >= total_measurements * 0.8:
                print(f"🟡 **GOOD**: {(clean_measurements/total_measurements*100):.1f}% clean separation")
            else:
                print(f"🔴 **NEEDS WORK**: Only {(clean_measurements/total_measurements*100):.1f}% clean")
        
        if percentage_measurements > 0:
            print(f"✅ Percentage measurements detected!")
        else:
            print(f"❌ No percentage measurements detected")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_word_boundary_and_percentage()