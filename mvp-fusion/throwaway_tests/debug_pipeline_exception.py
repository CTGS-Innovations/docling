#!/usr/bin/env python3
"""
GOAL: Debug what exception is clearing range indicators in pipeline
REASON: FLPC detects range indicators but they're cleared by exception handler
PROBLEM: Need to find exact point where range indicators are lost
"""

import sys
import os
import yaml
import logging

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_pipeline_exception():
    """Debug where range indicators are lost in pipeline"""
    print("🔍 DEBUGGING PIPELINE EXCEPTION FOR RANGE INDICATORS")
    print("=" * 60)
    
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Test the exact ServiceProcessor flow
    from pipeline.legacy.service_processor import ServiceProcessor
    
    print("📋 INITIALIZING SERVICE PROCESSOR:")
    print("-" * 40)
    
    processor = ServiceProcessor(config)
    
    print("✅ ServiceProcessor initialized")
    
    # Test the FLPC extraction method directly  
    test_text = "Height 30-37 inches between 50 and 75 pounds"
    
    print(f"\n📋 TESTING _extract_universal_entities METHOD:")
    print("-" * 40)
    print(f"Text: '{test_text}'")
    
    try:
        # Call the extraction method directly
        entities = processor._extract_universal_entities(test_text)
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"Total entity keys: {list(entities.keys())}")
        
        for key, value in entities.items():
            print(f"  {key}: {len(value)} entities")
            if key == 'range_indicator':
                print(f"    range_indicator content: {value}")
        
        # Check if range indicators exist
        range_indicators = entities.get('range_indicator', [])
        if range_indicators:
            print(f"\n✅ RANGE INDICATORS PRESERVED: {len(range_indicators)}")
            for i, indicator in enumerate(range_indicators, 1):
                print(f"  {i}. {indicator}")
        else:
            print(f"\n❌ RANGE INDICATORS LOST OR EMPTY")
            
    except Exception as e:
        print(f"\n🔴 EXCEPTION OCCURRED: {e}")
        import traceback
        traceback.print_exc()
    
    # Also test FLPC directly to confirm it's working
    print(f"\n📋 CONFIRMING FLPC STILL WORKS:")
    print("-" * 40)
    
    from fusion.flpc_engine import FLPCEngine
    flpc_engine = FLPCEngine(config)
    
    flpc_results = flpc_engine.extract_entities(test_text, 'complete')
    flpc_entities = flpc_results.get('entities', {})
    range_indicators_flpc = flpc_entities.get('RANGE_INDICATOR', [])
    
    print(f"FLPC direct: {len(range_indicators_flpc)} range indicators")
    print(f"FLPC content: {range_indicators_flpc}")

if __name__ == "__main__":
    debug_pipeline_exception()