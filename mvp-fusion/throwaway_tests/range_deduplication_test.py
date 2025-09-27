#!/usr/bin/env python3
"""
Range Deduplication Test
========================

GOAL: Test range deduplication logic in ServiceProcessor
REASON: Fixed range detection but need to verify individual measurements are removed
PROBLEM: Should see ranges only, no overlapping individual measurements

Expected Results:
- "Growth projection: 10-15% range" → ||10-15%||range001|| (NOT 10-||15%||)
- "Temperature range -20°F to 120°F" → ||-20°F to 120°F||range002|| (NOT separate measurements)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_range_deduplication():
    """Test ServiceProcessor range deduplication"""
    print("🔍 RANGE DEDUPLICATION TEST")
    print("=" * 50)
    print("Testing range-first precedence in ServiceProcessor")
    print()
    
    # Test the deduplication method directly
    print("📊 STEP 1: Direct Method Test")
    print("-" * 30)
    
    # Import ServiceProcessor
    from pipeline.legacy.service_processor import ServiceProcessor
    
    # Create mock data
    measurements = [
        {'text': '15%', 'type': 'MEASUREMENT'},
        {'text': '20°F', 'type': 'MEASUREMENT'},
        {'text': '120°F', 'type': 'MEASUREMENT'},
        {'text': '30 inches', 'type': 'MEASUREMENT'},  # Should NOT be removed
        {'text': '10%', 'type': 'MEASUREMENT'}
    ]
    
    ranges = [
        {'text': '10-15%', 'type': 'RANGE'},
        {'text': '-20°F to 120°F', 'type': 'RANGE'}
    ]
    
    # Create processor instance (minimal config)
    import yaml
    from pathlib import Path
    config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    processor = ServiceProcessor(config)
    
    # Test deduplication
    print(f"Before deduplication:")
    print(f"  Measurements: {[m['text'] for m in measurements]}")
    print(f"  Ranges: {[r['text'] for r in ranges]}")
    
    filtered = processor._deduplicate_measurements_from_ranges(measurements, ranges)
    
    print(f"After deduplication:")
    print(f"  Measurements: {[m['text'] for m in filtered]}")
    print(f"  Ranges: {[r['text'] for r in ranges]} (unchanged)")
    
    # Verify results
    filtered_texts = [m['text'] for m in filtered]
    if '15%' not in filtered_texts and '20°F' not in filtered_texts and '120°F' not in filtered_texts and '10%' not in filtered_texts:
        if '30 inches' in filtered_texts:
            print("✅ PERFECT: Range components removed, independent measurements kept")
        else:
            print("❌ ERROR: Independent measurement incorrectly removed")
    else:
        print("❌ FAILED: Range components not properly removed")
    
    # Test with real ServiceProcessor extraction
    print("\n📊 STEP 2: Full Pipeline Test")
    print("-" * 30)
    
    test_content = "Growth projection: 10-15% range. Temperature varies from -20°F to 120°F. Height is 30 inches."
    print(f"Test content: \"{test_content}\"")
    
    try:
        entities = processor._extract_universal_entities(test_content)
        
        print(f"📋 Extracted entities:")
        for entity_type, entity_list in entities.items():
            if entity_list:
                entity_texts = [e.get('text', str(e)) for e in entity_list]
                print(f"  {entity_type.upper()}: {entity_texts}")
        
        # Check results
        measurements = entities.get('measurement', [])
        ranges = entities.get('range', [])
        
        measurement_texts = [m.get('text', '') for m in measurements]
        range_texts = [r.get('text', '') for r in ranges]
        
        print(f"\n🎯 ANALYSIS:")
        if '10-15%' in range_texts and '-20°F to 120°F' in range_texts:
            print("✅ Ranges detected correctly")
        else:
            print("❌ Ranges not detected")
            
        if not any(text in measurement_texts for text in ['15%', '20°F', '120°F', '10%']):
            print("✅ Range components removed from measurements")
        else:
            print("❌ Range components still in measurements")
            
        if '30 inches' in measurement_texts:
            print("✅ Independent measurements preserved")
        else:
            print("❌ Independent measurements incorrectly removed")
            
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")

if __name__ == "__main__":
    print("# GOAL: Test range deduplication in ServiceProcessor")
    print("# REASON: Implemented range-first precedence logic")
    print("# PROBLEM: Verify overlapping measurements are removed")
    print()
    
    test_range_deduplication()
    
    print("\n🎯 Expected outcome: Clean ranges with no overlapping individual measurements")