#!/usr/bin/env python3
"""
GOAL: Debug what keys are actually in the replacement map
REASON: Check if markdown detection is working correctly
PROBLEM: Still getting duplicate replacement issues
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_replacement_map_keys():
    """Debug what keys are actually in the replacement map"""
    print("🧪 DEBUGGING REPLACEMENT MAP KEYS")
    print("=" * 45)
    
    # Test the exact problematic text from Section 7
    test_text = """
### 7.1 Budget Items (10 amounts)
1. Safety equipment budget: **$500,000**
2. Training allocation: **$1.2 million**
3. Compliance software: **$250,000**
"""
    
    print(f"📄 TEST TEXT:")
    print(test_text)
    print("=" * 45)
    
    # Initialize ServiceProcessor and EntityNormalizer
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    from knowledge.extractors.entity_normalizer import EntityNormalizer
    
    processor = ServiceProcessor(config)
    normalizer = EntityNormalizer()
    
    try:
        print(f"🔍 STEP 1: ENTITY EXTRACTION")
        print("-" * 35)
        
        # Extract entities
        entities = processor._extract_universal_entities(test_text)
        money_entities = entities.get('money', [])
        
        print(f"Money entities found: {len(money_entities)}")
        for i, money in enumerate(money_entities, 1):
            text = money.get('text', '')
            value = money.get('value', '')
            span = money.get('span', {})
            print(f"  {i}. text: '{text}', value: '{value}', span: {span}")
        
        print(f"\n🔍 STEP 2: MANUAL REPLACEMENT MAP BUILDING")
        print("-" * 45)
        
        # Manually build replacement map to see the logic
        replacement_map = {}
        all_entities = {'money': money_entities}
        
        from dataclasses import dataclass
        from typing import List, Dict, Any
        
        @dataclass
        class NormalizedEntity:
            id: str
            normalized: str
            entity_type: str
            mentions: List[Dict[str, Any]]
        
        # Process money entities
        type_entities = []
        entity_id_counter = 1
        
        for entity in money_entities:
            entity_id = f"mon{entity_id_counter:03d}"
            entity_id_counter += 1
            
            normalized_entity = NormalizedEntity(
                id=entity_id,
                normalized=entity['text'].strip(),  # Preserve original format
                entity_type='MONEY',
                mentions=[{
                    'text': entity['text'],
                    'span': entity['span'],
                    'value': entity['value']
                }]
            )
            type_entities.append(normalized_entity)
        
        # Build replacement map with the same logic as in normalizer
        for entity in type_entities:
            for mention in entity.mentions:
                original_text = mention['text']
                
                print(f"Processing entity: '{original_text}'")
                
                # MARKDOWN COMPATIBILITY: Check if text is in markdown format first
                # Priority: most specific markdown > less specific > plain text
                markdown_versions = [
                    f"**{original_text}**",  # Bold (check first - most specific)
                    f"`{original_text}`",    # Code
                    f"*{original_text}*",    # Italic (check last - least specific)
                ]
                
                # Check for markdown versions in order of specificity
                found_markdown = False
                for markdown_version in markdown_versions:
                    if markdown_version in test_text:
                        print(f"  ✅ Found markdown version: '{markdown_version}' in text")
                        replacement_map[markdown_version] = (entity.normalized, entity.id)
                        found_markdown = True
                        break  # Only use the first (most specific) match
                    else:
                        print(f"  ❌ Markdown version NOT found: '{markdown_version}'")
                
                # Only add plain text if no markdown version was found
                if not found_markdown:
                    print(f"  ➡️ Adding plain text: '{original_text}'")
                    replacement_map[original_text] = (entity.normalized, entity.id)
                else:
                    print(f"  ➡️ Skipping plain text (markdown found): '{original_text}'")
        
        print(f"\n📋 FINAL REPLACEMENT MAP:")
        print("-" * 30)
        for key, (normalized, id_) in replacement_map.items():
            print(f"  '{key}' -> ('{normalized}', '{id_}')")
        
        print(f"\n📊 TOTAL REPLACEMENT KEYS: {len(replacement_map)}")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_replacement_map_keys()