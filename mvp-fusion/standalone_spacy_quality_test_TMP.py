#!/usr/bin/env python3
"""
Standalone spaCy Quality Test
============================
GOAL: Test if spaCy's full NLP pipeline provides significantly better entity detection
REASON: User wants to know if spaCy can achieve ~95% quality vs AC/FLPC approach  
PROBLEM: Need to evaluate spaCy NER quality vs performance trade-off

This test compares:
1. Current AC automaton approach
2. spaCy's built-in NER 
3. Hybrid approach (AC + spaCy gap filling)
4. Quality metrics for each approach
"""

import time
import spacy
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

def load_test_document() -> str:
    """Load the test document."""
    doc_path = Path("/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_TXT_DOCUMENT.txt")
    with open(doc_path, 'r') as f:
        return f.read()

def test_ac_automaton_approach(content: str) -> Tuple[List[Dict], float]:
    """Test current AC automaton approach."""
    print("🟡 **WAITING**: Testing AC automaton approach...")
    
    try:
        # Import our current system
        import sys
        sys.path.append('.')
        from utils.core8_corpus_loader import Core8CorpusLoader
        
        start_time = time.perf_counter()
        loader = Core8CorpusLoader(verbose=False)
        
        # Extract ORG entities using AC
        org_results = loader.search(content, 'ORG')
        org_entities = org_results.get('ORG', [])
        
        # Convert to standard format
        entities = []
        for entity in org_entities:
            entities.append({
                'text': entity['text'],
                'label': 'ORG', 
                'start': entity['start'],
                'end': entity['end'],
                'source': 'AC_automaton'
            })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: AC automaton completed")
        print(f"   Time: {processing_time:.2f}ms")
        print(f"   Entities: {len(entities)}")
        
        return entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: AC automaton test failed: {e}")
        return [], 0

def test_spacy_ner_approach(content: str) -> Tuple[List[Dict], float]:
    """Test spaCy's built-in NER approach."""
    print("\n🟡 **WAITING**: Testing spaCy NER approach...")
    
    try:
        start_time = time.perf_counter()
        
        # Load full spaCy model with NER
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(content)
        
        # Extract entities from spaCy NER
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'source': 'spaCy_NER'
            })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: spaCy NER completed")
        print(f"   Time: {processing_time:.2f}ms")  
        print(f"   Entities: {len(entities)}")
        
        return entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: spaCy NER test failed: {e}")
        return [], 0

def test_hybrid_approach(content: str, ac_entities: List[Dict]) -> Tuple[List[Dict], float]:
    """Test hybrid approach: AC + spaCy for gaps."""
    print("\n🟡 **WAITING**: Testing hybrid approach (AC + spaCy gaps)...")
    
    try:
        start_time = time.perf_counter()
        
        # Get spaCy entities
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(content)
        
        # Combine AC entities with spaCy entities
        all_entities = ac_entities.copy()
        
        # Add spaCy entities that don't overlap with AC entities
        ac_spans = {(e['start'], e['end']) for e in ac_entities}
        
        for ent in doc.ents:
            # Check if this spaCy entity overlaps with any AC entity
            overlaps = False
            for ac_start, ac_end in ac_spans:
                if ent.start_char < ac_end and ent.end_char > ac_start:
                    overlaps = True
                    break
            
            if not overlaps:
                all_entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'source': 'spaCy_gap_fill'
                })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: Hybrid approach completed")
        print(f"   Time: {processing_time:.2f}ms")
        print(f"   Entities: {len(all_entities)}")
        
        return all_entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Hybrid approach test failed: {e}")
        return ac_entities, 0

def analyze_entity_quality(entities: List[Dict], approach_name: str) -> Dict:
    """Analyze the quality of detected entities."""
    print(f"\n📊 QUALITY ANALYSIS: {approach_name}")
    print("=" * 50)
    
    # Group by entity type
    by_type = defaultdict(list)
    for entity in entities:
        by_type[entity['label']].append(entity)
    
    # Known high-quality entities we expect to find
    expected_orgs = [
        "Stanford University",
        "Harvard Business School", 
        "Johns Hopkins University",
        "Massachusetts Institute of Technology",
        "Microsoft Corporation",
        "Tesla, Inc.",
        "Apple Inc.",
        "Google LLC"
    ]
    
    # Check detection of expected entities
    found_expected = []
    entity_texts = [e['text'].lower() for e in entities]
    
    for expected in expected_orgs:
        if expected.lower() in entity_texts:
            found_expected.append(expected)
    
    detection_rate = len(found_expected) / len(expected_orgs) * 100
    
    # Show results
    print(f"📈 Entity Distribution:")
    for label, ents in sorted(by_type.items()):
        print(f"   {label}: {len(ents)} entities")
    
    print(f"\n🎯 Expected Organization Detection:")
    print(f"   Found: {len(found_expected)}/{len(expected_orgs)} ({detection_rate:.1f}%)")
    for org in found_expected:
        print(f"   ✅ {org}")
    
    missing = set(expected_orgs) - set(found_expected)
    if missing:
        print(f"\n❌ Missing Expected Entities:")
        for org in missing:
            print(f"   ❌ {org}")
    
    # Show interesting entities found
    org_entities = [e for e in entities if e['label'] in ['ORG', 'ORGANIZATION']]
    interesting_orgs = [e for e in org_entities if len(e['text']) > 10 and 'university' in e['text'].lower() or 'corporation' in e['text'].lower()]
    
    if interesting_orgs:
        print(f"\n🔍 Sample High-Quality Organizations:")
        for entity in interesting_orgs[:10]:
            print(f"   - \"{entity['text']}\" ({entity['source']})")
    
    return {
        'total_entities': len(entities),
        'detection_rate': detection_rate,
        'found_expected': len(found_expected),
        'by_type': dict(by_type),
        'entity_texts': entity_texts
    }

def main():
    """Run the standalone spaCy quality test."""
    print("🚀 STANDALONE SPACY QUALITY TEST")
    print("=" * 80)
    print("Testing entity detection quality: AC vs spaCy vs Hybrid")
    print()
    
    # Load test document
    content = load_test_document()
    print(f"📄 Test document: {len(content)} characters")
    
    # Test 1: Current AC automaton approach
    ac_entities, ac_time = test_ac_automaton_approach(content)
    ac_quality = analyze_entity_quality(ac_entities, "AC Automaton")
    
    # Test 2: spaCy NER approach  
    spacy_entities, spacy_time = test_spacy_ner_approach(content)
    spacy_quality = analyze_entity_quality(spacy_entities, "spaCy NER")
    
    # Test 3: Hybrid approach
    hybrid_entities, hybrid_time = test_hybrid_approach(content, ac_entities)
    hybrid_quality = analyze_entity_quality(hybrid_entities, "Hybrid (AC + spaCy)")
    
    # Final comparison
    print("\n🏆 FINAL COMPARISON")
    print("=" * 80)
    
    approaches = [
        ("AC Automaton", ac_quality, ac_time),
        ("spaCy NER", spacy_quality, spacy_time), 
        ("Hybrid", hybrid_quality, hybrid_time)
    ]
    
    for name, quality, timing in approaches:
        print(f"\n📊 {name}:")
        print(f"   Time: {timing:.2f}ms")
        print(f"   Entities: {quality['total_entities']}")
        print(f"   Detection Rate: {quality['detection_rate']:.1f}%")
        print(f"   Quality Score: {quality['detection_rate'] * (quality['total_entities'] / 100):.1f}")
    
    # Recommendation
    print(f"\n🎯 RECOMMENDATION:")
    best_quality = max(approaches, key=lambda x: x[1]['detection_rate'])
    best_performance = min(approaches, key=lambda x: x[2])
    
    print(f"   Best Quality: {best_quality[0]} ({best_quality[1]['detection_rate']:.1f}% detection)")
    print(f"   Best Performance: {best_performance[0]} ({best_performance[2]:.2f}ms)")
    
    # Check if any approach achieves ~95% target
    for name, quality, timing in approaches:
        if quality['detection_rate'] >= 95:
            print(f"   🎯 TARGET ACHIEVED: {name} reaches {quality['detection_rate']:.1f}% detection!")
            break
    else:
        print(f"   ⚠️  None reach 95% target. Best: {best_quality[1]['detection_rate']:.1f}%")

if __name__ == "__main__":
    main()