#!/usr/bin/env python3
"""
GOAL: Test the exact same GPE extraction that the real pipeline uses
REASON: Our isolated test found all entities but real pipeline missing some
PROBLEM: Need to exactly replicate ServiceProcessor._extract_universal_entities GPE logic
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.service_processor import ServiceProcessor
import yaml

def test_real_pipeline_gpe():
    """Test the exact GPE extraction logic used by the real pipeline"""
    
    print("🔍 TESTING REAL PIPELINE GPE EXTRACTION")
    print("=" * 50)
    
    # Load the EXACT same config the real pipeline uses
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize ServiceProcessor exactly like the real pipeline
    processor = ServiceProcessor(config)
    
    # Use the exact same document
    source_file = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_file, 'r') as f:
        content = f.read()
    
    print(f"📄 Document length: {len(content)} characters")
    
    # Call the EXACT method the real pipeline uses but let's debug the GPE section
    print(f"\n🔧 Testing GPE extraction with truncation analysis:")
    
    # Get the automaton exactly like the real pipeline
    gpe_automaton = processor.core8_automatons['GPE']
    
    # Extract all raw GPE entities (before deduplication and truncation)
    raw_entities = []
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = content[start_pos:end_pos + 1]
        
        if len(original_text) > 2:
            entity = {
                'value': original_text,
                'text': original_text,
                'type': 'GPE',
                'span': {
                    'start': start_pos,
                    'end': end_pos + 1
                },
                'length': len(original_text)
            }
            raw_entities.append(entity)
    
    print(f"   Raw entities before deduplication: {len(raw_entities)}")
    
    # Apply deduplication (same as real pipeline)
    deduplicated = processor._deduplicate_entities(raw_entities)
    print(f"   After deduplication: {len(deduplicated)}")
    
    # Apply [:50] truncation (updated real pipeline limit)
    truncated = deduplicated[:50]
    print(f"   After [:50] truncation: {len(truncated)}")
    
    entities = {'gpe': truncated}
    
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
    
    # Check GPE entities
    gpe_entities = entities.get('gpe', [])
    print(f"\n📊 GPE entities found: {len(gpe_entities)}")
    
    target_found = []
    for entity in gpe_entities:
        value = entity.get('value', '')
        span = entity.get('span', {})
        print(f"   - '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
        
        # Check if this is a target entity
        if any(target.lower() in value.lower() for target in target_entities):
            target_found.append(value)
    
    print(f"\n🎯 Target entities found: {len(target_found)}")
    for target in target_found:
        print(f"   ✅ {target}")
    
    print(f"\n❌ Missing target entities:")
    missing = [target for target in target_entities if not any(target.lower() in found.lower() for found in target_found)]
    for target in missing:
        print(f"   ❌ {target}")
    
    # Compare with our isolated test results
    print(f"\n📊 COMPARISON:")
    print(f"   Real pipeline: {len(target_found)} target entities")
    print(f"   Expected (from our tests): 8-9 target entities")
    
    if len(target_found) < 8:
        print(f"\n🚨 CONFIRMED: Real pipeline is dropping entities!")
        print(f"   Expected: 8-9 entities")
        print(f"   Actual: {len(target_found)} entities")
        print(f"   Loss: {8 - len(target_found)} entities")
    
    return entities

if __name__ == "__main__":
    test_real_pipeline_gpe()