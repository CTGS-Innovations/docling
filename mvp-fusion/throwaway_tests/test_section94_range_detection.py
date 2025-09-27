#!/usr/bin/env python3
"""
GOAL: Test AC+FLPC range detection on real Section 9.4 content
REASON: Verify the enhanced architecture works on actual problem case
PROBLEM: Need to test "30-37 inches" and other range measurements in real document
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_section94_range_detection():
    """Test range detection on the real Section 9.4 document"""
    print("🧪 TESTING SECTION 9.4 AC+FLPC HYBRID RANGE DETECTION")
    print("=" * 60)
    
    # Load the actual source document
    source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_path, 'r') as f:
        source_content = f.read()
    
    print(f"📄 SOURCE DOCUMENT:")
    print(f"   Length: {len(source_content):,} chars")
    print(f"   Source: {source_path}")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        # Test Stage 3 with enhanced range detection
        print(f"\n🔍 TESTING STAGE 3 ON SECTION 9.4:")
        print("-" * 40)
        
        entities = processor._extract_universal_entities(source_content)
        
        # Check measurements
        measurements = entities.get('measurement', [])
        print(f"📏 MEASUREMENTS DETECTED: {len(measurements)}")
        
        # Show all measurements with range info
        range_measurements = []
        standalone_measurements = []
        
        for measurement in measurements:
            text = measurement.get('text', 'N/A')
            range_info = measurement.get('range_indicator', {})
            detected = range_info.get('detected', False)
            
            if detected:
                range_measurements.append(measurement)
            else:
                standalone_measurements.append(measurement)
        
        print(f"   Range measurements: {len(range_measurements)}")
        print(f"   Standalone measurements: {len(standalone_measurements)}")
        
        # Show range measurements
        print(f"\n📐 RANGE MEASUREMENTS:")
        for i, measurement in enumerate(range_measurements[:10], 1):
            text = measurement.get('text', 'N/A')
            range_info = measurement.get('range_indicator', {})
            range_type = range_info.get('type', 'unknown')
            context = range_info.get('context', 'unknown')
            indicator = range_info.get('indicator_text', 'N/A')
            
            print(f"   {i}. '{text}' - {range_type}/{context} ('{indicator}')")
        
        # Show standalone measurements
        print(f"\n📏 STANDALONE MEASUREMENTS (first 10):")
        for i, measurement in enumerate(standalone_measurements[:10], 1):
            text = measurement.get('text', 'N/A')
            print(f"   {i}. '{text}'")
        
        # Check for specific "37 inches" case
        print(f"\n🎯 SEARCHING FOR '37 inches' CASE:")
        print("-" * 40)
        
        found_37_inches = False
        for measurement in measurements:
            text = measurement.get('text', '')
            if '37' in text and 'inch' in text.lower():
                found_37_inches = True
                range_info = measurement.get('range_indicator', {})
                detected = range_info.get('detected', False)
                
                print(f"   ✅ Found: '{text}'")
                print(f"   Range detected: {detected}")
                
                if detected:
                    range_type = range_info.get('type', 'unknown')
                    context = range_info.get('context', 'unknown')
                    indicator = range_info.get('indicator_text', 'N/A')
                    print(f"   → Type: {range_type}, Context: {context}, Indicator: '{indicator}'")
        
        if not found_37_inches:
            print(f"   ❌ '37 inches' not found in measurements")
            
            # Search for it in source content
            if '37 inches' in source_content:
                print(f"   📝 '37 inches' exists in source content")
                # Find context around it
                idx = source_content.find('37 inches')
                context = source_content[max(0, idx-30):idx+40]
                print(f"   Context: '{context}'")
        
        # Check range indicators
        range_indicators = entities.get('range_indicator', [])
        print(f"\n📐 RANGE INDICATORS DETECTED: {len(range_indicators)}")
        
        hyphen_indicators = [r for r in range_indicators if r.get('text', '') in ['-', '–', '—']]
        word_indicators = [r for r in range_indicators if r.get('text', '').lower() in ['to', 'through', 'between']]
        
        print(f"   Hyphen indicators: {len(hyphen_indicators)}")
        print(f"   Word indicators: {len(word_indicators)}")
        
        # Summary
        print(f"\n📊 RANGE DETECTION SUMMARY:")
        print("-" * 40)
        
        total_measurements = len(measurements)
        flagged_measurements = len(range_measurements)
        
        print(f"   Total measurements: {total_measurements}")
        print(f"   Range-flagged measurements: {flagged_measurements}")
        print(f"   Range indicators: {len(range_indicators)}")
        print(f"   Success rate: {(flagged_measurements/total_measurements*100):.1f}%" if total_measurements > 0 else "   No measurements detected")
        
        if total_measurements > 0 and flagged_measurements > 0:
            print(f"   🟢 **SUCCESS**: Range detection working on real document!")
        elif total_measurements > 0:
            print(f"   🟡 **PARTIAL**: Measurements detected but no ranges flagged")
        else:
            print(f"   🔴 **FAILED**: No measurements detected")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Section 9.4 test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_section94_range_detection()