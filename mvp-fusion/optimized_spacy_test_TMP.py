#!/usr/bin/env python3
"""
Optimized spaCy Quality Test - Following Best Practices
======================================================
GOAL: Test spaCy with proper CPU optimizations and NER-only configuration
REASON: Previous test may not have used spaCy optimally for CPU performance
PROBLEM: Need to follow spaCy industrial-strength best practices from Context7

Based on spaCy documentation best practices:
1. Use spacy.require_cpu() before loading models
2. Disable unnecessary components for NER-only tasks
3. Use proper batch processing with nlp.pipe()
4. Optimize pipeline configuration for CPU performance
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

def test_optimized_spacy_ner(content: str) -> Tuple[List[Dict], float]:
    """Test spaCy NER with proper CPU optimizations."""
    print("🟡 **WAITING**: Testing OPTIMIZED spaCy NER (following best practices)...")
    
    try:
        start_time = time.perf_counter()
        
        # STEP 1: Force CPU allocation BEFORE loading any pipelines
        spacy.require_cpu()
        
        # STEP 2: Load model with NER-only pipeline (disable unnecessary components)
        # Context7 best practice: Disable all components except NER for CPU optimization
        nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
        
        print(f"   Enabled components: {nlp.pipe_names}")
        
        # STEP 3: Use nlp.pipe() with optimized batch processing 
        # Context7 best practice: Use batch processing with optimal batch size for CPU
        texts = [content]  # Single document, but using pipe for consistency
        
        entities = []
        for doc in nlp.pipe(texts, batch_size=1000):  # Optimal batch size for CPU
            for ent in doc.ents:
                entities.append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'source': 'optimized_spaCy_NER'
                })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: Optimized spaCy NER completed")
        print(f"   Time: {processing_time:.2f}ms")  
        print(f"   Entities: {len(entities)}")
        print(f"   Pipeline: {nlp.pipe_names}")
        
        return entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Optimized spaCy NER test failed: {e}")
        return [], 0

def test_ner_only_pipeline(content: str) -> Tuple[List[Dict], float]:
    """Test spaCy with NER-only pipeline configuration."""
    print("\n🟡 **WAITING**: Testing NER-only pipeline configuration...")
    
    try:
        start_time = time.perf_counter()
        
        # Force CPU
        spacy.require_cpu()
        
        # Load model excluding ALL components except NER
        # This follows Context7 pattern for transformer models adapted to SM model
        nlp = spacy.load("en_core_web_sm", exclude=["tagger", "parser", "attribute_ruler", "lemmatizer"])
        
        # Process with disabled components for maximum NER focus
        doc = nlp(content)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'source': 'NER_only_pipeline'
            })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: NER-only pipeline completed")
        print(f"   Time: {processing_time:.2f}ms")  
        print(f"   Entities: {len(entities)}")
        print(f"   Components: {nlp.pipe_names}")
        
        return entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: NER-only pipeline test failed: {e}")
        return [], 0

def test_sentences_with_ner_only(content: str) -> Tuple[List[Dict], float]:
    """Test sentence-based processing with NER-only pipeline.""" 
    print("\n🟡 **WAITING**: Testing sentence-based + NER-only approach...")
    
    try:
        start_time = time.perf_counter()
        
        # Force CPU
        spacy.require_cpu()
        
        # Create NER-only pipeline
        nlp = spacy.load("en_core_web_sm", exclude=["tagger", "parser", "attribute_ruler", "lemmatizer"])
        
        # Process full document to get sentence boundaries AND entities
        doc = nlp(content)
        
        # Extract entities with sentence context
        entities = []
        for ent in doc.ents:
            # Find which sentence this entity belongs to
            sent_id = None
            for i, sent in enumerate(doc.sents):
                if ent.start >= sent.start and ent.end <= sent.end:
                    sent_id = i
                    break
            
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'sentence_id': sent_id,
                'source': 'sentence_NER_only'
            })
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        print(f"🟢 **SUCCESS**: Sentence-based NER-only completed")
        print(f"   Time: {processing_time:.2f}ms")
        print(f"   Entities: {len(entities)}")
        print(f"   Sentences: {len(list(doc.sents))}")
        
        return entities, processing_time
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Sentence-based NER test failed: {e}")
        return [], 0

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
    entity_texts = [e['text'] for e in entities]
    
    for expected in expected_orgs:
        # Look for exact match or substring match
        found = False
        for entity_text in entity_texts:
            if expected.lower() in entity_text.lower() or entity_text.lower() in expected.lower():
                found_expected.append(expected)
                found = True
                break
    
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
    
    # Show ORG entities specifically
    org_entities = [e for e in entities if e['label'] in ['ORG', 'ORGANIZATION']]
    if org_entities:
        print(f"\n🔍 All ORG Entities Found:")
        for i, entity in enumerate(org_entities, 1):
            print(f"   {i:2d}. \"{entity['text']}\"")
    
    return {
        'total_entities': len(entities),
        'detection_rate': detection_rate,
        'found_expected': len(found_expected),
        'by_type': dict(by_type),
        'org_entities': org_entities
    }

def main():
    """Run the optimized spaCy quality test."""
    print("🚀 OPTIMIZED SPACY QUALITY TEST - Following Best Practices")
    print("=" * 80)
    print("Testing spaCy with proper CPU optimization and NER-only configuration")
    print()
    
    # Load test document
    content = load_test_document()
    print(f"📄 Test document: {len(content)} characters")
    
    # Test 1: Optimized spaCy NER with disabled components
    opt_entities, opt_time = test_optimized_spacy_ner(content)
    opt_quality = analyze_entity_quality(opt_entities, "Optimized spaCy")
    
    # Test 2: NER-only pipeline
    ner_entities, ner_time = test_ner_only_pipeline(content)
    ner_quality = analyze_entity_quality(ner_entities, "NER-only Pipeline")
    
    # Test 3: Sentence-based with NER-only
    sent_entities, sent_time = test_sentences_with_ner_only(content)
    sent_quality = analyze_entity_quality(sent_entities, "Sentence + NER-only")
    
    # Compare results
    print("\n🏆 OPTIMIZED SPACY COMPARISON")
    print("=" * 80)
    
    approaches = [
        ("Optimized spaCy", opt_quality, opt_time),
        ("NER-only Pipeline", ner_quality, ner_time),
        ("Sentence + NER-only", sent_quality, sent_time)
    ]
    
    for name, quality, timing in approaches:
        print(f"\n📊 {name}:")
        print(f"   Time: {timing:.2f}ms")
        print(f"   Total Entities: {quality['total_entities']}")
        print(f"   ORG Entities: {len(quality['org_entities'])}")
        print(f"   Detection Rate: {quality['detection_rate']:.1f}%")
        if quality['detection_rate'] >= 95:
            print(f"   🎯 TARGET ACHIEVED!")
    
    # Best approach recommendation
    best_quality = max(approaches, key=lambda x: x[1]['detection_rate'])
    best_performance = min(approaches, key=lambda x: x[2])
    
    print(f"\n🎯 OPTIMIZED RECOMMENDATION:")
    print(f"   Best Quality: {best_quality[0]} ({best_quality[1]['detection_rate']:.1f}% detection)")
    print(f"   Best Performance: {best_performance[0]} ({best_performance[2]:.2f}ms)")

if __name__ == "__main__":
    main()