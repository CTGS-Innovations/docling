#!/usr/bin/env python3
"""
Optimized Entity Metadata Extractor with Deduplication
======================================================

Enhanced version that handles entity overlaps and provides priority-based classification.
Includes rich subcategory metadata with conflict resolution.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import json

sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class OptimizedEntityMetadata:
    """Enhanced entity with subcategory metadata and priority"""
    text: str
    entity_type: str  # GPE or LOC
    subcategory: str  # Primary subcategory
    alternative_subcategories: List[str]  # Other possible subcategories
    context: str
    confidence: float
    start_pos: int
    end_pos: int
    source_files: List[str]  # All source files that matched
    priority_score: int  # Higher = more specific/important

class OptimizedEntityExtractor:
    """
    Optimized entity extractor with deduplication and priority ranking
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Load foundation data with priority scoring
        self.gpe_data: Dict[str, Set[str]] = {}
        self.loc_data: Dict[str, Set[str]] = {}
        
        # Priority scores for subcategories (higher = more specific/important)
        self.gpe_priorities = {
            "us_government_agencies": 10,
            "federal_provincial_governments": 9,
            "major_city_governments": 8,
            "state_governments": 8,
            "government_forms": 7,
            "sovereign_entities_official_names": 6,
            "countries": 6,
            "us_states": 5,
            "major_cities": 4,
            "international_organizations": 4,
            "regional_political_entities": 3,
            "regional_and_geopolitical_blocs": 3,
            "collective_forms": 2,
            "demonyms_individuals": 2,
            "language_linked_identities": 1
        }
        
        self.loc_priorities = {
            "parks_protected_areas": 8,
            "mountain_ranges": 7,
            "mountains_peaks": 7,
            "valleys_canyons": 7,
            "deserts": 6,
            "forests": 6,
            "oceans": 6,
            "seas_and_gulfs": 6,
            "lakes": 6,
            "rivers": 6,
            "islands_archipelagos": 6,
            "peninsulas": 6,
            "bays_straits_channels": 6,
            "plateaus_plains": 5,
            "continents": 4,
            "geographic_regions": 3,
            "urban_settlements": 2
        }
        
        self._load_foundation_data()
    
    def _load_foundation_data(self):
        """Load all foundation data files with subcategory mapping"""
        
        # GPE subcategories
        gpe_subcategories = list(self.gpe_priorities.keys())
        
        # LOC subcategories  
        loc_subcategories = list(self.loc_priorities.keys())
        
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
        
        self.logger.logger.info(f"🟢 **SUCCESS**: Optimized foundation data loaded - GPE: {total_gpe} entities across {len(self.gpe_data)} subcategories, LOC: {total_loc} entities across {len(self.loc_data)} subcategories")
    
    def _load_subcategory_file(self, base_path: Path, subcategory: str) -> Set[str]:
        """Load entities from a specific subcategory file"""
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
        
        return set()
    
    def extract_entities_with_metadata(self, text: str, context_window: int = 50) -> List[OptimizedEntityMetadata]:
        """
        Extract entities with rich subcategory metadata and deduplication
        """
        
        # Step 1: Find all possible entity matches
        all_matches = []
        
        # Extract GPE entities
        gpe_matches = self._find_all_matches(text, self.gpe_data, "GPE", context_window)
        all_matches.extend(gpe_matches)
        
        # Extract LOC entities  
        loc_matches = self._find_all_matches(text, self.loc_data, "LOC", context_window)
        all_matches.extend(loc_matches)
        
        # Step 2: Deduplicate and resolve conflicts
        optimized_entities = self._deduplicate_and_prioritize(all_matches)
        
        # Step 3: Sort by position in text
        optimized_entities.sort(key=lambda x: x.start_pos)
        
        return optimized_entities
    
    def _find_all_matches(self, text: str, data_dict: Dict[str, Set[str]], entity_type: str, context_window: int) -> List[Dict]:
        """Find all entity matches without deduplication"""
        matches = []
        text_lower = text.lower()
        
        for subcategory, entity_set in data_dict.items():
            for entity in entity_set:
                entity_lower = entity.lower()
                start_pos = 0
                
                while True:
                    pos = text_lower.find(entity_lower, start_pos)
                    if pos == -1:
                        break
                    
                    if self._is_word_boundary(text, pos, len(entity)):
                        end_pos = pos + len(entity)
                        context = self._extract_context(text, pos, end_pos, context_window)
                        
                        match = {
                            'text': text[pos:end_pos],
                            'entity_type': entity_type,
                            'subcategory': subcategory,
                            'context': context,
                            'start_pos': pos,
                            'end_pos': end_pos,
                            'source_file': f"{entity_type.lower()}/{subcategory}_*.txt",
                            'priority_score': self.gpe_priorities.get(subcategory, 0) if entity_type == "GPE" else self.loc_priorities.get(subcategory, 0)
                        }
                        matches.append(match)
                    
                    start_pos = pos + 1
        
        return matches
    
    def _deduplicate_and_prioritize(self, all_matches: List[Dict]) -> List[OptimizedEntityMetadata]:
        """Deduplicate overlapping entities and assign priorities"""
        
        # Group matches by position overlap
        position_groups = {}
        
        for match in all_matches:
            # Find overlapping groups
            overlapping_group = None
            for key, group in position_groups.items():
                # Check if this match overlaps with any in the group
                if any(self._positions_overlap(match['start_pos'], match['end_pos'], 
                                             existing['start_pos'], existing['end_pos']) 
                       for existing in group):
                    overlapping_group = key
                    break
            
            if overlapping_group:
                position_groups[overlapping_group].append(match)
            else:
                # Create new group
                new_key = f"{match['start_pos']}_{match['end_pos']}"
                position_groups[new_key] = [match]
        
        # Resolve each group
        optimized_entities = []
        
        for group in position_groups.values():
            if len(group) == 1:
                # No conflict - single match
                match = group[0]
                entity = OptimizedEntityMetadata(
                    text=match['text'],
                    entity_type=match['entity_type'],
                    subcategory=match['subcategory'],
                    alternative_subcategories=[],
                    context=match['context'],
                    confidence=0.9,
                    start_pos=match['start_pos'],
                    end_pos=match['end_pos'],
                    source_files=[match['source_file']],
                    priority_score=match['priority_score']
                )
                optimized_entities.append(entity)
            else:
                # Conflict - multiple matches for same position
                # Choose highest priority, record alternatives
                group.sort(key=lambda x: x['priority_score'], reverse=True)
                primary = group[0]
                alternatives = group[1:]
                
                entity = OptimizedEntityMetadata(
                    text=primary['text'],
                    entity_type=primary['entity_type'],
                    subcategory=primary['subcategory'],
                    alternative_subcategories=[alt['subcategory'] for alt in alternatives],
                    context=primary['context'],
                    confidence=0.8,  # Lower confidence due to conflict
                    start_pos=primary['start_pos'],
                    end_pos=primary['end_pos'],
                    source_files=[match['source_file'] for match in group],
                    priority_score=primary['priority_score']
                )
                optimized_entities.append(entity)
        
        return optimized_entities
    
    def _positions_overlap(self, start1: int, end1: int, start2: int, end2: int) -> bool:
        """Check if two position ranges overlap"""
        return not (end1 <= start2 or end2 <= start1)
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Check if the match is at word boundaries"""
        end = start + length
        
        if start > 0 and text[start - 1].isalnum():
            return False
            
        if end < len(text) and text[end].isalnum():
            return False
            
        return True
    
    def _extract_context(self, text: str, start: int, end: int, window: int) -> str:
        """Extract context around the entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        context = text[context_start:context_end]
        entity_pos_in_context = start - context_start
        entity_text = text[start:end]
        context_with_marker = (
            context[:entity_pos_in_context] + 
            f"[{entity_text}]" + 
            context[entity_pos_in_context + len(entity_text):]
        )
        
        return context_with_marker.strip()
    
    def print_optimized_summary(self, entities: List[OptimizedEntityMetadata]):
        """Print formatted summary with conflict information"""
        
        # Count by subcategory
        gpe_counts = {}
        loc_counts = {}
        conflicts = 0
        
        for entity in entities:
            if entity.entity_type == "GPE":
                gpe_counts[entity.subcategory] = gpe_counts.get(entity.subcategory, 0) + 1
            elif entity.entity_type == "LOC":
                loc_counts[entity.subcategory] = loc_counts.get(entity.subcategory, 0) + 1
            
            if entity.alternative_subcategories:
                conflicts += 1
        
        # Format summaries
        gpe_parts = [f"{subcategory}:{count}" for subcategory, count in gpe_counts.items() if count > 0]
        if gpe_parts:
            print(f"📊 GPE entities: {', '.join(gpe_parts)}")
        
        loc_parts = [f"{subcategory}:{count}" for subcategory, count in loc_counts.items() if count > 0]
        if loc_parts:
            print(f"🌍 LOC entities: {', '.join(loc_parts)}")
        
        if conflicts > 0:
            print(f"⚖️ Resolved conflicts: {conflicts} entities had multiple possible classifications")

def test_optimized_extraction():
    """Test the optimized extraction system"""
    
    test_text = """
    The Environmental Protection Agency (EPA) coordinates with the Department of Defense
    on cleanup operations in Texas, California, and New York. The Mississippi River
    cleanup affects multiple states including Mississippi. Los Angeles and New York City
    officials are working with federal agencies. NATO and United Nations standards apply.
    """
    
    print("🧪 Testing Optimized Entity Extraction with Conflict Resolution")
    print("=" * 75)
    
    extractor = OptimizedEntityExtractor()
    entities = extractor.extract_entities_with_metadata(test_text)
    
    extractor.print_optimized_summary(entities)
    
    print(f"\n📋 Detailed Results ({len(entities)} optimized entities):")
    print("-" * 55)
    
    for i, entity in enumerate(entities, 1):
        priority_indicator = "🔥" if entity.priority_score >= 8 else "⭐" if entity.priority_score >= 5 else "💫"
        
        print(f"{i:2d}. {priority_indicator} [{entity.entity_type}:{entity.subcategory}] '{entity.text}' (Priority: {entity.priority_score})")
        
        if entity.alternative_subcategories:
            print(f"     📋 Also matched: {', '.join(entity.alternative_subcategories)}")
        
        print(f"     📍 Context: {entity.context}")
        print()

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_optimized_extraction()