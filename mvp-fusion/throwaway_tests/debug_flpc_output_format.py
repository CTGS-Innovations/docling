#!/usr/bin/env python3
"""
GOAL: Debug exact FLPC output format for range indicators vs measurements
REASON: Range indicators detected by FLPC but lost in pipeline conversion
PROBLEM: Need to see exact data structure FLPC returns for each entity type
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_flpc_output_format():
    """Debug the exact format FLPC returns for different entity types"""
    print("🔍 DEBUGGING FLPC OUTPUT FORMAT")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize FLPC engine
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    # Simple test text with both measurements and range indicators
    test_text = "Height 30-37 inches between 50 and 75 pounds"
    
    print(f"📋 TEST TEXT: '{test_text}'")
    print("-" * 40)
    
    # Get FLPC results
    flpc_results = flpc_engine.extract_entities(test_text, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    
    print("🔍 RAW FLPC OUTPUT FORMAT:")
    print("-" * 30)
    
    # Check each entity type that should be detected
    entity_types_to_check = [
        'RANGE_INDICATOR',
        'MEASUREMENT_LENGTH', 
        'MEASUREMENT_WEIGHT'
    ]
    
    for entity_type in entity_types_to_check:
        entities = flpc_entities.get(entity_type, [])
        print(f"\n{entity_type}:")
        print(f"  Count: {len(entities)}")
        print(f"  Type: {type(entities)}")
        
        if entities:
            for i, entity in enumerate(entities, 1):
                print(f"  {i}. Type: {type(entity)}")
                print(f"     Value: {repr(entity)}")
                
                if isinstance(entity, dict):
                    print(f"     Keys: {list(entity.keys())}")
                    for key, value in entity.items():
                        print(f"       {key}: {repr(value)} ({type(value)})")
        else:
            print("  ❌ No entities detected")
    
    # Test the conversion method directly
    print(f"\n🧪 TESTING _convert_flpc_entities METHOD:")
    print("-" * 40)
    
    # Import the conversion method
    from pipeline.legacy.service_processor import ServiceProcessor
    
    # Create a mock processor to access the method
    processor = ServiceProcessor(config)
    
    for entity_type in entity_types_to_check:
        entities = flpc_entities.get(entity_type, [])
        if entities:
            print(f"\n{entity_type} conversion:")
            converted = processor._convert_flpc_entities(entities, entity_type)
            print(f"  Input: {repr(entities)}")
            print(f"  Output: {repr(converted)}")
            print(f"  Output count: {len(converted)}")

if __name__ == "__main__":
    debug_flpc_output_format()