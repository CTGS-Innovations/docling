#!/usr/bin/env python3
"""
Debug Service Processor Enhanced Extraction
==========================================

Test exactly what's happening in the service processor enhanced extraction.
"""

import sys
from pathlib import Path
import traceback

sys.path.append(str(Path(__file__).parent))

def test_service_processor_enhanced_extraction():
    """Test the exact enhanced extraction method from service processor"""
    
    print("🔧 Direct Service Processor Enhanced Extraction Debug")
    print("=" * 60)
    
    # Test the exact method that should be called
    try:
        from hybrid_entity_metadata_system import HybridEntityMetadataSystem
        print("✅ HybridEntityMetadataSystem import successful")
        
        # Test with small sample
        test_text = "EPA announced regulations for Texas. Pacific Ocean cleanup involves Rocky Mountains."
        
        hybrid_system = HybridEntityMetadataSystem()
        print("✅ HybridEntityMetadataSystem initialized")
        
        hybrid_result = hybrid_system.extract_hybrid_metadata(test_text)
        print("✅ extract_hybrid_metadata successful")
        
        # Convert to service processor format
        enhanced_entities = {'gpe': [], 'location': []}
        
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
                'type': 'LOCATION',
                'subcategory': raw_entity.subcategory,  # ENHANCED: Add subcategory
                'span': raw_entity.span
            }
            enhanced_entities['location'].append(entity)
        
        print("✅ Entity conversion successful")
        
        print(f"\n🎯 Results:")
        print(f"GPE entities: {len(enhanced_entities['gpe'])}")
        for entity in enhanced_entities['gpe']:
            print(f"  • {entity['value']} [{entity['subcategory']}]")
        
        print(f"LOC entities: {len(enhanced_entities['location'])}")
        for entity in enhanced_entities['location']:
            print(f"  • {entity['value']} [{entity['subcategory']}]")
        
        return enhanced_entities
        
    except Exception as e:
        print(f"❌ Enhanced extraction failed: {e}")
        print(f"❌ Full traceback:")
        traceback.print_exc()
        return None

def test_service_processor_direct():
    """Test calling the service processor method directly"""
    
    print(f"\n🧪 Testing Service Processor Direct Call")
    print("-" * 45)
    
    try:
        # Create a mock service processor to test the method
        class MockServiceProcessor:
            def __init__(self):
                from utils.logging_config import get_fusion_logger
                self.logger = get_fusion_logger(__name__)
            
            def _extract_enhanced_gpe_loc(self, content: str):
                """Copy of the exact method from service processor"""
                try:
                    from hybrid_entity_metadata_system import HybridEntityMetadataSystem
                    
                    hybrid_system = HybridEntityMetadataSystem()
                    hybrid_result = hybrid_system.extract_hybrid_metadata(content)
                    
                    enhanced_entities = {'gpe': [], 'location': []}
                    
                    for raw_entity in hybrid_result["raw_entities"]["gpe"]:
                        entity = {
                            'value': raw_entity.value,
                            'text': raw_entity.text,
                            'type': raw_entity.entity_type,
                            'subcategory': raw_entity.subcategory,
                            'span': raw_entity.span
                        }
                        enhanced_entities['gpe'].append(entity)
                    
                    for raw_entity in hybrid_result["raw_entities"]["loc"]:
                        entity = {
                            'value': raw_entity.value,
                            'text': raw_entity.text,
                            'type': 'LOCATION',
                            'subcategory': raw_entity.subcategory,
                            'span': raw_entity.span
                        }
                        enhanced_entities['location'].append(entity)
                    
                    return enhanced_entities
                    
                except Exception as e:
                    self.logger.logger.warning(f"Direct enhanced extraction failed: {e}")
                    raise e
        
        processor = MockServiceProcessor()
        test_text = "EPA announced regulations for Texas. Pacific Ocean cleanup involves Rocky Mountains."
        
        result = processor._extract_enhanced_gpe_loc(test_text)
        
        print("✅ Service processor method call successful")
        print(f"GPE: {len(result['gpe'])}, LOC: {len(result['location'])}")
        
        if result['gpe']:
            sample = result['gpe'][0]
            print(f"Sample GPE: {sample['value']} [{sample.get('subcategory', 'NO_SUBCATEGORY')}]")
        
        return True
        
    except Exception as e:
        print(f"❌ Service processor method failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    # Test 1: Direct hybrid system
    result1 = test_service_processor_enhanced_extraction()
    
    # Test 2: Service processor method
    result2 = test_service_processor_direct()
    
    if result1 and result2:
        print(f"\n🟢 **SUCCESS**: Enhanced extraction working - issue must be elsewhere")
    else:
        print(f"\n🔴 **BLOCKED**: Enhanced extraction has fundamental issues")
        
    print(f"\nNext: Check if service processor _extract_universal_entities is actually calling enhanced method")