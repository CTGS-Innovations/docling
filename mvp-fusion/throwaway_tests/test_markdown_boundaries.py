#!/usr/bin/env python3
"""
GOAL: Test non-word character boundaries handle markdown and punctuation
REASON: Verify **30-37 inches** detection works with updated patterns
PROBLEM: Previous patterns failed on markdown symbols and punctuation
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_markdown_boundaries():
    """Test that non-word boundaries handle all punctuation and markdown"""
    print("🧪 TESTING NON-WORD CHARACTER BOUNDARIES")
    print("=" * 60)
    
    # Test cases with various punctuation/markdown
    test_cases = [
        "**30-37 inches** (markdown)",
        "(30 feet) in parentheses",
        '"30 meters" in quotes',
        "30. inches with period",
        "[30 cm] in brackets",
        "30: measurement with colon",
        "30, 40 inches with comma",
        "Height is 30 inches normal",
        "*30 inches* italic markdown",
        "~30 inches~ strikethrough"
    ]
    
    print(f"📄 TEST CASES ({len(test_cases)} total):")
    for i, case in enumerate(test_cases, 1):
        print(f"   {i}. {case}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING EACH CASE:")
        print("-" * 40)
        
        successful_detections = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n   Test {i}: '{test_case}'")
            
            entities = processor._extract_universal_entities(test_case)
            measurements = entities.get('measurement', [])
            
            if measurements:
                successful_detections += 1
                print(f"      ✅ DETECTED: {len(measurements)} measurements")
                for measurement in measurements:
                    text = measurement.get('text', 'N/A')
                    print(f"         - '{text}'")
            else:
                print(f"      ❌ MISSED: No measurements detected")
        
        # Test specific "**30-37 inches**" case
        print(f"\n🎯 SPECIFIC MARKDOWN TEST:")
        print("-" * 40)
        
        markdown_test = "**30-37 inches**"
        entities = processor._extract_universal_entities(markdown_test)
        measurements = entities.get('measurement', [])
        range_indicators = entities.get('range_indicator', [])
        
        print(f"   Test: '{markdown_test}'")
        print(f"   Measurements: {len(measurements)}")
        print(f"   Range indicators: {len(range_indicators)}")
        
        # Check if we get both "30" and "37" measurements
        found_30 = False
        found_37 = False
        
        for measurement in measurements:
            text = measurement.get('text', '')
            if '30' in text and 'inch' in text.lower():
                found_30 = True
                print(f"      ✅ Found 30: '{text}'")
            if '37' in text and 'inch' in text.lower():
                found_37 = True
                print(f"      ✅ Found 37: '{text}'")
        
        # Check range indicator
        found_hyphen = False
        for indicator in range_indicators:
            if indicator.get('text', '') == '-':
                found_hyphen = True
                print(f"      ✅ Found hyphen: '-'")
        
        # Test Section 9.4 with new patterns
        print(f"\n🔍 TESTING SECTION 9.4 WITH NEW PATTERNS:")
        print("-" * 40)
        
        source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
        with open(source_path, 'r') as f:
            source_content = f.read()
        
        entities = processor._extract_universal_entities(source_content)
        measurements = entities.get('measurement', [])
        
        print(f"   Total measurements: {len(measurements)}")
        
        # Look for measurements that should now be detected
        markdown_measurements = 0
        for measurement in measurements:
            text = measurement.get('text', '')
            span = measurement.get('span', {})
            start = span.get('start', 0)
            end = span.get('end', 0)
            
            # Check if measurement is surrounded by markdown
            context_start = max(0, start - 5)
            context_end = min(len(source_content), end + 5)
            context = source_content[context_start:context_end]
            
            if '**' in context or '*' in context:
                markdown_measurements += 1
                print(f"      📝 Markdown measurement: '{text}' in context '{context}'")
        
        print(f"\n📊 NON-WORD BOUNDARY SUMMARY:")
        print("-" * 40)
        print(f"   Successful detections: {successful_detections}/{len(test_cases)}")
        print(f"   Section 9.4 measurements: {len(measurements)}")
        print(f"   Markdown measurements: {markdown_measurements}")
        
        if successful_detections >= len(test_cases) * 0.8:  # 80% success rate
            print(f"   🟢 **SUCCESS**: Non-word boundaries working effectively!")
        elif successful_detections >= len(test_cases) * 0.5:  # 50% success rate
            print(f"   🟡 **PARTIAL**: Some improvements but not complete")
        else:
            print(f"   🔴 **FAILED**: Non-word boundaries not working")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Non-word boundary test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_markdown_boundaries()