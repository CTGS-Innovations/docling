#!/usr/bin/env python3
"""
Enhanced Extraction Pipeline with Hybrid Metadata
=================================================

Integrates the hybrid metadata system into the existing extraction pipeline
to produce both raw entities with subcategories and rich normalized metadata.

Output format matches existing pipeline but with enhanced subcategorization.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

sys.path.append(str(Path(__file__).parent))
from hybrid_entity_metadata_system import HybridEntityMetadataSystem
from utils.logging_config import get_fusion_logger

class EnhancedExtractionPipeline:
    """
    Enhanced pipeline that produces both traditional and hybrid metadata outputs
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self.hybrid_system = HybridEntityMetadataSystem()
    
    def extract_entities_with_enhanced_metadata(self, text: str, include_normalized: bool = True) -> Dict[str, Any]:
        """
        Extract entities with enhanced subcategory metadata
        
        Args:
            text: Input text to process
            include_normalized: Whether to include rich normalized metadata
            
        Returns:
            Enhanced extraction results with both raw and normalized entities
        """
        
        # Extract hybrid metadata
        hybrid_result = self.hybrid_system.extract_hybrid_metadata(text)
        
        # Convert to enhanced traditional format with subcategories
        traditional_format = self._convert_to_traditional_format(hybrid_result)
        
        # Build comprehensive result
        result = {
            "entities": traditional_format,
            "metadata": {
                "extraction_method": "hybrid_subcategory_system",
                "total_entities": hybrid_result["metadata"]["total_raw_entities"],
                "confidence": hybrid_result["metadata"]["extraction_confidence"],
                "subcategory_breakdown": self._generate_subcategory_breakdown(hybrid_result)
            }
        }
        
        # Add normalized entities if requested
        if include_normalized:
            result["normalized_entities"] = hybrid_result["normalized_entities"]
            result["normalization_metadata"] = {
                "total_normalized": hybrid_result["metadata"]["total_normalized_entities"],
                "hierarchy_depth": self._calculate_hierarchy_depth(hybrid_result["normalized_entities"]),
                "authority_distribution": self._analyze_authority_distribution(hybrid_result["normalized_entities"])
            }
        
        return result
    
    def _convert_to_traditional_format(self, hybrid_result: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Convert hybrid results to traditional extraction format with subcategories"""
        
        traditional = {"gpe": [], "loc": []}
        
        # Convert GPE entities
        for raw_entity in hybrid_result["raw_entities"]["gpe"]:
            traditional_entity = {
                "value": raw_entity.value,
                "text": raw_entity.text,
                "type": raw_entity.entity_type,
                "subcategory": raw_entity.subcategory,  # NEW: Subcategory metadata
                "span": raw_entity.span
            }
            traditional["gpe"].append(traditional_entity)
        
        # Convert LOC entities
        for raw_entity in hybrid_result["raw_entities"]["loc"]:
            traditional_entity = {
                "value": raw_entity.value,
                "text": raw_entity.text,
                "type": raw_entity.entity_type,
                "subcategory": raw_entity.subcategory,  # NEW: Subcategory metadata
                "span": raw_entity.span
            }
            traditional["loc"].append(traditional_entity)
        
        return traditional
    
    def _generate_subcategory_breakdown(self, hybrid_result: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
        """Generate breakdown of entities by subcategory"""
        
        breakdown = {"gpe": {}, "loc": {}}
        
        # Count GPE subcategories
        for entity in hybrid_result["raw_entities"]["gpe"]:
            subcategory = entity.subcategory
            breakdown["gpe"][subcategory] = breakdown["gpe"].get(subcategory, 0) + 1
        
        # Count LOC subcategories
        for entity in hybrid_result["raw_entities"]["loc"]:
            subcategory = entity.subcategory
            breakdown["loc"][subcategory] = breakdown["loc"].get(subcategory, 0) + 1
        
        return breakdown
    
    def _calculate_hierarchy_depth(self, normalized_entities: Dict[str, List]) -> Dict[str, float]:
        """Calculate average hierarchy depth for normalized entities"""
        
        depths = {"geopolitical": [], "geographic": []}
        
        for entity in normalized_entities.get("geopolitical", []):
            depths["geopolitical"].append(len(entity.hierarchy))
        
        for entity in normalized_entities.get("geographic", []):
            depths["geographic"].append(len(entity.hierarchy))
        
        return {
            "geopolitical_avg_depth": sum(depths["geopolitical"]) / len(depths["geopolitical"]) if depths["geopolitical"] else 0,
            "geographic_avg_depth": sum(depths["geographic"]) / len(depths["geographic"]) if depths["geographic"] else 0
        }
    
    def _analyze_authority_distribution(self, normalized_entities: Dict[str, List]) -> Dict[str, Dict[str, int]]:
        """Analyze distribution of authority types in geopolitical entities"""
        
        authority_dist = {}
        
        for entity in normalized_entities.get("geopolitical", []):
            authority_type = entity.geopolitical_properties.get("authority_type", "unknown")
            authority_dist[authority_type] = authority_dist.get(authority_type, 0) + 1
        
        return authority_dist
    
    def extract_and_format_like_existing(self, text: str) -> str:
        """
        Extract entities and format exactly like existing pipeline output
        but with enhanced subcategory metadata
        """
        
        result = self.extract_entities_with_enhanced_metadata(text, include_normalized=False)
        
        # Format as YAML-like structure (similar to your example)
        output_lines = []
        
        # GPE entities
        if result["entities"]["gpe"]:
            output_lines.append("gpe:")
            for entity in result["entities"]["gpe"]:
                output_lines.append(f"  - value: {entity['value']}")
                output_lines.append(f"    text: {entity['text']}")
                output_lines.append(f"    type: {entity['type']}")
                output_lines.append(f"    subcategory: {entity['subcategory']}")  # NEW
                output_lines.append(f"    span: {{start: {entity['span']['start']}, end: {entity['span']['end']}}}")
        
        # LOC entities
        if result["entities"]["loc"]:
            if output_lines:  # Add separator if GPE entities exist
                output_lines.append("")
            output_lines.append("loc:")
            for entity in result["entities"]["loc"]:
                output_lines.append(f"  - value: {entity['value']}")
                output_lines.append(f"    text: {entity['text']}")
                output_lines.append(f"    type: {entity['type']}")
                output_lines.append(f"    subcategory: {entity['subcategory']}")  # NEW
                output_lines.append(f"    span: {{start: {entity['span']['start']}, end: {entity['span']['end']}}}")
        
        return "\n".join(output_lines)
    
    def print_enhanced_summary(self, result: Dict[str, Any]):
        """Print enhanced summary with subcategory breakdowns"""
        
        breakdown = result["metadata"]["subcategory_breakdown"]
        
        # GPE summary
        gpe_parts = [f"{subcat}:{count}" for subcat, count in breakdown["gpe"].items()]
        if gpe_parts:
            print(f"📊 GPE entities: {', '.join(gpe_parts)}")
        
        # LOC summary
        loc_parts = [f"{subcat}:{count}" for subcat, count in breakdown["loc"].items()]
        if loc_parts:
            print(f"🌍 LOC entities: {', '.join(loc_parts)}")
        
        # Confidence and totals
        print(f"🎯 Extraction confidence: {result['metadata']['confidence']}")
        print(f"📈 Total entities: {result['metadata']['total_entities']}")

def test_enhanced_pipeline():
    """Test the enhanced pipeline with realistic text"""
    
    # Sample text similar to your document
    test_text = """
    The Department of Defense announced new regulations affecting New York, 
    California, and Texas. The EU has expressed concerns about the policy.
    
    Operations in Moscow and coordination with Brazilian officials are expected.
    Major cities including New York City, Los Angeles, Chicago, Houston, 
    Phoenix, Philadelphia, San Antonio, San Diego, Dallas, and San Jose 
    will implement the changes.
    
    The policy affects Florida, United States, and Canada as well.
    International coordination with NATO is planned.
    """
    
    print("🧪 Testing Enhanced Extraction Pipeline")
    print("=" * 50)
    
    pipeline = EnhancedExtractionPipeline()
    
    # Test traditional format output
    print("📋 Traditional Format with Enhanced Subcategories:")
    print("-" * 52)
    traditional_output = pipeline.extract_and_format_like_existing(test_text)
    print(traditional_output[:800] + "..." if len(traditional_output) > 800 else traditional_output)
    
    # Test full enhanced output
    print("\n🎯 Enhanced Summary:")
    print("-" * 20)
    full_result = pipeline.extract_entities_with_enhanced_metadata(test_text)
    pipeline.print_enhanced_summary(full_result)
    
    return full_result

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_enhanced_pipeline()