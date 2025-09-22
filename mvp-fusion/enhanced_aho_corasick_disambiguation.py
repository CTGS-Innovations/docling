#!/usr/bin/env python3
"""
Enhanced Aho-Corasick with Disambiguation
=========================================

Extends existing Aho-Corasick engine with specificity-first disambiguation
in the algorithm layer, not the corpus organization layer.
"""

import ahocorasick
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from utils.logging_config import get_fusion_logger

@dataclass
class EntityMatch:
    """Entity match with disambiguation metadata"""
    text: str
    start_pos: int
    end_pos: int
    entity_type: str  # GPE, LOC, ORG
    subcategory: str
    specificity_score: int  # Word count
    priority_score: int     # Category priority
    source_info: str

class EnhancedAhoCorasickDisambiguation:
    """
    Enhanced Aho-Corasick with LeftmostLongest disambiguation strategy
    
    Implements industry best practice from Context7 research:
    - Single-pass detection with O(n) performance
    - LeftmostLongest matching eliminates overlap conflicts at algorithm level
    - Specificity-first tiebreaking for same-length matches
    - No post-processing overlap resolution needed
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self.automaton = ahocorasick.Automaton()
        self.entity_metadata = {}  # Maps pattern_id to metadata
        self._foundation_path = Path(__file__).parent / "knowledge/corpus/foundation_data"
        
        # Priority scores for entity types and subcategories
        self.type_priorities = {'ORG': 10, 'GPE': 8, 'LOC': 6}
        self.subcategory_priorities = {
            'us_government_agencies': 10, 'organizations': 9,
            'countries': 8, 'us_states': 7, 'major_cities': 6,
            'rivers': 8, 'oceans': 8, 'forests': 7, 'lakes': 7
        }
        
        self._build_enhanced_automaton()
    
    def _build_enhanced_automaton(self):
        """Build Aho-Corasick automaton with all entities and metadata"""
        
        pattern_id = 0
        
        # Load GPE entities
        gpe_subcategories = ["us_government_agencies", "countries", "us_states", "major_cities", 
                           "international_organizations"]
        
        for subcategory in gpe_subcategories:
            entities = self._load_subcategory_file("gpe", subcategory)
            for entity in entities:
                self._add_entity_to_automaton(entity, "GPE", subcategory, pattern_id)
                pattern_id += 1
        
        # Load LOC entities  
        loc_subcategories = ["rivers", "lakes", "oceans", "forests", "mountain_ranges",
                           "parks_protected_areas", "geographic_regions"]
        
        for subcategory in loc_subcategories:
            entities = self._load_subcategory_file("loc", subcategory)
            for entity in entities:
                self._add_entity_to_automaton(entity, "LOC", subcategory, pattern_id)
                pattern_id += 1
        
        # Load ORG entities
        org_entities = self._load_subcategory_file("", "organizations")
        for entity in org_entities:
            self._add_entity_to_automaton(entity, "ORG", "organizations", pattern_id)
            pattern_id += 1
        
        # Finalize automaton
        self.automaton.make_automaton()
        
        self.logger.logger.info(f"🟢 Enhanced Aho-Corasick built: {pattern_id} patterns with disambiguation")
    
    def _add_entity_to_automaton(self, entity: str, entity_type: str, subcategory: str, pattern_id: int):
        """Add entity to automaton with metadata"""
        
        # Calculate scores
        specificity_score = len(entity.split())  # Word count
        priority_score = (self.type_priorities.get(entity_type, 5) + 
                         self.subcategory_priorities.get(subcategory, 5))
        
        # Store metadata
        metadata = EntityMatch(
            text=entity,
            start_pos=0,  # Will be set during search
            end_pos=0,    # Will be set during search
            entity_type=entity_type,
            subcategory=subcategory,
            specificity_score=specificity_score,
            priority_score=priority_score,
            source_info=f"{entity_type.lower()}/{subcategory}"
        )
        
        self.entity_metadata[pattern_id] = metadata
        
        # Add to automaton (case-insensitive)
        self.automaton.add_word(entity.lower(), pattern_id)
    
    def _load_subcategory_file(self, subdir: str, subcategory: str) -> Set[str]:
        """Load entities from subcategory file"""
        date_patterns = ["2025_09_22", "2025_09_18"]
        
        for date_pattern in date_patterns:
            if subdir:
                file_path = self._foundation_path / subdir / f"{subcategory}_{date_pattern}.txt"
            else:
                file_path = self._foundation_path / f"{subcategory}_{date_pattern}.txt"
                
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        return {line.strip() for line in f if line.strip()}
                except Exception as e:
                    self.logger.logger.warning(f"⚠️ Error loading {file_path}: {e}")
        return set()
    
    def extract_with_disambiguation(self, text: str) -> List[EntityMatch]:
        """
        Extract entities with LeftmostLongest strategy (optimal Aho-Corasick approach)
        """
        
        # Step 1: Find ALL matches with positions
        candidate_matches = []
        text_lower = text.lower()
        
        for end_pos, pattern_id in self.automaton.iter(text_lower):
            metadata = self.entity_metadata[pattern_id]
            start_pos = end_pos - len(metadata.text) + 1
            
            # Verify word boundaries first (performance optimization)
            if not self._is_word_boundary(text, start_pos, len(metadata.text)):
                continue
            
            # Create match candidate
            match = EntityMatch(
                text=text[start_pos:end_pos + 1],  # Original case from text
                start_pos=start_pos,
                end_pos=end_pos + 1,
                entity_type=metadata.entity_type,
                subcategory=metadata.subcategory,
                specificity_score=metadata.specificity_score,
                priority_score=metadata.priority_score,
                source_info=metadata.source_info
            )
            candidate_matches.append(match)
        
        # Step 2: Apply LeftmostLongest algorithm (industry best practice)
        resolved_matches = self._apply_leftmost_longest_strategy(candidate_matches)
        
        # Step 3: Sort by position
        resolved_matches.sort(key=lambda x: x.start_pos)
        
        return resolved_matches
    
    def _apply_leftmost_longest_strategy(self, candidates: List[EntityMatch]) -> List[EntityMatch]:
        """
        Apply LeftmostLongest strategy: for overlapping matches, return leftmost match
        that is also the longest among all overlapping matches at that position.
        
        This implements the industry best practice from Context7 research.
        """
        
        if not candidates:
            return []
        
        # Sort by start position, then by length (longest first)
        candidates.sort(key=lambda x: (x.start_pos, -len(x.text)))
        
        resolved = []
        last_end_pos = 0
        
        i = 0
        while i < len(candidates):
            current = candidates[i]
            
            # Skip if this match overlaps with already selected match
            if current.start_pos < last_end_pos:
                i += 1
                continue
            
            # Find all matches starting at the same position
            same_start_matches = [current]
            j = i + 1
            while j < len(candidates) and candidates[j].start_pos == current.start_pos:
                same_start_matches.append(candidates[j])
                j += 1
            
            # Among matches at same start position, select the longest
            # If multiple have same length, apply disambiguation rules
            longest_match = self._select_longest_with_tiebreaking(same_start_matches)
            
            resolved.append(longest_match)
            last_end_pos = longest_match.end_pos
            
            # Skip all matches at this position
            i = j
        
        return resolved
    
    def _select_longest_with_tiebreaking(self, matches: List[EntityMatch]) -> EntityMatch:
        """
        Select longest match, with tiebreaking rules for same-length matches
        """
        
        # Get longest matches
        max_length = max(len(m.text) for m in matches)
        longest_matches = [m for m in matches if len(m.text) == max_length]
        
        if len(longest_matches) == 1:
            return longest_matches[0]
        
        # Tiebreaking rules for same-length matches
        # Rule 1: Highest specificity score (word count)
        max_specificity = max(m.specificity_score for m in longest_matches)
        most_specific = [m for m in longest_matches if m.specificity_score == max_specificity]
        
        if len(most_specific) == 1:
            return most_specific[0]
        
        # Rule 2: Highest priority score (entity type + subcategory)
        max_priority = max(m.priority_score for m in most_specific)
        highest_priority = [m for m in most_specific if m.priority_score == max_priority]
        
        # Return first of highest priority (deterministic)
        return highest_priority[0]
    
    def _resolve_overlapping_matches(self, matches: List[EntityMatch], text: str) -> List[EntityMatch]:
        """
        Algorithm-level disambiguation - this is where the magic happens
        """
        
        if not matches:
            return []
        
        # Group overlapping matches
        conflict_groups = []
        
        for match in matches:
            placed = False
            for group in conflict_groups:
                if any(self._matches_overlap(match, existing) for existing in group):
                    group.append(match)
                    placed = True
                    break
            
            if not placed:
                conflict_groups.append([match])
        
        # Resolve each group using specificity-first strategy
        resolved = []
        
        for group in conflict_groups:
            if len(group) == 1:
                resolved.append(group[0])
            else:
                best_match = self._select_best_match(group, text)
                resolved.append(best_match)
        
        return resolved
    
    def _select_best_match(self, candidates: List[EntityMatch], text: str) -> EntityMatch:
        """
        Specificity-first disambiguation strategy
        """
        
        # Rule 1: Longest match wins (most specific)
        max_length = max(len(c.text) for c in candidates)
        longest_matches = [c for c in candidates if len(c.text) == max_length]
        
        if len(longest_matches) == 1:
            return longest_matches[0]
        
        # Rule 2: Highest word count (specificity score)
        max_specificity = max(c.specificity_score for c in longest_matches)
        most_specific = [c for c in longest_matches if c.specificity_score == max_specificity]
        
        if len(most_specific) == 1:
            return most_specific[0]
        
        # Rule 3: Context analysis (Amazon Web Services vs Amazon River)
        context_winner = self._analyze_context(most_specific, text)
        if context_winner:
            return context_winner
        
        # Rule 4: Priority score (entity type + subcategory importance)
        max_priority = max(c.priority_score for c in most_specific)
        highest_priority = [c for c in most_specific if c.priority_score == max_priority]
        
        return highest_priority[0]  # Return first of highest priority
    
    def _analyze_context(self, candidates: List[EntityMatch], text: str) -> EntityMatch:
        """Context-aware disambiguation"""
        
        for candidate in candidates:
            # Extract 200-char context window
            context_start = max(0, candidate.start_pos - 100)
            context_end = min(len(text), candidate.end_pos + 100)
            context = text[context_start:context_end].lower()
            
            # Context keywords
            if candidate.entity_type == "ORG":
                org_keywords = ['company', 'corporation', 'services', 'inc', 'business', 'technology', 'cloud']
                if any(keyword in context for keyword in org_keywords):
                    return candidate
            
            elif candidate.entity_type == "LOC":
                loc_keywords = ['river', 'forest', 'basin', 'flows', 'environmental', 'geographic']
                if any(keyword in context for keyword in loc_keywords):
                    return candidate
        
        return None
    
    def _matches_overlap(self, match1: EntityMatch, match2: EntityMatch) -> bool:
        """Check if two matches overlap"""
        return not (match1.end_pos <= match2.start_pos or match2.end_pos <= match1.start_pos)
    
    def _is_word_boundary(self, text: str, start: int, length: int) -> bool:
        """Check word boundaries"""
        end = start + length
        
        if start > 0 and text[start - 1].isalnum():
            return False
        if end < len(text) and text[end].isalnum():
            return False
        return True

def test_enhanced_aho_corasick():
    """Test the enhanced Aho-Corasick disambiguation"""
    
    test_cases = [
        "Amazon Web Services provides cloud computing.",
        "Amazon River flows through South America.",
        "Amazon company partnered with Amazon AI services.",
        "Environmental studies of Amazon Rainforest continue.",
        "Amazon Prime and Amazon Fresh are Amazon services."
    ]
    
    print("🧪 Enhanced Aho-Corasick Disambiguation Test")
    print("=" * 50)
    
    extractor = EnhancedAhoCorasickDisambiguation()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n{i}. Test: '{test_text}'")
        matches = extractor.extract_with_disambiguation(test_text)
        
        for match in matches:
            print(f"   → {match.entity_type}:{match.subcategory} - '{match.text}' (len:{len(match.text)}, spec:{match.specificity_score}, pri:{match.priority_score})")

if __name__ == "__main__":
    import os
    os.chdir('/home/corey/projects/docling/mvp-fusion')
    
    test_enhanced_aho_corasick()