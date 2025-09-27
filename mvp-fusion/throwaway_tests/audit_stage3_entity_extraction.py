#!/usr/bin/env python3
"""
GOAL: Audit Stage 3 - Entity extraction (_extract_universal_entities)
REASON: Need to verify if FLPC detects 77 measurements but only 12 reach normalization
PROBLEM: Gap between FLPC capability (77) and pipeline output (12)
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def audit_stage3_entity_extraction():
    """Audit Stage 3: Entity extraction in isolation"""
    print("🔍 STAGE 3 AUDIT: ENTITY EXTRACTION")
    print("=" * 60)
    
    # Step 1: Load the source document
    source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_path, 'r') as f:
        source_content = f.read()
    
    print(f"📄 SOURCE DOCUMENT: {len(source_content):,} chars")
    
    # Step 2: Test Stage 3 directly
    print(f"\n🔍 TESTING STAGE 3 DIRECTLY:")
    print("-" * 40)
    
    # Initialize ServiceProcessor like the pipeline does
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    # Call _extract_universal_entities directly
    print("🧪 Calling _extract_universal_entities() directly...")
    
    try:
        # This is the exact function called in Stage 3
        entities = processor._extract_universal_entities(source_content)
        
        print(f"✅ Stage 3 completed successfully")
        print(f"📊 Entity types returned: {list(entities.keys())}")
        
        # Audit measurements specifically
        measurement_entities = entities.get('measurement', [])
        range_indicators = entities.get('range_indicator', [])
        
        print(f"\n📏 MEASUREMENT AUDIT:")
        print(f"   Measurements detected: {len(measurement_entities)}")
        print(f"   Range indicators detected: {len(range_indicators)}")
        
        # Show first 10 measurements
        print(f"\n🔍 MEASUREMENT SAMPLE:")
        for i, measurement in enumerate(measurement_entities[:10], 1):
            text = measurement.get('text', 'N/A')
            mtype = measurement.get('type', 'N/A')
            span = measurement.get('span', {})
            print(f"   {i}. '{text}' ({mtype}) [{span.get('start')}-{span.get('end')}]")
        
        # Check for "37 inches" specifically
        print(f"\n🎯 SPECIFIC: '37 inches' CHECK:")
        found_37 = False
        for measurement in measurement_entities:
            text = measurement.get('text', '')
            if '37' in text and 'inch' in text.lower():
                found_37 = True
                print(f"   ✅ Found: '{text}' ({measurement.get('type', 'unknown')})")
        
        if not found_37:
            print(f"   ❌ '37 inches' NOT found in Stage 3 output")
        
        # Show range indicators
        print(f"\n📐 RANGE INDICATOR SAMPLE:")
        for i, indicator in enumerate(range_indicators[:10], 1):
            text = indicator.get('text', 'N/A')
            span = indicator.get('span', {})
            print(f"   {i}. '{text}' [{span.get('start')}-{span.get('end')}]")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Stage 3 failed with error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Compare with FLPC direct test
    print(f"\n🧪 COMPARING WITH FLPC DIRECT TEST:")
    print("-" * 40)
    
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test with 'complete' pattern set
    flpc_results = flpc_engine.extract_entities(source_content, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    
    flpc_measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(flpc_entities.get(mtype, []))
        flpc_measurement_count += count
    
    flpc_range_count = len(flpc_entities.get('RANGE_INDICATOR', []))
    
    print(f"🔬 FLPC DIRECT (complete pattern set):")
    print(f"   Measurements: {flpc_measurement_count}")
    print(f"   Range indicators: {flpc_range_count}")
    
    print(f"\n📊 STAGE 3 VS FLPC COMPARISON:")
    print(f"   Stage 3 measurements: {len(measurement_entities)}")
    print(f"   FLPC direct measurements: {flpc_measurement_count}")
    print(f"   Difference: {flpc_measurement_count - len(measurement_entities)}")
    
    if len(measurement_entities) < flpc_measurement_count:
        print(f"🔴 **PROBLEM**: Stage 3 loses {flpc_measurement_count - len(measurement_entities)} measurements")
        print(f"   This is the bottleneck! FLPC can detect more but Stage 3 doesn't return them.")
    else:
        print(f"✅ Stage 3 matches FLPC capability")
    
    # Step 4: Check pattern set being used in Stage 3
    print(f"\n🔍 PATTERN SET INVESTIGATION:")
    print("-" * 40)
    
    # Check what pattern set Stage 3 actually uses
    print("Looking at ServiceProcessor._extract_universal_entities() code...")
    
    # Read the actual code to see pattern set
    with open('/home/corey/projects/docling/mvp-fusion/pipeline/legacy/service_processor.py', 'r') as f:
        sp_content = f.read()
    
    # Find the FLPC call
    if 'extract_entities(content, \'complete\')' in sp_content:
        print("✅ ServiceProcessor uses 'complete' pattern set")
    elif 'extract_entities(content)' in sp_content:
        print("🟡 ServiceProcessor uses default pattern set")
    else:
        print("❌ Cannot determine pattern set used")
    
    print(f"\n🎯 STAGE 3 AUDIT CONCLUSION:")
    print("-" * 40)
    if len(measurement_entities) == flpc_measurement_count:
        print("✅ Stage 3 working correctly - bottleneck is in later stages")
    else:
        print("🔴 Stage 3 is the bottleneck - losing measurements here")

if __name__ == "__main__":
    audit_stage3_entity_extraction()