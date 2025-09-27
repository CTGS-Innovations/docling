#!/usr/bin/env python3
"""
GOAL: Simple trace of measurement detection issue
REASON: FLPC detects measurements but they don't reach final output
PROBLEM: Need to find where measurements get lost in the pipeline
"""

import sys
import os

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def simple_measurement_test():
    """Test measurement detection and check the actual source document"""
    print("🔍 SIMPLE MEASUREMENT PIPELINE TEST")
    print("=" * 50)
    
    # Step 1: Read the source document that should have measurements
    source_file = "/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md"
    
    print("📋 STEP 1: Read Source Document")
    with open(source_file, 'r') as f:
        content = f.read()
    
    # Find the 9.4 measurements section
    start_marker = "### 9.4 Measurements (20 measurements)"
    end_marker = "### 9.5"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1:
        print("❌ Could not find 9.4 measurements section")
        return
    
    measurements_section = content[start_idx:end_idx] if end_idx != -1 else content[start_idx:start_idx+2000]
    print(f"✅ Found measurements section: {len(measurements_section)} characters")
    print("\n📋 Sample from measurements section:")
    lines = measurements_section.split('\n')[:10]
    for line in lines:
        if line.strip():
            print(f"   {line}")
    
    # Step 2: Test FLPC on this exact text
    print(f"\n📋 STEP 2: Test FLPC on Source Text")
    print("-" * 30)
    
    import yaml
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    flpc_results = flpc_engine.extract_entities(measurements_section, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    
    print("🎯 FLPC Results on Source Document:")
    total_measurements = 0
    for entity_type, entities in flpc_entities.items():
        if 'MEASUREMENT' in entity_type:
            count = len(entities)
            total_measurements += count
            print(f"   {entity_type}: {count}")
            for entity in entities[:3]:  # Show first 3
                print(f"      - {entity}")
    
    print(f"📊 Total measurements detected by FLPC: {total_measurements}")
    
    # Step 3: Check the actual output file
    print(f"\n📋 STEP 3: Check Pipeline Output")
    print("-" * 30)
    
    output_file = "/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md"
    
    try:
        with open(output_file, 'r') as f:
            output_content = f.read()
        
        # Check if measurements section has tags
        output_start = output_content.find(start_marker)
        if output_start == -1:
            print("❌ Measurements section not found in output")
            return
            
        output_end = output_content.find(end_marker, output_start)
        output_measurements = output_content[output_start:output_end] if output_end != -1 else output_content[output_start:output_start+2000]
        
        # Count measurement tags in output
        tag_count = output_measurements.count('||meas')
        print(f"🎯 Measurement tags in output: {tag_count}")
        
        # Show sample lines
        print("\n📋 Sample output lines:")
        output_lines = output_measurements.split('\n')[:10]
        for line in output_lines:
            if 'feet' in line or 'inches' in line or 'cm' in line:
                print(f"   {line}")
        
        # Analysis
        print(f"\n📊 ANALYSIS:")
        print(f"   FLPC detected: {total_measurements} measurements")
        print(f"   Output tagged: {tag_count} measurements") 
        
        if total_measurements > 0 and tag_count == 0:
            print("🔴 ISSUE: FLPC working but measurements not reaching normalization")
        elif total_measurements == 0:
            print("🔴 ISSUE: FLPC not detecting measurements in source document")
        elif tag_count > 0:
            print("🟢 SUCCESS: Measurements being detected and tagged")
            
    except FileNotFoundError:
        print("❌ Output file not found - pipeline may not have run")

if __name__ == "__main__":
    simple_measurement_test()