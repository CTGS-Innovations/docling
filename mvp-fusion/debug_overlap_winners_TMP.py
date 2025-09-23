#!/usr/bin/env python3
"""
GOAL: Find what longer entities are winning overlap conflicts and dropping our target entities
REASON: Deduplication working correctly in isolation but dropping entities in full document
PROBLEM: Need to see which entities are beating Texas, Florida, etc. in overlap detection
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def debug_overlap_winners():
    """Debug which entities are winning overlap conflicts"""
    
    print("🔍 DEBUGGING OVERLAP WINNERS IN DEDUPLICATION")
    print("=" * 60)
    
    # Load Core-8 automatons
    core8_corpus_loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = core8_corpus_loader.automatons['GPE']
    
    # Use full document content
    source_file = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_file, 'r') as f:
        content = f.read()
    
    print(f"📄 Document length: {len(content)} characters")
    
    # Extract all GPE entities
    raw_entities = []
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
    
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = content[start_pos:end_pos + 1]
        
        if len(original_text) > 2:
            entity = {
                'value': original_text,
                'span': {
                    'start': start_pos,
                    'end': end_pos + 1
                },
                'length': len(original_text),
                'is_target': any(target.lower() in original_text.lower() for target in target_entities)
            }
            raw_entities.append(entity)
    
    print(f"\n🔧 Raw entities analysis:")
    print(f"   Total entities: {len(raw_entities)}")
    target_raw = [e for e in raw_entities if e['is_target']]
    print(f"   Target entities: {len(target_raw)}")
    
    # Sort by length FIRST (longer first), then by position for ties
    sorted_entities = sorted(raw_entities, key=lambda e: (
        -e['length'],  # Length FIRST (longer first)
        e['span']['start']  # Position SECOND (earlier first for ties)
    ))
    
    print(f"\n🔧 Applying deduplication with detailed logging:")
    
    deduplicated = []
    seen_values = set()
    accepted_spans = []
    rejected_entities = []
    
    for i, entity in enumerate(sorted_entities):
        value = entity['value']
        span = entity['span']
        start = span['start']
        end = span['end']
        is_target = entity['is_target']
        
        # Skip if we've seen this exact value
        if value in seen_values:
            rejected_entities.append({
                'entity': entity,
                'reason': 'duplicate_value',
                'position_in_sort': i
            })
            continue
            
        # Check if this entity overlaps with ANY previously accepted entity
        overlaps = False
        overlapping_with = None
        for j, (accepted_start, accepted_end) in enumerate(accepted_spans):
            # True overlap: ranges intersect
            if start < accepted_end and end > accepted_start:
                overlaps = True
                overlapping_with = j
                break
        
        if overlaps:
            rejected_entities.append({
                'entity': entity,
                'reason': 'overlap',
                'overlapping_with': overlapping_with,
                'position_in_sort': i
            })
            continue
        
        # Accept this entity
        seen_values.add(value)
        deduplicated.append(entity)
        accepted_spans.append((start, end))
    
    print(f"\n📊 RESULTS:")
    print(f"   Accepted entities: {len(deduplicated)}")
    print(f"   Rejected entities: {len(rejected_entities)}")
    
    # Show rejected target entities
    rejected_targets = [r for r in rejected_entities if r['entity']['is_target']]
    print(f"\n❌ REJECTED TARGET ENTITIES ({len(rejected_targets)}):")
    
    for rejection in rejected_targets:
        entity = rejection['entity']
        reason = rejection['reason']
        pos = rejection['position_in_sort']
        span = entity['span']
        
        print(f"   {pos+1:2d}. '{entity['value']}' at {span['start']}-{span['end']} | Reason: {reason}")
        
        if reason == 'overlap':
            overlapping_index = rejection['overlapping_with']
            winning_entity = deduplicated[overlapping_index]
            winning_span = winning_entity['span']
            print(f"       Overlaps with: '{winning_entity['value']}' at {winning_span['start']}-{winning_span['end']} (len: {winning_entity['length']})")
    
    # Show what target entities survived
    surviving_targets = [e for e in deduplicated if e['is_target']]
    print(f"\n✅ SURVIVING TARGET ENTITIES ({len(surviving_targets)}):")
    for entity in surviving_targets:
        span = entity['span']
        print(f"   '{entity['value']}' at {span['start']}-{span['end']} (len: {entity['length']})")
    
    # Show longest entities (top 10)
    print(f"\n📏 LONGEST ENTITIES (top 10 - these win overlaps):")
    longest_entities = sorted(raw_entities, key=lambda e: -e['length'])[:10]
    for i, entity in enumerate(longest_entities):
        span = entity['span']
        target_marker = "🎯" if entity['is_target'] else "  "
        print(f"   {i+1:2d}. {target_marker} '{entity['value']}' at {span['start']}-{span['end']} (len: {entity['length']})")

if __name__ == "__main__":
    debug_overlap_winners()