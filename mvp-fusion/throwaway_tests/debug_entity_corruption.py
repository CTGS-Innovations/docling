#!/usr/bin/env python3
"""
GOAL: Debug raw entity extraction to find whitespace corruption
REASON: User reported entities like 'Boston\n\n\nBoston' with formatting issues
PROBLEM: Need to identify where corruption happens in the pipeline
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_entity_corruption():
    """Debug entity extraction phases to find where corruption occurs"""
    
    # Test text that might cause corruption (simulating HTML-to-markdown conversion)
    test_cases = [
        "Boston",  # Clean text
        "Boston\n\nBoston",  # Text with newlines
        "Boston\n\n\n      Boston",  # Text with newlines and spaces
        "San Francisco\n\n\n      San Fransisco",  # Typo + corruption
    ]
    
    print("🧪 DEBUGGING ENTITY CORRUPTION")
    print("=" * 45)
    
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    
    processor = ServiceProcessor(config)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {repr(test_case)}")
        print("-" * 30)
        
        # Extract raw entities
        entities = processor._extract_universal_entities(test_case)
        
        # Check all entity types for corruption
        for entity_type in ['person', 'org', 'gpe', 'loc']:
            if entity_type in entities and entities[entity_type]:
                print(f"  {entity_type.upper()}: {len(entities[entity_type])} entities")
                for entity in entities[entity_type]:
                    text = entity.get('text', '')
                    value = entity.get('value', '')
                    
                    # Check for corruption indicators
                    has_newlines = '\n' in text
                    has_extra_spaces = '  ' in text
                    text_differs = text != value
                    
                    print(f"    - text: {repr(text)}")
                    print(f"      value: {repr(value)}")
                    if has_newlines:
                        print(f"      🔴 HAS NEWLINES")
                    if has_extra_spaces:
                        print(f"      🔴 HAS EXTRA SPACES")
                    if text_differs:
                        print(f"      🔴 TEXT/VALUE DIFFER")
                    print()

if __name__ == "__main__":
    debug_entity_corruption()