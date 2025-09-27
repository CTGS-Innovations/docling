#!/usr/bin/env python3
"""
GOAL: Test parenthetical measurement filtering
REASON: Debug why parenthetical measurements are still being tagged
PROBLEM: Need to verify filtering logic works correctly
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_parenthetical_filter():
    """Test the parenthetical filtering logic directly"""
    print("🧪 TESTING PARENTHETICAL MEASUREMENT FILTERING")
    print("=" * 55)
    
    # Test case that should be filtered out
    test_content = "Fall protection required above **6 feet** (1.8 meters) in construction"
    
    print(f"📄 Test content: '{test_content}'")
    
    # Initialize ServiceProcessor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    
    try:
        print(f"\n🔍 TESTING FLPC EXTRACTION BEFORE FILTERING:")
        print("-" * 50)
        
        # Test FLPC extraction directly
        if processor.flpc_engine:
            flpc_results = processor.flpc_engine.extract_entities(test_content, 'complete')
            flpc_entities = flpc_results.get('entities', {})
            
            print(f"FLPC raw results:")
            for measurement_type in ['MEASUREMENT_LENGTH']:
                matches = flpc_entities.get(measurement_type, [])
                print(f"  {measurement_type}: {len(matches)} matches")
                for match in matches:
                    if isinstance(match, dict):
                        text = match.get('text', '')
                        start = match.get('start', 0)
                        end = match.get('end', 0)
                        print(f"    - '{text}' at [{start}-{end}]")
                    else:
                        print(f"    - '{match}' (string format - no span info)")
            
            # Convert to service processor format
            measurement_entities = []
            for measurement_type in ['MEASUREMENT_LENGTH']:
                measurement_entities.extend(processor._convert_flpc_entities(flpc_entities.get(measurement_type, []), measurement_type))
            
            print(f"\n🔍 BEFORE FILTERING: {len(measurement_entities)} entities")
            for i, entity in enumerate(measurement_entities, 1):
                text = entity.get('text', '')
                span = entity.get('span', {})
                print(f"  {i}. '{text}' at [{span.get('start')}-{span.get('end')}]")
            
            # Test the filtering
            filtered_entities = processor._filter_parenthetical_measurements(measurement_entities, test_content)
            
            print(f"\n🎯 AFTER FILTERING: {len(filtered_entities)} entities")
            for i, entity in enumerate(filtered_entities, 1):
                text = entity.get('text', '')
                span = entity.get('span', {})
                print(f"  {i}. '{text}' at [{span.get('start')}-{span.get('end')}]")
            
            # Check if filtering worked correctly
            expected_kept = ['6 feet']
            expected_filtered = ['1.8 meters']
            
            kept_texts = [e.get('text', '') for e in filtered_entities]
            
            print(f"\n📊 FILTERING ANALYSIS:")
            print("-" * 30)
            for expected in expected_kept:
                if expected in kept_texts:
                    print(f"  ✅ KEPT: '{expected}' (correct)")
                else:
                    print(f"  ❌ MISSING: '{expected}' (should be kept)")
            
            all_texts = [e.get('text', '') for e in measurement_entities]
            for expected in expected_filtered:
                if expected not in kept_texts and expected in all_texts:
                    print(f"  ✅ FILTERED: '{expected}' (correct)")
                elif expected in kept_texts:
                    print(f"  ❌ NOT FILTERED: '{expected}' (should be removed)")
                else:
                    print(f"  ❓ NOT FOUND: '{expected}' (not detected)")
            
            if len(filtered_entities) < len(measurement_entities):
                print(f"🟢 **SUCCESS**: Filtering removed {len(measurement_entities) - len(filtered_entities)} parenthetical measurements")
            else:
                print(f"🔴 **FAILED**: No measurements were filtered")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parenthetical_filter()