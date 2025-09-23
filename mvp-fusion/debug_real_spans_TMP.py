#!/usr/bin/env python3
"""
GOAL: Debug the exact spans being processed in the real document
REASON: California detected (span 1141-1151) but Texas/Florida not detected
PROBLEM: Need to see what text is at those exact spans
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def debug_real_document_spans():
    """Debug the exact document content and spans"""
    
    print("🔍 DEBUGGING REAL DOCUMENT SPANS")
    print("=" * 50)
    
    # Read the actual source document
    with open('/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md', 'r') as f:
        content = f.read()
    
    print(f"📄 Document length: {len(content)} characters")
    
    # Check the California span that WAS detected (1141-1151)
    california_span = content[1141:1151]
    print(f"\n✅ Detected California span (1141-1151): '{california_span}'")
    
    # Look at context around California
    context_start = max(0, 1141 - 100)
    context_end = min(len(content), 1151 + 100)
    context = content[context_start:context_end]
    print(f"📝 Context around California:")
    print(f"   {context}")
    
    # Now let's run entity detection on the whole document
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    print(f"\n🔍 Running GPE detection on full document:")
    
    detected_entities = []
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
    
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = content[start_pos:end_pos + 1]
        
        # Only show entities longer than 2 chars that are our targets
        if len(original_text) > 2 and any(target.lower() in original_text.lower() for target in target_entities):
            detected_entities.append({
                'text': original_text,
                'canonical': canonical,
                'start': start_pos,
                'end': end_pos + 1,
                'span_text': content[start_pos:end_pos + 1]
            })
            print(f"   Found: '{original_text}' at span {start_pos}-{end_pos+1}")
    
    print(f"\n📊 Target entity detection summary:")
    for target in target_entities:
        found = any(target.lower() == det['text'].lower() for det in detected_entities)
        status = "✅" if found else "❌"
        print(f"   {status} {target}")
    
    # Check if multiple spans exist for same entities
    print(f"\n🔍 Multiple spans check:")
    entity_spans = {}
    for det in detected_entities:
        entity_name = det['text'].lower()
        if entity_name not in entity_spans:
            entity_spans[entity_name] = []
        entity_spans[entity_name].append(f"{det['start']}-{det['end']}")
    
    for entity, spans in entity_spans.items():
        if len(spans) > 1:
            print(f"   📍 {entity}: {len(spans)} occurrences at {spans}")
        else:
            print(f"   📍 {entity}: 1 occurrence at {spans[0]}")

if __name__ == "__main__":
    debug_real_document_spans()