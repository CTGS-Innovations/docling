#!/usr/bin/env python3
"""
GOAL: Debug why person extraction works in isolation but fails in full document
REASON: Debug test showed persons detected but full pipeline shows person: []
PROBLEM: Something is failing when processing the entire document
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.service_processor import ServiceProcessor
import yaml

def debug_full_document_person_extraction():
    """Debug person extraction on the full document"""
    
    print("🔍 DEBUGGING FULL DOCUMENT PERSON EXTRACTION")
    print("=" * 60)
    
    # Load config and initialize processor
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    processor = ServiceProcessor(config)
    
    # Load the full document
    source_file = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_file, 'r') as f:
        content = f.read()
    
    print(f"📄 Full document length: {len(content)} characters")
    
    # Test extractors on full document
    print(f"\n🔧 Testing extractors on full document:")
    
    # Test world-scale extractor
    if processor.world_scale_person_extractor:
        try:
            world_scale_persons = processor.world_scale_person_extractor.extract_persons(content)
            print(f"   World-scale extractor: {len(world_scale_persons)} persons")
            for i, person in enumerate(world_scale_persons[:5]):  # Show first 5
                name = person.get('text', person.get('name', ''))
                pos = person.get('position', 0)
                print(f"     {i+1}. '{name}' at position {pos}")
        except Exception as e:
            print(f"   World-scale extractor ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Test conservative extractor
    if processor.person_extractor:
        try:
            conservative_persons = processor.person_extractor.extract_persons(content)
            print(f"\n   Conservative extractor: {len(conservative_persons)} persons")
            for i, person in enumerate(conservative_persons[:5]):  # Show first 5
                name = person.get('text', person.get('name', ''))
                pos = person.get('position', 0)
                print(f"     {i+1}. '{name}' at position {pos}")
        except Exception as e:
            print(f"   Conservative extractor ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Test the full _extract_universal_entities method
    print(f"\n🔧 Testing _extract_universal_entities on full document:")
    try:
        entities = processor._extract_universal_entities(content)
        person_entities = entities.get('person', [])
        print(f"   Universal extraction: {len(person_entities)} persons")
        
        for i, entity in enumerate(person_entities[:10]):  # Show first 10
            value = entity.get('value', '')
            span = entity.get('span', {})
            print(f"     {i+1}. '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
        
        if len(person_entities) == 0:
            print(f"   🚨 NO PERSONS FOUND - This explains the empty person: [] in output")
        
    except Exception as e:
        print(f"   Universal extraction ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if the issue is with extractors not being initialized properly
    print(f"\n🔧 Extractor status:")
    print(f"   world_scale_person_extractor: {type(processor.world_scale_person_extractor)}")
    print(f"   person_extractor: {type(processor.person_extractor)}")
    
    # Test with a known working section
    known_working_section = '''1. **John Smith**, Chief Executive Officer at Global Dynamics Corporation, reported strong earnings.
2. **Mary Johnson**, Director of Engineering, will present at the conference on 2024-03-20.
3. **Robert Chen**, Senior Analyst, completed the regulatory review yesterday.'''
    
    print(f"\n🔧 Testing known working section again:")
    try:
        entities = processor._extract_universal_entities(known_working_section)
        person_entities = entities.get('person', [])
        print(f"   Known section: {len(person_entities)} persons")
        for entity in person_entities:
            value = entity.get('value', '')
            span = entity.get('span', {})
            print(f"     - '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
    except Exception as e:
        print(f"   Known section ERROR: {e}")

if __name__ == "__main__":
    debug_full_document_person_extraction()