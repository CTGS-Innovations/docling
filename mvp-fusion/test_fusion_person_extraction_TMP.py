#!/usr/bin/env python3
"""
GOAL: Test the fusion pipeline person extraction method directly
REASON: Person entities still showing as empty after our fix
PROBLEM: Need to verify the fusion pipeline method is working
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from pipeline.fusion_pipeline import FusionPipeline
import yaml

def test_fusion_person_extraction():
    """Test the fusion pipeline person extraction directly"""
    
    print("🔍 TESTING FUSION PIPELINE PERSON EXTRACTION")
    print("=" * 50)
    
    # Load config
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize fusion pipeline
    fusion = FusionPipeline(config)
    
    # Test with simple person names first
    test_text = "John Smith is the CEO. Mary Johnson works at the company. Robert Chen completed the project."
    
    print(f"📝 Test text: {test_text}")
    
    # Test the specific method we fixed
    try:
        persons = fusion._extract_core8_person_flpc(test_text, None)
        print(f"\n✅ Fusion person extraction: {len(persons)} persons found")
        for person in persons:
            value = person.get('value', '')
            span = person.get('span', {})
            print(f"   - '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
            
    except Exception as e:
        print(f"\n❌ Fusion person extraction ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with challenging international names
    challenging_section = '''1. **Dr. Michael O'Brien** is the Chief Medical Officer.
2. **Xi Zhang** is a Software Engineer.
3. **José García-López** is an Environmental Consultant.
4. **François Dubois** is the International Liaison.
5. **Ahmed Al-Rashid** is a Security Specialist.
6. **Dr. Li** presented breakthrough research.
7. **Madonna** is the celebrity spokesperson.
8. **João Silva Santos** is the Brazilian Operations Manager.'''
    
    print(f"\n📝 Challenging international names test:")
    try:
        persons = fusion._extract_core8_person_flpc(challenging_section, None)
        print(f"✅ Full section: {len(persons)} persons found")
        for person in persons:
            value = person.get('value', '')
            span = person.get('span', {})
            print(f"   - '{value}' at {span.get('start', 0)}-{span.get('end', 0)}")
            
    except Exception as e:
        print(f"❌ Full section ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fusion_person_extraction()