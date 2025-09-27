#!/usr/bin/env python3
"""
GOAL: Trace where 77 FLPC-detected measurements become only 5 tagged measurements
REASON: FLPC detection works but pipeline processing loses measurements
PROBLEM: Need to find exact stage where measurements are filtered out or lost
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def trace_measurement_pipeline():
    """Trace measurement processing through pipeline stages"""
    print("🔍 TRACING MEASUREMENT PIPELINE PROCESSING")
    print("=" * 60)
    
    # Load the large document
    large_doc_path = '/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(large_doc_path, 'r') as f:
        large_content = f.read()
    
    print(f"📄 DOCUMENT: {len(large_content):,} chars")
    print()
    
    # Check YAML frontmatter for processing info
    if large_content.startswith('---'):
        frontmatter_end = large_content.find('---', 3)
        if frontmatter_end != -1:
            frontmatter = large_content[3:frontmatter_end]
            
            print("📋 PROCESSING METADATA:")
            print("-" * 30)
            
            # Parse YAML to see processing details
            try:
                import yaml
                metadata = yaml.safe_load(frontmatter)
                
                # Check engine used
                engine = metadata.get('conversion', {}).get('engine', 'unknown')
                print(f"   Engine: {engine}")
                
                # Check raw entities
                raw_entities = metadata.get('raw_entities', {})
                print(f"   Raw entities found: {len(raw_entities)} types")
                
                measurement_entities = raw_entities.get('measurement', [])
                range_indicators = raw_entities.get('range_indicator', [])
                
                print(f"   📏 Raw measurements: {len(measurement_entities)}")
                print(f"   📐 Raw range indicators: {len(range_indicators)}")
                
                # Check normalized entities  
                normalization = metadata.get('normalization', {})
                canonical_entities = normalization.get('canonical_entities', [])
                
                measurement_canonical = [e for e in canonical_entities if e.get('type') == 'MEASUREMENT']
                print(f"   📊 Canonical measurements: {len(measurement_canonical)}")
                
                print()
                
                # Show first few raw measurements
                print("🔍 RAW MEASUREMENT SAMPLE:")
                print("-" * 30)
                for i, measurement in enumerate(measurement_entities[:10], 1):
                    text = measurement.get('text', 'N/A')
                    mtype = measurement.get('type', 'N/A')
                    print(f"   {i}. '{text}' ({mtype})")
                
                print()
                
                # Show first few canonical measurements
                print("🔍 CANONICAL MEASUREMENT SAMPLE:")
                print("-" * 30)
                for i, measurement in enumerate(measurement_canonical[:10], 1):
                    normalized = measurement.get('normalized', 'N/A')
                    mentions = measurement.get('mentions', [])
                    if mentions:
                        text = mentions[0].get('text', 'N/A')
                        print(f"   {i}. '{text}' → {normalized}")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error parsing YAML: {e}")
    
    # Now test current FLPC detection on same content
    print("🧪 CURRENT FLPC DETECTION TEST:")
    print("-" * 40)
    
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Test with 'complete' pattern set (our fix)
    results = flpc_engine.extract_entities(large_content, 'complete')
    entities = results.get('entities', {})
    
    current_measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(entities.get(mtype, []))
        current_measurement_count += count
        if count > 0:
            print(f"   {mtype}: {count}")
    
    current_range_count = len(entities.get('RANGE_INDICATOR', []))
    print(f"   RANGE_INDICATOR: {current_range_count}")
    print(f"   Total current FLPC: {current_measurement_count} measurements")
    print()
    
    # Test with 'default' pattern set (legacy)
    results_default = flpc_engine.extract_entities(large_content, 'default')
    entities_default = results_default.get('entities', {})
    
    default_measurement_count = 0
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        count = len(entities_default.get(mtype, []))
        default_measurement_count += count
    
    default_range_count = len(entities_default.get('RANGE_INDICATOR', []))
    print(f"   Legacy 'default' pattern set:")
    print(f"     Total measurements: {default_measurement_count}")
    print(f"     Range indicators: {default_range_count}")
    print()
    
    # Compare pattern sets
    print("📊 PATTERN SET COMPARISON:")
    print("-" * 40)
    print(f"   'complete' pattern set: {current_measurement_count} measurements, {current_range_count} range indicators")
    print(f"   'default' pattern set:  {default_measurement_count} measurements, {default_range_count} range indicators")
    
    if default_measurement_count < current_measurement_count:
        print(f"   🔴 PROBLEM: Document likely processed with 'default' pattern set")
        print(f"   🔴 LOST: {current_measurement_count - default_measurement_count} measurements due to pattern set")
    else:
        print(f"   ✅ Pattern set not the issue")
    
    print()
    
    # Check specific '30-37 inches' case
    print("🎯 SPECIFIC: '30-37 inches' DETECTION:")
    print("-" * 40)
    
    # Look in complete pattern results
    found_37_complete = False
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        for measurement in entities.get(mtype, []):
            if '37' in str(measurement) and ('inch' in str(measurement).lower() or 'in' in str(measurement).lower()):
                found_37_complete = True
                print(f"   ✅ Complete: Found '{measurement}' in {mtype}")
    
    # Look in default pattern results  
    found_37_default = False
    for mtype in ['MEASUREMENT_LENGTH', 'MEASUREMENT_WEIGHT', 'MEASUREMENT_TIME', 'MEASUREMENT_TEMPERATURE', 'MEASUREMENT_SOUND']:
        for measurement in entities_default.get(mtype, []):
            if '37' in str(measurement) and ('inch' in str(measurement).lower() or 'in' in str(measurement).lower()):
                found_37_default = True
                print(f"   🟡 Default: Found '{measurement}' in {mtype}")
    
    if not found_37_default and found_37_complete:
        print(f"   🔴 CONFIRMED: '30-37 inches' lost due to 'default' pattern set usage")

if __name__ == "__main__":
    trace_measurement_pipeline()