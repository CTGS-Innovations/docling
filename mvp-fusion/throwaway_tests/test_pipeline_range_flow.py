#!/usr/bin/env python3
"""
GOAL: Test full pipeline for range detection (measurements + range indicators)
REASON: Verify both measurements and range indicators reach final entity output
PROBLEM: Need to confirm pipeline integration works for normalization approach
"""

import sys
import os

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_pipeline_range_flow():
    """Test full pipeline processing for range detection setup"""
    print("🔍 TESTING FULL PIPELINE RANGE FLOW")
    print("=" * 50)
    
    # Test with service processor pipeline
    from pipeline.legacy.service_processor import ServiceProcessor
    from pathlib import Path
    import yaml
    
    # Load config
    config_path = '/home/corey/projects/docling/mvp-fusion/config/config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize processor
    processor = ServiceProcessor(config)
    
    # Use test file
    test_file = Path('/home/corey/projects/docling/mvp-fusion/throwaway_tests/range_test_input.txt')
    
    print("📋 PROCESSING TEST FILE:")
    print("-" * 30)
    with open(test_file, 'r') as f:
        content = f.read()
    print(content.strip())
    print()
    
    # Process through pipeline
    print("🔄 PROCESSING THROUGH PIPELINE:")
    print("-" * 30)
    
    # Process the file
    documents, processing_time = processor.process_files_service([test_file])
    
    if not documents:
        print("❌ No documents returned from processing")
        return None, None
    
    # Get the first document result
    doc = documents[0]
    
    # Access entities directly from document
    entities = doc.entities if hasattr(doc, 'entities') else {}
    
    print("📊 ENTITY DETECTION RESULTS:")
    print("-" * 30)
    
    # Show measurements
    measurement_entities = entities.get('measurement', [])
    if measurement_entities:
        print(f"✅ MEASUREMENTS ({len(measurement_entities)}):")
        for i, entity in enumerate(measurement_entities[:10], 1):  # Show first 10
            text = entity.get('text', 'N/A')
            start = entity.get('start', 'N/A')
            end = entity.get('end', 'N/A')
            print(f"   {i}. '{text}' [{start}-{end}]")
    else:
        print("❌ No measurements detected")
    
    print()
    
    # Show range indicators  
    range_entities = entities.get('range_indicator', [])
    if range_entities:
        print(f"✅ RANGE INDICATORS ({len(range_entities)}):")
        for i, entity in enumerate(range_entities[:10], 1):  # Show first 10
            text = entity.get('text', 'N/A')
            start = entity.get('start', 'N/A')
            end = entity.get('end', 'N/A')
            print(f"   {i}. '{text}' [{start}-{end}]")
    else:
        print("❌ No range indicators detected")
    
    print()
    
    # Analysis for normalization approach
    print("🎯 NORMALIZATION READINESS ANALYSIS:")
    print("-" * 30)
    
    if measurement_entities and range_entities:
        print("✅ READY: Both measurements and range indicators detected")
        print("✅ Can implement proximity-based range consolidation")
        print("✅ Example: '37 inches' + '-' indicator can find '30' nearby")
    elif measurement_entities:
        print("🟡 PARTIAL: Measurements detected but no range indicators")
        print("🔍 Check range_indicator pattern integration")
    elif range_entities:
        print("🟡 PARTIAL: Range indicators detected but no measurements") 
        print("🔍 Check measurement pattern integration")
    else:
        print("❌ BLOCKED: Neither measurements nor range indicators detected")
        print("🔍 Check FLPC pattern compilation and pipeline integration")
    
    return measurement_entities, range_entities

if __name__ == "__main__":
    test_pipeline_range_flow()