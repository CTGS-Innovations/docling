#!/usr/bin/env python3
"""
High-Performance Entity Metadata System
=======================================

Fixed version using proper Aho-Corasick non-linear processing.
Replaces O(n²) loops with single-pass Aho-Corasick automaton.

PERFORMANCE TARGET: Restore 10,368 pages/sec (5.1ms per document)
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import ahocorasick

sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class EntityMatch:
    """Optimized entity match with metadata"""
    text: str
    entity_type: str  # GPE or LOC
    subcategory: str
    start: int
    end: int
    priority: int
    canonical_name: str

class HighPerformanceEntityMetadata:
    """
    High-performance entity metadata extraction using Aho-Corasick single-pass processing
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Single Aho-Corasick automaton for ALL entities
        self.entity_automaton = None
        self.entity_metadata = {}  # Maps entity -> metadata
        
        # Hierarchy configurations
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
        
        self._build_automaton()
    
    def _build_automaton(self):
        """Build single Aho-Corasick automaton for ALL entities (GPE + LOC)"""
        self.entity_automaton = ahocorasick.Automaton()
        entity_count = 0
        
        # Load GPE entities into automaton
        gpe_path = self._foundation_path / "gpe"
        for subcategory, hierarchy_info in self.gpe_hierarchy.items():
            entities = self._load_subcategory_file(gpe_path, subcategory)
            
            for entity in entities:
                entity_lower = entity.lower()
                
                # Store metadata for entity
                self.entity_metadata[entity_lower] = {
                    'canonical_name': entity,
                    'entity_type': 'GPE',
                    'subcategory': subcategory,
                    'priority': hierarchy_info.get('priority', 0),
                    'hierarchy_info': hierarchy_info
                }
                
                # Add to automaton
                self.entity_automaton.add_word(entity_lower, (entity_lower, 'GPE', subcategory))
                entity_count += 1
        
        # Load LOC entities into automaton  
        loc_path = self._foundation_path / "loc"
        for subcategory, hierarchy_info in self.loc_hierarchy.items():
            entities = self._load_subcategory_file(loc_path, subcategory)
            
            for entity in entities:
                entity_lower = entity.lower()
                
                # Store metadata for entity
                self.entity_metadata[entity_lower] = {
                    'canonical_name': entity,
                    'entity_type': 'LOC',
                    'subcategory': subcategory,
                    'priority': hierarchy_info.get('priority', 0),
                    'hierarchy_info': hierarchy_info
                }
                
                # Add to automaton
                self.entity_automaton.add_word(entity_lower, (entity_lower, 'LOC', subcategory))
                entity_count += 1
        
        # Compile automaton for searching
        self.entity_automaton.make_automaton()
        
        self.logger.logger.info(f"🟢 **SUCCESS**: Aho-Corasick automaton built with {entity_count} entities")
    
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
    
    def extract_entities_fast(self, text: str) -> Dict[str, Any]:
        """
        SINGLE-PASS entity extraction using Aho-Corasick automaton
        NON-LINEAR: O(n + m) where n=text length, m=pattern count
        """
        
        # Single pass through text to find ALL matches
        raw_matches = []
        text_lower = text.lower()
        
        # PERFORMANCE: Single Aho-Corasick scan finds ALL entities
        for end_index, (entity_key, entity_type, subcategory) in self.entity_automaton.iter(text_lower):
            entity_metadata = self.entity_metadata[entity_key]
            entity_length = len(entity_key)
            start_index = end_index - entity_length + 1
            
            # Word boundary check
            if self._is_word_boundary(text, start_index, entity_length):
                match = EntityMatch(
                    text=text[start_index:end_index + 1],
                    entity_type=entity_type,
                    subcategory=subcategory,
                    start=start_index,
                    end=end_index + 1,
                    priority=entity_metadata['priority'],
                    canonical_name=entity_metadata['canonical_name']
                )
                raw_matches.append(match)
        
        # Resolve overlaps using LeftmostLongest strategy (non-linear)
        resolved_matches = self._resolve_overlaps_fast(raw_matches)
        
        # Structure results
        gpe_entities = []
        loc_entities = []
        
        for match in resolved_matches:
            entity_data = {
                'value': match.canonical_name,
                'text': match.text,
                'subcategory': match.subcategory,
                'span': {'start': match.start, 'end': match.end},
                'metadata': self.entity_metadata[match.canonical_name.lower()]
            }
            
            if match.entity_type == 'GPE':
                gpe_entities.append(entity_data)
            else:
                loc_entities.append(entity_data)
        
        return {
            'gpe': gpe_entities,
            'location': loc_entities,
            'metadata': {
                'total_matches': len(raw_matches),
                'resolved_matches': len(resolved_matches),
                'processing_method': 'aho_corasick_single_pass'
            }
        }
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Fast word boundary check"""
        end = start + length
        
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True
    
    def _resolve_overlaps_fast(self, matches: List[EntityMatch]) -> List[EntityMatch]:
        """
        Fast LeftmostLongest overlap resolution
        NON-LINEAR: Sort once, single pass resolution
        """
        if not matches:
            return matches
        
        # Sort by start position, then by length (longest first)
        matches_sorted = sorted(matches, key=lambda x: (x.start, -(x.end - x.start), -x.priority))
        
        resolved = []
        last_end = -1
        
        # Single pass resolution
        for match in matches_sorted:
            if match.start >= last_end:  # No overlap with previous
                resolved.append(match)
                last_end = match.end
        
        return resolved

def test_performance():
    """Test performance vs hybrid system"""
    
    test_text = """
    The Environmental Protection Agency (EPA) announced new regulations affecting 
    Texas, California, and New York. The Mississippi River cleanup will coordinate 
    with NATO and United Nations standards. Los Angeles and Chicago officials 
    are meeting with federal representatives near the Rocky Mountains region.
    Amazon Web Services provides cloud computing. Amazon River flows through Brazil.
    Amazon company is headquartered in Seattle. The Great Lakes include Lake Superior.
    """
    
    print("🚀 Testing High-Performance Entity Metadata System")
    print("=" * 60)
    
    import time
    
    system = HighPerformanceEntityMetadata()
    
    # Benchmark extraction
    start_time = time.time()
    result = system.extract_entities_fast(test_text)
    end_time = time.time()
    
    processing_time_ms = (end_time - start_time) * 1000
    chars_per_sec = len(test_text) / (end_time - start_time) if end_time > start_time else 0
    
    print(f"📊 Performance Metrics:")
    print(f"  - Processing time: {processing_time_ms:.2f}ms")
    print(f"  - Characters/sec: {chars_per_sec:,.0f}")
    print(f"  - Text length: {len(test_text)} chars")
    
    print(f"\n📋 Results:")
    print(f"  - GPE entities: {len(result['gpe'])}")
    print(f"  - LOC entities: {len(result['location'])}")
    print(f"  - Total matches found: {result['metadata']['total_matches']}")
    print(f"  - Resolved matches: {result['metadata']['resolved_matches']}")
    
    # Sample entities
    print(f"\n🎯 Sample GPE Entities:")
    for entity in result['gpe'][:3]:
        print(f"  - {entity['value']} [{entity['subcategory']}]")
    
    print(f"\n🏔️ Sample LOC Entities:")
    for entity in result['location'][:3]:
        print(f"  - {entity['value']} [{entity['subcategory']}]")
    
    return result

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_performance()