#!/usr/bin/env python3
"""
Enhanced Entity Metadata Extractor with Subcategorization
=========================================================

Extracts entities with rich metadata using foundation data subcategories.
Maps GPE and LOC entities to specific subtypes for enhanced context.

GPE Subcategories:
- countries, major_cities, us_states, us_government_agencies
- major_city_governments, state_governments, federal_provincial_governments
- government_forms, sovereign_entities_official_names, regional_political_entities
- regional_and_geopolitical_blocs, international_organizations
- collective_forms, demonyms_individuals, language_linked_identities

LOC Subcategories:
- continents, oceans, seas_and_gulfs, lakes, rivers, mountain_ranges
- mountains_peaks, deserts, islands_archipelagos, peninsulas
- bays_straits_channels, forests, valleys_canyons, plateaus_plains
- parks_protected_areas, geographic_regions, urban_settlements
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import json

# Import logging
sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class EntityMetadata:
    """Enhanced entity with subcategory metadata"""
    text: str
    entity_type: str  # GPE or LOC
    subcategory: str  # Specific subcategory from foundation data
    context: str     # Surrounding text context
    confidence: float
    start_pos: int
    end_pos: int
    source_file: str  # Which foundation data file matched

class EnhancedEntityExtractor:
    """
    Enhanced entity extractor with subcategory metadata from foundation data
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Load foundation data with subcategory mapping
        self.gpe_data: Dict[str, Set[str]] = {}
        self.loc_data: Dict[str, Set[str]] = {}
        
        self._load_foundation_data()
    
    def _load_foundation_data(self):
        """Load all foundation data files with subcategory mapping"""
        
        # GPE subcategories
        gpe_subcategories = [
            "countries", "major_cities", "us_states", "us_government_agencies",
            "major_city_governments", "state_governments", "federal_provincial_governments", 
            "government_forms", "sovereign_entities_official_names", "regional_political_entities",
            "regional_and_geopolitical_blocs", "international_organizations",
            "collective_forms", "demonyms_individuals", "language_linked_identities"
        ]
        
        # LOC subcategories  
        loc_subcategories = [
            "continents", "oceans", "seas_and_gulfs", "lakes", "rivers", "mountain_ranges",
            "mountains_peaks", "deserts", "islands_archipelagos", "peninsulas", 
            "bays_straits_channels", "forests", "valleys_canyons", "plateaus_plains",
            "parks_protected_areas", "geographic_regions", "urban_settlements"
        ]
        
        # Load GPE data
        gpe_path = self._foundation_path / "gpe"
        for subcategory in gpe_subcategories:
            entities = self._load_subcategory_file(gpe_path, subcategory)
            if entities:
                self.gpe_data[subcategory] = entities
                self.logger.logger.debug(f"📊 Loaded GPE {subcategory}: {len(entities)} entities")
        
        # Load LOC data
        loc_path = self._foundation_path / "loc" 
        for subcategory in loc_subcategories:
            entities = self._load_subcategory_file(loc_path, subcategory)
            if entities:
                self.loc_data[subcategory] = entities
                self.logger.logger.debug(f"🌍 Loaded LOC {subcategory}: {len(entities)} entities")
        
        total_gpe = sum(len(entities) for entities in self.gpe_data.values())
        total_loc = sum(len(entities) for entities in self.loc_data.values())
        
        self.logger.logger.info(f"🟢 **SUCCESS**: Foundation data loaded - GPE: {total_gpe} entities across {len(self.gpe_data)} subcategories, LOC: {total_loc} entities across {len(self.loc_data)} subcategories")
    
    def _load_subcategory_file(self, base_path: Path, subcategory: str) -> Set[str]:
        """Load entities from a specific subcategory file"""
        # Try multiple date patterns
        date_patterns = ["2025_09_22", "2025_09_18"]
        
        for date_pattern in date_patterns:
            file_path = base_path / f"{subcategory}_{date_pattern}.txt"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        entities = {line.strip() for line in f if line.strip()}
                    return entities
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ Error loading {file_path}: {e}")
        
        # File not found
        self.logger.logger.debug(f"📋 No file found for subcategory: {subcategory}")
        return set()
    
    def extract_entities_with_metadata(self, text: str, context_window: int = 50) -> List[EntityMetadata]:
        """
        Extract entities with rich subcategory metadata
        
        Args:
            text: Input text to analyze
            context_window: Number of characters before/after entity for context
            
        Returns:
            List of EntityMetadata objects with subcategory information
        """
        entities = []
        
        # Extract GPE entities
        gpe_entities = self._extract_gpe_entities(text, context_window)
        entities.extend(gpe_entities)
        
        # Extract LOC entities  
        loc_entities = self._extract_loc_entities(text, context_window)
        entities.extend(loc_entities)
        
        # Sort by position in text
        entities.sort(key=lambda x: x.start_pos)
        
        return entities
    
    def _extract_gpe_entities(self, text: str, context_window: int) -> List[EntityMetadata]:
        """Extract GPE entities with subcategory metadata"""
        entities = []
        text_lower = text.lower()
        
        for subcategory, entity_set in self.gpe_data.items():
            for entity in entity_set:
                entity_lower = entity.lower()
                start_pos = 0
                
                while True:
                    # Find next occurrence
                    pos = text_lower.find(entity_lower, start_pos)
                    if pos == -1:
                        break
                    
                    # Word boundary check
                    if self._is_word_boundary(text, pos, len(entity)):
                        end_pos = pos + len(entity)
                        context = self._extract_context(text, pos, end_pos, context_window)
                        
                        metadata = EntityMetadata(
                            text=text[pos:end_pos],
                            entity_type="GPE",
                            subcategory=subcategory,
                            context=context,
                            confidence=0.9,  # High confidence for exact matches
                            start_pos=pos,
                            end_pos=end_pos,
                            source_file=f"gpe/{subcategory}_*.txt"
                        )
                        entities.append(metadata)
                    
                    start_pos = pos + 1
        
        return entities
    
    def _extract_loc_entities(self, text: str, context_window: int) -> List[EntityMetadata]:
        """Extract LOC entities with subcategory metadata"""
        entities = []
        text_lower = text.lower()
        
        for subcategory, entity_set in self.loc_data.items():
            for entity in entity_set:
                entity_lower = entity.lower()
                start_pos = 0
                
                while True:
                    # Find next occurrence
                    pos = text_lower.find(entity_lower, start_pos)
                    if pos == -1:
                        break
                    
                    # Word boundary check
                    if self._is_word_boundary(text, pos, len(entity)):
                        end_pos = pos + len(entity)
                        context = self._extract_context(text, pos, end_pos, context_window)
                        
                        metadata = EntityMetadata(
                            text=text[pos:end_pos],
                            entity_type="LOC",
                            subcategory=subcategory,
                            context=context,
                            confidence=0.9,  # High confidence for exact matches
                            start_pos=pos,
                            end_pos=end_pos,
                            source_file=f"loc/{subcategory}_*.txt"
                        )
                        entities.append(metadata)
                    
                    start_pos = pos + 1
        
        return entities
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Check if the match is at word boundaries"""
        end = start + length
        
        # Check character before
        if start > 0 and text[start - 1].isalnum():
            return False
            
        # Check character after
        if end < len(text) and text[end].isalnum():
            return False
            
        return True
    
    def _extract_context(self, text: str, start: int, end: int, window: int) -> str:
        """Extract context around the entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        # Mark the entity in context
        entity_pos_in_context = start - context_start
        entity_text = text[start:end]
        context_with_marker = (
            context[:entity_pos_in_context] + 
            f"[{entity_text}]" + 
            context[entity_pos_in_context + len(entity_text):]
        )
        
        return context_with_marker.strip()
    
    def generate_summary_report(self, entities: List[EntityMetadata]) -> Dict:
        """Generate summary report of extracted entities"""
        
        # Count by type and subcategory
        gpe_counts = {}
        loc_counts = {}
        
        for entity in entities:
            if entity.entity_type == "GPE":
                gpe_counts[entity.subcategory] = gpe_counts.get(entity.subcategory, 0) + 1
            elif entity.entity_type == "LOC":
                loc_counts[entity.subcategory] = loc_counts.get(entity.subcategory, 0) + 1
        
        # Generate structured report
        report = {
            "summary": {
                "total_entities": len(entities),
                "gpe_entities": sum(gpe_counts.values()),
                "loc_entities": sum(loc_counts.values())
            },
            "gpe_breakdown": gpe_counts,
            "loc_breakdown": loc_counts,
            "entities": [
                {
                    "text": e.text,
                    "type": e.entity_type,
                    "subcategory": e.subcategory,
                    "confidence": e.confidence,
                    "position": [e.start_pos, e.end_pos],
                    "context": e.context,
                    "source": e.source_file
                }
                for e in entities
            ]
        }
        
        return report
    
    def print_structured_summary(self, entities: List[EntityMetadata]):
        """Print formatted summary following Rule #11 logging standard"""
        
        # Count by subcategory
        gpe_counts = {}
        loc_counts = {}
        
        for entity in entities:
            if entity.entity_type == "GPE":
                gpe_counts[entity.subcategory] = gpe_counts.get(entity.subcategory, 0) + 1
            elif entity.entity_type == "LOC":
                loc_counts[entity.subcategory] = loc_counts.get(entity.subcategory, 0) + 1
        
        # Format GPE summary (only non-zero counts)
        gpe_parts = [f"{subcategory}:{count}" for subcategory, count in gpe_counts.items() if count > 0]
        if gpe_parts:
            print(f"📊 GPE entities: {', '.join(gpe_parts)}")
        
        # Format LOC summary (only non-zero counts)  
        loc_parts = [f"{subcategory}:{count}" for subcategory, count in loc_counts.items() if count > 0]
        if loc_parts:
            print(f"🌍 LOC entities: {', '.join(loc_parts)}")


def test_enhanced_extraction():
    """Test the enhanced extraction system"""
    
    # Sample test text with various entity types
    test_text = """
    The Department of Defense announced new regulations for FDA approval processes. 
    The EPA will coordinate with OSHA on environmental safety standards.
    Texas and California have implemented new policies, while New York City
    government officials met with federal representatives. The United States
    government is working with international organizations like NATO and the UN.
    
    Geographically, the Pacific Ocean borders several mountain ranges including
    the Rocky Mountains. Lake Superior and the Great Lakes region connect to
    major rivers like the Mississippi River. The Sahara Desert spans across
    multiple continents, while Yellowstone National Park protects important
    forest ecosystems in North America.
    """
    
    print("🧪 Testing Enhanced Entity Extraction with Subcategory Metadata")
    print("=" * 70)
    
    # Initialize extractor
    extractor = EnhancedEntityExtractor()
    
    # Extract entities
    entities = extractor.extract_entities_with_metadata(test_text)
    
    # Print structured summary
    extractor.print_structured_summary(entities)
    
    print(f"\n📋 Detailed Results ({len(entities)} entities found):")
    print("-" * 50)
    
    for i, entity in enumerate(entities, 1):
        print(f"{i:2d}. [{entity.entity_type}:{entity.subcategory}] '{entity.text}'")
        print(f"    Context: {entity.context}")
        print(f"    Source: {entity.source_file}")
        print()
    
    # Generate JSON report
    report = extractor.generate_summary_report(entities)
    
    return report


if __name__ == "__main__":
    # Activate virtual environment and run test
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    print("🟡 **WAITING**: Activating virtual environment...")
    report = test_enhanced_extraction()
    
    # Save detailed report
    with open('enhanced_metadata_test_results.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"🟢 **SUCCESS**: Test completed. Results saved to enhanced_metadata_test_results.json")