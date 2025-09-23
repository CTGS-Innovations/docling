#!/usr/bin/env python3
"""
GOAL: Debug why person detection is failing for basic names like John Smith, Mary Johnson
REASON: Current output only shows fragments like "Michael", "James" instead of full names
PROBLEM: Person extractors may not be working or initialized properly
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.service_processor import ServiceProcessor
import yaml

def debug_person_extraction():
    """Debug the person extraction system"""
    
    print("🔍 DEBUGGING PERSON EXTRACTION")
    print("=" * 50)
    
    # Load config and initialize processor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    processor = ServiceProcessor(config)
    
    # Test with simple person names
    test_cases = [
        "John Smith is the CEO.",
        "Mary Johnson works at the company.",
        "Robert Chen completed the project.",
        "Dr. Sarah Williams presented the findings.",
        "Jennifer Martinez and David Kim attended the meeting."
    ]
    
    print(f"\n🔧 Testing person extractors:")
    print(f"   World-scale extractor available: {processor.world_scale_person_extractor is not None}")
    print(f"   Conservative extractor available: {processor.person_extractor is not None}")
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_text}")
        
        # Test world-scale extractor
        if processor.world_scale_person_extractor:
            try:
                world_scale_persons = processor.world_scale_person_extractor.extract_persons(test_text)
                print(f"     World-scale: {len(world_scale_persons)} persons")
                for person in world_scale_persons:
                    name = person.get('text', person.get('name', ''))
                    pos = person.get('position', 0)
                    print(f"       - '{name}' at position {pos}")
            except Exception as e:
                print(f"     World-scale ERROR: {e}")
        
        # Test conservative extractor
        if processor.person_extractor:
            try:
                conservative_persons = processor.person_extractor.extract_persons(test_text)
                print(f"     Conservative: {len(conservative_persons)} persons")
                for person in conservative_persons:
                    name = person.get('text', person.get('name', ''))
                    pos = person.get('position', 0)
                    print(f"       - '{name}' at position {pos}")
            except Exception as e:
                print(f"     Conservative ERROR: {e}")
    
    # Test with the actual document problematic section
    problematic_text = '''1. **John Smith**, Chief Executive Officer at Global Dynamics Corporation, reported strong earnings.
2. **Mary Johnson**, Director of Engineering, will present at the conference on 2024-03-20.
3. **Robert Chen**, Senior Analyst, completed the regulatory review yesterday.'''
    
    print(f"\n🔧 Testing with problematic document section:")
    print(f"   Text: {problematic_text}")
    
    # Test _extract_universal_entities method
    try:
        entities = processor._extract_universal_entities(problematic_text)
        person_entities = entities.get('person', [])
        print(f"\n   Universal extraction result: {len(person_entities)} persons")
        for entity in person_entities:
            value = entity.get('value', '')
            span = entity.get('span', {})
            print(f"     - '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
    except Exception as e:
        print(f"   Universal extraction ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if we can use Core-8 automatons for person detection as fallback
    if hasattr(processor, 'core8_automatons') and 'PERSON' in processor.core8_automatons:
        print(f"\n🔧 Testing Core-8 PERSON automaton as fallback:")
        person_automaton = processor.core8_automatons['PERSON']
        
        automaton_results = []
        for end_pos, (entity_type, canonical) in person_automaton.iter(problematic_text.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = problematic_text[start_pos:end_pos + 1]
            if len(original_text) > 2:
                automaton_results.append((original_text, start_pos, end_pos + 1))
        
        print(f"   Core-8 automaton: {len(automaton_results)} matches")
        for text, start, end in automaton_results[:10]:  # Show first 10
            print(f"     - '{text}' at {start}-{end}")

if __name__ == "__main__":
    debug_person_extraction()