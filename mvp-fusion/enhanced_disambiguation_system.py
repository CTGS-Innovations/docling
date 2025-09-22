#!/usr/bin/env python3
"""
Enhanced Entity Disambiguation System
====================================

Implements specificity-first matching and context-aware entity resolution
for cases like Amazon (company) vs Amazon River vs Amazon Web Services.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from dataclasses import dataclass
import re

sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class EntityCandidate:
    """Entity candidate with disambiguation metadata"""
    text: str
    entity_type: str  # GPE, LOC, ORG
    subcategory: str
    start_pos: int
    end_pos: int
    specificity_score: int  # Length-based specificity
    context_score: int      # Context relevance score
    source_file: str

class EnhancedDisambiguationSystem:
    """
    Enhanced disambiguation using specificity-first matching and context awareness
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Load all entity data with disambiguation metadata
        self.entity_registry: Dict[str, List[EntityCandidate]] = {}
        self._load_foundation_data_with_disambiguation()
    
    def _load_foundation_data_with_disambiguation(self):
        """Load foundation data with disambiguation metadata"""
        
        # Load GPE data
        gpe_path = self._foundation_path / "gpe"
        gpe_subcategories = [
            "us_government_agencies", "federal_provincial_governments", "major_city_governments",
            "state_governments", "government_forms", "sovereign_entities_official_names",
            "countries", "us_states", "major_cities", "international_organizations",
            "regional_political_entities", "regional_and_geopolitical_blocs",
            "collective_forms", "demonyms_individuals", "language_linked_identities"
        ]
        
        for subcategory in gpe_subcategories:
            entities = self._load_subcategory_file(gpe_path, subcategory)
            for entity in entities:
                self._register_entity(entity, "GPE", subcategory, f"gpe/{subcategory}_*.txt")
        
        # Load LOC data
        loc_path = self._foundation_path / "loc"
        loc_subcategories = [
            "continents", "oceans", "seas_and_gulfs", "lakes", "rivers", "mountain_ranges",
            "mountains_peaks", "deserts", "islands_archipelagos", "peninsulas",
            "bays_straits_channels", "forests", "valleys_canyons", "plateaus_plains",
            "parks_protected_areas", "geographic_regions", "urban_settlements"
        ]
        
        for subcategory in loc_subcategories:
            entities = self._load_subcategory_file(loc_path, subcategory)
            for entity in entities:
                self._register_entity(entity, "LOC", subcategory, f"loc/{subcategory}_*.txt")
        
        # Load ORG data (if available)
        org_entities = self._load_subcategory_file(self._foundation_path, "organizations")
        for entity in org_entities:
            self._register_entity(entity, "ORG", "organizations", "organizations_*.txt")
        
        total_entities = sum(len(candidates) for candidates in self.entity_registry.values())
        self.logger.logger.info(f"🟢 Enhanced disambiguation loaded: {total_entities} entity candidates across {len(self.entity_registry)} unique texts")
    
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
    
    def _register_entity(self, entity_text: str, entity_type: str, subcategory: str, source_file: str):
        """Register entity candidate with disambiguation metadata"""
        
        # Calculate specificity score (longer = more specific)
        specificity_score = len(entity_text.split())  # Word count based
        
        # Calculate context score based on type and subcategory
        context_score = self._calculate_context_score(entity_type, subcategory)
        
        candidate = EntityCandidate(
            text=entity_text,
            entity_type=entity_type,
            subcategory=subcategory,
            start_pos=0,  # Will be set during extraction
            end_pos=0,    # Will be set during extraction
            specificity_score=specificity_score,
            context_score=context_score,
            source_file=source_file
        )
        
        # Use lowercase key for case-insensitive matching
        key = entity_text.lower()
        if key not in self.entity_registry:
            self.entity_registry[key] = []
        self.entity_registry[key].append(candidate)
    
    def _calculate_context_score(self, entity_type: str, subcategory: str) -> int:
        """Calculate context relevance score"""
        
        # Higher scores for more specific/authoritative sources
        context_scores = {
            # GPE subcategories
            "us_government_agencies": 10,
            "international_organizations": 9,
            "countries": 8,
            "us_states": 7,
            "major_cities": 6,
            
            # LOC subcategories  
            "parks_protected_areas": 9,
            "mountain_ranges": 8,
            "rivers": 8,
            "oceans": 8,
            "forests": 7,
            "lakes": 7,
            
            # ORG subcategories
            "organizations": 5  # Lower than specific geographic features
        }
        
        return context_scores.get(subcategory, 3)
    
    def extract_entities_with_disambiguation(self, text: str) -> List[EntityCandidate]:
        """
        Extract entities using specificity-first disambiguation
        """
        
        # Step 1: Find all potential matches
        candidates = []
        text_lower = text.lower()
        
        for entity_key, entity_candidates in self.entity_registry.items():
            # Find all occurrences of this entity text
            start_pos = 0
            while True:
                pos = text_lower.find(entity_key, start_pos)
                if pos == -1:
                    break
                
                # Check word boundaries
                if self._is_word_boundary(text, pos, len(entity_key)):
                    end_pos = pos + len(entity_key)
                    
                    # Add all candidates for this position
                    for candidate in entity_candidates:
                        positioned_candidate = EntityCandidate(
                            text=text[pos:end_pos],  # Use original case from text
                            entity_type=candidate.entity_type,
                            subcategory=candidate.subcategory,
                            start_pos=pos,
                            end_pos=end_pos,
                            specificity_score=candidate.specificity_score,
                            context_score=candidate.context_score,
                            source_file=candidate.source_file
                        )
                        candidates.append(positioned_candidate)
                
                start_pos = pos + 1
        
        # Step 2: Resolve conflicts using specificity-first strategy
        resolved_entities = self._resolve_entity_conflicts(candidates, text)
        
        # Step 3: Sort by position
        resolved_entities.sort(key=lambda x: x.start_pos)
        
        return resolved_entities
    
    def _resolve_entity_conflicts(self, candidates: List[EntityCandidate], text: str) -> List[EntityCandidate]:
        """
        Resolve entity conflicts using specificity-first strategy
        """
        
        if not candidates:
            return []
        
        # Group overlapping candidates
        conflict_groups = []
        
        for candidate in candidates:
            # Find overlapping group
            placed = False
            for group in conflict_groups:
                if any(self._positions_overlap(candidate, existing) for existing in group):
                    group.append(candidate)
                    placed = True
                    break
            
            if not placed:
                conflict_groups.append([candidate])
        
        # Resolve each conflict group
        resolved = []
        
        for group in conflict_groups:
            if len(group) == 1:
                # No conflict
                resolved.append(group[0])
            else:
                # Conflict - apply disambiguation strategy
                best_candidate = self._select_best_candidate(group, text)
                resolved.append(best_candidate)
        
        return resolved
    
    def _select_best_candidate(self, candidates: List[EntityCandidate], text: str) -> EntityCandidate:
        """
        Select best candidate using specificity-first strategy
        """
        
        # Strategy 1: Longest match wins (most specific)
        max_length = max(len(c.text) for c in candidates)
        longest_candidates = [c for c in candidates if len(c.text) == max_length]
        
        if len(longest_candidates) == 1:
            return longest_candidates[0]
        
        # Strategy 2: Highest specificity score (word count)
        max_specificity = max(c.specificity_score for c in longest_candidates)
        most_specific = [c for c in longest_candidates if c.specificity_score == max_specificity]
        
        if len(most_specific) == 1:
            return most_specific[0]
        
        # Strategy 3: Context analysis
        context_candidate = self._analyze_context_preference(most_specific, text)
        if context_candidate:
            return context_candidate
        
        # Strategy 4: Highest context score (authority)
        max_context = max(c.context_score for c in most_specific)
        best_context = [c for c in most_specific if c.context_score == max_context]
        
        # Return first of best context candidates
        return best_context[0]
    
    def _analyze_context_preference(self, candidates: List[EntityCandidate], text: str) -> EntityCandidate:
        """
        Analyze surrounding context to prefer appropriate entity type
        """
        
        # Extract context around the entity
        for candidate in candidates:
            context_start = max(0, candidate.start_pos - 100)
            context_end = min(len(text), candidate.end_pos + 100)
            context = text[context_start:context_end].lower()
            
            # Context keywords for different entity types
            org_keywords = ['company', 'corporation', 'inc', 'services', 'business', 'technology', 'cloud', 'platform']
            loc_keywords = ['river', 'forest', 'rainforest', 'basin', 'region', 'area', 'geographic', 'environmental']
            gpe_keywords = ['government', 'state', 'country', 'city', 'administration', 'agency', 'department']
            
            # Score context preferences
            if candidate.entity_type == "ORG" and any(keyword in context for keyword in org_keywords):
                return candidate
            elif candidate.entity_type == "LOC" and any(keyword in context for keyword in loc_keywords):
                return candidate
            elif candidate.entity_type == "GPE" and any(keyword in context for keyword in gpe_keywords):
                return candidate
        
        return None  # No clear context preference
    
    def _positions_overlap(self, candidate1: EntityCandidate, candidate2: EntityCandidate) -> bool:
        """Check if two candidates overlap in position"""
        return not (candidate1.end_pos <= candidate2.start_pos or candidate2.end_pos <= candidate1.start_pos)
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Check word boundaries"""
        end = start + length
        
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True

def test_enhanced_disambiguation():
    """Test enhanced disambiguation system"""
    
    test_cases = [
        "Amazon Web Services provides cloud computing solutions.",
        "Amazon River flows through the Amazon Rainforest.",
        "Amazon sells books and Amazon Prime offers streaming.",
        "Environmental studies in the Amazon basin continue.",
        "The company Amazon partners with government agencies."
    ]
    
    print("🧪 Enhanced Disambiguation System Test")
    print("=" * 45)
    
    system = EnhancedDisambiguationSystem()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. Test: '{test_text}'")
        entities = system.extract_entities_with_disambiguation(test_text)
        
        for entity in entities:
            print(f"   → {entity.entity_type}:{entity.subcategory} - '{entity.text}' (spec:{entity.specificity_score}, ctx:{entity.context_score})")

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_enhanced_disambiguation()