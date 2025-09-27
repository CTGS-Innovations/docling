#!/usr/bin/env python3
"""
GOAL: Debug why 77 FLPC-detected measurements don't get tagged as ||value||id||
REASON: FLPC detects measurements but final markdown shows untagged measurements
PROBLEM: Entity tagging system is the bottleneck, not FLPC detection
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def debug_entity_tagging():
    """Debug the entity tagging system that converts entities to ||value||id|| format"""
    print("🔍 DEBUGGING ENTITY TAGGING SYSTEM")
    print("=" * 60)
    
    # Check YAML frontmatter from newly processed document
    with open('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_MD_DOCUMENT.md', 'r') as f:
        content = f.read()
    
    # Parse YAML frontmatter
    if content.startswith('---'):
        frontmatter_end = content.find('---', 3)
        if frontmatter_end != -1:
            frontmatter = content[3:frontmatter_end]
            
            try:
                metadata = yaml.safe_load(frontmatter)
                
                print("📋 PROCESSING PIPELINE ANALYSIS:")
                print("-" * 40)
                
                # Check raw entities
                raw_entities = metadata.get('raw_entities', {})
                measurement_entities = raw_entities.get('measurement', [])
                range_indicators = raw_entities.get('range_indicator', [])
                
                print(f"✅ Raw measurements detected: {len(measurement_entities)}")
                print(f"✅ Raw range indicators detected: {len(range_indicators)}")
                
                # Show sample raw measurements
                print("\n🔍 RAW MEASUREMENT SAMPLE:")
                for i, measurement in enumerate(measurement_entities[:10], 1):
                    text = measurement.get('text', 'N/A')
                    mtype = measurement.get('type', 'N/A')
                    span = measurement.get('span', {})
                    print(f"   {i}. '{text}' ({mtype}) [{span.get('start')}-{span.get('end')}]")
                
                # Check normalized entities
                normalization = metadata.get('normalization', {})
                canonical_entities = normalization.get('canonical_entities', [])
                
                measurement_canonical = [e for e in canonical_entities if e.get('type') == 'MEASUREMENT']
                print(f"\n✅ Canonical measurements: {len(measurement_canonical)}")
                
                # Show sample canonical measurements
                print("\n🔍 CANONICAL MEASUREMENT SAMPLE:")
                for i, measurement in enumerate(measurement_canonical[:10], 1):
                    normalized = measurement.get('normalized', 'N/A')
                    entity_id = measurement.get('id', 'N/A')
                    mentions = measurement.get('mentions', [])
                    if mentions:
                        text = mentions[0].get('text', 'N/A')
                        print(f"   {i}. '{text}' → {normalized} (ID: {entity_id})")
                
                print()
                
                # Critical question: Are the entities being tagged in the content?
                print("🎯 ENTITY TAGGING ANALYSIS:")
                print("-" * 40)
                
                # Check if any of the canonical measurements appear as tags in content
                tagged_count = 0
                untagged_count = 0
                
                for measurement in measurement_canonical:
                    entity_id = measurement.get('id', 'unknown')
                    normalized = measurement.get('normalized', 'unknown')
                    
                    # Look for the tag pattern ||normalized||entity_id|| in content
                    tag_pattern = f"||{normalized}||{entity_id}||"
                    if tag_pattern in content:
                        tagged_count += 1
                        print(f"   ✅ Tagged: {tag_pattern}")
                    else:
                        untagged_count += 1
                        if untagged_count <= 5:  # Show first 5 untagged
                            mentions = measurement.get('mentions', [])
                            if mentions:
                                original_text = mentions[0].get('text', 'N/A')
                                print(f"   ❌ Untagged: '{original_text}' → should be {tag_pattern}")
                
                print(f"\n📊 TAGGING SUMMARY:")
                print(f"   Tagged entities: {tagged_count}")
                print(f"   Untagged entities: {untagged_count}")
                print(f"   Tagging success rate: {(tagged_count / (tagged_count + untagged_count) * 100):.1f}%")
                
                # Check specific "30-37 inches" case
                print(f"\n🎯 SPECIFIC: '30-37 inches' TRACING:")
                print("-" * 40)
                
                # Look for any measurements related to 37 inches
                found_37_raw = False
                found_37_canonical = False
                
                for measurement in measurement_entities:
                    text = measurement.get('text', '')
                    if '37' in text and 'inch' in text.lower():
                        found_37_raw = True
                        print(f"   ✅ Raw: Found '{text}' in raw measurements")
                
                for measurement in measurement_canonical:
                    mentions = measurement.get('mentions', [])
                    for mention in mentions:
                        text = mention.get('text', '')
                        if '37' in text and 'inch' in text.lower():
                            found_37_canonical = True
                            entity_id = measurement.get('id', 'unknown')
                            normalized = measurement.get('normalized', 'unknown')
                            expected_tag = f"||{normalized}||{entity_id}||"
                            print(f"   ✅ Canonical: Found '{text}' → {expected_tag}")
                            
                            # Check if this tag exists in content
                            if expected_tag in content:
                                print(f"   🟢 **SUCCESS**: Tag found in content!")
                            else:
                                print(f"   🔴 **FAILED**: Tag NOT found in content")
                
                if not found_37_raw:
                    print(f"   ❌ '37 inches' NOT found in raw measurements")
                if not found_37_canonical:
                    print(f"   ❌ '37 inches' NOT found in canonical measurements")
                
            except Exception as e:
                print(f"❌ Error parsing YAML: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    debug_entity_tagging()