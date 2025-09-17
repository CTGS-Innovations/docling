#!/usr/bin/env python3
"""
Test Enhanced Entity Disambiguation and Fact Extraction
========================================================
Demonstrates the improved entity filtering and atomic fact generation.
"""

import json
import sys
from pathlib import Path

# Add project paths
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / 'utils'))

from utils.entity_disambiguator import EntityDisambiguator
from utils.enhanced_semantic_extractor import EnhancedSemanticExtractor

def test_disambiguation():
    """Test entity disambiguation with challenging examples."""
    
    print("=" * 60)
    print("TESTING ENTITY DISAMBIGUATION")
    print("=" * 60)
    
    disambiguator = EntityDisambiguator()
    
    # Test content with ambiguous entities
    test_content = """
    Tim Cook, CEO of Apple Inc., announced that Apple will invest $1 billion in AI research.
    The investment was praised by Morgan Stanley analysts. John Morgan, senior analyst at 
    Morgan Stanley, said this positions Apple ahead of Microsoft Corporation in the AI race.
    
    Meanwhile, Ford Motor Company CEO Jim Farley met with Tesla's Elon Musk to discuss 
    electric vehicle partnerships. Harrison Ford attended the meeting as a brand ambassador.
    
    Salesforce acquired Slack for $27.7 billion, while Adobe acquired Figma for $20 billion.
    Marc Benioff, founder and CEO of Salesforce, called it a transformative deal.
    
    Google's parent company Alphabet reported 32% growth year-over-year. Sundar Pichai,
    CEO of both Google and Alphabet, highlighted their cloud division's performance.
    """
    
    # Simulate extracted entities (with some misclassifications to fix)
    raw_entities = {
        'person': [
            {'value': 'Tim Cook', 'span': {'start': 5, 'end': 13}},
            {'value': 'Morgan Stanley', 'span': {'start': 134, 'end': 148}},  # Misclassified
            {'value': 'John Morgan', 'span': {'start': 159, 'end': 170}},
            {'value': 'Jim Farley', 'span': {'start': 340, 'end': 350}},
            {'value': 'Elon Musk', 'span': {'start': 370, 'end': 379}},
            {'value': 'Harrison Ford', 'span': {'start': 425, 'end': 438}},
            {'value': 'Marc Benioff', 'span': {'start': 577, 'end': 589}},
            {'value': 'Sundar Pichai', 'span': {'start': 724, 'end': 737}},
        ],
        'org': [
            {'value': 'Apple Inc', 'span': {'start': 22, 'end': 31}},
            {'value': 'Apple', 'span': {'start': 48, 'end': 53}},  # Duplicate
            {'value': 'Microsoft Corporation', 'span': {'start': 256, 'end': 277}},
            {'value': 'Ford Motor Company', 'span': {'start': 312, 'end': 330}},
            {'value': 'Tesla', 'span': {'start': 361, 'end': 366}},
            {'value': 'Salesforce', 'span': {'start': 487, 'end': 497}},
            {'value': 'Slack', 'span': {'start': 507, 'end': 512}},
            {'value': 'Adobe', 'span': {'start': 540, 'end': 545}},
            {'value': 'Figma', 'span': {'start': 555, 'end': 560}},
            {'value': 'Google', 'span': {'start': 660, 'end': 666}},
            {'value': 'Alphabet', 'span': {'start': 685, 'end': 693}},
        ]
    }
    
    # Run disambiguation
    disambiguated = disambiguator.disambiguate_entities(raw_entities, test_content)
    
    # Display results
    print("\n🔍 PERSONS (Disambiguated):")
    print("-" * 40)
    for person in disambiguated.get('persons', []):
        print(f"  • {person.normalized_text}")
        print(f"    Type: {person.entity_type}, Subtype: {person.entity_subtype or 'None'}")
        print(f"    Confidence: {person.confidence:.2f}")
        if person.aliases:
            print(f"    Aliases: {', '.join(person.aliases)}")
        if person.relationships:
            print(f"    Relationships: {person.relationships}")
        print()
    
    print("\n🏢 ORGANIZATIONS (Disambiguated):")
    print("-" * 40)
    for org in disambiguated.get('organizations', []):
        print(f"  • {org.normalized_text}")
        print(f"    Type: {org.entity_type}, Subtype: {org.entity_subtype or 'None'}")
        print(f"    Confidence: {org.confidence:.2f}")
        if org.aliases:
            print(f"    Aliases: {', '.join(org.aliases)}")
        if org.relationships:
            print(f"    Relationships: {org.relationships}")
        print()
    
    # Show summary
    summary = disambiguator.generate_entity_summary(disambiguated)
    print("\n📊 DISAMBIGUATION SUMMARY:")
    print("-" * 40)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    return disambiguated, test_content

def test_enhanced_extraction(disambiguated_entities, content):
    """Test enhanced semantic extraction with disambiguated entities."""
    
    print("\n" + "=" * 60)
    print("TESTING ENHANCED FACT EXTRACTION")
    print("=" * 60)
    
    extractor = EnhancedSemanticExtractor()
    
    # Convert disambiguated format to raw format for testing
    raw_entities = {
        'person': [{'value': e.original_text} for e in disambiguated_entities.get('persons', [])],
        'org': [{'value': e.original_text} for e in disambiguated_entities.get('organizations', [])]
    }
    
    # Extract enhanced facts
    result = extractor.extract_enhanced_facts(content, raw_entities)
    
    print("\n🎯 ATOMIC FACTS EXTRACTED:")
    print("-" * 40)
    
    facts = result['facts']['atomic_facts']
    for fact in facts[:10]:  # Show first 10 facts
        print(f"\n  Fact #{fact['fact_id']}:")
        print(f"    Type: {fact['type']}")
        print(f"    {fact['subject']} ({fact['subject_type']})")
        print(f"    → {fact['predicate']}")
        print(f"    → {fact['object']} ({fact.get('object_type', 'N/A')})")
        if fact.get('context'):
            print(f"    Context: {fact['context']}")
        print(f"    Confidence: {fact['confidence']:.2f}")
    
    print(f"\n  ... and {len(facts) - 10} more facts" if len(facts) > 10 else "")
    
    print("\n📊 FACT TYPE DISTRIBUTION:")
    print("-" * 40)
    for fact_type, count in result['facts']['fact_types'].items():
        print(f"  {fact_type}: {count}")
    
    print(f"\n  Total Facts: {result['facts']['total_facts']}")
    
    print("\n🚀 FOUNDER INTELLIGENCE CLUSTERS:")
    print("-" * 40)
    founder_intel = result['founder_intelligence']
    for cluster, facts in founder_intel.items():
        if cluster == 'key_entities':
            print(f"\n  📌 {cluster}:")
            if 'top_persons' in facts:
                print("    Top Persons:")
                for person in facts['top_persons']:
                    print(f"      • {person['name']} ({person['confidence']:.2f})")
            if 'top_organizations' in facts:
                print("    Top Organizations:")
                for org in facts['top_organizations']:
                    print(f"      • {org['name']} ({org['confidence']:.2f})")
        elif facts:
            print(f"\n  📌 {cluster}: {len(facts)} facts")
    
    return result

def test_edge_cases():
    """Test edge cases and challenging scenarios."""
    
    print("\n" + "=" * 60)
    print("TESTING EDGE CASES")
    print("=" * 60)
    
    disambiguator = EntityDisambiguator()
    
    # Edge case 1: Company names that look like person names
    test1 = "Morgan Stanley upgraded Apple to buy. Stanley Morgan, analyst at Morgan Stanley, agrees."
    
    # Edge case 2: Person with company-like name
    test2 = "John Company founded a startup. Company Inc. was later acquired by Microsoft."
    
    # Edge case 3: Mixed context
    test3 = "Apple Cook (the chef) works at Apple Inc. Tim Cook leads Apple's innovation."
    
    test_cases = [
        ("Company as Person Name", test1),
        ("Person with Company-like Name", test2),
        ("Mixed Context", test3)
    ]
    
    for case_name, content in test_cases:
        print(f"\n🔬 {case_name}:")
        print(f"   Content: {content[:80]}...")
        
        # Simple entity extraction simulation
        entities = {
            'person': [{'value': name} for name in ['Stanley Morgan', 'John Company', 'Apple Cook', 'Tim Cook']],
            'org': [{'value': name} for name in ['Morgan Stanley', 'Apple', 'Company Inc', 'Microsoft', 'Apple Inc']]
        }
        
        result = disambiguator.disambiguate_entities(entities, content)
        print(f"   Persons: {[p.normalized_text for p in result['persons']]}")
        print(f"   Orgs: {[o.normalized_text for o in result['organizations']]}")

if __name__ == "__main__":
    print("🚀 Enhanced Entity Disambiguation & Fact Extraction Test")
    print("=" * 60)
    
    # Test disambiguation
    disambiguated, content = test_disambiguation()
    
    # Test enhanced extraction
    result = test_enhanced_extraction(disambiguated, content)
    
    # Test edge cases
    test_edge_cases()
    
    print("\n✅ Test completed successfully!")
    
    # Optionally save results
    output_file = Path("enhanced_extraction_results.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n💾 Results saved to {output_file}")