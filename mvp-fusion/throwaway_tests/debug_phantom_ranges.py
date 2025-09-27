#!/usr/bin/env python3
"""
GOAL: Debug phantom range indicators in measurements
REASON: "8 G" measurement shows range detected but no dash exists near it
PROBLEM: Range flagging logic incorrectly associating ranges with measurements
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_phantom_ranges():
    """Debug why measurements are getting phantom range indicators"""
    print("🔍 DEBUGGING PHANTOM RANGE INDICATORS")
    print("=" * 60)
    
    # Load the actual source document
    source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_path, 'r') as f:
        source_content = f.read()
    
    print(f"📄 SOURCE DOCUMENT:")
    print(f"   Length: {len(source_content):,} chars")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        # Get raw entities BEFORE range flagging
        print(f"\n🔍 TESTING ENTITIES BEFORE RANGE FLAGGING:")
        print("-" * 40)
        
        # Call FLPC directly to see raw results
        flpc_results = processor.flpc_engine.extract_entities(source_content, 'complete')
        flpc_entities = flpc_results.get('entities', {})
        
        # Check raw measurements
        raw_measurements = []
        for measurement_type in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
            raw_measurements.extend(processor._convert_flpc_entities(flpc_entities.get(measurement_type, []), measurement_type))
        
        print(f"📏 RAW MEASUREMENTS (before range flagging): {len(raw_measurements)}")
        
        # Show first few raw measurements
        for i, measurement in enumerate(raw_measurements[:5], 1):
            text = measurement.get('text', 'N/A')
            span = measurement.get('span', {})
            start = span.get('start', 0)
            end = span.get('end', 0)
            
            # Show actual text at span
            actual_text = source_content[start:end] if start < len(source_content) and end <= len(source_content) else "INVALID_SPAN"
            
            print(f"   {i}. Detected: '{text}' | Span: [{start}-{end}] | Actual: '{actual_text}'")
        
        # Check raw range indicators
        raw_range_indicators = processor._convert_flpc_entities(flpc_entities.get('RANGE_INDICATOR', []), 'RANGE_INDICATOR')
        
        print(f"\n📐 RAW RANGE INDICATORS: {len(raw_range_indicators)}")
        
        for i, indicator in enumerate(raw_range_indicators, 1):
            text = indicator.get('text', 'N/A')
            span = indicator.get('span', {})
            start = span.get('start', 0)
            end = span.get('end', 0)
            
            # Show actual text at span
            actual_text = source_content[start:end] if start < len(source_content) and end <= len(source_content) else "INVALID_SPAN"
            
            print(f"   {i}. Detected: '{text}' | Span: [{start}-{end}] | Actual: '{actual_text}'")
        
        # Now test the range flagging logic
        print(f"\n🔍 TESTING RANGE FLAGGING LOGIC:")
        print("-" * 40)
        
        # Create mock entities dict like the real pipeline
        entities = {
            'measurement': raw_measurements,
            'range_indicator': raw_range_indicators
        }
        
        # Apply our range flagging
        flagged_entities = processor._flag_range_entities(entities, source_content)
        
        flagged_measurements = flagged_entities.get('measurement', [])
        
        print(f"📏 MEASUREMENTS AFTER RANGE FLAGGING: {len(flagged_measurements)}")
        
        # Check each measurement for phantom ranges
        print(f"\n🎯 PHANTOM RANGE ANALYSIS:")
        print("-" * 40)
        
        for i, measurement in enumerate(flagged_measurements, 1):
            text = measurement.get('text', 'N/A')
            span = measurement.get('span', {})
            start = span.get('start', 0)
            end = span.get('end', 0)
            
            range_info = measurement.get('range_indicator', {})
            detected = range_info.get('detected', False)
            
            # Show actual text at span
            actual_text = source_content[start:end] if start < len(source_content) and end <= len(source_content) else "INVALID_SPAN"
            
            print(f"   {i}. '{text}' | Span: [{start}-{end}] | Actual: '{actual_text}' | Range: {detected}")
            
            if detected:
                indicator_text = range_info.get('indicator_text', 'N/A')
                indicator_span = range_info.get('indicator_span', {})
                ind_start = indicator_span.get('start', 0)
                ind_end = indicator_span.get('end', 0)
                
                # Check if indicator is actually near the measurement
                distance = min(abs(start - ind_end), abs(end - ind_start))
                
                print(f"      → Indicator: '{indicator_text}' at [{ind_start}-{ind_end}], Distance: {distance} chars")
                
                if distance > 10:  # More than 10 chars away
                    print(f"      🔴 PHANTOM: Range indicator too far from measurement!")
                    
                    # Show context around measurement
                    ctx_start = max(0, start - 20)
                    ctx_end = min(len(source_content), end + 20)
                    context = source_content[ctx_start:ctx_end]
                    print(f"      Context: '{context}'")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Debug failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_phantom_ranges()