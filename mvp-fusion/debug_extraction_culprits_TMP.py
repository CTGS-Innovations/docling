#!/usr/bin/env python3
"""
GOAL: Systematically check each possible culprit in entity extraction
REASON: California detected, Texas/Florida missed from same sentence
PROBLEM: Need to isolate the exact cause of selective entity dropping
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def check_culprit_1_span_calculation():
    """Culprit 1: Span calculation bug with overlapping entities"""
    print("🔍 CULPRIT 1: Span Calculation & Overlapping Entities")
    print("-" * 60)
    
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    # Test the exact problematic sentence
    test_text = "International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**."
    
    print(f"📝 Test text: {test_text}")
    print(f"\n🔍 Raw detection with spans:")
    
    raw_detections = []
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(test_text.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = test_text[start_pos:end_pos + 1]
        
        detection = {
            'text': original_text,
            'canonical': canonical,
            'start': start_pos,
            'end': end_pos + 1,
            'length': len(original_text)
        }
        raw_detections.append(detection)
        print(f"   {original_text:15} | span: {start_pos:3}-{end_pos+1:3} | len: {len(original_text):2} | canonical: '{canonical}'")
    
    print(f"\n📊 Total raw detections: {len(raw_detections)}")
    
    # Check for overlapping spans
    print(f"\n🔍 Checking for overlapping spans:")
    overlaps = []
    for i, det1 in enumerate(raw_detections):
        for j, det2 in enumerate(raw_detections[i+1:], i+1):
            # Check if spans overlap
            if not (det1['end'] <= det2['start'] or det2['end'] <= det1['start']):
                overlap = {
                    'entity1': det1['text'],
                    'entity2': det2['text'],
                    'span1': f"{det1['start']}-{det1['end']}",
                    'span2': f"{det2['start']}-{det2['end']}"
                }
                overlaps.append(overlap)
                print(f"   ⚠️  OVERLAP: '{det1['text']}' ({det1['start']}-{det1['end']}) vs '{det2['text']}' ({det2['start']}-{det2['end']})")
    
    if not overlaps:
        print(f"   ✅ No overlapping spans found")
    
    return raw_detections, overlaps

def check_culprit_2_deduplication():
    """Culprit 2: Deduplication logic filtering out legitimate entities"""
    print(f"\n🔍 CULPRIT 2: Deduplication Logic")
    print("-" * 60)
    
    # Simulate the deduplication logic from service_processor.py
    # Let me check what _deduplicate_entities does
    print("   📋 Need to test deduplication logic from service processor")
    print("   📋 This requires checking _deduplicate_entities method behavior")
    return True

def check_culprit_3_length_filtering():
    """Culprit 3: Length filtering failing entities"""
    print(f"\n🔍 CULPRIT 3: Length Filtering (len > 2)")
    print("-" * 60)
    
    raw_detections, _ = check_culprit_1_span_calculation()
    
    print(f"\n🔍 Applying length filter (len > 2):")
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada']
    
    for detection in raw_detections:
        passes_filter = len(detection['text']) > 2
        is_target = any(target.lower() in detection['text'].lower() for target in target_entities)
        
        if is_target:
            status = "✅" if passes_filter else "❌"
            print(f"   {status} '{detection['text']}' (len: {detection['length']}) - {'PASS' if passes_filter else 'FAIL'}")
    
    return True

def check_culprit_4_text_preprocessing():
    """Culprit 4: Text preprocessing modifying content"""
    print(f"\n🔍 CULPRIT 4: Text Preprocessing")
    print("-" * 60)
    
    # Test different versions of the text to see if preprocessing changes results
    test_variations = [
        ("Original", "International presence in: **California**, **Texas**, **Florida**"),
        ("Lowercase", "international presence in: **california**, **texas**, **florida**"),
        ("No markdown", "International presence in: California, Texas, Florida"),
        ("Extra spaces", "International  presence  in:  **California**,  **Texas**,  **Florida**"),
    ]
    
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    for variation_name, text in test_variations:
        print(f"\n   📝 {variation_name}: {text}")
        detections = []
        
        for end_pos, (entity_type, canonical) in gpe_automaton.iter(text.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = text[start_pos:end_pos + 1]
            if len(original_text) > 2:
                detections.append(original_text)
        
        target_found = [d for d in detections if d.lower() in ['california', 'texas', 'florida']]
        print(f"      Found targets: {target_found}")
    
    return True

def main():
    print("🎯 SYSTEMATIC CULPRIT ANALYSIS")
    print("=" * 70)
    
    # Check each culprit systematically
    raw_detections, overlaps = check_culprit_1_span_calculation()
    check_culprit_2_deduplication()
    check_culprit_3_length_filtering()
    check_culprit_4_text_preprocessing()
    
    print(f"\n🎯 SUMMARY:")
    print(f"   Raw detections found: {len(raw_detections)}")
    print(f"   Overlapping spans: {len(overlaps) if 'overlaps' in locals() else 0}")
    print(f"   Ready for next culprit investigation...")

if __name__ == "__main__":
    main()