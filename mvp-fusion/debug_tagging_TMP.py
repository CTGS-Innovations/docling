#!/usr/bin/env python3
"""
GOAL: Debug why detected entities aren't getting tagged in final output
REASON: California, Texas, Florida are detected but not tagged as ||California||gpe###||
PROBLEM: Gap between detection and tagging/replacement phase
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def debug_tagging_issue():
    """Test the gap between detection and tagging"""
    
    print("🔍 DEBUGGING TAGGING ISSUE")
    print("=" * 40)
    
    # Load corpus
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    # Test the exact text from the output file
    test_text = "International presence in: California, Texas, Florida, United States, Canada, United Kingdom, Germany, Japan, Australia, and Brazil."
    
    print(f"📝 Test text: {test_text}")
    print(f"🔍 Raw GPE detection:")
    
    # Simulate the exact detection logic from service_processor.py
    detected_entities = []
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(test_text.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = test_text[start_pos:end_pos + 1]
        detected_entities.append({
            'text': original_text,
            'canonical': canonical,
            'start': start_pos,
            'end': end_pos + 1,
            'type': 'GPE'
        })
        print(f"   Detected: '{original_text}' at {start_pos}-{end_pos+1} (canonical: '{canonical}')")
    
    print(f"\n📊 Summary:")
    print(f"   Total detected: {len(detected_entities)}")
    
    # Check specific entities
    key_entities = ['California', 'Texas', 'Florida', 'United States', 'Canada', 'Germany', 'Japan']
    for entity in key_entities:
        found = any(e['text'] == entity for e in detected_entities)
        status = "✅" if found else "❌"
        print(f"   {status} {entity}")
    
    # Show what would need to be tagged
    print(f"\n🏷️  What should be tagged:")
    for i, entity in enumerate(detected_entities):
        tag_id = f"gpe{i+1:03d}"
        tagged_version = f"||{entity['text']}||{tag_id}||"
        print(f"   '{entity['text']}' → '{tagged_version}'")

if __name__ == "__main__":
    debug_tagging_issue()