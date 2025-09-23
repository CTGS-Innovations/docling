#!/usr/bin/env python3
"""
GOAL: Debug the complete pipeline flow to find where entities are being lost
REASON: Deduplication logic works fine, entities lost somewhere else in pipeline
PROBLEM: Need to trace entities through each pipeline stage
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.service_processor import ServiceProcessor
from utils.core8_corpus_loader import Core8CorpusLoader

def debug_complete_pipeline():
    """Debug entities through the complete pipeline flow"""
    
    print("🔍 DEBUGGING COMPLETE PIPELINE FLOW")
    print("=" * 60)
    
    # Read the actual source document
    source_file = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_file, 'r') as f:
        content = f.read()
    
    print(f"📄 Source document: {len(content)} characters")
    
    # Load proper config
    import yaml
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    processor = ServiceProcessor(config)
    
    print(f"\n🔧 Testing raw entity extraction methods:")
    
    # Test 1: Direct automaton extraction (what we know works)
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada']
    direct_entities = []
    
    print(f"\n   1️⃣ Direct automaton extraction:")
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(content.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = content[start_pos:end_pos + 1]
        
        if len(original_text) > 2 and any(target.lower() in original_text.lower() for target in target_entities):
            direct_entities.append({
                'text': original_text,
                'canonical': canonical,
                'start': start_pos,
                'end': end_pos + 1
            })
    
    print(f"      Found {len(direct_entities)} target entities")
    for entity in direct_entities[:10]:  # Show first 10
        print(f"        - '{entity['text']}' at {entity['start']}-{entity['end']}")
    
    # Test 2: Processor's sentence-based extraction
    print(f"\n   2️⃣ Processor sentence-based extraction:")
    try:
        sentence_entities = processor._extract_entities_sentence_based(content, 'GPE')
        target_sentence_entities = [e for e in sentence_entities if any(target.lower() in e.get('value', '').lower() for target in target_entities)]
        
        print(f"      Found {len(target_sentence_entities)} target entities from sentences")
        for entity in target_sentence_entities[:10]:  # Show first 10
            span = entity.get('span', {})
            print(f"        - '{entity.get('value', '')}' at {span.get('start', 0)}-{span.get('end', 0)}")
    
    except Exception as e:
        print(f"      ❌ ERROR: {e}")
    
    # Test 3: Full entity extraction process
    print(f"\n   3️⃣ Full entity extraction process:")
    try:
        full_entities = processor._extract_entities(content)
        gpe_entities = [e for e in full_entities if e.get('type') == 'GPE']
        target_full_entities = [e for e in gpe_entities if any(target.lower() in e.get('value', '').lower() for target in target_entities)]
        
        print(f"      Total GPE entities: {len(gpe_entities)}")
        print(f"      Target GPE entities: {len(target_full_entities)}")
        for entity in target_full_entities[:10]:  # Show first 10
            span = entity.get('span', {})
            print(f"        - '{entity.get('value', '')}' at {span.get('start', 0)}-{span.get('end', 0)}")
    
    except Exception as e:
        print(f"      ❌ ERROR: {e}")
    
    # Test 4: Check for specific problematic sentence
    problematic_sentence = "International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**."
    sentence_start = content.find(problematic_sentence)
    
    if sentence_start >= 0:
        print(f"\n   4️⃣ Problematic sentence analysis:")
        print(f"      Found at position: {sentence_start}")
        print(f"      Sentence: {problematic_sentence}")
        
        # Extract entities just from this sentence
        sentence_entities = processor._extract_entities_sentence_based(problematic_sentence, 'GPE')
        print(f"      Entities from this sentence: {len(sentence_entities)}")
        
        for entity in sentence_entities:
            span = entity.get('span', {})
            print(f"        - '{entity.get('value', '')}' at {span.get('start', 0)}-{span.get('end', 0)}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Direct automaton: {len(direct_entities)} target entities")
    print(f"   Sentence-based: {len(target_sentence_entities) if 'target_sentence_entities' in locals() else 'ERROR'}")
    print(f"   Full extraction: {len(target_full_entities) if 'target_full_entities' in locals() else 'ERROR'}")

if __name__ == "__main__":
    debug_complete_pipeline()