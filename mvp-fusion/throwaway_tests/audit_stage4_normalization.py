#!/usr/bin/env python3
"""
GOAL: Audit Stage 4 - Entity normalization (canonicalize_entities)
REASON: 12 measurements enter Stage 4, but only 6 get tagged in final output
PROBLEM: Need to verify if normalization loses measurements or creates wrong mappings
"""

import sys
import os
import yaml

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def audit_stage4_normalization():
    """Audit Stage 4: Entity normalization in isolation"""
    print("🔍 STAGE 4 AUDIT: ENTITY NORMALIZATION")
    print("=" * 60)
    
    # Step 1: Get Stage 3 output (the input to Stage 4)
    source_path = '/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_MD_DOCUMENT.md'
    with open(source_path, 'r') as f:
        source_content = f.read()
    
    # Get entities from Stage 3
    with open('/home/corey/projects/docling/mvp-fusion/config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from pipeline.legacy.service_processor import ServiceProcessor
    processor = ServiceProcessor(config)
    stage3_entities = processor._extract_universal_entities(source_content)
    
    print(f"📄 STAGE 3 OUTPUT (Input to Stage 4):")
    print(f"   Measurements: {len(stage3_entities.get('measurement', []))}")
    print(f"   Range indicators: {len(stage3_entities.get('range_indicator', []))}")
    
    # Step 2: Test Stage 4 directly
    print(f"\n🔍 TESTING STAGE 4 DIRECTLY:")
    print("-" * 40)
    
    from knowledge.extractors.entity_normalizer import EntityNormalizer
    normalizer = EntityNormalizer(config)
    
    try:
        # This is the exact function called in Stage 4
        print("🧪 Calling canonicalize_entities() directly...")
        
        normalization_result = normalizer.normalize_entities_phase(stage3_entities, source_content)
        
        print(f"✅ Stage 4 completed successfully")
        
        # Audit the normalization result
        canonical_entities = normalization_result.normalized_entities
        normalized_text = normalization_result.normalized_text
        
        # Filter measurement entities
        measurement_canonical = [e for e in canonical_entities if e.type == 'MEASUREMENT']
        
        print(f"📊 NORMALIZATION RESULTS:")
        print(f"   Input measurements: {len(stage3_entities.get('measurement', []))}")
        print(f"   Output canonical measurements: {len(measurement_canonical)}")
        print(f"   Text length before: {len(source_content):,} chars")
        print(f"   Text length after: {len(normalized_text):,} chars")
        
        # Show canonical measurement entities
        print(f"\n🔍 CANONICAL MEASUREMENT SAMPLE:")
        for i, entity in enumerate(measurement_canonical[:10], 1):
            entity_id = entity.id
            normalized = entity.normalized
            mentions = entity.mentions
            if mentions:
                original_text = mentions[0]['text']
                print(f"   {i}. '{original_text}' → ||{normalized}||{entity_id}||")
        
        # Check for "37 inches" specifically
        print(f"\n🎯 SPECIFIC: '37 inches' NORMALIZATION:")
        found_37_canonical = False
        for entity in measurement_canonical:
            mentions = entity.mentions
            for mention in mentions:
                text = mention['text']
                if '37' in text and 'inch' in text.lower():
                    found_37_canonical = True
                    expected_tag = f"||{entity.normalized}||{entity.id}||"
                    print(f"   ✅ Found: '{text}' → {expected_tag}")
        
        if not found_37_canonical:
            print(f"   ❌ '37 inches' NOT found in canonical entities")
        
        # Step 3: Check text replacement
        print(f"\n🔍 TEXT REPLACEMENT VERIFICATION:")
        print("-" * 40)
        
        # Count tags in normalized text
        import re
        tag_pattern = r'\|\|[^|]+\|\|[^|]+\|\|'
        tags_found = re.findall(tag_pattern, normalized_text)
        
        print(f"📊 TAGS IN NORMALIZED TEXT:")
        print(f"   Total ||value||id|| tags found: {len(tags_found)}")
        
        # Show first 10 tags
        print(f"\n🔍 TAG SAMPLE:")
        for i, tag in enumerate(tags_found[:10], 1):
            print(f"   {i}. {tag}")
        
        # Check if "37 inches" tag exists in normalized text
        if found_37_canonical:
            # Find the specific 37 inches entity
            target_entity = None
            for entity in measurement_canonical:
                mentions = entity.mentions
                for mention in mentions:
                    text = mention['text']
                    if '37' in text and 'inch' in text.lower():
                        target_entity = entity
                        break
                if target_entity:
                    break
            
            if target_entity:
                expected_tag = f"||{target_entity.normalized}||{target_entity.id}||"
                if expected_tag in normalized_text:
                    print(f"\n🟢 **SUCCESS**: '37 inches' tag found in normalized text!")
                    print(f"   Tag: {expected_tag}")
                else:
                    print(f"\n🔴 **FAILED**: '37 inches' tag NOT found in normalized text")
                    print(f"   Expected: {expected_tag}")
                    
                    # Show context where original text should be
                    original_text = target_entity.mentions[0]['text']
                    if original_text in source_content:
                        print(f"   Original '{original_text}' exists in source")
                        if original_text in normalized_text:
                            print(f"   🔴 PROBLEM: Original text still exists in normalized text (replacement failed)")
                        else:
                            print(f"   🔴 PROBLEM: Original text gone but no tag found (replacement error)")
        
        # Step 4: Compare input vs output entity counts
        print(f"\n📊 STAGE 4 SUMMARY:")
        print("-" * 40)
        
        stage3_measurement_count = len(stage3_entities.get('measurement', []))
        stage4_measurement_count = len(measurement_canonical)
        tags_in_text = len(tags_found)
        
        print(f"   Stage 3 → Stage 4: {stage3_measurement_count} measurements")
        print(f"   Stage 4 canonical: {stage4_measurement_count} measurements")
        print(f"   Tags in text: {tags_in_text} total tags")
        
        if stage3_measurement_count == stage4_measurement_count:
            print(f"   ✅ No measurements lost in normalization")
        else:
            print(f"   🔴 Lost {stage3_measurement_count - stage4_measurement_count} measurements in normalization")
        
        if tags_in_text > 0:
            print(f"   ✅ Text replacement partially working")
        else:
            print(f"   🔴 Text replacement completely failed")
        
    except Exception as e:
        print(f"🔴 **BLOCKED**: Stage 4 failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    audit_stage4_normalization()