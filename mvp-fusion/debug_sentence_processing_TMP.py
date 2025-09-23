#!/usr/bin/env python3
"""
GOAL: Test if sentence-based processing is dropping multiple GPEs from same sentence
REASON: User suspects detection algorithm can't handle multiple GPEs per sentence
PROBLEM: The problematic sentence has 8+ countries/states in one line
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.service_processor import ServiceProcessor
from utils.core8_corpus_loader import Core8CorpusLoader

def test_sentence_vs_document_level():
    """Compare sentence-based vs document-level entity extraction"""
    
    print("🔍 TESTING SENTENCE vs DOCUMENT LEVEL GPE EXTRACTION")
    print("=" * 60)
    
    # The problematic sentence
    problematic_sentence = "International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**."
    
    print(f"📝 Test sentence: {problematic_sentence}")
    print(f"   Length: {len(problematic_sentence)} characters")
    
    # Load proper config for ServiceProcessor
    import yaml
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    processor = ServiceProcessor(config)
    
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'Australia', 'Brazil']
    
    print(f"\n🔧 TEST 1: Sentence-based extraction (processor method)")
    try:
        sentence_entities = processor._extract_entities_sentence_based(problematic_sentence, 'GPE')
        sentence_targets = [e for e in sentence_entities if any(target.lower() in e.get('value', '').lower() for target in target_entities)]
        
        print(f"   Total GPE entities from sentence: {len(sentence_entities)}")
        print(f"   Target entities found: {len(sentence_targets)}")
        for entity in sentence_targets:
            span = entity.get('span', {})
            print(f"     - '{entity.get('value', '')}' at {span.get('start', 0)}-{span.get('end', 0)}")
    
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        sentence_targets = []
    
    print(f"\n🔧 TEST 2: Document-level extraction (processor method)")
    try:
        document_entities = processor._extract_entities_document_level(problematic_sentence, 'GPE')
        document_targets = [e for e in document_entities if any(target.lower() in e.get('value', '').lower() for target in target_entities)]
        
        print(f"   Total GPE entities from document-level: {len(document_entities)}")
        print(f"   Target entities found: {len(document_targets)}")
        for entity in document_targets:
            span = entity.get('span', {})
            print(f"     - '{entity.get('value', '')}' at {span.get('start', 0)}-{span.get('end', 0)}")
    
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        document_targets = []
    
    print(f"\n🔧 TEST 3: Direct automaton (baseline - should work)")
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    direct_targets = []
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(problematic_sentence.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = problematic_sentence[start_pos:end_pos + 1]
        
        if len(original_text) > 2 and any(target.lower() in original_text.lower() for target in target_entities):
            direct_targets.append({
                'text': original_text,
                'start': start_pos,
                'end': end_pos + 1
            })
    
    print(f"   Direct automaton target entities: {len(direct_targets)}")
    for entity in direct_targets:
        print(f"     - '{entity['text']}' at {entity['start']}-{entity['end']}")
    
    print(f"\n📊 COMPARISON SUMMARY:")
    print(f"   Direct automaton (baseline): {len(direct_targets)} target entities")
    print(f"   Sentence-based processing: {len(sentence_targets)} target entities")
    print(f"   Document-level processing: {len(document_targets)} target entities")
    
    # Check if sentence-based is the bottleneck
    if len(direct_targets) > len(sentence_targets):
        print(f"\n🚨 BOTTLENECK IDENTIFIED: Sentence-based processing is dropping entities!")
        print(f"   Expected: {len(direct_targets)} entities")
        print(f"   Actual: {len(sentence_targets)} entities")
        print(f"   Loss: {len(direct_targets) - len(sentence_targets)} entities")
    elif len(sentence_targets) == len(direct_targets):
        print(f"\n✅ Sentence-based processing works correctly")
    
    return {
        'direct': len(direct_targets),
        'sentence': len(sentence_targets) if 'sentence_targets' in locals() else 0,
        'document': len(document_targets) if 'document_targets' in locals() else 0
    }

if __name__ == "__main__":
    test_sentence_vs_document_level()