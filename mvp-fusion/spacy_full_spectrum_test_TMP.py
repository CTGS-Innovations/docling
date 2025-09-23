#!/usr/bin/env python3
"""
spaCy Full Spectrum Capability Test
===================================
GOAL: Show EVERYTHING spaCy can do end-to-end without external systems
REASON: User wants to see if spaCy can handle the complete pipeline autonomously
PROBLEM: Need to test: raw extraction, normalization, rules, semantic analysis, etc.

This test demonstrates spaCy's complete capabilities:
1. Raw entity extraction (NER)
2. Entity normalization and linking  
3. Dependency parsing and syntax rules
4. Sentence segmentation
5. Part-of-speech tagging
6. Lemmatization and morphology
7. Noun chunk extraction
8. Semantic similarity
9. Custom rule-based matching
10. Entity relationship extraction
"""

import time
import spacy
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import json

def load_test_document() -> str:
    """Load the test document."""
    doc_path = Path("/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_TXT_DOCUMENT.txt")
    with open(doc_path, 'r') as f:
        return f.read()

def test_spacy_full_pipeline(content: str) -> Dict[str, Any]:
    """Test spaCy's complete pipeline capabilities."""
    print("🚀 SPACY FULL SPECTRUM TEST")
    print("=" * 80)
    print("Testing EVERYTHING spaCy can do end-to-end")
    print()
    
    # Force CPU optimization
    spacy.require_cpu()
    
    # Load FULL spaCy model with ALL components
    print("🟡 **WAITING**: Loading full spaCy pipeline...")
    nlp = spacy.load("en_core_web_sm")
    print(f"✅ Pipeline components: {nlp.pipe_names}")
    
    start_time = time.perf_counter()
    doc = nlp(content)
    processing_time = (time.perf_counter() - start_time) * 1000
    
    print(f"🟢 **SUCCESS**: Full pipeline processing completed in {processing_time:.2f}ms")
    print()
    
    results = {
        'processing_time_ms': processing_time,
        'document_stats': {},
        'raw_entities': [],
        'normalized_entities': {},
        'linguistic_analysis': {},
        'semantic_rules': [],
        'relationships': [],
        'custom_patterns': []
    }
    
    # SECTION 1: DOCUMENT STATISTICS
    print("📊 DOCUMENT STATISTICS")
    print("=" * 40)
    
    sentences = list(doc.sents)
    tokens = list(doc)
    
    stats = {
        'total_characters': len(content),
        'total_tokens': len(tokens),
        'total_sentences': len(sentences),
        'avg_sentence_length': len(tokens) / len(sentences) if sentences else 0,
        'unique_lemmas': len(set(token.lemma_ for token in tokens if not token.is_space)),
        'complexity_score': sum(1 for token in tokens if len(token.text) > 8) / len(tokens)
    }
    
    for key, value in stats.items():
        print(f"   {key}: {value:.1f}" if isinstance(value, float) else f"   {key}: {value}")
    
    results['document_stats'] = stats
    
    # SECTION 2: RAW ENTITY EXTRACTION
    print(f"\n🏷️  RAW ENTITY EXTRACTION")
    print("=" * 40)
    
    entities_by_type = defaultdict(list)
    for ent in doc.ents:
        entity_data = {
            'text': ent.text,
            'label': ent.label_,
            'start': ent.start_char,
            'end': ent.end_char,
            'confidence': getattr(ent, 'confidence', 1.0),
            'description': spacy.explain(ent.label_)
        }
        entities_by_type[ent.label_].append(entity_data)
        results['raw_entities'].append(entity_data)
    
    print(f"📈 Entity Distribution:")
    for label, entities in sorted(entities_by_type.items()):
        description = spacy.explain(label)
        print(f"   {label} ({description}): {len(entities)} entities")
    
    print(f"\n🔍 Sample Entities:")
    for label, entities in list(entities_by_type.items())[:5]:
        print(f"   {label}: {[e['text'] for e in entities[:3]]}")
    
    # SECTION 3: ENTITY NORMALIZATION & LINKING
    print(f"\n🔗 ENTITY NORMALIZATION & LINKING")
    print("=" * 40)
    
    normalized_entities = {}
    for label, entities in entities_by_type.items():
        # Group similar entities (basic normalization)
        normalized_groups = defaultdict(list)
        for entity in entities:
            # Normalize by lemmatizing entity text
            entity_tokens = nlp(entity['text'])
            normalized_form = ' '.join(token.lemma_.lower() for token in entity_tokens if not token.is_stop)
            normalized_groups[normalized_form].append(entity)
        
        normalized_entities[label] = {
            'groups': len(normalized_groups),
            'total_mentions': len(entities),
            'normalized_forms': [
                {
                    'canonical': canonical,
                    'mentions': len(mentions),
                    'variants': [m['text'] for m in mentions[:3]]
                }
                for canonical, mentions in sorted(normalized_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            ]
        }
    
    results['normalized_entities'] = normalized_entities
    
    print(f"📋 Normalization Results:")
    for label, data in normalized_entities.items():
        print(f"   {label}: {data['total_mentions']} mentions → {data['groups']} canonical forms")
    
    print(f"\n🎯 Top Canonical Forms:")
    for label, data in list(normalized_entities.items())[:3]:
        print(f"   {label}:")
        for form in data['normalized_forms'][:2]:
            print(f"      {form['canonical']}: {form['mentions']} mentions {form['variants']}")
    
    # SECTION 4: LINGUISTIC ANALYSIS
    print(f"\n📝 LINGUISTIC ANALYSIS")
    print("=" * 40)
    
    # POS tag distribution
    pos_counts = defaultdict(int)
    dep_counts = defaultdict(int)
    
    for token in doc:
        if not token.is_space:
            pos_counts[token.pos_] += 1
            dep_counts[token.dep_] += 1
    
    linguistic_data = {
        'pos_distribution': dict(pos_counts),
        'dependency_distribution': dict(dep_counts),
        'noun_chunks': [
            {
                'text': chunk.text,
                'root': chunk.root.text,
                'start': chunk.start_char,
                'end': chunk.end_char
            }
            for chunk in doc.noun_chunks
        ][:10],
        'sentence_structures': [
            {
                'text': sent.text[:100] + '...' if len(sent.text) > 100 else sent.text,
                'root_verb': sent.root.text if sent.root.pos_ == 'VERB' else None,
                'complexity': len([token for token in sent if token.dep_ in ['compound', 'conj']])
            }
            for sent in list(doc.sents)[:5]
        ]
    }
    
    results['linguistic_analysis'] = linguistic_data
    
    print(f"📊 POS Distribution (top 5):")
    for pos, count in sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {pos}: {count}")
    
    print(f"\n🏗️  Noun Chunks (first 5):")
    for chunk in linguistic_data['noun_chunks'][:5]:
        print(f"   \"{chunk['text']}\" (root: {chunk['root']})")
    
    # SECTION 5: SEMANTIC RULES & PATTERNS
    print(f"\n⚡ SEMANTIC RULES & PATTERNS")
    print("=" * 40)
    
    # Extract semantic patterns
    semantic_rules = []
    
    # Rule 1: Organization-Person relationships
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            # Find people mentioned in same sentence
            sent = ent.sent
            people_in_sent = [e for e in sent.ents if e.label_ == 'PERSON' and e != ent]
            if people_in_sent:
                semantic_rules.append({
                    'rule_type': 'organization_person_relationship',
                    'organization': ent.text,
                    'people': [p.text for p in people_in_sent],
                    'context': sent.text[:150] + '...' if len(sent.text) > 150 else sent.text
                })
    
    # Rule 2: Money-Organization relationships
    for ent in doc.ents:
        if ent.label_ == 'MONEY':
            sent = ent.sent
            orgs_in_sent = [e for e in sent.ents if e.label_ == 'ORG']
            if orgs_in_sent:
                semantic_rules.append({
                    'rule_type': 'financial_transaction',
                    'amount': ent.text,
                    'organizations': [o.text for o in orgs_in_sent],
                    'context': sent.text[:150] + '...' if len(sent.text) > 150 else sent.text
                })
    
    # Rule 3: Date-Event relationships
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            sent = ent.sent
            # Look for action verbs in the sentence
            action_verbs = [token for token in sent if token.pos_ == 'VERB' and token.dep_ in ['ROOT', 'conj']]
            if action_verbs:
                semantic_rules.append({
                    'rule_type': 'temporal_event',
                    'date': ent.text,
                    'actions': [v.lemma_ for v in action_verbs],
                    'context': sent.text[:150] + '...' if len(sent.text) > 150 else sent.text
                })
    
    results['semantic_rules'] = semantic_rules
    
    print(f"📋 Semantic Rules Extracted:")
    rule_counts = defaultdict(int)
    for rule in semantic_rules:
        rule_counts[rule['rule_type']] += 1
    
    for rule_type, count in rule_counts.items():
        print(f"   {rule_type}: {count} instances")
    
    print(f"\n🔍 Sample Rules:")
    for rule_type in list(rule_counts.keys())[:3]:
        sample = next(r for r in semantic_rules if r['rule_type'] == rule_type)
        print(f"   {rule_type}:")
        for key, value in sample.items():
            if key != 'rule_type' and key != 'context':
                print(f"      {key}: {value}")
    
    # SECTION 6: ENTITY RELATIONSHIPS
    print(f"\n🕸️  ENTITY RELATIONSHIPS")
    print("=" * 40)
    
    relationships = []
    
    # Find entities in same sentences (co-occurrence)
    for sent in doc.sents:
        sent_entities = list(sent.ents)
        if len(sent_entities) >= 2:
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i+1:]:
                    relationships.append({
                        'entity1': {'text': ent1.text, 'label': ent1.label_},
                        'entity2': {'text': ent2.text, 'label': ent2.label_},
                        'relationship_type': 'co_occurrence',
                        'context': sent.text[:100] + '...' if len(sent.text) > 100 else sent.text
                    })
    
    results['relationships'] = relationships[:20]  # Limit to first 20
    
    print(f"📊 Relationships Found: {len(relationships)}")
    
    # Group by relationship types
    rel_type_counts = defaultdict(int)
    for rel in relationships:
        rel_key = f"{rel['entity1']['label']}-{rel['entity2']['label']}"
        rel_type_counts[rel_key] += 1
    
    print(f"🔗 Top Relationship Types:")
    for rel_type, count in sorted(rel_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"   {rel_type}: {count} instances")
    
    # SECTION 7: CUSTOM PATTERN MATCHING
    print(f"\n🎯 CUSTOM PATTERN MATCHING")
    print("=" * 40)
    
    # Add EntityRuler for custom patterns
    from spacy.pipeline import EntityRuler
    ruler = EntityRuler(nlp)
    
    # Define custom patterns for common business entities
    custom_patterns = [
        {"label": "BUSINESS_ENTITY", "pattern": [{"LOWER": {"IN": ["inc", "corp", "llc", "ltd"]}}]},
        {"label": "UNIVERSITY", "pattern": [{"LOWER": "university"}]},
        {"label": "SAFETY_TERM", "pattern": [{"LOWER": {"IN": ["safety", "compliance", "regulation", "violation"]}}]}
    ]
    
    ruler.add_patterns(custom_patterns)
    
    # Create temporary nlp with ruler
    temp_nlp = spacy.blank("en")
    temp_nlp.add_pipe("sentencizer")
    temp_nlp.add_pipe(ruler)
    
    temp_doc = temp_nlp(content)
    
    custom_entities = defaultdict(list)
    for ent in temp_doc.ents:
        custom_entities[ent.label_].append({
            'text': ent.text,
            'start': ent.start_char,
            'end': ent.end_char
        })
    
    results['custom_patterns'] = dict(custom_entities)
    
    print(f"📋 Custom Pattern Results:")
    for label, entities in custom_entities.items():
        print(f"   {label}: {len(entities)} matches")
        if entities:
            sample_texts = [e['text'] for e in entities[:3]]
            print(f"      Examples: {sample_texts}")
    
    return results

def generate_spacy_report(results: Dict[str, Any]) -> str:
    """Generate a comprehensive report of spaCy capabilities."""
    
    report = f"""
🚀 SPACY FULL SPECTRUM CAPABILITY REPORT
{'=' * 80}

📊 PERFORMANCE METRICS:
   Processing Time: {results['processing_time_ms']:.2f}ms
   Tokens Processed: {results['document_stats']['total_tokens']:,}
   Processing Speed: {results['document_stats']['total_tokens'] / (results['processing_time_ms'] / 1000):.0f} tokens/sec

🏷️  RAW ENTITY EXTRACTION:
   Total Entities: {len(results['raw_entities'])}
   Entity Types: {len(set(e['label'] for e in results['raw_entities']))}
   
📝 LINGUISTIC ANALYSIS:
   Sentences: {results['document_stats']['total_sentences']}
   Noun Chunks: {len(results['linguistic_analysis']['noun_chunks'])}
   Unique Lemmas: {results['document_stats']['unique_lemmas']}

⚡ SEMANTIC CAPABILITIES:
   Semantic Rules: {len(results['semantic_rules'])}
   Entity Relationships: {len(results['relationships'])}
   Custom Patterns: {sum(len(entities) for entities in results['custom_patterns'].values())}

🎯 NORMALIZATION QUALITY:
"""
    
    for label, data in results['normalized_entities'].items():
        if data['total_mentions'] > 0:
            reduction = (1 - data['groups'] / data['total_mentions']) * 100
            report += f"   {label}: {data['total_mentions']} → {data['groups']} ({reduction:.1f}% reduction)\n"
    
    report += f"""
⚖️  SPACY vs TRADITIONAL NLP:
   ✅ Unified Pipeline: Single model handles multiple tasks
   ✅ Contextual Understanding: Dependency parsing + NER integration  
   ✅ Extensible: Custom rules + patterns can be added
   ✅ Industrial Strength: Battle-tested on real-world data
   ✅ Memory Efficient: Optimized for production use
   
❓ GAPS vs AC/FLPC APPROACH:
   ⚠️  Domain Knowledge: Limited to training data
   ⚠️  Performance: Slower than specialized AC automaton  
   ⚠️  Coverage: May miss domain-specific entities
   ⚠️  Consistency: ML-based, may have edge case variations

💡 HYBRID POTENTIAL:
   Combine spaCy's linguistic analysis with AC's domain knowledge
   Use spaCy for structure, AC for precise entity matching
   spaCy provides relationships + context, AC provides comprehensive coverage
"""
    
    return report

def main():
    """Run the comprehensive spaCy capability test."""
    content = load_test_document()
    
    # Run full spectrum test
    results = test_spacy_full_pipeline(content)
    
    # Generate comprehensive report
    report = generate_spacy_report(results)
    print(report)
    
    # Save detailed results to JSON
    output_file = "spacy_full_spectrum_results_TMP.json"
    with open(output_file, 'w') as f:
        # Convert defaultdict and other non-serializable objects
        serializable_results = json.loads(json.dumps(results, default=str))
        json.dump(serializable_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")
    print(f"\n🎯 CONCLUSION: spaCy provides a comprehensive NLP pipeline")
    print(f"   but may need AC/FLPC augmentation for domain-specific precision.")

if __name__ == "__main__":
    main()