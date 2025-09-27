#!/usr/bin/env python3
"""
Span-Based Range Linker - Industry Best Practice Implementation
==============================================================

GOAL: Implement industry-standard span-based range linking
REASON: Single-pass detection + post-processing normalization is proven best practice
PROBLEM: Replaces flawed wide→narrow pattern precedence with proper span analysis

ARCHITECTURE:
- Phase 1: Universal single-pass entity detection (catches everything)
- Phase 2: Intelligent span analysis to link related entities into ranges
- Based on spaCy, CoreNLP, and OpenNLP architectural patterns

EXAMPLE:
Input entities: [{"30", span: 10-12}, {"37", span: 13-15}, {"inches", span: 16-22}]
Connector: "-" (span: 12-13)
Output range: {"30-37 inches", span: 10-22, components: [entity1, entity2, entity3]}
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class EntitySpan:
    """Universal entity representation with precise span information"""
    text: str
    start: int
    end: int
    entity_type: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

@dataclass
class RangeCandidate:
    """Potential range identified through span analysis"""
    start_entity: EntitySpan
    end_entity: EntitySpan
    connector: str
    connector_span: Tuple[int, int]
    unit_entity: Optional[EntitySpan] = None
    confidence: float = 1.0
    
    @property
    def full_span(self) -> Tuple[int, int]:
        """Calculate full span of the range"""
        start = self.start_entity.start
        end = self.unit_entity.end if self.unit_entity else self.end_entity.end
        return (start, end)
    
    @property
    def text(self) -> str:
        """Generate text representation of the range"""
        if self.unit_entity:
            return f"{self.start_entity.text}{self.connector}{self.end_entity.text} {self.unit_entity.text}"
        else:
            return f"{self.start_entity.text}{self.connector}{self.end_entity.text}"

class SpanBasedRangeLinker:
    """
    Industry-standard span-based range linking component.
    
    Implements the proven architecture used by spaCy, CoreNLP, and OpenNLP:
    1. Single-pass universal detection captures all entities
    2. Span analysis identifies proximity and connector patterns
    3. Intelligent linking creates consolidated range entities
    """
    
    def __init__(self):
        """Initialize span-based range linker with industry-standard patterns"""
        self.range_connectors = {
            '-': {'type': 'hyphen', 'strength': 0.9},
            '–': {'type': 'en_dash', 'strength': 0.9}, 
            '—': {'type': 'em_dash', 'strength': 0.8},
            ' to ': {'type': 'word', 'strength': 0.95},
            ' through ': {'type': 'word', 'strength': 0.9},
            ' between ': {'type': 'word', 'strength': 0.85},
            ' and ': {'type': 'word', 'strength': 0.7}  # Lower strength - more ambiguous
        }
        
        self.compatible_types = {
            'UNIVERSAL_NUMBERS': ['UNIVERSAL_NUMBERS', 'PERCENT', 'MONEY', 'MEASUREMENT'],
            'PERCENT': ['UNIVERSAL_NUMBERS', 'PERCENT'], 
            'MONEY': ['UNIVERSAL_NUMBERS', 'MONEY'],
            'MEASUREMENT': ['UNIVERSAL_NUMBERS', 'MEASUREMENT'],
            'DATE': ['UNIVERSAL_NUMBERS', 'DATE'],
            'TIME': ['UNIVERSAL_NUMBERS', 'TIME']
        }
    
    def link_ranges(self, entities: List[EntitySpan], original_text: str) -> List[EntitySpan]:
        """
        Industry-standard span-based range linking.
        
        Args:
            entities: List of entities detected in single pass
            original_text: Original text for span validation
            
        Returns:
            List of entities with ranges consolidated and individuals filtered
        """
        # Step 1: Find all potential range candidates
        range_candidates = self._find_range_candidates(entities, original_text)
        
        # Step 2: Score and validate candidates
        validated_ranges = self._validate_range_candidates(range_candidates, original_text)
        
        # Step 3: Convert to entity format and filter overlaps
        range_entities = self._convert_ranges_to_entities(validated_ranges, original_text)
        
        # Step 4: Remove individual entities that are part of ranges
        filtered_entities = self._filter_overlapping_entities(entities, range_entities)
        
        # Step 5: Combine ranges with remaining individual entities
        final_entities = range_entities + filtered_entities
        
        return sorted(final_entities, key=lambda e: e.start)
    
    def _find_range_candidates(self, entities: List[EntitySpan], text: str) -> List[RangeCandidate]:
        """Find potential ranges using span proximity analysis"""
        candidates = []
        
        # Sort entities by position for sequential analysis
        sorted_entities = sorted(entities, key=lambda e: e.start)
        
        for i, entity1 in enumerate(sorted_entities):
            # Only consider numeric-like entities as range starts
            if not self._is_numeric_entity(entity1):
                continue
                
            # Look for nearby compatible entities (but be more selective)
            for j in range(i + 1, min(i + 3, len(sorted_entities))):  # Check only next 2 entities
                entity2 = sorted_entities[j]
                
                # Check type compatibility
                if not self._are_types_compatible(entity1.entity_type, entity2.entity_type):
                    continue
                
                # SELECTIVITY: Entities should be reasonably close (within 10 characters)
                if entity2.start - entity1.end > 10:
                    continue
                
                # Check for connector between entities
                connector_info = self._find_connector_between(entity1, entity2, text)
                if not connector_info:
                    continue
                    
                connector, connector_span = connector_info
                
                # Look for unit entity after the second number
                unit_entity = self._find_unit_after(entity2, sorted_entities[j:], text)
                
                # SELECTIVITY: If unit exists, it should be immediately adjacent
                if unit_entity and unit_entity.start - entity2.end > 2:
                    unit_entity = None
                
                # Create range candidate
                candidate = RangeCandidate(
                    start_entity=entity1,
                    end_entity=entity2,
                    connector=connector,
                    connector_span=connector_span,
                    unit_entity=unit_entity,
                    confidence=self.range_connectors[connector]['strength']
                )
                
                candidates.append(candidate)
        
        return candidates
    
    def _find_connector_between(self, entity1: EntitySpan, entity2: EntitySpan, text: str) -> Optional[Tuple[str, Tuple[int, int]]]:
        """Find range connector between two entities"""
        # Extract text between entities
        between_start = entity1.end
        between_end = entity2.start
        
        if between_end <= between_start:
            return None
            
        between_text = text[between_start:between_end]
        
        # Check for each connector type
        for connector, info in self.range_connectors.items():
            if connector in between_text:
                # Find exact position of connector
                connector_pos = between_text.find(connector)
                connector_start = between_start + connector_pos
                connector_end = connector_start + len(connector)
                
                return (connector, (connector_start, connector_end))
        
        return None
    
    def _find_unit_after(self, number_entity: EntitySpan, remaining_entities: List[EntitySpan], text: str) -> Optional[EntitySpan]:
        """Find unit entity immediately after the number"""
        for entity in remaining_entities[1:3]:  # Check next 2 entities
            # Must be immediately adjacent or very close
            if entity.start - number_entity.end > 3:  # Allow for 1-2 spaces
                break
                
            # Must be a unit type
            if entity.entity_type in ['UNIVERSAL_UNITS', 'MEASUREMENT', 'PERCENT']:
                return entity
                
        return None
    
    def _validate_range_candidates(self, candidates: List[RangeCandidate], text: str) -> List[RangeCandidate]:
        """Validate range candidates using context and span analysis"""
        validated = []
        
        for candidate in candidates:
            # Basic validation checks
            if not self._is_valid_range_values(candidate):
                continue
                
            # PRIORITIZE ranges with units (more likely to be real ranges)
            if candidate.unit_entity:
                candidate.confidence *= 1.3
                
            # Context validation - look for range-indicating context
            context_score = self._score_range_context(candidate, text)
            candidate.confidence *= context_score
            
            # Minimum confidence threshold (higher for ranges without units)
            min_confidence = 0.5 if candidate.unit_entity else 0.8
            if candidate.confidence >= min_confidence:
                validated.append(candidate)
        
        # Sort by confidence and prefer ranges with units
        validated.sort(key=lambda c: (c.unit_entity is not None, c.confidence), reverse=True)
        
        # Remove overlapping candidates (keep highest confidence)
        final_validated = []
        for candidate in validated:
            # Check if this candidate overlaps with any already validated
            overlaps = False
            for existing in final_validated:
                if self._candidates_overlap(candidate, existing):
                    overlaps = True
                    break
            
            if not overlaps:
                final_validated.append(candidate)
        
        return final_validated
    
    def _is_valid_range_values(self, candidate: RangeCandidate) -> bool:
        """Validate that range values make logical sense"""
        try:
            # Extract numeric values
            start_val = float(candidate.start_entity.text.replace(',', ''))
            end_val = float(candidate.end_entity.text.replace(',', ''))
            
            # Range should have different values (not 5-5)
            if start_val == end_val:
                return False
                
            # Start should typically be less than end (with some exceptions)
            # Allow reverse ranges for things like temperature: 120°F to -20°F
            return True
            
        except (ValueError, AttributeError):
            # If we can't parse as numbers, still allow (might be dates, etc.)
            return True
    
    def _score_range_context(self, candidate: RangeCandidate, text: str) -> float:
        """Score range based on surrounding context"""
        # Extract context around the range
        context_start = max(0, candidate.start_entity.start - 50)
        context_end = min(len(text), candidate.full_span[1] + 50)
        context = text[context_start:context_end].lower()
        
        score = 1.0
        
        # Positive indicators
        range_indicators = ['range', 'between', 'from', 'varies', 'span', 'measurement']
        for indicator in range_indicators:
            if indicator in context:
                score *= 1.1
                
        # Negative indicators (things that suggest it's not a range)
        anti_indicators = ['phone', 'number', 'code', 'id', 'serial']
        for indicator in anti_indicators:
            if indicator in context:
                score *= 0.5
                
        return min(score, 1.5)  # Cap the boost
    
    def _convert_ranges_to_entities(self, ranges: List[RangeCandidate], text: str) -> List[EntitySpan]:
        """Convert validated range candidates to EntitySpan objects"""
        range_entities = []
        
        for range_candidate in ranges:
            entity = EntitySpan(
                text=range_candidate.text,
                start=range_candidate.full_span[0],
                end=range_candidate.full_span[1],
                entity_type='RANGE',
                confidence=range_candidate.confidence,
                metadata={
                    'range_type': 'span_linked',
                    'components': [
                        range_candidate.start_entity,
                        range_candidate.end_entity,
                        range_candidate.unit_entity
                    ],
                    'connector': range_candidate.connector
                }
            )
            range_entities.append(entity)
            
        return range_entities
    
    def _filter_overlapping_entities(self, original_entities: List[EntitySpan], range_entities: List[EntitySpan]) -> List[EntitySpan]:
        """Remove individual entities that are now part of ranges"""
        filtered = []
        
        for entity in original_entities:
            # Check if this entity overlaps with any range
            is_overlapping = False
            
            for range_entity in range_entities:
                if self._spans_overlap(entity, range_entity):
                    is_overlapping = True
                    break
                    
            if not is_overlapping:
                filtered.append(entity)
                
        return filtered
    
    def _spans_overlap(self, entity1: EntitySpan, entity2: EntitySpan) -> bool:
        """Check if two entity spans overlap"""
        return not (entity1.end <= entity2.start or entity2.end <= entity1.start)
    
    def _is_numeric_entity(self, entity: EntitySpan) -> bool:
        """Check if entity contains numeric content suitable for ranges"""
        return any(char.isdigit() for char in entity.text)
    
    def _are_types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two entity types can form a range together"""
        if type1 in self.compatible_types:
            return type2 in self.compatible_types[type1]
        return type1 == type2  # Fallback to same-type matching
    
    def _candidates_overlap(self, candidate1: RangeCandidate, candidate2: RangeCandidate) -> bool:
        """Check if two range candidates overlap"""
        span1_start, span1_end = candidate1.full_span
        span2_start, span2_end = candidate2.full_span
        return not (span1_end <= span2_start or span2_end <= span1_start)

def main():
    """Demo of span-based range linking"""
    # Example entities from single-pass detection
    entities = [
        EntitySpan("30", 0, 2, "UNIVERSAL_NUMBERS"),
        EntitySpan("37", 3, 5, "UNIVERSAL_NUMBERS"), 
        EntitySpan("inches", 6, 12, "UNIVERSAL_UNITS"),
        EntitySpan("76", 15, 17, "UNIVERSAL_NUMBERS"),
        EntitySpan("94", 18, 20, "UNIVERSAL_NUMBERS"),
        EntitySpan("cm", 21, 23, "UNIVERSAL_UNITS")
    ]
    
    text = "30-37 inches (76-94 cm)"
    
    linker = SpanBasedRangeLinker()
    result = linker.link_ranges(entities, text)
    
    print("🔗 Span-Based Range Linking Results:")
    for entity in result:
        print(f"  {entity.entity_type}: '{entity.text}' [{entity.start}-{entity.end}]")

if __name__ == "__main__":
    main()