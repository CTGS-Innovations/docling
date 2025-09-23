#!/usr/bin/env python3
"""
spaCy Output Format Converter
=============================
GOAL: Convert spaCy output to match MVP-Fusion's standard YAML/JSON format
REASON: User wants consistent formatting across all systems for easy comparison
PROBLEM: spaCy uses different field names and structure than MVP-Fusion

Converts:
- spaCy format: {start_char: 123, end_char: 456, text: "example"}
- MVP format: {span: {start: 123, end: 456}, text: "example", value: "example"}
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any

def convert_entity_to_mvp_format(entity: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single spaCy entity to MVP-Fusion format."""
    mvp_entity = {
        'value': entity.get('text', ''),
        'text': entity.get('text', ''),
        'type': entity.get('label', ''),
        'span': {
            'start': entity.get('start_char', 0),
            'end': entity.get('end_char', 0)
        }
    }
    
    # Add optional fields if they exist
    if 'confidence' in entity:
        mvp_entity['confidence'] = entity['confidence']
    if 'sentence_id' in entity:
        mvp_entity['sentence_id'] = entity['sentence_id']
    
    return mvp_entity

def convert_raw_entities(input_file: Path, output_file: Path):
    """Convert raw entities YAML to MVP format."""
    print(f"Converting {input_file} to MVP format...")
    
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Convert metadata
    mvp_data = {
        'metadata': {
            'extraction_time': data['metadata']['extraction_time'],
            'total_entities': data['metadata']['total_entities'], 
            'entity_types': data['metadata']['entity_types'],
            'model': data['metadata']['spacy_model']
        },
        'entities_by_type': {},
        'all_entities': []
    }
    
    # Convert entities by type
    for entity_type, entities in data.get('entities_by_type', {}).items():
        mvp_entities = []
        for entity in entities:
            mvp_entities.append(convert_entity_to_mvp_format(entity))
        mvp_data['entities_by_type'][entity_type] = mvp_entities
    
    # Convert all entities
    for entity in data.get('all_entities', []):
        mvp_data['all_entities'].append(convert_entity_to_mvp_format(entity))
    
    # Save in MVP format
    with open(output_file, 'w') as f:
        yaml.dump(mvp_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"✅ Saved MVP-formatted version: {output_file}")

def convert_semantic_rules(input_file: Path, output_file: Path):
    """Convert semantic rules to MVP format."""
    print(f"Converting {input_file} to MVP format...")
    
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)
    
    mvp_data = {
        'metadata': data.get('metadata', {}),
        'rules': []
    }
    
    # Convert each rule
    for rule in data.get('all_rules', []):
        mvp_rule = {
            'rule_id': rule.get('rule_id', ''),
            'rule_type': rule.get('rule_type', ''),
            'confidence': rule.get('confidence', 0.0),
            'entities': []
        }
        
        # Convert organization entities
        if 'organization' in rule:
            org = rule['organization']
            mvp_rule['entities'].append({
                'value': org.get('text', ''),
                'text': org.get('text', ''),
                'type': 'ORG',
                'span': {
                    'start': org.get('start', 0),
                    'end': org.get('end', 0)
                },
                'role': 'organization'
            })
        
        # Convert people entities
        for person in rule.get('people', []):
            mvp_rule['entities'].append({
                'value': person.get('text', ''),
                'text': person.get('text', ''),
                'type': 'PERSON',
                'span': {
                    'start': person.get('start', 0),
                    'end': person.get('end', 0)
                },
                'role': 'person'
            })
        
        # Convert money amounts
        if 'amount' in rule:
            amount = rule['amount']
            mvp_rule['entities'].append({
                'value': amount.get('text', ''),
                'text': amount.get('text', ''),
                'type': 'MONEY',
                'span': {
                    'start': amount.get('start', 0),
                    'end': amount.get('end', 0)
                },
                'role': 'amount'
            })
        
        # Convert dates
        if 'date' in rule:
            date = rule['date']
            mvp_rule['entities'].append({
                'value': date.get('text', ''),
                'text': date.get('text', ''),
                'type': 'DATE',
                'span': {
                    'start': date.get('start', 0),
                    'end': date.get('end', 0)
                },
                'role': 'date'
            })
        
        # Convert locations
        if 'location' in rule:
            loc = rule['location']
            mvp_rule['entities'].append({
                'value': loc.get('text', ''),
                'text': loc.get('text', ''),
                'type': loc.get('label', 'LOC'),
                'span': {
                    'start': loc.get('start', 0),
                    'end': loc.get('end', 0)
                },
                'role': 'location'
            })
        
        mvp_rule['context'] = rule.get('context', '')
        mvp_rule['sentence_id'] = rule.get('sentence_id', 0)
        
        mvp_data['rules'].append(mvp_rule)
    
    # Save in MVP format
    with open(output_file, 'w') as f:
        yaml.dump(mvp_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"✅ Saved MVP-formatted version: {output_file}")

def convert_relationships(input_file: Path, output_file: Path):
    """Convert relationships to MVP format."""
    print(f"Converting {input_file} to MVP format...")
    
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)
    
    mvp_data = {
        'metadata': data.get('metadata', {}),
        'relationships': []
    }
    
    # Convert each relationship
    for rel in data.get('all_relationships', []):
        mvp_rel = {
            'relationship_id': rel.get('relationship_id', ''),
            'relationship_type': rel.get('relationship_type', ''),
            'confidence': rel.get('relationship_strength', 0.0),
            'entity1': {
                'value': rel['entity1'].get('text', ''),
                'text': rel['entity1'].get('text', ''),
                'type': rel['entity1'].get('label', ''),
                'span': {
                    'start': rel['entity1'].get('start', 0),
                    'end': rel['entity1'].get('end', 0)
                }
            },
            'entity2': {
                'value': rel['entity2'].get('text', ''),
                'text': rel['entity2'].get('text', ''),
                'type': rel['entity2'].get('label', ''),
                'span': {
                    'start': rel['entity2'].get('start', 0),
                    'end': rel['entity2'].get('end', 0)
                }
            },
            'context': rel.get('context', ''),
            'sentence_id': rel.get('sentence_id', 0)
        }
        
        mvp_data['relationships'].append(mvp_rel)
    
    # Save in MVP format
    with open(output_file, 'w') as f:
        yaml.dump(mvp_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"✅ Saved MVP-formatted version: {output_file}")

def convert_normalized_entities(input_file: Path, output_file: Path):
    """Convert normalized entities to MVP format."""
    print(f"Converting {input_file} to MVP format...")
    
    with open(input_file, 'r') as f:
        data = yaml.safe_load(f)
    
    mvp_data = {
        'metadata': data.get('metadata', {}),
        'normalized_entities': {}
    }
    
    # Convert normalized entities by type
    for entity_type, type_data in data.get('normalized_by_type', {}).items():
        mvp_normalized = {
            'total_mentions': type_data.get('total_mentions', 0),
            'canonical_groups': type_data.get('canonical_groups', 0),
            'reduction_percentage': type_data.get('reduction_percentage', 0.0),
            'canonical_forms': []
        }
        
        for canonical in type_data.get('canonical_entities', []):
            mvp_canonical = {
                'canonical_form': canonical.get('canonical_form', ''),
                'canonical_text': canonical.get('canonical_text', ''),
                'mention_count': canonical.get('mention_count', 0),
                'variants': canonical.get('variants', []),
                'mentions': []
            }
            
            # Convert each mention
            for mention in canonical.get('all_mentions', []):
                mvp_mention = {
                    'text': mention.get('text', ''),
                    'span': {
                        'start': mention.get('start_char', 0),
                        'end': mention.get('end_char', 0)
                    }
                }
                mvp_canonical['mentions'].append(mvp_mention)
            
            mvp_normalized['canonical_forms'].append(mvp_canonical)
        
        mvp_data['normalized_entities'][entity_type] = mvp_normalized
    
    # Save in MVP format
    with open(output_file, 'w') as f:
        yaml.dump(mvp_data, f, default_flow_style=False, allow_unicode=True, indent=2)
    
    print(f"✅ Saved MVP-formatted version: {output_file}")

def main():
    """Convert all spaCy output files to MVP-Fusion format."""
    print("🚀 spaCy to MVP-Fusion Format Converter")
    print("=" * 60)
    
    base_dir = Path("/home/corey/projects/docling/mvp-fusion/spacy_test_outputs")
    
    # Define conversions
    conversions = [
        ('raw_entities.yaml', 'raw_entities_mvp.yaml', convert_raw_entities),
        ('normalized_entities.yaml', 'normalized_entities_mvp.yaml', convert_normalized_entities),
        ('semantic_rules.yaml', 'semantic_rules_mvp.yaml', convert_semantic_rules),
        ('relationships.yaml', 'relationships_mvp.yaml', convert_relationships)
    ]
    
    # Perform conversions
    for input_name, output_name, converter_func in conversions:
        input_file = base_dir / input_name
        output_file = base_dir / output_name
        
        if input_file.exists():
            converter_func(input_file, output_file)
        else:
            print(f"⚠️  Skipping {input_name} - file not found")
    
    print("\n✅ Format conversion complete!")
    print("All files now follow MVP-Fusion span format: {span: {start: X, end: Y}}")

if __name__ == "__main__":
    main()