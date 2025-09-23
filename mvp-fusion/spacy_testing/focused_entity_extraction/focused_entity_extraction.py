#!/usr/bin/env python3
"""
Focused spaCy Entity Extraction Test
====================================
GOAL: Test spaCy's core strength - entity extraction for PERSON, ORG, GPE, LOC only
REASON: User wants to evaluate spaCy vs AC automaton for specific entity types
PROBLEM: Previous tests included semantics/relationships which spaCy handles poorly

Focus Areas:
- PERSON: Names of people (spaCy's strength)
- ORG: Organizations (spaCy's strength) 
- GPE: Geopolitical entities (spaCy's strength)
- LOC: Locations (spaCy's strength)

No semantics, no relationships, just pure entity detection quality.
"""

import time
import spacy
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict
from datetime import datetime

# Output directory - same directory as this script
OUTPUT_DIR = Path(__file__).parent

def load_test_document() -> str:
    """Load the clean test document."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    doc_path = script_dir / "test_document.md"
    with open(doc_path, 'r') as f:
        return f.read()

def extract_focused_entities(content: str) -> Dict[str, Any]:
    """Extract only PERSON, ORG, GPE, LOC entities using optimized spaCy."""
    print("🟡 **WAITING**: Extracting focused entities with spaCy...")
    
    start_time = time.perf_counter()
    
    # Force CPU and load optimized pipeline
    spacy.require_cpu()
    nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Process document
    doc = nlp(content)
    processing_time = (time.perf_counter() - start_time) * 1000
    
    # Extract only target entity types
    target_types = {'PERSON', 'ORG', 'GPE', 'LOC'}
    entities_by_type = defaultdict(list)
    all_entities = []
    
    for ent in doc.ents:
        if ent.label_ in target_types:
            entity_data = {
                'value': ent.text,
                'text': ent.text,
                'type': ent.label_,
                'span': {
                    'start': ent.start_char,
                    'end': ent.end_char
                },
                'confidence': getattr(ent, 'confidence', 1.0),
                'source': 'spacy_ner'
            }
            
            entities_by_type[ent.label_].append(entity_data)
            all_entities.append(entity_data)
    
    result = {
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'total_entities': len(all_entities),
            'entity_types': len(entities_by_type),
            'model': 'en_core_web_sm',
            'target_types': list(target_types),
            'pipeline_components': nlp.pipe_names
        },
        'entities_by_type': dict(entities_by_type),
        'all_entities': all_entities,
        'distribution': {label: len(entities) for label, entities in entities_by_type.items()}
    }
    
    print(f"🟢 **SUCCESS**: Extracted {len(all_entities)} focused entities in {processing_time:.2f}ms")
    for entity_type, count in result['distribution'].items():
        print(f"   {entity_type}: {count} entities")
    
    return result

def extract_person_only_spacy(content: str) -> Dict[str, Any]:
    """Extract only PERSON entities using optimized spaCy for speed comparison."""
    print("🟡 **WAITING**: Extracting PERSON-only entities with spaCy...")
    
    start_time = time.perf_counter()
    
    # Force CPU and load optimized pipeline
    spacy.require_cpu()
    nlp = spacy.load("en_core_web_sm", disable=["tok2vec", "tagger", "parser", "attribute_ruler", "lemmatizer"])
    
    # Process document
    doc = nlp(content)
    processing_time = (time.perf_counter() - start_time) * 1000
    
    # Extract only PERSON entities
    person_entities = []
    for ent in doc.ents:
        if ent.label_ == 'PERSON':
            entity_data = {
                'value': ent.text,
                'text': ent.text,
                'type': 'PERSON',
                'span': {
                    'start': ent.start_char,
                    'end': ent.end_char
                },
                'confidence': getattr(ent, 'confidence', 1.0),
                'source': 'spacy_ner_person_only'
            }
            person_entities.append(entity_data)
    
    result = {
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'processing_time_ms': processing_time,
            'total_entities': len(person_entities),
            'entity_types': 1,
            'model': 'en_core_web_sm_person_only',
            'target_types': ['PERSON'],
            'pipeline_components': nlp.pipe_names
        },
        'entities_by_type': {'PERSON': person_entities},
        'all_entities': person_entities,
        'distribution': {'PERSON': len(person_entities)}
    }
    
    print(f"🟢 **SUCCESS**: Extracted {len(person_entities)} PERSON entities in {processing_time:.2f}ms")
    
    return result

def test_mvp_fusion_baseline(content: str) -> Dict[str, Any]:
    """Test MVP-Fusion production system baseline for fair comparison."""
    print("\n🟡 **WAITING**: Testing MVP-Fusion production baseline...")
    
    try:
        # Import MVP-Fusion system
        import sys
        import os
        # Ensure we're working from MVP-Fusion root directory
        mvp_fusion_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sys.path.insert(0, mvp_fusion_root)
        from utils.core8_corpus_loader import Core8CorpusLoader
        from utils.world_scale_person_extractor import WorldScalePersonExtractor
        from pathlib import Path
        
        start_time = time.perf_counter()
        
        # Initialize systems
        loader = Core8CorpusLoader(verbose=False)
        
        # Initialize World-Scale Person Extractor (production system)
        corpus_dir = Path(mvp_fusion_root) / "knowledge" / "corpus" / "foundation_data"
        person_extractor = WorldScalePersonExtractor(
            first_names_path=corpus_dir / "first_names_2025_09_18.txt",
            last_names_path=corpus_dir / "last_names_2025_09_18.txt",
            organizations_path=corpus_dir / "organizations_2025_09_18.txt"
        )
        
        results = {}
        total_entities = 0
        timing_results = {}
        
        # PERSON - Use World-Scale Person Extractor (production system)
        person_start = time.perf_counter()
        person_results = person_extractor.extract_persons(content)
        person_time = (time.perf_counter() - person_start) * 1000
        timing_results['PERSON'] = person_time
        
        converted_persons = []
        for person in person_results:
            converted_persons.append({
                'value': person['text'],
                'text': person['text'],
                'type': 'PERSON',
                'span': {
                    'start': person['span']['start'],
                    'end': person['span']['end']
                },
                'confidence': person.get('confidence', 1.0),
                'source': 'world_scale_person_extractor'
            })
        results['PERSON'] = converted_persons
        total_entities += len(converted_persons)
        
        # ORG, GPE, LOC - Use AC automaton (time each separately)
        for entity_type in ['ORG', 'GPE', 'LOC']:
            type_start = time.perf_counter()
            type_results = loader.search(content, entity_type)
            type_time = (time.perf_counter() - type_start) * 1000
            timing_results[entity_type] = type_time
            
            entities = type_results.get(entity_type, [])
            
            # Convert to standard format
            converted_entities = []
            for entity in entities:
                converted_entities.append({
                    'value': entity['text'],
                    'text': entity['text'],
                    'type': entity_type,
                    'span': {
                        'start': entity['start'],
                        'end': entity['end']
                    },
                    'confidence': 1.0,
                    'source': 'ac_automaton'
                })
            
            results[entity_type] = converted_entities
            total_entities += len(converted_entities)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        result = {
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'processing_time_ms': processing_time,
                'individual_timings_ms': timing_results,
                'total_entities': total_entities,
                'entity_types': len([k for k, v in results.items() if v]),
                'model': 'mvp_fusion_production'
            },
            'entities_by_type': results,
            'all_entities': [entity for entities in results.values() for entity in entities],
            'distribution': {label: len(entities) for label, entities in results.items()}
        }
        
        print(f"🟢 **SUCCESS**: MVP-Fusion extracted {total_entities} entities in {processing_time:.2f}ms")
        print(f"📊 Individual Timings:")
        for entity_type, timing in timing_results.items():
            count = result['distribution'].get(entity_type, 0)
            print(f"   {entity_type}: {count} entities in {timing:.2f}ms")
        
        return result
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: MVP-Fusion baseline test failed: {e}")
        return {
            'metadata': {'extraction_time': datetime.now().isoformat(), 'total_entities': 0},
            'entities_by_type': {},
            'all_entities': [],
            'distribution': {}
        }

def analyze_entity_quality(spacy_results: Dict, mvp_fusion_results: Dict, entity_type: str) -> Dict[str, Any]:
    """Analyze quality for a specific entity type."""
    print(f"\n📊 QUALITY ANALYSIS: {entity_type}")
    print("=" * 40)
    
    # Get entities for this type
    spacy_entities = spacy_results['entities_by_type'].get(entity_type, [])
    mvp_fusion_entities = mvp_fusion_results['entities_by_type'].get(entity_type, [])
    
    # Expected entities (ground truth from document)
    expected_entities = {
        'PERSON': [
            "John Smith", "Mary Johnson", "Robert Chen", "Sarah Williams-Brown",
            "Dr. Michael O'Brien", "Jennifer Martinez", "David Kim", "Lisa Anderson",
            "James Wilson", "Patricia Thompson", "Xi Zhang", "José García-López",
            "Priya Patel", "François Dubois", "Yuki Tanaka", "Ahmed Al-Rashid",
            "Olga Volkov", "João Silva Santos", "Van Der Berg", "Dr. Li",
            "Madonna", "John John", "Mary Mary Quite Contrary", "Bob Johnson",
            "Sir Charles Winchester III"
        ],
        'ORG': [
            "OSHA", "Department of Labor", "EPA", "Centers for Disease Control and Prevention",
            "National Institute for Occupational Safety and Health", "Federal Aviation Administration",
            "Department of Transportation", "Food and Drug Administration", "Consumer Product Safety Commission",
            "Nuclear Regulatory Commission", "Microsoft Corporation", "Amazon Web Services, Inc.",
            "General Electric Company", "Johnson & Johnson", "3M Company", "Boeing Corporation",
            "Tesla, Inc.", "Walmart Inc.", "Apple Inc.", "Google LLC", "Facebook Technologies, LLC",
            "United Parcel Service", "FedEx Corporation", "Lockheed Martin Corporation",
            "Raytheon Technologies", "Massachusetts Institute of Technology", "Stanford University",
            "Harvard Business School", "University of California, Berkeley", "Johns Hopkins University"
        ],
        'GPE': [
            "United States", "China", "Russia", "India", "European Union", "Mexico", "South Korea", "Israel"
        ],
        'LOC': [
            "New York City", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "Dallas", "San Jose", "California", "Texas", "Florida",
            "Canada", "United Kingdom", "Germany", "Japan", "Australia", "Brazil"
        ]
    }
    
    expected = expected_entities.get(entity_type, [])
    
    # Find matches (case-insensitive, partial matching)
    def find_matches(entities, expected_list):
        found = set()
        entity_texts = [e['text'].lower() for e in entities]
        
        for expected_entity in expected_list:
            expected_lower = expected_entity.lower()
            for entity_text in entity_texts:
                if (expected_lower in entity_text or entity_text in expected_lower or 
                    any(word in entity_text for word in expected_lower.split() if len(word) > 3)):
                    found.add(expected_entity)
                    break
        
        return found
    
    spacy_found = find_matches(spacy_entities, expected)
    mvp_fusion_found = find_matches(mvp_fusion_entities, expected)
    
    spacy_detection_rate = len(spacy_found) / len(expected) * 100 if expected else 0
    mvp_fusion_detection_rate = len(mvp_fusion_found) / len(expected) * 100 if expected else 0
    
    # Show results
    print(f"📈 Expected {entity_type} entities: {len(expected)}")
    print(f"🎯 spaCy Detection: {len(spacy_found)}/{len(expected)} ({spacy_detection_rate:.1f}%)")
    print(f"🎯 MVP-Fusion Detection: {len(mvp_fusion_found)}/{len(expected)} ({mvp_fusion_detection_rate:.1f}%)")
    
    # Show what each found
    print(f"\n✅ spaCy Found:")
    for entity in sorted(spacy_found):
        print(f"   - {entity}")
    
    print(f"\n✅ MVP-Fusion Found:")
    for entity in sorted(mvp_fusion_found):
        print(f"   - {entity}")
    
    # Show unique to each
    spacy_unique = spacy_found - mvp_fusion_found
    mvp_fusion_unique = mvp_fusion_found - spacy_found
    
    if spacy_unique:
        print(f"\n🆕 spaCy Unique Finds:")
        for entity in sorted(spacy_unique):
            print(f"   - {entity}")
    
    if mvp_fusion_unique:
        print(f"\n🆕 MVP-Fusion Unique Finds:")
        for entity in sorted(mvp_fusion_unique):
            print(f"   - {entity}")
    
    # Show missed by both
    missed = set(expected) - spacy_found - mvp_fusion_found
    if missed:
        print(f"\n❌ Missed by Both:")
        for entity in sorted(missed):
            print(f"   - {entity}")
    
    return {
        'entity_type': entity_type,
        'expected_count': len(expected),
        'spacy': {
            'total_extracted': len(spacy_entities),
            'expected_found': len(spacy_found),
            'detection_rate': spacy_detection_rate,
            'found_entities': list(spacy_found),
            'unique_finds': list(spacy_unique)
        },
        'mvp_fusion': {
            'total_extracted': len(mvp_fusion_entities),
            'expected_found': len(mvp_fusion_found),
            'detection_rate': mvp_fusion_detection_rate,
            'found_entities': list(mvp_fusion_found),
            'unique_finds': list(mvp_fusion_unique)
        },
        'missed_by_both': list(missed)
    }

def save_results(data: Dict[str, Any], filename: str):
    """Save results in both YAML and JSON formats."""
    # Save YAML
    yaml_path = OUTPUT_DIR / f"{filename}.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    # Save JSON
    json_path = OUTPUT_DIR / f"{filename}.json"
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"🟢 **SUCCESS**: Saved {yaml_path} and {json_path}")

def main():
    """Run focused entity extraction comparison."""
    print("🚀 FOCUSED SPACY ENTITY EXTRACTION TEST")
    print("=" * 80)
    print("Testing spaCy's core strength: PERSON, ORG, GPE, LOC extraction")
    print("No semantics, no relationships - just pure entity detection")
    print()
    
    # Load test document
    content = load_test_document()
    print(f"📄 Test document: {len(content)} characters")
    
    # Test spaCy focused extraction
    spacy_results = extract_focused_entities(content)
    save_results(spacy_results, 'spacy_focused_entities')
    
    # Test spaCy PERSON-only extraction (for timing comparison)
    spacy_person_only_results = extract_person_only_spacy(content)
    save_results(spacy_person_only_results, 'spacy_person_only_entities')
    
    # Test MVP-Fusion baseline (production system)
    mvp_fusion_results = test_mvp_fusion_baseline(content)
    save_results(mvp_fusion_results, 'mvp_fusion_baseline_entities')
    
    # Analyze quality for each entity type
    target_types = ['PERSON', 'ORG', 'GPE', 'LOC']
    quality_analysis = {}
    
    for entity_type in target_types:
        analysis = analyze_entity_quality(spacy_results, mvp_fusion_results, entity_type)
        quality_analysis[entity_type] = analysis
    
    # Save quality analysis
    save_results(quality_analysis, 'entity_quality_comparison')
    
    # Final comparison summary
    print("\n🏆 FINAL COMPARISON SUMMARY")
    print("=" * 80)
    
    print(f"\n⚡ Performance:")
    print(f"   spaCy (all types): {spacy_results['metadata']['processing_time_ms']:.2f}ms")
    print(f"   spaCy (PERSON only): {spacy_person_only_results['metadata']['processing_time_ms']:.2f}ms")
    if 'processing_time_ms' in mvp_fusion_results['metadata']:
        print(f"   MVP-Fusion: {mvp_fusion_results['metadata']['processing_time_ms']:.2f}ms")
        if 'individual_timings_ms' in mvp_fusion_results['metadata']:
            person_time = mvp_fusion_results['metadata']['individual_timings_ms'].get('PERSON', 0)
            print(f"   MVP-Fusion (PERSON only): {person_time:.2f}ms")
    else:
        print(f"   MVP-Fusion: Failed to load")
    
    print(f"\n📊 Total Entities:")
    print(f"   spaCy: {spacy_results['metadata']['total_entities']}")
    print(f"   MVP-Fusion: {mvp_fusion_results['metadata']['total_entities']}")
    
    print(f"\n🎯 Detection Quality:")
    for entity_type in target_types:
        if entity_type in quality_analysis:
            analysis = quality_analysis[entity_type]
            spacy_rate = analysis['spacy']['detection_rate']
            mvp_fusion_rate = analysis['mvp_fusion']['detection_rate']
            winner = "spaCy" if spacy_rate > mvp_fusion_rate else "MVP-Fusion" if mvp_fusion_rate > spacy_rate else "TIE"
            print(f"   {entity_type:6}: spaCy {spacy_rate:5.1f}% | MVP-Fusion {mvp_fusion_rate:5.1f}% | Winner: {winner}")
    
    print(f"\n💡 RECOMMENDATION:")
    
    # Calculate overall winner
    total_spacy_rate = sum(quality_analysis[t]['spacy']['detection_rate'] for t in target_types if t in quality_analysis)
    total_mvp_fusion_rate = sum(quality_analysis[t]['mvp_fusion']['detection_rate'] for t in target_types if t in quality_analysis)
    
    if total_spacy_rate > total_mvp_fusion_rate:
        print(f"   🏅 spaCy wins overall with {total_spacy_rate/len(target_types):.1f}% avg detection")
        print(f"   💡 Consider spaCy for PERSON/ORG/GPE/LOC extraction")
    elif total_mvp_fusion_rate > total_spacy_rate:
        print(f"   🏅 MVP-Fusion wins overall with {total_mvp_fusion_rate/len(target_types):.1f}% avg detection")
        print(f"   💡 MVP-Fusion production system remains superior")
    else:
        print(f"   🤝 Tie - consider hybrid approach")
    
    print(f"\n📁 All results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()