#!/usr/bin/env python3
"""
Hybrid Entity Metadata System (Option C Implementation)
======================================================

Professional GPE/LOC metadata architecture with:
1. Raw entity level: Basic subcategory tagging for immediate use
2. Normalized entity level: Rich metadata for advanced applications

Supports both GPE and LOC entities with hierarchical classification.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
import json

sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class RawEntityMetadata:
    """Raw entity with basic subcategory for immediate use"""
    value: str
    text: str
    entity_type: str  # GPE or LOC
    subcategory: str  # Basic subcategory
    span: Dict[str, int]  # {start: int, end: int}

@dataclass
class NormalizedEntityMetadata:
    """Rich normalized entity with comprehensive metadata"""
    canonical_name: str
    entity_type: str
    subcategory: str
    classification_confidence: float
    geopolitical_properties: Dict[str, Any] = field(default_factory=dict)
    geographic_properties: Dict[str, Any] = field(default_factory=dict)
    hierarchy: List[str] = field(default_factory=list)
    raw_mentions: List[Dict] = field(default_factory=list)
    alternative_classifications: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)

class HybridEntityMetadataSystem:
    """
    Professional hybrid metadata system for GPE and LOC entities
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Foundation data with metadata
        self.gpe_data: Dict[str, Dict[str, Any]] = {}
        self.loc_data: Dict[str, Dict[str, Any]] = {}
        
        # Hierarchy and classification rules
        self.gpe_hierarchy = {
            "us_government_agencies": {"level": "federal", "authority": "governmental", "priority": 10},
            "federal_provincial_governments": {"level": "federal", "authority": "governmental", "priority": 9},
            "major_city_governments": {"level": "municipal", "authority": "governmental", "priority": 8},
            "state_governments": {"level": "state", "authority": "governmental", "priority": 8},
            "government_forms": {"level": "national", "authority": "governmental", "priority": 7},
            "sovereign_entities_official_names": {"level": "national", "authority": "sovereign", "priority": 6},
            "countries": {"level": "national", "authority": "sovereign", "priority": 6},
            "us_states": {"level": "state", "authority": "administrative", "priority": 5},
            "major_cities": {"level": "municipal", "authority": "administrative", "priority": 4},
            "international_organizations": {"level": "international", "authority": "multilateral", "priority": 4},
            "regional_political_entities": {"level": "regional", "authority": "administrative", "priority": 3},
            "regional_and_geopolitical_blocs": {"level": "regional", "authority": "political", "priority": 3},
            "collective_forms": {"level": "collective", "authority": "cultural", "priority": 2},
            "demonyms_individuals": {"level": "individual", "authority": "cultural", "priority": 2},
            "language_linked_identities": {"level": "cultural", "authority": "linguistic", "priority": 1}
        }
        
        self.loc_hierarchy = {
            "parks_protected_areas": {"type": "protected", "scale": "regional", "priority": 8},
            "mountain_ranges": {"type": "orographic", "scale": "regional", "priority": 7},
            "mountains_peaks": {"type": "orographic", "scale": "local", "priority": 7},
            "valleys_canyons": {"type": "orographic", "scale": "regional", "priority": 7},
            "deserts": {"type": "climate", "scale": "regional", "priority": 6},
            "forests": {"type": "biome", "scale": "regional", "priority": 6},
            "oceans": {"type": "hydrographic", "scale": "global", "priority": 6},
            "seas_and_gulfs": {"type": "hydrographic", "scale": "regional", "priority": 6},
            "lakes": {"type": "hydrographic", "scale": "regional", "priority": 6},
            "rivers": {"type": "hydrographic", "scale": "regional", "priority": 6},
            "islands_archipelagos": {"type": "insular", "scale": "regional", "priority": 6},
            "peninsulas": {"type": "coastal", "scale": "regional", "priority": 6},
            "bays_straits_channels": {"type": "hydrographic", "scale": "local", "priority": 6},
            "plateaus_plains": {"type": "topographic", "scale": "regional", "priority": 5},
            "continents": {"type": "continental", "scale": "global", "priority": 4},
            "geographic_regions": {"type": "regional", "scale": "macroregional", "priority": 3},
            "urban_settlements": {"type": "anthropogenic", "scale": "local", "priority": 2}
        }
        
        self._load_foundation_data()
    
    def _load_foundation_data(self):
        """Load foundation data with enhanced metadata"""
        
        # Load GPE data
        gpe_path = self._foundation_path / "gpe"
        for subcategory in self.gpe_hierarchy.keys():
            entities = self._load_subcategory_file(gpe_path, subcategory)
            if entities:
                self.gpe_data[subcategory] = {
                    'entities': entities,
                    'metadata': self.gpe_hierarchy[subcategory]
                }
        
        # Load LOC data
        loc_path = self._foundation_path / "loc"
        for subcategory in self.loc_hierarchy.keys():
            entities = self._load_subcategory_file(loc_path, subcategory)
            if entities:
                self.loc_data[subcategory] = {
                    'entities': entities,
                    'metadata': self.loc_hierarchy[subcategory]
                }
        
        total_gpe = sum(len(data['entities']) for data in self.gpe_data.values())
        total_loc = sum(len(data['entities']) for data in self.loc_data.values())
        
        self.logger.logger.info(f"🟢 **SUCCESS**: Hybrid metadata system loaded - GPE: {total_gpe} entities across {len(self.gpe_data)} subcategories, LOC: {total_loc} entities across {len(self.loc_data)} subcategories")
    
    def _load_subcategory_file(self, base_path: Path, subcategory: str) -> Set[str]:
        """Load entities from subcategory file"""
        date_patterns = ["2025_09_22", "2025_09_18"]
        
        for date_pattern in date_patterns:
            file_path = base_path / f"{subcategory}_{date_pattern}.txt"
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return {line.strip() for line in f if line.strip()}
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ Error loading {file_path}: {e}")
        return set()
    
    def extract_hybrid_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract entities with hybrid metadata architecture
        Returns both raw entities and normalized entities
        """
        
        # Step 1: Extract raw entities with basic subcategories
        raw_entities = self._extract_raw_entities(text)
        
        # Step 2: Create normalized entities with rich metadata
        normalized_entities = self._create_normalized_entities(raw_entities)
        
        # Step 3: Generate hybrid output structure
        result = {
            "raw_entities": {
                "gpe": [e for e in raw_entities if e.entity_type == "GPE"],
                "loc": [e for e in raw_entities if e.entity_type == "LOC"]
            },
            "normalized_entities": {
                "geopolitical": [e for e in normalized_entities if e.entity_type.startswith("geo_")],
                "geographic": [e for e in normalized_entities if e.entity_type.startswith("loc_")]
            },
            "metadata": {
                "total_raw_entities": len(raw_entities),
                "total_normalized_entities": len(normalized_entities),
                "extraction_confidence": self._calculate_extraction_confidence(raw_entities)
            }
        }
        
        return result
    
    def _extract_raw_entities(self, text: str) -> List[RawEntityMetadata]:
        """Extract raw entities with basic subcategory tagging"""
        entities = []
        text_lower = text.lower()
        
        # Extract GPE entities
        for subcategory, data in self.gpe_data.items():
            for entity in data['entities']:
                entities.extend(self._find_entity_mentions(text, text_lower, entity, "GPE", subcategory))
        
        # Extract LOC entities
        for subcategory, data in self.loc_data.items():
            for entity in data['entities']:
                entities.extend(self._find_entity_mentions(text, text_lower, entity, "LOC", subcategory))
        
        # Remove duplicates and resolve conflicts
        entities = self._resolve_raw_conflicts(entities)
        
        return sorted(entities, key=lambda x: x.span['start'])
    
    def _find_entity_mentions(self, text: str, text_lower: str, entity: str, entity_type: str, subcategory: str) -> List[RawEntityMetadata]:
        """Find all mentions of an entity in text"""
        mentions = []
        entity_lower = entity.lower()
        start_pos = 0
        
        while True:
            pos = text_lower.find(entity_lower, start_pos)
            if pos == -1:
                break
            
            if self._is_word_boundary(text, pos, len(entity)):
                end_pos = pos + len(entity)
                
                mention = RawEntityMetadata(
                    value=entity,
                    text=text[pos:end_pos],
                    entity_type=entity_type,
                    subcategory=subcategory,
                    span={"start": pos, "end": end_pos}
                )
                mentions.append(mention)
            
            start_pos = pos + 1
        
        return mentions
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Check word boundaries"""
        end = start + length
        
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True
    
    def _resolve_raw_conflicts(self, entities: List[RawEntityMetadata]) -> List[RawEntityMetadata]:
        """Resolve overlapping raw entities using priority"""
        if not entities:
            return entities
        
        # Group by overlapping positions
        position_groups = []
        
        for entity in entities:
            # Find overlapping group
            placed = False
            for group in position_groups:
                if any(self._positions_overlap(entity.span, existing.span) for existing in group):
                    group.append(entity)
                    placed = True
                    break
            
            if not placed:
                position_groups.append([entity])
        
        # Resolve each group by priority
        resolved = []
        for group in position_groups:
            if len(group) == 1:
                resolved.append(group[0])
            else:
                # Choose highest priority
                if group[0].entity_type == "GPE":
                    priorities = {e.subcategory: self.gpe_hierarchy.get(e.subcategory, {}).get('priority', 0) for e in group}
                else:
                    priorities = {e.subcategory: self.loc_hierarchy.get(e.subcategory, {}).get('priority', 0) for e in group}
                
                best_entity = max(group, key=lambda x: priorities.get(x.subcategory, 0))
                resolved.append(best_entity)
        
        return resolved
    
    def _positions_overlap(self, span1: Dict[str, int], span2: Dict[str, int]) -> bool:
        """Check if two spans overlap"""
        return not (span1['end'] <= span2['start'] or span2['end'] <= span1['start'])
    
    def _create_normalized_entities(self, raw_entities: List[RawEntityMetadata]) -> List[NormalizedEntityMetadata]:
        """Create rich normalized entities from raw entities"""
        normalized = []
        
        # Group raw entities by canonical name
        entity_groups = {}
        for raw in raw_entities:
            canonical = raw.value.lower()
            if canonical not in entity_groups:
                entity_groups[canonical] = []
            entity_groups[canonical].append(raw)
        
        # Create normalized entities
        for canonical_name, raw_group in entity_groups.items():
            primary_raw = raw_group[0]  # Use first as primary
            
            if primary_raw.entity_type == "GPE":
                normalized_entity = self._create_gpe_normalized(canonical_name, raw_group)
            else:
                normalized_entity = self._create_loc_normalized(canonical_name, raw_group)
            
            normalized.append(normalized_entity)
        
        return normalized
    
    def _create_gpe_normalized(self, canonical_name: str, raw_group: List[RawEntityMetadata]) -> NormalizedEntityMetadata:
        """Create normalized GPE entity"""
        primary = raw_group[0]
        subcategory_metadata = self.gpe_hierarchy.get(primary.subcategory, {})
        
        # Build geopolitical properties
        geopolitical_props = {
            "authority_level": subcategory_metadata.get('level', 'unknown'),
            "authority_type": subcategory_metadata.get('authority', 'unknown'),
            "governmental_entity": subcategory_metadata.get('authority') in ['governmental', 'sovereign'],
            "jurisdiction_scope": self._determine_jurisdiction_scope(primary.subcategory)
        }
        
        # Build hierarchy
        hierarchy = self._build_geopolitical_hierarchy(primary.value, primary.subcategory)
        
        return NormalizedEntityMetadata(
            canonical_name=primary.value,
            entity_type=f"geo_{primary.subcategory}",
            subcategory=primary.subcategory,
            classification_confidence=0.9 if len(raw_group) == 1 else 0.8,
            geopolitical_properties=geopolitical_props,
            hierarchy=hierarchy,
            raw_mentions=[{"text": r.text, "span": r.span} for r in raw_group],
            alternative_classifications=[r.subcategory for r in raw_group[1:]],
            source_files=[f"gpe/{r.subcategory}_*.txt" for r in raw_group]
        )
    
    def _create_loc_normalized(self, canonical_name: str, raw_group: List[RawEntityMetadata]) -> NormalizedEntityMetadata:
        """Create normalized LOC entity"""
        primary = raw_group[0]
        subcategory_metadata = self.loc_hierarchy.get(primary.subcategory, {})
        
        # Build geographic properties
        geographic_props = {
            "feature_type": subcategory_metadata.get('type', 'unknown'),
            "geographic_scale": subcategory_metadata.get('scale', 'unknown'),
            "natural_feature": subcategory_metadata.get('type') not in ['anthropogenic', 'protected'],
            "physical_geography": self._determine_physical_geography(primary.subcategory)
        }
        
        # Build hierarchy
        hierarchy = self._build_geographic_hierarchy(primary.value, primary.subcategory)
        
        return NormalizedEntityMetadata(
            canonical_name=primary.value,
            entity_type=f"loc_{primary.subcategory}",
            subcategory=primary.subcategory,
            classification_confidence=0.9 if len(raw_group) == 1 else 0.8,
            geographic_properties=geographic_props,
            hierarchy=hierarchy,
            raw_mentions=[{"text": r.text, "span": r.span} for r in raw_group],
            alternative_classifications=[r.subcategory for r in raw_group[1:]],
            source_files=[f"loc/{r.subcategory}_*.txt" for r in raw_group]
        )
    
    def _determine_jurisdiction_scope(self, subcategory: str) -> str:
        """Determine jurisdiction scope for GPE entities"""
        scope_map = {
            'international_organizations': 'international',
            'countries': 'national',
            'us_states': 'state',
            'major_cities': 'municipal',
            'us_government_agencies': 'federal'
        }
        return scope_map.get(subcategory, 'unknown')
    
    def _determine_physical_geography(self, subcategory: str) -> str:
        """Determine physical geography type for LOC entities"""
        phys_map = {
            'oceans': 'hydrosphere',
            'mountain_ranges': 'lithosphere',
            'rivers': 'hydrosphere',
            'deserts': 'climate_zone',
            'forests': 'biosphere'
        }
        return phys_map.get(subcategory, 'terrestrial')
    
    def _build_geopolitical_hierarchy(self, entity: str, subcategory: str) -> List[str]:
        """Build geopolitical hierarchy"""
        # Simplified hierarchy building
        if subcategory == 'us_states':
            return ['United States', entity]
        elif subcategory == 'major_cities':
            return ['United States', 'Municipal', entity]
        elif subcategory == 'countries':
            return [entity]
        else:
            return [entity]
    
    def _build_geographic_hierarchy(self, entity: str, subcategory: str) -> List[str]:
        """Build geographic hierarchy"""
        if subcategory == 'continents':
            return [entity]
        elif subcategory == 'countries':
            return ['Earth', entity]
        else:
            return ['Earth', entity]
    
    def _calculate_extraction_confidence(self, raw_entities: List[RawEntityMetadata]) -> float:
        """Calculate overall extraction confidence"""
        if not raw_entities:
            return 0.0
        
        # Base confidence on entity distribution and conflicts
        unique_entities = len(set(e.value.lower() for e in raw_entities))
        confidence = min(0.95, 0.7 + (unique_entities / len(raw_entities)) * 0.25)
        return round(confidence, 2)

def test_hybrid_system():
    """Test the hybrid metadata system"""
    
    test_text = """
    The Environmental Protection Agency (EPA) announced new regulations affecting 
    Texas, California, and New York. The Mississippi River cleanup will coordinate 
    with NATO and United Nations standards. Los Angeles and Chicago officials 
    are meeting with federal representatives near the Rocky Mountains region.
    """
    
    print("🧪 Testing Hybrid Entity Metadata System (Option C)")
    print("=" * 60)
    
    system = HybridEntityMetadataSystem()
    result = system.extract_hybrid_metadata(test_text)
    
    # Print raw entities
    print("📋 Raw Entities (Immediate Use):")
    print("-" * 35)
    
    print(f"GPE ({len(result['raw_entities']['gpe'])} entities):")
    for entity in result['raw_entities']['gpe']:
        print(f"  - {entity.value} [{entity.subcategory}] @ {entity.span}")
    
    print(f"\nLOC ({len(result['raw_entities']['loc'])} entities):")
    for entity in result['raw_entities']['loc']:
        print(f"  - {entity.value} [{entity.subcategory}] @ {entity.span}")
    
    # Print normalized entities (sample)
    print(f"\n🎯 Normalized Entities (Rich Metadata):")
    print("-" * 40)
    
    for entity in result['normalized_entities']['geopolitical'][:3]:
        print(f"• {entity.canonical_name}")
        print(f"  Type: {entity.entity_type}")
        print(f"  Authority: {entity.geopolitical_properties.get('authority_type')}")
        print(f"  Level: {entity.geopolitical_properties.get('authority_level')}")
        print(f"  Mentions: {len(entity.raw_mentions)}")
        if entity.alternative_classifications:
            print(f"  Alternatives: {entity.alternative_classifications}")
        print()
    
    return result

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_hybrid_system()