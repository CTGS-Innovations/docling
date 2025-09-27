#!/usr/bin/env python3
"""
GOAL: Test text preprocessing fix for entity corruption
REASON: Implemented _clean_text_formatting to prevent dual PERSON/GPE detection
PROBLEM: Need to verify fix resolves corruption issues
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def test_text_preprocessing_fix():
    """Test that text preprocessing prevents dual entity detection"""
    
    # Test cases that previously caused dual detection
    test_cases = [
        {
            "name": "Clean Boston",
            "text": "Boston",
            "expected": "GPE only"
        },
        {
            "name": "Corrupted Boston",
            "text": "Boston\n\n\n      Boston",
            "expected": "GPE only (no PERSON)"
        },
        {
            "name": "Corrupted San Francisco",
            "text": "San Francisco\n\n\n      San Fransisco",
            "expected": "GPE only (no PERSON)"
        }
    ]
    
    print("🧪 TESTING TEXT PREPROCESSING FIX")
    print("=" * 45)
    
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    
    processor = ServiceProcessor(config)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Input: {repr(test_case['text'])}")
        print(f"   Expected: {test_case['expected']}")
        print("-" * 40)
        
        # Extract entities with the fix
        entities = processor._extract_universal_entities(test_case['text'])
        
        # Check results
        person_count = len(entities.get('person', []))
        gpe_count = len(entities.get('gpe', []))
        
        print(f"   Results:")
        print(f"     PERSON entities: {person_count}")
        print(f"     GPE entities: {gpe_count}")
        
        # Analyze if fix worked
        if person_count == 0 and gpe_count > 0:
            print(f"   ✅ SUCCESS: No dual detection - only GPE entity found")
        elif person_count > 0 and gpe_count > 0:
            print(f"   ❌ ISSUE: Still has dual detection (PERSON + GPE)")
            # Show the corrupted entity
            for person in entities.get('person', []):
                text = person.get('text', '')
                print(f"       PERSON text: {repr(text)}")
        else:
            print(f"   ⚠️  UNEXPECTED: person={person_count}, gpe={gpe_count}")

if __name__ == "__main__":
    test_text_preprocessing_fix()