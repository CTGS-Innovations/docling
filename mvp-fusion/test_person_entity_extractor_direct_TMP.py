#!/usr/bin/env python3
"""
GOAL: Test PersonEntityExtractor directly to see why it's returning 0 persons
REASON: Fusion pipeline shows 0 persons from PersonEntityExtractor
PROBLEM: Need to debug PersonEntityExtractor initialization or usage
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_person_entity_extractor_direct():
    """Test PersonEntityExtractor directly"""
    
    print("🔍 TESTING PERSONENTITYEXTRACTOR DIRECTLY")
    print("=" * 50)
    
    # Test import
    try:
        from utils.person_entity_extractor import PersonEntityExtractor
        print("✅ PersonEntityExtractor imported successfully")
        
        # Test initialization
        person_extractor = PersonEntityExtractor()
        print("✅ PersonEntityExtractor initialized successfully")
        
        # Test with simple text
        test_text = "John Smith is the CEO. Mary Johnson works at the company."
        print(f"\n📝 Test text: {test_text}")
        
        # Test extraction
        try:
            persons = person_extractor.extract_persons(test_text)
            print(f"✅ Extraction successful: {len(persons)} persons")
            
            for i, person in enumerate(persons):
                name = person.get('text', person.get('name', ''))
                position = person.get('position', 0)
                print(f"   {i+1}. '{name}' at position {position}")
                print(f"       Full person data: {person}")
                
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        
        # Try alternative imports that might exist
        print(f"\n🔧 Trying alternative imports:")
        
        alternatives = [
            "utils.conservative_person_extractor",
            "knowledge.extractors.person_extractor", 
            "extractors.person_extractor"
        ]
        
        for alt in alternatives:
            try:
                module = __import__(alt, fromlist=[''])
                print(f"   ✅ Found: {alt}")
                if hasattr(module, 'PersonEntityExtractor'):
                    print(f"      Has PersonEntityExtractor class")
                if hasattr(module, 'extract_persons'):
                    print(f"      Has extract_persons function")
            except ImportError:
                print(f"   ❌ Not found: {alt}")

if __name__ == "__main__":
    test_person_entity_extractor_direct()