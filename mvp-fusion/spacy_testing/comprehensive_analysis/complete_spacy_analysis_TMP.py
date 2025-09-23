#!/usr/bin/env python3
"""
Complete spaCy Analysis with Full Output Generation
==================================================
GOAL: Generate ALL spaCy outputs (YAML, JSON, detailed files) for user examination
REASON: User wants complete transparency - physical access to all generated data
PROBLEM: Previous tests only showed summary numbers, not the actual detailed outputs

This script generates:
1. Raw entities (YAML + JSON)
2. Normalized entities (YAML + JSON) 
3. Semantic rules (YAML + JSON)
4. Entity relationships (YAML + JSON)
5. Linguistic analysis (YAML + JSON)
6. Performance metrics (YAML + JSON)
7. Complete combined results (JSON)
8. Detailed analysis report (Markdown)
"""

import time
import spacy
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Output directory
OUTPUT_DIR = Path("/home/corey/projects/docling/mvp-fusion/spacy_test_outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def load_test_document() -> str:
    """Load the test document."""
    doc_path = Path("/home/corey/projects/docling/mvp-fusion/spacy_test_outputs/ENTITY_EXTRACTION_MD_DOCUMENT.md")
    with open(doc_path, 'r') as f:
        return f.read()

def save_to_yaml(data: Any, filename: str) -> None:
    """Save data to YAML file."""
    filepath = OUTPUT_DIR / f"{filename}.yaml"
    with open(filepath, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
    print(f"🟢 **SUCCESS**: Saved {filepath}")

def save_to_json(data: Any, filename: str) -> None:
    """Save data to JSON file."""
    filepath = OUTPUT_DIR / f"{filename}.json"
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"🟢 **SUCCESS**: Saved {filepath}")

def extract_raw_entities(doc) -> Dict[str, Any]:
    """Extract raw entities from spaCy document."""
    print("🟡 **WAITING**: Extracting raw entities...")
    
    raw_entities = []
    entities_by_type = defaultdict(list)
    
    for ent in doc.ents:
        entity_data = {
            'text': ent.text,
            'label': ent.label_,
            'start_char': ent.start_char,
            'end_char': ent.end_char,
            'start_token': ent.start,
            'end_token': ent.end,
            'confidence': getattr(ent, 'confidence', 1.0),
            'description': spacy.explain(ent.label_),
            'sentence_id': None  # Will be filled later
        }
        
        # Find which sentence this entity belongs to
        for i, sent in enumerate(doc.sents):
            if ent.start >= sent.start and ent.end <= sent.end:
                entity_data['sentence_id'] = i
                break
        
        raw_entities.append(entity_data)
        entities_by_type[ent.label_].append(entity_data)
    
    result = {
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'total_entities': len(raw_entities),
            'entity_types': len(entities_by_type),
            'spacy_model': 'en_core_web_sm'
        },
        'entities_by_type': dict(entities_by_type),
        'all_entities': raw_entities,
        'distribution': {label: len(entities) for label, entities in entities_by_type.items()}
    }
    
    print(f"🟢 **SUCCESS**: Extracted {len(raw_entities)} raw entities across {len(entities_by_type)} types")
    return result

def normalize_entities(doc, raw_entities: List[Dict]) -> Dict[str, Any]:
    """Normalize and canonicalize entities."""
    print("🟡 **WAITING**: Normalizing entities...")
    
    # Group entities by type for normalization
    entities_by_type = defaultdict(list)
    for entity in raw_entities:
        entities_by_type[entity['label']].append(entity)
    
    normalized_results = {}
    
    for label, entities in entities_by_type.items():
        # Group similar entities (basic normalization)
        normalized_groups = defaultdict(list)
        
        for entity in entities:
            # Normalize by lemmatizing entity text
            entity_tokens = doc[entity['start_token']:entity['end_token']]
            normalized_form = ' '.join(token.lemma_.lower() for token in entity_tokens if not token.is_stop)
            
            # If normalized form is empty, use original text
            if not normalized_form.strip():
                normalized_form = entity['text'].lower()
            
            normalized_groups[normalized_form].append(entity)
        
        # Create canonical forms
        canonical_entities = []
        for canonical_form, mentions in normalized_groups.items():
            # Choose the most common variant as canonical
            variant_counts = defaultdict(int)
            for mention in mentions:
                variant_counts[mention['text']] += 1
            
            canonical_text = max(variant_counts.items(), key=lambda x: x[1])[0]
            
            canonical_entities.append({
                'canonical_form': canonical_form,
                'canonical_text': canonical_text,
                'mention_count': len(mentions),
                'variants': list(set(m['text'] for m in mentions)),
                'all_mentions': mentions
            })
        
        # Sort by mention count (most frequent first)
        canonical_entities.sort(key=lambda x: x['mention_count'], reverse=True)
        
        normalized_results[label] = {
            'total_mentions': len(entities),
            'canonical_groups': len(canonical_entities),
            'reduction_percentage': (1 - len(canonical_entities) / len(entities)) * 100 if entities else 0,
            'canonical_entities': canonical_entities
        }
    
    result = {
        'metadata': {
            'normalization_time': datetime.now().isoformat(),
            'normalization_method': 'lemmatization_with_stopword_removal',
            'total_original_entities': sum(len(entities) for entities in entities_by_type.values()),
            'total_canonical_forms': sum(len(data['canonical_entities']) for data in normalized_results.values())
        },
        'normalized_by_type': normalized_results,
        'summary': {
            label: {
                'original': data['total_mentions'],
                'canonical': data['canonical_groups'],
                'reduction': f"{data['reduction_percentage']:.1f}%"
            }
            for label, data in normalized_results.items()
        }
    }
    
    total_reduction = (1 - result['metadata']['total_canonical_forms'] / result['metadata']['total_original_entities']) * 100
    print(f"🟢 **SUCCESS**: Normalized entities with {total_reduction:.1f}% reduction")
    return result

def extract_semantic_rules(doc) -> Dict[str, Any]:
    """Extract semantic rules and patterns."""
    print("🟡 **WAITING**: Extracting semantic rules...")
    
    semantic_rules = []
    
    # Rule 1: Organization-Person relationships
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            sent = ent.sent
            people_in_sent = [e for e in sent.ents if e.label_ == 'PERSON' and e != ent]
            if people_in_sent:
                semantic_rules.append({
                    'rule_type': 'organization_person_relationship',
                    'rule_id': f"org_person_{len(semantic_rules)}",
                    'organization': {
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'people': [{'text': p.text, 'start': p.start_char, 'end': p.end_char} for p in people_in_sent],
                    'context': sent.text,
                    'sentence_id': list(doc.sents).index(sent),
                    'confidence': 0.8
                })
    
    # Rule 2: Money-Organization relationships
    for ent in doc.ents:
        if ent.label_ == 'MONEY':
            sent = ent.sent
            orgs_in_sent = [e for e in sent.ents if e.label_ == 'ORG']
            if orgs_in_sent:
                semantic_rules.append({
                    'rule_type': 'financial_transaction',
                    'rule_id': f"money_org_{len(semantic_rules)}",
                    'amount': {
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'organizations': [{'text': o.text, 'start': o.start_char, 'end': o.end_char} for o in orgs_in_sent],
                    'context': sent.text,
                    'sentence_id': list(doc.sents).index(sent),
                    'confidence': 0.9
                })
    
    # Rule 3: Date-Event relationships
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            sent = ent.sent
            action_verbs = [token for token in sent if token.pos_ == 'VERB' and token.dep_ in ['ROOT', 'conj']]
            if action_verbs:
                semantic_rules.append({
                    'rule_type': 'temporal_event',
                    'rule_id': f"date_event_{len(semantic_rules)}",
                    'date': {
                        'text': ent.text,
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'actions': [{'lemma': v.lemma_, 'text': v.text, 'pos': v.pos_} for v in action_verbs],
                    'context': sent.text,
                    'sentence_id': list(doc.sents).index(sent),
                    'confidence': 0.7
                })
    
    # Rule 4: Location-Organization relationships
    for ent in doc.ents:
        if ent.label_ in ['GPE', 'LOC']:
            sent = ent.sent
            orgs_in_sent = [e for e in sent.ents if e.label_ == 'ORG']
            if orgs_in_sent:
                semantic_rules.append({
                    'rule_type': 'location_organization',
                    'rule_id': f"loc_org_{len(semantic_rules)}",
                    'location': {
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    },
                    'organizations': [{'text': o.text, 'start': o.start_char, 'end': o.end_char} for o in orgs_in_sent],
                    'context': sent.text,
                    'sentence_id': list(doc.sents).index(sent),
                    'confidence': 0.8
                })
    
    # Group rules by type
    rules_by_type = defaultdict(list)
    for rule in semantic_rules:
        rules_by_type[rule['rule_type']].append(rule)
    
    result = {
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'total_rules': len(semantic_rules),
            'rule_types': len(rules_by_type),
            'extraction_method': 'co_occurrence_with_dependency_analysis'
        },
        'rules_by_type': dict(rules_by_type),
        'all_rules': semantic_rules,
        'distribution': {rule_type: len(rules) for rule_type, rules in rules_by_type.items()}
    }
    
    print(f"🟢 **SUCCESS**: Extracted {len(semantic_rules)} semantic rules across {len(rules_by_type)} types")
    return result

def extract_relationships(doc) -> Dict[str, Any]:
    """Extract entity relationships."""
    print("🟡 **WAITING**: Extracting entity relationships...")
    
    relationships = []
    
    # Find entities in same sentences (co-occurrence)
    for sent_id, sent in enumerate(doc.sents):
        sent_entities = list(sent.ents)
        if len(sent_entities) >= 2:
            for i, ent1 in enumerate(sent_entities):
                for ent2 in sent_entities[i+1:]:
                    # Calculate distance between entities
                    distance = abs(ent1.start - ent2.start)
                    
                    # Check for connecting words between entities
                    start_token = min(ent1.end, ent2.end)
                    end_token = max(ent1.start, ent2.start)
                    connecting_tokens = doc[start_token:end_token]
                    connecting_text = ' '.join(token.text for token in connecting_tokens)
                    
                    relationships.append({
                        'relationship_id': f"rel_{len(relationships)}",
                        'entity1': {
                            'text': ent1.text,
                            'label': ent1.label_,
                            'start': ent1.start_char,
                            'end': ent1.end_char
                        },
                        'entity2': {
                            'text': ent2.text,
                            'label': ent2.label_,
                            'start': ent2.start_char,
                            'end': ent2.end_char
                        },
                        'relationship_type': 'co_occurrence',
                        'relationship_strength': max(0.1, 1.0 - (distance / 50)),  # Closer = stronger
                        'connecting_text': connecting_text,
                        'context': sent.text,
                        'sentence_id': sent_id,
                        'token_distance': distance
                    })
    
    # Group relationships by entity pair types
    relationships_by_type = defaultdict(list)
    for rel in relationships:
        pair_type = f"{rel['entity1']['label']}-{rel['entity2']['label']}"
        relationships_by_type[pair_type].append(rel)
    
    # Sort relationships by strength
    relationships.sort(key=lambda x: x['relationship_strength'], reverse=True)
    
    result = {
        'metadata': {
            'extraction_time': datetime.now().isoformat(),
            'total_relationships': len(relationships),
            'relationship_types': len(relationships_by_type),
            'extraction_method': 'sentence_co_occurrence_with_distance'
        },
        'relationships_by_type': dict(relationships_by_type),
        'all_relationships': relationships[:50],  # Top 50 by strength
        'distribution': {rel_type: len(rels) for rel_type, rels in relationships_by_type.items()},
        'top_relationships': relationships[:10]
    }
    
    print(f"🟢 **SUCCESS**: Extracted {len(relationships)} relationships across {len(relationships_by_type)} types")
    return result

def analyze_linguistics(doc, nlp) -> Dict[str, Any]:
    """Perform linguistic analysis."""
    print("🟡 **WAITING**: Performing linguistic analysis...")
    
    # POS tag distribution
    pos_counts = defaultdict(int)
    dep_counts = defaultdict(int)
    lemma_counts = defaultdict(int)
    
    for token in doc:
        if not token.is_space:
            pos_counts[token.pos_] += 1
            dep_counts[token.dep_] += 1
            if not token.is_stop and not token.is_punct:
                lemma_counts[token.lemma_.lower()] += 1
    
    # Noun chunks analysis
    noun_chunks = []
    for chunk in doc.noun_chunks:
        noun_chunks.append({
            'text': chunk.text,
            'root': chunk.root.text,
            'root_pos': chunk.root.pos_,
            'start': chunk.start_char,
            'end': chunk.end_char,
            'length_tokens': len(chunk),
            'modifiers': [token.text for token in chunk if token != chunk.root]
        })
    
    # Sentence analysis
    sentences = []
    for i, sent in enumerate(doc.sents):
        sent_tokens = [token for token in sent if not token.is_space]
        sentences.append({
            'sentence_id': i,
            'text': sent.text,
            'token_count': len(sent_tokens),
            'entity_count': len(list(sent.ents)),
            'root_verb': sent.root.text if sent.root.pos_ == 'VERB' else None,
            'complexity_score': len([token for token in sent if token.dep_ in ['compound', 'conj', 'prep']]),
            'named_entities': [{'text': ent.text, 'label': ent.label_} for ent in sent.ents]
        })
    
    result = {
        'metadata': {
            'analysis_time': datetime.now().isoformat(),
            'total_tokens': len([token for token in doc if not token.is_space]),
            'total_sentences': len(list(doc.sents)),
            'spacy_pipeline': nlp.pipe_names
        },
        'pos_distribution': dict(sorted(pos_counts.items(), key=lambda x: x[1], reverse=True)),
        'dependency_distribution': dict(sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)),
        'top_lemmas': dict(sorted(lemma_counts.items(), key=lambda x: x[1], reverse=True)[:50]),
        'noun_chunks': noun_chunks,
        'sentences': sentences,
        'document_stats': {
            'total_characters': len(doc.text),
            'unique_lemmas': len(lemma_counts),
            'avg_sentence_length': len([token for token in doc if not token.is_space]) / len(list(doc.sents)),
            'complexity_score': sum(len([token for token in sent if token.dep_ in ['compound', 'conj']]) for sent in doc.sents) / len(list(doc.sents))
        }
    }
    
    print(f"🟢 **SUCCESS**: Completed linguistic analysis - {len(pos_counts)} POS tags, {len(noun_chunks)} noun chunks")
    return result

def run_performance_analysis(processing_times: Dict[str, float]) -> Dict[str, Any]:
    """Analyze performance metrics."""
    print("🟡 **WAITING**: Analyzing performance metrics...")
    
    total_time = sum(processing_times.values())
    
    result = {
        'metadata': {
            'analysis_time': datetime.now().isoformat(),
            'spacy_model': 'en_core_web_sm',
            'cpu_optimized': True
        },
        'processing_times': processing_times,
        'total_processing_time': total_time,
        'time_breakdown': {
            component: {
                'time_ms': time_ms,
                'percentage': (time_ms / total_time) * 100
            }
            for component, time_ms in processing_times.items()
        },
        'performance_summary': {
            'fastest_component': min(processing_times.items(), key=lambda x: x[1]),
            'slowest_component': max(processing_times.items(), key=lambda x: x[1]),
            'average_component_time': total_time / len(processing_times)
        }
    }
    
    print(f"🟢 **SUCCESS**: Performance analysis completed - total time: {total_time:.2f}ms")
    return result

def generate_analysis_report(all_results: Dict[str, Any]) -> str:
    """Generate comprehensive analysis report."""
    print("🟡 **WAITING**: Generating comprehensive analysis report...")
    
    report = f"""# spaCy Complete Analysis Report

Generated: {datetime.now().isoformat()}

## Executive Summary

This report provides a comprehensive analysis of spaCy's capabilities applied to the entity extraction test document. All data has been exported to YAML and JSON formats for detailed examination.

### Key Metrics
- **Total Processing Time**: {all_results['performance']['total_processing_time']:.2f}ms
- **Raw Entities Extracted**: {all_results['raw_entities']['metadata']['total_entities']}
- **Entity Types Identified**: {all_results['raw_entities']['metadata']['entity_types']}
- **Canonical Forms Created**: {all_results['normalized_entities']['metadata']['total_canonical_forms']}
- **Semantic Rules Extracted**: {all_results['semantic_rules']['metadata']['total_rules']}
- **Relationships Identified**: {all_results['relationships']['metadata']['total_relationships']}

### Processing Pipeline Performance

| Component | Time (ms) | Percentage |
|-----------|-----------|------------|
"""
    
    for component, data in all_results['performance']['time_breakdown'].items():
        report += f"| {component.replace('_', ' ').title()} | {data['time_ms']:.2f} | {data['percentage']:.1f}% |\n"
    
    report += f"""
### Entity Extraction Results

#### Raw Entity Distribution
"""
    
    for entity_type, count in all_results['raw_entities']['distribution'].items():
        description = spacy.explain(entity_type)
        report += f"- **{entity_type}** ({description}): {count} entities\n"
    
    report += f"""
#### Normalization Effectiveness
"""
    
    for entity_type, data in all_results['normalized_entities']['summary'].items():
        report += f"- **{entity_type}**: {data['original']} → {data['canonical']} ({data['reduction']} reduction)\n"
    
    report += f"""
### Semantic Analysis Results

#### Semantic Rules by Type
"""
    
    for rule_type, count in all_results['semantic_rules']['distribution'].items():
        report += f"- **{rule_type.replace('_', ' ').title()}**: {count} rules\n"
    
    report += f"""
#### Relationship Analysis
"""
    
    for rel_type, count in sorted(all_results['relationships']['distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
        report += f"- **{rel_type}**: {count} relationships\n"
    
    report += f"""
### Linguistic Analysis

#### Document Statistics
- **Total Characters**: {all_results['linguistics']['document_stats']['total_characters']:,}
- **Total Sentences**: {all_results['linguistics']['metadata']['total_sentences']}
- **Average Sentence Length**: {all_results['linguistics']['document_stats']['avg_sentence_length']:.1f} tokens
- **Unique Lemmas**: {all_results['linguistics']['document_stats']['unique_lemmas']:,}
- **Complexity Score**: {all_results['linguistics']['document_stats']['complexity_score']:.2f}

#### Top Part-of-Speech Tags
"""
    
    for pos, count in list(all_results['linguistics']['pos_distribution'].items())[:10]:
        report += f"- **{pos}**: {count} occurrences\n"
    
    report += f"""
### File Outputs Generated

All detailed data has been exported to the following files for examination:

#### YAML Files
- `raw_entities.yaml` - All extracted entities with full metadata
- `normalized_entities.yaml` - Canonicalized entity forms and variants
- `semantic_rules.yaml` - Extracted semantic patterns and rules
- `relationships.yaml` - Entity relationships and co-occurrences
- `linguistics.yaml` - Complete linguistic analysis
- `performance.yaml` - Performance metrics and timing

#### JSON Files
- `raw_entities.json` - Raw entities in JSON format
- `normalized_entities.json` - Normalized entities in JSON format
- `semantic_rules.json` - Semantic rules in JSON format
- `relationships.json` - Relationships in JSON format
- `linguistics.json` - Linguistic analysis in JSON format
- `performance.json` - Performance data in JSON format
- `complete_results.json` - All results combined

### Conclusions

1. **Entity Extraction**: spaCy successfully identified {all_results['raw_entities']['metadata']['total_entities']} entities across {all_results['raw_entities']['metadata']['entity_types']} different types.

2. **Normalization**: Entity normalization achieved an average reduction of {(1 - all_results['normalized_entities']['metadata']['total_canonical_forms'] / all_results['normalized_entities']['metadata']['total_original_entities']) * 100:.1f}% through lemmatization and variant grouping.

3. **Semantic Analysis**: Extracted {all_results['semantic_rules']['metadata']['total_rules']} semantic rules and {all_results['relationships']['metadata']['total_relationships']} entity relationships.

4. **Performance**: Total processing time of {all_results['performance']['total_processing_time']:.2f}ms demonstrates good performance for comprehensive NLP analysis.

5. **Data Availability**: All detailed results are available in both YAML and JSON formats for thorough examination and validation.

---

*Report generated by spaCy Complete Analysis Tool*
*All data files available in: `/home/corey/projects/docling/mvp-fusion/spacy_test_outputs/`*
"""
    
    print(f"🟢 **SUCCESS**: Generated comprehensive analysis report")
    return report

def main():
    """Run complete spaCy analysis with full output generation."""
    print("🚀 spaCy COMPLETE ANALYSIS - FULL OUTPUT GENERATION")
    print("=" * 80)
    print("Generating ALL outputs (YAML, JSON, detailed files) for examination")
    print()
    
    # Load test document
    content = load_test_document()
    print(f"📄 Test document: {len(content)} characters")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print()
    
    # Initialize spaCy with CPU optimization
    print("🟡 **WAITING**: Loading spaCy pipeline...")
    spacy.require_cpu()
    nlp = spacy.load("en_core_web_sm")
    print(f"✅ Pipeline components: {nlp.pipe_names}")
    
    # Process document and track timing
    processing_times = {}
    all_results = {}
    
    # Process document
    start_time = time.perf_counter()
    doc = nlp(content)
    processing_times['document_processing'] = (time.perf_counter() - start_time) * 1000
    print(f"🟢 **SUCCESS**: Document processed in {processing_times['document_processing']:.2f}ms")
    print()
    
    # Extract raw entities
    start_time = time.perf_counter()
    raw_entities_result = extract_raw_entities(doc)
    processing_times['raw_entity_extraction'] = (time.perf_counter() - start_time) * 1000
    all_results['raw_entities'] = raw_entities_result
    
    # Save raw entities
    save_to_yaml(raw_entities_result, 'raw_entities')
    save_to_json(raw_entities_result, 'raw_entities')
    print()
    
    # Normalize entities
    start_time = time.perf_counter()
    normalized_result = normalize_entities(doc, raw_entities_result['all_entities'])
    processing_times['entity_normalization'] = (time.perf_counter() - start_time) * 1000
    all_results['normalized_entities'] = normalized_result
    
    # Save normalized entities
    save_to_yaml(normalized_result, 'normalized_entities')
    save_to_json(normalized_result, 'normalized_entities')
    print()
    
    # Extract semantic rules
    start_time = time.perf_counter()
    semantic_rules_result = extract_semantic_rules(doc)
    processing_times['semantic_rule_extraction'] = (time.perf_counter() - start_time) * 1000
    all_results['semantic_rules'] = semantic_rules_result
    
    # Save semantic rules
    save_to_yaml(semantic_rules_result, 'semantic_rules')
    save_to_json(semantic_rules_result, 'semantic_rules')
    print()
    
    # Extract relationships
    start_time = time.perf_counter()
    relationships_result = extract_relationships(doc)
    processing_times['relationship_extraction'] = (time.perf_counter() - start_time) * 1000
    all_results['relationships'] = relationships_result
    
    # Save relationships
    save_to_yaml(relationships_result, 'relationships')
    save_to_json(relationships_result, 'relationships')
    print()
    
    # Linguistic analysis
    start_time = time.perf_counter()
    linguistics_result = analyze_linguistics(doc, nlp)
    processing_times['linguistic_analysis'] = (time.perf_counter() - start_time) * 1000
    all_results['linguistics'] = linguistics_result
    
    # Save linguistics
    save_to_yaml(linguistics_result, 'linguistics')
    save_to_json(linguistics_result, 'linguistics')
    print()
    
    # Performance analysis
    performance_result = run_performance_analysis(processing_times)
    all_results['performance'] = performance_result
    
    # Save performance
    save_to_yaml(performance_result, 'performance')
    save_to_json(performance_result, 'performance')
    print()
    
    # Save complete combined results
    save_to_json(all_results, 'complete_results')
    print()
    
    # Generate analysis report
    report = generate_analysis_report(all_results)
    report_path = OUTPUT_DIR / "analysis_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"🟢 **SUCCESS**: Saved {report_path}")
    print()
    
    print("🎯 COMPLETE ANALYSIS FINISHED")
    print("=" * 80)
    print(f"📁 All outputs available in: {OUTPUT_DIR}")
    print()
    print("📄 Generated Files:")
    for file_path in sorted(OUTPUT_DIR.glob("*")):
        print(f"   - {file_path.name}")
    print()
    print("💡 You can now physically examine all YAML, JSON, and detailed output files!")

if __name__ == "__main__":
    main()