"""
SPO Assembler - Zero-Cost Fact Assembly from Cached Components

This module implements the high-performance SPO triplet assembly logic that operates
on pre-extracted components from the SPOComponentCache. It provides intelligent
relationship detection, proximity-based assembly, and confidence scoring.

Performance Characteristics:
- Assembly Time: O(m) where m = number of components
- No Text Processing: Works entirely from cached components
- Proximity-Based: Uses sentence boundaries and positional relationships
- Confidence Scoring: Validates relationships with semantic confidence
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
import logging
from collections import defaultdict
import re

try:
    from .spo_component_cache import (
        SPOComponentCache, SPOEntity, SPOPredicate, SPOModifier, 
        SPOTriplet, PredicateCategory, ComponentType
    )
except ImportError:
    from spo_component_cache import (
        SPOComponentCache, SPOEntity, SPOPredicate, SPOModifier, 
        SPOTriplet, PredicateCategory, ComponentType
    )

@dataclass
class AssemblyRule:
    """Rules for SPO triplet assembly based on predicate categories"""
    category: PredicateCategory
    max_distance: int           # Maximum character distance between S-P-O
    subject_types: List[str]    # Allowed subject entity types
    object_types: List[str]     # Allowed object entity types
    requires_modifiers: bool = False
    confidence_weight: float = 1.0

class SPOAssembler:
    """
    High-performance SPO triplet assembler for zero-cost fact extraction
    
    Operates entirely on pre-extracted components from SPOComponentCache.
    Uses proximity, sentence boundaries, and semantic rules for intelligent assembly.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Assembly rules by predicate category
        self.assembly_rules = self._initialize_assembly_rules()
        
        # Performance tracking
        self.stats = {
            'triplets_assembled': 0,
            'components_processed': 0,
            'assembly_time_ms': 0,
            'confidence_distribution': defaultdict(int)
        }
    
    def _initialize_assembly_rules(self) -> Dict[PredicateCategory, AssemblyRule]:
        """Initialize assembly rules for different predicate categories"""
        return {
            PredicateCategory.STATE: AssemblyRule(
                category=PredicateCategory.STATE,
                max_distance=100,
                subject_types=['PERSON', 'ORG', 'GPE'],
                object_types=['PERSON', 'ORG', 'GPE', 'MISC'],
                confidence_weight=0.9
            ),
            
            PredicateCategory.OWNERSHIP: AssemblyRule(
                category=PredicateCategory.OWNERSHIP,
                max_distance=150,
                subject_types=['PERSON', 'ORG'],
                object_types=['ORG', 'MISC', 'MONEY'],
                confidence_weight=0.95
            ),
            
            PredicateCategory.LOCATION: AssemblyRule(
                category=PredicateCategory.LOCATION,
                max_distance=200,
                subject_types=['PERSON', 'ORG'],
                object_types=['GPE', 'LOC'],
                confidence_weight=0.9
            ),
            
            PredicateCategory.RELATIONSHIP: AssemblyRule(
                category=PredicateCategory.RELATIONSHIP,
                max_distance=100,
                subject_types=['PERSON'],
                object_types=['PERSON', 'ORG'],
                confidence_weight=0.85
            ),
            
            PredicateCategory.BUSINESS: AssemblyRule(
                category=PredicateCategory.BUSINESS,
                max_distance=150,
                subject_types=['PERSON', 'ORG'],
                object_types=['ORG', 'MONEY'],
                confidence_weight=0.9
            ),
            
            PredicateCategory.LEGAL_REGULATORY: AssemblyRule(
                category=PredicateCategory.LEGAL_REGULATORY,
                max_distance=200,
                subject_types=['PERSON', 'ORG'],
                object_types=['ORG', 'MISC'],
                requires_modifiers=True,
                confidence_weight=0.95
            ),
            
            PredicateCategory.OBLIGATIONS: AssemblyRule(
                category=PredicateCategory.OBLIGATIONS,
                max_distance=150,
                subject_types=['PERSON', 'ORG'],
                object_types=['MISC'],
                requires_modifiers=True,
                confidence_weight=0.9
            ),
            
            PredicateCategory.QUANTITATIVE: AssemblyRule(
                category=PredicateCategory.QUANTITATIVE,
                max_distance=100,
                subject_types=['PERSON', 'ORG'],
                object_types=['MONEY', 'PERCENT', 'MISC'],
                confidence_weight=0.85
            ),
            
            PredicateCategory.CAUSALITY: AssemblyRule(
                category=PredicateCategory.CAUSALITY,
                max_distance=200,
                subject_types=['PERSON', 'ORG', 'MISC'],
                object_types=['PERSON', 'ORG', 'MISC'],
                confidence_weight=0.8
            )
        }
    
    def assemble_spo_facts(self, cache: SPOComponentCache) -> List[SPOTriplet]:
        """
        Main entry point: Assemble SPO triplets from cached components
        
        Args:
            cache: SPOComponentCache with pre-extracted components
            
        Returns:
            List of assembled SPO triplets with confidence scores
        """
        import time
        start_time = time.time()
        
        self.logger.info("Starting SPO triplet assembly from cached components")
        
        # Reset stats
        self.stats['triplets_assembled'] = 0
        self.stats['components_processed'] = 0
        
        # Get component counts
        component_stats = cache.get_stats()
        total_components = sum(component_stats['component_counts'].values())
        self.stats['components_processed'] = total_components
        
        self.logger.debug(f"Processing {total_components} cached components")
        
        # Assembly strategy: Process by sentence for optimal relationships
        all_triplets = []
        
        for sentence_start, sentence_end in cache.sentence_boundaries:
            sentence_triplets = self._assemble_sentence_triplets(cache, sentence_start, sentence_end)
            all_triplets.extend(sentence_triplets)
        
        # Post-processing: Deduplicate and score
        final_triplets = self._post_process_triplets(all_triplets)
        
        # Update stats
        assembly_time = (time.time() - start_time) * 1000
        self.stats['assembly_time_ms'] = assembly_time
        self.stats['triplets_assembled'] = len(final_triplets)
        
        self.logger.info(f"Assembled {len(final_triplets)} SPO triplets in {assembly_time:.1f}ms")
        
        return final_triplets
    
    def _assemble_sentence_triplets(self, cache: SPOComponentCache, start: int, end: int) -> List[SPOTriplet]:
        """Assemble triplets within a single sentence"""
        # Get all components in this sentence
        components = cache.get_components_in_range(start, end)
        
        subjects = components['subjects']
        predicates = components['predicates']
        objects = components['objects']
        modifiers = components['modifiers']
        
        if not subjects or not predicates or not objects:
            return []  # Need at least S-P-O for triplet
        
        triplets = []
        
        # Try all combinations of S-P-O within sentence
        for predicate in predicates:
            rule = self.assembly_rules.get(predicate.category)
            if not rule:
                continue
            
            # Find compatible subjects and objects
            compatible_subjects = self._find_compatible_entities(
                subjects, predicate, rule.subject_types, rule.max_distance, 'subject'
            )
            
            compatible_objects = self._find_compatible_entities(
                objects, predicate, rule.object_types, rule.max_distance, 'object'
            )
            
            # Assemble triplets from compatible combinations
            for subject in compatible_subjects:
                for obj in compatible_objects:
                    # Validate S-P-O ordering and distance
                    if self._validate_spo_ordering(subject, predicate, obj):
                        # Find relevant modifiers
                        relevant_modifiers = self._find_relevant_modifiers(
                            modifiers, subject, predicate, obj
                        )
                        
                        # Check modifier requirements
                        if rule.requires_modifiers and not relevant_modifiers:
                            continue
                        
                        # Calculate confidence
                        confidence = self._calculate_triplet_confidence(
                            subject, predicate, obj, relevant_modifiers, rule
                        )
                        
                        # Create triplet
                        triplet = SPOTriplet(
                            subject=subject,
                            predicate=predicate,
                            object=obj,
                            modifiers=relevant_modifiers,
                            confidence=confidence,
                            sentence_id=len(cache.sentence_boundaries),  # Sentence index
                            extraction_method="AC+FLPC Hybrid Assembly"
                        )
                        
                        triplets.append(triplet)
        
        return triplets
    
    def _find_compatible_entities(self, entities: List[SPOEntity], predicate: SPOPredicate, 
                                allowed_types: List[str], max_distance: int, role: str) -> List[SPOEntity]:
        """Find entities compatible with predicate based on type and distance"""
        compatible = []
        
        for entity in entities:
            # Check entity type compatibility
            if entity.entity_type not in allowed_types:
                continue
            
            # Check distance from predicate
            distance = abs(entity.start_pos - predicate.start_pos)
            if distance > max_distance:
                continue
            
            compatible.append(entity)
        
        return compatible
    
    def _validate_spo_ordering(self, subject: SPOEntity, predicate: SPOPredicate, obj: SPOEntity) -> bool:
        """Validate that S-P-O components appear in logical order"""
        positions = [
            (subject.start_pos, 'S'),
            (predicate.start_pos, 'P'),
            (obj.start_pos, 'O')
        ]
        
        # Sort by position
        positions.sort(key=lambda x: x[0])
        
        # Check for reasonable orderings
        valid_patterns = [
            ['S', 'P', 'O'],  # Standard: "John owns Microsoft"
            ['S', 'O', 'P'],  # Inverse: "John, Microsoft owns" (rare but valid)
            ['P', 'S', 'O'],  # Predicate first: "Owns John Microsoft" (rare)
        ]
        
        ordering = [pos[1] for pos in positions]
        return ordering in valid_patterns
    
    def _find_relevant_modifiers(self, modifiers: List[SPOModifier], subject: SPOEntity, 
                               predicate: SPOPredicate, obj: SPOEntity) -> List[SPOModifier]:
        """Find modifiers relevant to the S-P-O triplet"""
        relevant = []
        
        # Define proximity to any component in the triplet
        triplet_start = min(subject.start_pos, predicate.start_pos, obj.start_pos)
        triplet_end = max(subject.end_pos, predicate.end_pos, obj.end_pos)
        
        for modifier in modifiers:
            # Check if modifier is close to any component
            modifier_distance_to_triplet = min(
                abs(modifier.start_pos - triplet_start),
                abs(modifier.start_pos - triplet_end)
            )
            
            # Include modifiers within reasonable distance
            if modifier_distance_to_triplet <= 100:  # 100 characters
                relevant.append(modifier)
        
        return relevant
    
    def _calculate_triplet_confidence(self, subject: SPOEntity, predicate: SPOPredicate, 
                                    obj: SPOEntity, modifiers: List[SPOModifier], 
                                    rule: AssemblyRule) -> float:
        """Calculate confidence score for assembled triplet"""
        base_confidence = rule.confidence_weight
        
        # Factors that increase confidence
        confidence_boosts = 0.0
        
        # Distance factor: Closer components = higher confidence
        max_distance = max(
            abs(subject.start_pos - predicate.start_pos),
            abs(predicate.start_pos - obj.start_pos)
        )
        
        if max_distance <= 50:
            confidence_boosts += 0.1
        elif max_distance <= 100:
            confidence_boosts += 0.05
        
        # Entity confidence factor
        entity_confidence = (subject.confidence + obj.confidence) / 2
        confidence_boosts += (entity_confidence - 0.8) * 0.1  # Boost for high-confidence entities
        
        # Predicate confidence
        confidence_boosts += (predicate.confidence - 0.8) * 0.1
        
        # Modifier support
        if modifiers:
            modifier_boost = min(len(modifiers) * 0.02, 0.1)  # Max 0.1 boost from modifiers
            confidence_boosts += modifier_boost
        
        # Ordering bonus: Standard S-P-O order gets bonus
        if subject.start_pos < predicate.start_pos < obj.start_pos:
            confidence_boosts += 0.05
        
        final_confidence = min(base_confidence + confidence_boosts, 1.0)
        
        # Track confidence distribution for analytics
        confidence_bucket = int(final_confidence * 10) / 10
        self.stats['confidence_distribution'][confidence_bucket] += 1
        
        return final_confidence
    
    def _post_process_triplets(self, triplets: List[SPOTriplet]) -> List[SPOTriplet]:
        """Post-process triplets: deduplicate, filter, and rank"""
        if not triplets:
            return []
        
        # Deduplicate based on component positions
        unique_triplets = {}
        
        for triplet in triplets:
            # Create unique key based on component positions
            key = (
                triplet.subject.start_pos,
                triplet.predicate.start_pos,
                triplet.object.start_pos
            )
            
            # Keep highest confidence triplet for each position combination
            if key not in unique_triplets or triplet.confidence > unique_triplets[key].confidence:
                unique_triplets[key] = triplet
        
        # Convert back to list and sort by confidence
        final_triplets = list(unique_triplets.values())
        final_triplets.sort(key=lambda t: t.confidence, reverse=True)
        
        # Filter low-confidence triplets
        min_confidence = 0.5
        filtered_triplets = [t for t in final_triplets if t.confidence >= min_confidence]
        
        self.logger.debug(f"Post-processing: {len(triplets)} -> {len(final_triplets)} unique -> {len(filtered_triplets)} filtered")
        
        return filtered_triplets
    
    def get_assembly_stats(self) -> Dict:
        """Get assembly performance statistics"""
        return dict(self.stats)
    
    def export_triplets_for_semantic_analysis(self, triplets: List[SPOTriplet]) -> Dict:
        """
        Export triplets in format suitable for semantic analysis stage
        
        Returns structured facts compatible with current semantic fact format.
        """
        spo_facts = []
        
        for triplet in triplets:
            fact = {
                'fact_type': 'SPOFact',
                'confidence': triplet.confidence,
                'subject': {
                    'text': triplet.subject.text,
                    'type': triplet.subject.entity_type,
                    'span': {
                        'start': triplet.subject.start_pos,
                        'end': triplet.subject.end_pos
                    }
                },
                'predicate': {
                    'text': triplet.predicate.text,
                    'category': triplet.predicate.category.value,
                    'span': {
                        'start': triplet.predicate.start_pos,
                        'end': triplet.predicate.end_pos
                    }
                },
                'object': {
                    'text': triplet.object.text,
                    'type': triplet.object.entity_type,
                    'span': {
                        'start': triplet.object.start_pos,
                        'end': triplet.object.end_pos
                    }
                },
                'modifiers': [
                    {
                        'text': mod.text,
                        'type': mod.modifier_type,
                        'span': {
                            'start': mod.start_pos,
                            'end': mod.end_pos
                        }
                    }
                    for mod in triplet.modifiers
                ],
                'extraction_layer': 'spo_assembly',
                'sentence_id': triplet.sentence_id
            }
            
            spo_facts.append(fact)
        
        return {
            'spo_facts': spo_facts,
            'extraction_summary': {
                'total_facts': len(spo_facts),
                'extraction_method': 'AC+FLPC Hybrid Assembly',
                'performance_model': 'O(m) Zero-Cost Assembly',
                'average_confidence': sum(t.confidence for t in triplets) / len(triplets) if triplets else 0,
                'assembly_stats': self.get_assembly_stats()
            }
        }

# Testing function
if __name__ == "__main__":
    # Test SPO assembler with mock data
    from spo_component_cache import SPOComponentCache
    
    print("SPO Assembler Test")
    print("=" * 50)
    
    # Create mock cache with sample components
    cache = SPOComponentCache()
    
    # Add sample sentence boundaries
    cache.set_sentence_boundaries([(0, 100), (101, 200)])
    
    # Add sample entities
    subject = SPOEntity("Microsoft", "ORG", 0, 9, 0.9)
    predicate = SPOPredicate("acquired", PredicateCategory.BUSINESS, 10, 18, 0.9)
    obj = SPOEntity("LinkedIn", "ORG", 19, 27, 0.9)
    
    cache.add_subject(subject)
    cache.add_predicate(predicate)
    cache.add_object(obj)
    
    # Test assembler
    assembler = SPOAssembler()
    triplets = assembler.assemble_spo_facts(cache)
    
    print(f"Assembled {len(triplets)} triplets")
    
    for i, triplet in enumerate(triplets):
        print(f"\nTriplet {i+1}:")
        print(f"  Subject: {triplet.subject.text} ({triplet.subject.entity_type})")
        print(f"  Predicate: {triplet.predicate.text} ({triplet.predicate.category.value})")
        print(f"  Object: {triplet.object.text} ({triplet.object.entity_type})")
        print(f"  Confidence: {triplet.confidence:.2f}")
    
    # Test export format
    exported = assembler.export_triplets_for_semantic_analysis(triplets)
    print(f"\nExported {len(exported['spo_facts'])} facts for semantic analysis")
    print(f"Average confidence: {exported['extraction_summary']['average_confidence']:.2f}")