#!/usr/bin/env python3
"""
Direct Integration Test
======================

Test the enhanced extraction directly in the service processor.
"""

import sys
from pathlib import Path
import re
from typing import Dict, List, Any

sys.path.append(str(Path(__file__).parent))

# Import the enhanced system directly
from hybrid_entity_metadata_system import HybridEntityMetadataSystem

def test_direct_extraction():
    """Test enhanced extraction directly"""
    
    # Read test document
    doc_path = Path("/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_TXT_DOCUMENT.txt")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🧪 Direct Enhanced Extraction Test")
    print("=" * 40)
    
    # Test hybrid system directly
    hybrid_system = HybridEntityMetadataSystem()
    result = hybrid_system.extract_hybrid_metadata(content)
    
    # Show results
    gpe_entities = result["raw_entities"]["gpe"]
    loc_entities = result["raw_entities"]["loc"]
    
    print(f"📊 GPE Entities: {len(gpe_entities)}")
    print(f"🌍 LOC Entities: {len(loc_entities)}")
    
    # Show samples with subcategories
    print(f"\nGPE Sample (first 10):")
    for i, entity in enumerate(gpe_entities[:10], 1):
        print(f"  {i:2d}. {entity.value} [{entity.subcategory}] @ {entity.span}")
    
    print(f"\nLOC Sample (first 10):")
    for i, entity in enumerate(loc_entities[:10], 1):
        print(f"  {i:2d}. {entity.value} [{entity.subcategory}] @ {entity.span}")
    
    # Test if we can convert to service processor format
    print(f"\n🔧 Service Processor Format Conversion:")
    enhanced_format = {
        'gpe': [],
        'location': []
    }
    
    # Convert GPE
    for entity in gpe_entities:
        enhanced_format['gpe'].append({
            'value': entity.value,
            'text': entity.text,
            'type': entity.entity_type,
            'subcategory': entity.subcategory,  # This is the key addition
            'span': entity.span
        })
    
    # Convert LOC
    for entity in loc_entities:
        enhanced_format['location'].append({
            'value': entity.value,
            'text': entity.text,
            'type': 'LOCATION',
            'subcategory': entity.subcategory,  # This is the key addition
            'span': entity.span
        })
    
    print(f"Converted GPE: {len(enhanced_format['gpe'])}")
    print(f"Converted LOC: {len(enhanced_format['location'])}")
    
    # Show format example
    if enhanced_format['gpe']:
        print(f"\nGPE Format Example:")
        sample_gpe = enhanced_format['gpe'][0]
        for key, value in sample_gpe.items():
            print(f"  {key}: {value}")
    
    if enhanced_format['location']:
        print(f"\nLOC Format Example:")
        sample_loc = enhanced_format['location'][0]
        for key, value in sample_loc.items():
            print(f"  {key}: {value}")
    
    return enhanced_format

def test_import_integration():
    """Test if the enhanced extraction can be imported from service processor"""
    
    print(f"\n🔧 Testing Import Integration:")
    print("-" * 30)
    
    try:
        from enhanced_service_processor_integration import EnhancedEntityExtraction
        enhancer = EnhancedEntityExtraction()
        print("✅ Enhanced extraction import successful")
        
        # Test with sample text
        test_text = "EPA announced regulations for Texas. Pacific Ocean cleanup involves Rocky Mountains."
        result = enhancer.extract_enhanced_gpe_loc(test_text)
        
        print(f"✅ Enhanced extraction working: GPE={len(result['gpe'])}, LOC={len(result['location'])}")
        
        # Show one example
        if result['gpe']:
            example = result['gpe'][0]
            print(f"✅ Subcategory present: {example.get('subcategory', 'MISSING')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    # Test direct extraction
    result = test_direct_extraction()
    
    # Test import integration
    success = test_import_integration()
    
    if success:
        print(f"\n🟢 **SUCCESS**: Enhanced extraction working - ready for service processor integration")
    else:
        print(f"\n🔴 **BLOCKED**: Enhanced extraction has integration issues")
        
    print(f"\nNext step: Ensure service processor calls enhanced extraction method")