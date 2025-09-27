#!/usr/bin/env python3
"""
GOAL: Test clean separation - FLPC detects "37 inches", AC detects "-" separately
REASON: User clarified architecture should separate detection from range indicators
PROBLEM: Previous patterns included hyphens in measurements, violating clean separation
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_clean_separation():
    """Test that FLPC detects clean measurements and AC detects range indicators separately"""
    print("🧪 TESTING CLEAN SEPARATION ARCHITECTURE")
    print("=" * 60)
    
    # Test case: "30-37 inches"
    test_content = "Handrail height 30-37 inches required"
    
    print(f"📄 TEST CONTENT: '{test_content}'")
    print(f"   Expected FLPC: '37 inches' (clean number)")
    print(f"   Expected AC: '-' (range indicator)")
    print(f"   Expected Range Flag: True (on '37 inches' entity)")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING STAGE 3 CLEAN SEPARATION:")
        print("-" * 40)
        
        entities = processor._extract_universal_entities(test_content)
        
        # Check measurements
        measurements = entities.get('measurement', [])
        range_indicators = entities.get('range_indicator', [])
        
        print(f"📏 MEASUREMENTS DETECTED: {len(measurements)}")
        for i, measurement in enumerate(measurements, 1):
            text = measurement.get('text', 'N/A')
            span = measurement.get('span', {})
            range_info = measurement.get('range_indicator', {})
            
            print(f"   {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
            print(f"      Range detected: {range_info.get('detected', False)}")
            
            if range_info.get('detected'):
                indicator = range_info.get('indicator_text', 'N/A')
                context = range_info.get('context', 'N/A')
                print(f"      → Indicator: '{indicator}', Context: {context}")
        
        print(f"\n📐 RANGE INDICATORS DETECTED: {len(range_indicators)}")
        for i, indicator in enumerate(range_indicators, 1):
            text = indicator.get('text', 'N/A')
            span = indicator.get('span', {})
            print(f"   {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
        
        # Verify clean separation
        print(f"\n🎯 CLEAN SEPARATION VERIFICATION:")
        print("-" * 40)
        
        # Check if we have "37 inches" (not "-37 inches")
        found_clean_measurement = False
        found_hyphen_indicator = False
        
        for measurement in measurements:
            text = measurement.get('text', '')
            if '37' in text and 'inch' in text.lower():
                if text.strip() == '37 inches':
                    found_clean_measurement = True
                    print(f"   ✅ Clean measurement: '{text}' (no hyphen prefix)")
                    
                    # Check if it has range flag
                    range_info = measurement.get('range_indicator', {})
                    if range_info.get('detected'):
                        print(f"   ✅ Range flag: True (correctly flagged)")
                    else:
                        print(f"   ❌ Range flag: False (should be True)")
                else:
                    print(f"   ❌ Dirty measurement: '{text}' (includes hyphen)")
        
        # Check if hyphen detected separately
        for indicator in range_indicators:
            text = indicator.get('text', '')
            if text == '-':
                found_hyphen_indicator = True
                print(f"   ✅ Hyphen indicator: '{text}' (detected separately)")
        
        if not found_clean_measurement:
            print(f"   ❌ Clean '37 inches' not found")
        
        if not found_hyphen_indicator:
            print(f"   ❌ Hyphen '-' indicator not found")
        
        # Test against Section 9.4 document
        print(f"\n🔍 TESTING SECTION 9.4 DOCUMENT:")
        print("-" * 40)
        
        source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
        with open(source_path, 'r') as f:
            source_content = f.read()
        
        entities = processor._extract_universal_entities(source_content)
        measurements = entities.get('measurement', [])
        
        print(f"   Total measurements: {len(measurements)}")
        
        # Look for clean measurements (no hyphens)
        clean_measurements = 0
        dirty_measurements = 0
        
        for measurement in measurements:
            text = measurement.get('text', '')
            if text.startswith('-') or '- ' in text:
                dirty_measurements += 1
                print(f"   🔴 Dirty: '{text}'")
            else:
                clean_measurements += 1
        
        print(f"\n📊 CLEAN SEPARATION SUMMARY:")
        print("-" * 40)
        print(f"   Clean measurements: {clean_measurements}")
        print(f"   Dirty measurements (with hyphens): {dirty_measurements}")
        print(f"   Range indicators: {len(entities.get('range_indicator', []))}")
        
        if dirty_measurements == 0 and clean_measurements > 0:
            print(f"   🟢 **SUCCESS**: Clean separation achieved!")
        elif dirty_measurements > 0:
            print(f"   🔴 **FAILED**: Still detecting dirty measurements with hyphens")
        else:
            print(f"   🟡 **PARTIAL**: No dirty measurements but also no clean ones")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Clean separation test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_clean_separation()