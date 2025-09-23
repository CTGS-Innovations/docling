#!/usr/bin/env python3
"""
GOAL: Test the exact GPE extraction logic from _extract_universal_entities
REASON: This method should find all entities but something is failing  
PROBLEM: Need to test lines 494-523 of service_processor.py exactly
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def test_exact_gpe_extraction():
    """Test the exact GPE extraction logic from the service processor"""
    
    print("🔍 TESTING EXACT GPE EXTRACTION LOGIC")
    print("=" * 50)
    
    # Load Core-8 automatons (same as service processor)
    core8_corpus_loader = Core8CorpusLoader(verbose=False)
    core8_automatons = core8_corpus_loader.automatons
    
    # Use full document content
    source_file = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_file, 'r') as f:
        content = f.read()
    
    print(f"📄 Document length: {len(content)} characters")
    
    # Extract GPE entities using Core-8 automaton (EXACT logic from service processor)
    entities_gpe = []
    if 'GPE' in core8_automatons:
        print(f"\n🔧 Running exact GPE extraction logic...")
        try:
            gpe_automaton = core8_automatons['GPE']
            target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
            
            print(f"   Processing with Aho-Corasick automaton...")
            raw_entities = []
            
            for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
                start_pos = end_pos - len(canonical) + 1
                # Get original text from content
                original_text = content[start_pos:end_pos + 1]
                
                # Only add if it's a reasonable match (not single letters, etc.)
                if len(original_text) > 2:
                    # Get subcategory metadata
                    subcategory = None
                    if hasattr(core8_corpus_loader, 'get_subcategory'):
                        subcategory = core8_corpus_loader.get_subcategory('GPE', original_text)
                    
                    entity = {
                        'value': original_text,
                        'text': original_text,
                        'type': 'GPE',
                        'span': {
                            'start': start_pos,
                            'end': end_pos + 1
                        }
                    }
                    
                    # Add subcategory metadata if available
                    if subcategory:
                        entity['metadata'] = {'subcategory': subcategory}
                    
                    raw_entities.append(entity)
            
            print(f"   Raw entities before deduplication: {len(raw_entities)}")
            
            # Show target entities found
            target_found = [e for e in raw_entities if any(target.lower() in e['value'].lower() for target in target_entities)]
            print(f"   Target entities found: {len(target_found)}")
            for entity in target_found:
                span = entity['span']
                print(f"     - '{entity['value']}' at {span['start']}-{span['end']}")
            
            # Apply deduplication (EXACT logic from service processor)
            def _deduplicate_entities(entities):
                """Same deduplication logic as service processor"""
                if not entities:
                    return []
                
                # Sort by length FIRST (longer first), then by position for ties
                sorted_entities = sorted(entities, key=lambda e: (
                    -(e.get('span', {}).get('end', 0) - e.get('span', {}).get('start', 0)),  # Length FIRST (longer first)
                    e.get('span', {}).get('start', 0)  # Position SECOND (earlier first for ties)
                ))
                
                deduplicated = []
                seen_values = set()
                accepted_spans = []  # Track all accepted spans for overlap checking
                
                for entity in sorted_entities:
                    value = entity.get('value', '')
                    span = entity.get('span', {})
                    start = span.get('start', 0)
                    end = span.get('end', 0)
                    
                    # Skip if we've seen this exact value
                    if value in seen_values:
                        continue
                        
                    # Check if this entity overlaps with ANY previously accepted entity
                    overlaps = False
                    for accepted_start, accepted_end in accepted_spans:
                        # True overlap: ranges intersect
                        if start < accepted_end and end > accepted_start:
                            overlaps = True
                            break
                    
                    if overlaps:
                        continue
                    
                    seen_values.add(value)
                    deduplicated.append(entity)
                    accepted_spans.append((start, end))
                
                return deduplicated
            
            # Deduplicate and limit
            entities_gpe = _deduplicate_entities(raw_entities)[:20]
            print(f"\n   After deduplication: {len(entities_gpe)} entities")
            
            # Check target entities in final result
            final_target_found = [e for e in entities_gpe if any(target.lower() in e['value'].lower() for target in target_entities)]
            print(f"   Target entities in final result: {len(final_target_found)}")
            for entity in final_target_found:
                span = entity['span']
                print(f"     ✅ '{entity['value']}' at {span['start']}-{span['end']}")
            
            # Check what targets are missing
            missing_targets = []
            for target in target_entities:
                found = any(target.lower() in entity['value'].lower() for entity in entities_gpe)
                if not found:
                    missing_targets.append(target)
            
            if missing_targets:
                print(f"\n   ❌ MISSING from final result: {', '.join(missing_targets)}")
            else:
                print(f"\n   🎯 ALL targets found in final result!")
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            entities_gpe = []
    else:
        print(f"   ❌ No GPE automaton found")
        entities_gpe = []
    
    print(f"\n📊 SUMMARY:")
    print(f"   Final GPE entities: {len(entities_gpe)}")
    
    return entities_gpe

if __name__ == "__main__":
    test_exact_gpe_extraction()