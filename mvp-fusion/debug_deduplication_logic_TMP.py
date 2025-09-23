#!/usr/bin/env python3
"""
GOAL: Debug the exact deduplication logic behavior with real entity data
REASON: Entities detected (California, Texas, Florida) but only some make it through deduplication
PROBLEM: _deduplicate_entities dropping legitimate non-overlapping entities
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def simulate_deduplication_logic():
    """Simulate the exact deduplication logic from service_processor.py"""
    
    print("🔍 DEBUGGING DEDUPLICATION LOGIC")
    print("=" * 50)
    
    # Load corpus to get real detection data
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    # Use the exact problematic sentence
    test_text = "International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**."
    
    print(f"📝 Test text: {test_text}")
    print(f"   Length: {len(test_text)} characters")
    
    # Simulate raw entity extraction (what comes into deduplication)
    raw_entities = []
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(test_text.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = test_text[start_pos:end_pos + 1]
        
        # Only process meaningful entities (length > 2)
        if len(original_text) > 2:
            entity = {
                'value': original_text,
                'canonical': canonical,
                'type': 'GPE',
                'span': {
                    'start': start_pos,
                    'end': end_pos + 1
                },
                'length': len(original_text)
            }
            raw_entities.append(entity)
    
    print(f"\n🔍 Raw entities before deduplication ({len(raw_entities)} total):")
    for i, entity in enumerate(raw_entities):
        span = entity['span']
        print(f"   {i+1:2d}. '{entity['value']}' | span: {span['start']:3d}-{span['end']:3d} | len: {entity['length']:2d} | canonical: '{entity['canonical']}'")
    
    # Now apply the exact deduplication logic from service_processor.py
    print(f"\n🔧 APPLYING DEDUPLICATION LOGIC:")
    print(f"   Step 1: Sort by length (longer first), then position")
    
    # Sort by length FIRST (longer first), then by position for ties
    sorted_entities = sorted(raw_entities, key=lambda e: (
        -(e.get('span', {}).get('end', 0) - e.get('span', {}).get('start', 0)),  # Length FIRST (longer first)
        e.get('span', {}).get('start', 0)  # Position SECOND (earlier first for ties)
    ))
    
    print(f"\n   Sorted order:")
    for i, entity in enumerate(sorted_entities):
        span = entity['span']
        length = span['end'] - span['start']
        print(f"   {i+1:2d}. '{entity['value']}' | span: {span['start']:3d}-{span['end']:3d} | len: {length:2d}")
    
    # Apply deduplication step by step
    print(f"\n   Step 2: Apply deduplication logic:")
    deduplicated = []
    seen_values = set()
    accepted_spans = []
    
    for i, entity in enumerate(sorted_entities):
        value = entity.get('value', '')
        span = entity.get('span', {})
        start = span.get('start', 0)
        end = span.get('end', 0)
        
        print(f"\n   Processing entity {i+1}: '{value}' (span {start}-{end})")
        
        # Skip if we've seen this exact value
        if value in seen_values:
            print(f"     ❌ REJECTED: Duplicate value already seen")
            continue
            
        # Check if this entity overlaps with ANY previously accepted entity
        overlaps = False
        for j, (accepted_start, accepted_end) in enumerate(accepted_spans):
            # True overlap: ranges intersect
            if start < accepted_end and end > accepted_start:
                print(f"     ❌ REJECTED: Overlaps with accepted span {j+1} ({accepted_start}-{accepted_end})")
                overlaps = True
                break
        
        if overlaps:
            continue
        
        # Accept this entity
        print(f"     ✅ ACCEPTED: No overlap, adding to results")
        seen_values.add(value)
        deduplicated.append(entity)
        accepted_spans.append((start, end))
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Input entities: {len(raw_entities)}")
    print(f"   Deduplicated entities: {len(deduplicated)}")
    
    print(f"\n   Final entities that survived deduplication:")
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
    
    for entity in deduplicated:
        span = entity['span']
        print(f"     ✅ '{entity['value']}' | span: {span['start']:3d}-{span['end']:3d}")
    
    print(f"\n   Target entities status:")
    for target in target_entities:
        found = any(target.lower() in entity['value'].lower() for entity in deduplicated)
        status = "✅" if found else "❌"
        print(f"     {status} {target}")
    
    return raw_entities, deduplicated

if __name__ == "__main__":
    raw_entities, final_entities = simulate_deduplication_logic()