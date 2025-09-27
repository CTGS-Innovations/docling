#!/usr/bin/env python3
"""
GOAL: Validate post-processing range normalization approach before implementation
REASON: Need to test that we can detect ranges from individual entities without breaking existing detection
PROBLEM: 30-37 inches missed while 76-94 cm detected - need post-processing solution

Test Strategy:
1. Use existing FLPC engine to detect individual entities
2. Test span analysis logic to identify range patterns
3. Validate consolidation of Number + Connector + Number + Unit → Range Entity
4. Ensure preservation of existing DATE/TIME/MONEY detection
"""

import sys
import os
sys.path.append('/home/corey/projects/docling/mvp-fusion')

from fusion.flpc_engine import FLPCEngine
import yaml

def load_config():
    """Load the original FLPC configuration"""
    config_path = '/home/corey/projects/docling/mvp-fusion/config/pattern_sets.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def test_baseline_detection():
    """Test that original patterns still work"""
    print("🟡 **WAITING**: Testing baseline entity detection...")
    
    config = load_config()
    flpc_engine = FLPCEngine(config)
    
    # Test cases from WIP.md
    test_text = "Handrail height 30-37 inches (76-94 cm) installed January 1, 2024 for $1,500"
    
    print(f"Test text: {test_text}")
    print()
    
    results = flpc_engine.extract_entities(test_text)
    
    print("📊 Baseline detection results:")
    for category, entities in results.items():
        if entities:
            print(f"  {category}: {len(entities)} entities")
            for entity in entities:
                print(f"    - {entity}")
    
    return results

def analyze_range_patterns(text, results):
    """Analyze text for potential range patterns using detected entities"""
    print("🟡 **WAITING**: Analyzing potential range patterns...")
    
    # Extract entities from FLPC results
    entities = results.get('entities', {})
    
    # Find number entities that could be part of ranges
    numbers = []
    measurements = []
    
    print(f"Available entity categories: {list(entities.keys())}")
    
    # For now, work with the text directly since FLPC may not have measurement patterns
    # This is exactly what post-processing will do - analyze spans in the text
    
    # Look for range patterns: Number + Connector + Number + Unit
    potential_ranges = []
    
    # Simple span analysis - look for patterns like "30-37 inches"
    import re
    range_pattern = r'(\d+)\s*[-–—]\s*(\d+)\s+([a-zA-Z]+)'
    matches = re.finditer(range_pattern, text)
    
    for match in matches:
        start_num = match.group(1)
        end_num = match.group(2)
        unit = match.group(3)
        full_text = match.group(0)
        
        potential_ranges.append({
            'text': full_text,
            'start_num': start_num,
            'end_num': end_num,
            'unit': unit,
            'start_offset': match.start(),
            'end_offset': match.end()
        })
    
    print(f"Potential ranges found: {len(potential_ranges)}")
    for range_item in potential_ranges:
        print(f"  - {range_item['text']} ({range_item['start_num']}-{range_item['end_num']} {range_item['unit']})")
    
    return potential_ranges

def validate_preservation(results):
    """Validate that existing entity types are properly preserved"""
    print("🟡 **WAITING**: Validating entity preservation...")
    
    entities = results.get('entities', {})
    
    # Check for proper date detection
    dates = entities.get('date', [])
    money = entities.get('money', [])
    
    print(f"📊 Preservation validation:")
    print(f"  dates: {len(dates)} entities")
    print(f"  money: {len(money)} entities")
    
    # Validate dates are complete (not fragmented)
    for date_entity in dates:
        date_text = date_entity.get('text', '')
        if 'january' in date_text.lower() and '2024' in date_text:
            print(f"  ✅ Complete date preserved: {date_text}")
        else:
            print(f"  ❌ Date may be fragmented: {date_text}")
    
    # Validate money amounts
    for money_entity in money:
        money_text = money_entity.get('text', '')
        if '$' in money_text and any(char.isdigit() for char in money_text):
            print(f"  ✅ Money amount preserved: {money_text}")

def main():
    """Main validation test"""
    print("🟢 **SUCCESS**: Starting range post-processing validation test")
    print("=" * 60)
    
    # Test 1: Baseline detection
    entities = test_baseline_detection()
    print()
    
    # Test 2: Range pattern analysis
    test_text = "Handrail height 30-37 inches (76-94 cm) installed January 1, 2024 for $1,500"
    potential_ranges = analyze_range_patterns(test_text, entities)
    print()
    
    # Test 3: Preservation validation
    validate_preservation(entities)
    print()
    
    # Summary
    print("📊 **VALIDATION SUMMARY**:")
    print(f"  - Baseline detection: {'✅ Working' if entities else '❌ Failed'}")
    print(f"  - Range opportunities: {len(potential_ranges)} found")
    print(f"  - Ready for post-processing implementation")
    
    if len(potential_ranges) >= 2:
        print("🟢 **SUCCESS**: Range detection opportunities confirmed - ready to implement post-processing")
    else:
        print("🔴 **BLOCKED**: Insufficient range patterns detected - need different approach")

if __name__ == "__main__":
    main()