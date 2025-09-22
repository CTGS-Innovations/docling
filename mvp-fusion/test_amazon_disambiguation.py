#!/usr/bin/env python3
"""
Amazon Entity Disambiguation Test
================================

Test how different Amazon entities are currently being detected and ranked.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from hybrid_entity_metadata_system import HybridEntityMetadataSystem

def test_amazon_disambiguation():
    """Test current Amazon disambiguation behavior"""
    
    test_cases = [
        "Amazon River flows through South America.",
        "Amazon Web Services provides cloud computing.",
        "Amazon sells books online.",
        "Amazon Rainforest is being protected.",
        "Amazon AI develops machine learning tools.",
        "The Amazon basin covers multiple countries.",
        "Amazon Prime offers streaming services.",
        "Environmental studies of the Amazon region continue."
    ]
    
    print("🧪 Amazon Entity Disambiguation Analysis")
    print("=" * 50)
    
    system = HybridEntityMetadataSystem()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. Test: '{test_text}'")
        result = system.extract_hybrid_metadata(test_text)
        
        all_entities = []
        for entity in result["raw_entities"]["gpe"]:
            all_entities.append(f"GPE:{entity.subcategory} - {entity.value}")
        for entity in result["raw_entities"]["loc"]:
            all_entities.append(f"LOC:{entity.subcategory} - {entity.value}")
        
        amazon_entities = [e for e in all_entities if "amazon" in e.lower()]
        
        if amazon_entities:
            print(f"   → {amazon_entities[0]}")
        else:
            print("   → No Amazon entities detected")

def analyze_current_detection_order():
    """Analyze how entities are currently prioritized"""
    
    print(f"\n🔍 Current Detection Order Analysis")
    print("-" * 40)
    
    # Test text with multiple Amazon variants
    test_text = """
    Amazon Web Services announced a partnership with Amazon AI to improve 
    cloud services. This affects the Amazon Rainforest research funded by 
    Amazon and conducted near the Amazon River basin.
    """
    
    system = HybridEntityMetadataSystem()
    result = system.extract_hybrid_metadata(test_text)
    
    print("Detected entities in order:")
    all_entities = []
    
    # Collect all entities with positions
    for entity in result["raw_entities"]["gpe"]:
        all_entities.append({
            'text': entity.value,
            'type': f"GPE:{entity.subcategory}",
            'start': entity.span['start'],
            'end': entity.span['end']
        })
    
    for entity in result["raw_entities"]["loc"]:
        all_entities.append({
            'text': entity.value,
            'type': f"LOC:{entity.subcategory}",
            'start': entity.span['start'],
            'end': entity.span['end']
        })
    
    # Sort by position
    all_entities.sort(key=lambda x: x['start'])
    
    for i, entity in enumerate(all_entities, 1):
        print(f"  {i}. {entity['text']} [{entity['type']}] @ {entity['start']}-{entity['end']}")

def check_foundation_data_conflicts():
    """Check what Amazon variants exist in foundation data"""
    
    print(f"\n📋 Foundation Data Amazon Variants")
    print("-" * 35)
    
    foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
    
    amazon_variants = {}
    
    # Check ORG data (likely where Amazon company is)
    try:
        # Look for organization files
        for file_path in foundation_path.glob("**/*.txt"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = [line.strip() for line in content.split('\n') if 'amazon' in line.lower()]
                        if lines:
                            category = file_path.stem.replace('_2025_09_22', '').replace('_2025_09_18', '')
                            amazon_variants[category] = lines
                except:
                    continue
        
        for category, variants in amazon_variants.items():
            print(f"  {category}:")
            for variant in variants:
                print(f"    - {variant}")
    
    except Exception as e:
        print(f"Error scanning foundation data: {e}")

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_amazon_disambiguation()
    analyze_current_detection_order()
    check_foundation_data_conflicts()