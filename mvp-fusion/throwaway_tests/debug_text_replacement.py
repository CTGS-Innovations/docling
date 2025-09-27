#!/usr/bin/env python3
"""
GOAL: Debug why entity text replacement fails for measurements
REASON: Entities are detected and normalized but ||value||id|| tags don't appear in content
PROBLEM: _perform_global_replacement function is failing to substitute entity text
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_text_replacement():
    """Debug the text replacement system that should tag entities"""
    print("🔍 DEBUGGING TEXT REPLACEMENT SYSTEM")
    print("=" * 60)
    
    # Get the problematic entities from YAML
    with open('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md', 'r') as f:
        content = f.read()
    
    # Parse YAML frontmatter
    if content.startswith('---'):
        frontmatter_end = content.find('---', 3)
        if frontmatter_end != -1:
            frontmatter = content[3:frontmatter_end]
            markdown_content = content[frontmatter_end + 3:]
            
            try:
                metadata = yaml.safe_load(frontmatter)
                
                # Get canonical entities
                normalization = metadata.get('normalization', {})
                canonical_entities = normalization.get('canonical_entities', [])
                
                measurement_entities = [e for e in canonical_entities if e.get('type') == 'MEASUREMENT']
                
                print(f"📋 FOUND {len(measurement_entities)} CANONICAL MEASUREMENTS:")
                print("-" * 50)
                
                # Test each measurement entity
                for i, entity in enumerate(measurement_entities, 1):
                    entity_id = entity.get('id', 'unknown')
                    normalized = entity.get('normalized', 'unknown')
                    mentions = entity.get('mentions', [])
                    
                    if mentions:
                        original_text = mentions[0].get('text', 'unknown')
                        expected_tag = f"||{normalized}||{entity_id}||"
                        
                        print(f"🧪 Test {i}: '{original_text}'")
                        print(f"   Expected tag: {expected_tag}")
                        
                        # Check if original text exists in markdown
                        if original_text in markdown_content:
                            print(f"   ✅ Original text found in content")
                            
                            # Check if expected tag exists in markdown
                            if expected_tag in markdown_content:
                                print(f"   🟢 **SUCCESS**: Tag found in content")
                            else:
                                print(f"   🔴 **FAILED**: Tag NOT found in content")
                                
                                # Show context around original text
                                orig_pos = markdown_content.find(original_text)
                                if orig_pos != -1:
                                    context_start = max(0, orig_pos - 30)
                                    context_end = min(len(markdown_content), orig_pos + len(original_text) + 30)
                                    context = markdown_content[context_start:context_end]
                                    print(f"   📍 Context: ...{context}...")
                        else:
                            print(f"   ❌ Original text NOT found in content")
                            
                            # Try to find similar text
                            original_clean = original_text.strip()
                            if original_clean in markdown_content:
                                print(f"   🟡 Found trimmed version: '{original_clean}'")
                            else:
                                print(f"   ❌ Even trimmed version not found")
                        
                        print()
                
                # Special focus on "37 inches" case
                print(f"🎯 SPECIAL FOCUS: '37 inches' CASE:")
                print("-" * 40)
                
                # Find the 37 inches entity
                target_entity = None
                for entity in measurement_entities:
                    mentions = entity.get('mentions', [])
                    for mention in mentions:
                        text = mention.get('text', '')
                        if '37' in text and 'inch' in text.lower():
                            target_entity = entity
                            break
                    if target_entity:
                        break
                
                if target_entity:
                    entity_id = target_entity.get('id', 'unknown')
                    normalized = target_entity.get('normalized', 'unknown')
                    mentions = target_entity.get('mentions', [])
                    original_text = mentions[0].get('text', 'unknown')
                    span = mentions[0].get('span', {})
                    
                    print(f"Entity found: '{original_text}' → ||{normalized}||{entity_id}||")
                    print(f"Span: {span}")
                    
                    # Look for ALL occurrences of "37" and "inches" in content
                    import re
                    inch_patterns = re.findall(r'\d+[^\w]*inches?', markdown_content, re.IGNORECASE)
                    print(f"All inch measurements in content: {inch_patterns}")
                    
                    # Look for the specific range pattern
                    range_patterns = re.findall(r'\d+-\d+\s*inches?', markdown_content, re.IGNORECASE)
                    print(f"Range inch measurements: {range_patterns}")
                else:
                    print(f"❌ No 37 inches entity found in canonical entities")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    debug_text_replacement()