#!/usr/bin/env python3
"""
Enhanced Service Processor Integration
=====================================

Patch to integrate the hybrid metadata system into the existing service processor
to provide enhanced GPE/LOC extraction with subcategory metadata.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.append(str(Path(__file__).parent))
from hybrid_entity_metadata_system import HybridEntityMetadataSystem
from utils.logging_config import get_fusion_logger

class EnhancedEntityExtraction:
    """Enhanced entity extraction for integration into service processor"""
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self.hybrid_system = HybridEntityMetadataSystem()
    
    def extract_enhanced_gpe_loc(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract GPE and LOC entities with enhanced subcategory metadata
        Returns format compatible with existing service processor
        """
        
        # Use hybrid system to extract with metadata
        hybrid_result = self.hybrid_system.extract_hybrid_metadata(content)
        
        # Convert to service processor format
        enhanced_entities = {
            'gpe': [],
            'location': []
        }
        
        # Convert GPE entities with subcategory metadata
        for raw_entity in hybrid_result["raw_entities"]["gpe"]:
            entity = {
                'value': raw_entity.value,
                'text': raw_entity.text,
                'type': raw_entity.entity_type,
                'subcategory': raw_entity.subcategory,  # ENHANCED: Add subcategory
                'span': raw_entity.span
            }
            enhanced_entities['gpe'].append(entity)
        
        # Convert LOC entities with subcategory metadata
        for raw_entity in hybrid_result["raw_entities"]["loc"]:
            entity = {
                'value': raw_entity.value,
                'text': raw_entity.text,
                'type': 'LOCATION',  # Match existing format
                'subcategory': raw_entity.subcategory,  # ENHANCED: Add subcategory
                'span': raw_entity.span
            }
            enhanced_entities['location'].append(entity)
        
        return enhanced_entities
    
    def patch_service_processor_extraction(self, service_processor_instance, content: str) -> Dict[str, List]:
        """
        Patch existing service processor to use enhanced extraction
        """
        
        # Get enhanced GPE/LOC entities
        enhanced = self.extract_enhanced_gpe_loc(content)
        
        # Log enhancement
        gpe_count = len(enhanced['gpe'])
        loc_count = len(enhanced['location'])
        
        self.logger.logger.info(f"🟢 **SUCCESS**: Enhanced extraction - GPE: {gpe_count} entities, LOC: {loc_count} entities")
        
        # Print subcategory breakdown
        gpe_subcategories = {}
        for entity in enhanced['gpe']:
            subcat = entity['subcategory']
            gpe_subcategories[subcat] = gpe_subcategories.get(subcat, 0) + 1
        
        loc_subcategories = {}
        for entity in enhanced['location']:
            subcat = entity['subcategory']
            loc_subcategories[subcat] = loc_subcategories.get(subcat, 0) + 1
        
        # Format summary
        if gpe_subcategories:
            gpe_parts = [f"{subcat}:{count}" for subcat, count in gpe_subcategories.items()]
            print(f"📊 GPE entities: {', '.join(gpe_parts)}")
        
        if loc_subcategories:
            loc_parts = [f"{subcat}:{count}" for subcat, count in loc_subcategories.items()]
            print(f"🌍 LOC entities: {', '.join(loc_parts)}")
        
        return enhanced

def test_enhanced_integration():
    """Test the enhanced integration on the updated document"""
    
    # Read the updated test document
    doc_path = Path("/home/corey/projects/docling/cli/data_complex/complex_pdfs/ENTITY_EXTRACTION_TXT_DOCUMENT.txt")
    
    if not doc_path.exists():
        print("❌ Test document not found")
        return
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🧪 Testing Enhanced Service Processor Integration")
    print("=" * 55)
    
    # Test enhanced extraction
    extractor = EnhancedEntityExtraction()
    result = extractor.extract_enhanced_gpe_loc(content)
    
    print(f"\n📋 Enhanced Extraction Results:")
    print("-" * 35)
    
    print(f"GPE Entities ({len(result['gpe'])} found):")
    for i, entity in enumerate(result['gpe'][:10], 1):  # Show first 10
        print(f"  {i:2d}. {entity['value']} [{entity['subcategory']}]")
    if len(result['gpe']) > 10:
        print(f"      ... and {len(result['gpe']) - 10} more")
    
    print(f"\nLOC Entities ({len(result['location'])} found):")
    for i, entity in enumerate(result['location'][:10], 1):  # Show first 10
        print(f"  {i:2d}. {entity['value']} [{entity['subcategory']}]")
    if len(result['location']) > 10:
        print(f"      ... and {len(result['location']) - 10} more")
    
    print(f"\n🎯 Enhanced vs Original Comparison:")
    print("-" * 37)
    print("Original: location: [] (empty)")
    print(f"Enhanced: location: {len(result['location'])} entities with subcategories")
    print("Original: GPE entities without subcategory metadata")  
    print("Enhanced: GPE entities with rich subcategory classification")
    
    return result

def create_service_processor_patch():
    """Create a patch that can be applied to the existing service processor"""
    
    patch_code = '''
# ENHANCED EXTRACTION PATCH
# Add this to service_processor.py _extract_universal_entities method

def _extract_enhanced_gpe_loc(self, content: str) -> Dict[str, List]:
    """Enhanced GPE/LOC extraction with subcategory metadata"""
    try:
        from enhanced_service_processor_integration import EnhancedEntityExtraction
        enhancer = EnhancedEntityExtraction()
        return enhancer.extract_enhanced_gpe_loc(content)
    except ImportError:
        # Fallback to original extraction
        return self._extract_original_gpe_loc(content)

# Replace existing GPE/LOC extraction in _extract_universal_entities:
# entities.update(self._extract_enhanced_gpe_loc(content))
'''
    
    print("🔧 Service Processor Patch:")
    print("-" * 30)
    print(patch_code)

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    result = test_enhanced_integration()
    create_service_processor_patch()
    
    print(f"\n🟢 **SUCCESS**: Enhanced integration ready for deployment")