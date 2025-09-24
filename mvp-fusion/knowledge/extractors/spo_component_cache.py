"""
SPO Component Cache - In-Memory Storage for SPO Fact Assembly

This module implements the high-performance in-memory cache for Subject-Predicate-Object
components extracted during the entity extraction phase. The cache enables zero-cost
fact assembly during semantic analysis.

Performance Characteristics:
- Memory: 100-400KB per document (temporary)
- Lookup: O(1) for position-based access
- Assembly: O(m) where m = number of components
- Cleanup: Automatic after semantic analysis
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set, Any
from collections import defaultdict
import sys
from enum import Enum

class ComponentType(Enum):
    """Types of SPO components for efficient categorization"""
    SUBJECT = "subject"
    PREDICATE = "predicate" 
    OBJECT = "object"
    MODIFIER = "modifier"

class PredicateCategory(Enum):
    """Predicate categories for semantic classification"""
    STATE = "state"                          # is, was, became
    OWNERSHIP = "ownership"                  # owns, controls, manages
    LOCATION = "location"                    # located in, based in
    RELATIONSHIP = "relationship"            # married to, child of
    BUSINESS = "business"                    # founded, acquired
    LEGAL_REGULATORY = "legal_regulatory"    # fined, approved
    OBLIGATIONS = "obligations_compliance"   # must, shall, required
    QUANTITATIVE = "quantitative_performance" # reported, achieved
    CAUSALITY = "causality_conditions"       # caused, led to

@dataclass
class SPOEntity:
    """Represents an entity that can serve as Subject or Object"""
    text: str
    entity_type: str        # PERSON, ORG, GPE, etc.
    start_pos: int
    end_pos: int
    confidence: float
    canonical_id: Optional[str] = None
    entity_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass  
class SPOPredicate:
    """Represents a relationship/verb between entities"""
    text: str
    category: PredicateCategory
    start_pos: int
    end_pos: int
    confidence: float
    tense: Optional[str] = None     # past, present, future
    polarity: str = "positive"      # positive, negative
    modality: Optional[str] = None  # must, can, should, etc.

@dataclass
class SPOModifier:
    """Represents qualifiers that modify relationships"""
    text: str
    modifier_type: str      # temporal, spatial, quantitative, conditional
    start_pos: int
    end_pos: int
    confidence: float
    value: Optional[str] = None     # extracted value for structured modifiers
    unit: Optional[str] = None      # units for quantitative modifiers

@dataclass
class SPOTriplet:
    """Assembled Subject-Predicate-Object relationship with modifiers"""
    subject: SPOEntity
    predicate: SPOPredicate
    object: SPOEntity
    modifiers: List[SPOModifier] = field(default_factory=list)
    confidence: float = 0.0
    sentence_id: Optional[int] = None
    extraction_method: str = "AC+FLPC Hybrid"

class SPOComponentCache:
    """
    High-performance in-memory cache for SPO components
    
    Optimized for fast lookup and assembly with minimal memory overhead.
    Components are indexed by position for efficient proximity-based assembly.
    """
    
    def __init__(self):
        # Core component storage (position-indexed)
        self.subjects: Dict[int, SPOEntity] = {}
        self.predicates: Dict[int, SPOPredicate] = {}
        self.objects: Dict[int, SPOEntity] = {}
        self.modifiers: Dict[int, SPOModifier] = {}
        
        # Sentence boundaries for scoping relationships
        self.sentence_boundaries: List[Tuple[int, int]] = []
        
        # Fast lookup indexes
        self.subject_index: Dict[str, List[int]] = defaultdict(list)
        self.predicate_index: Dict[str, List[int]] = defaultdict(list)
        self.object_index: Dict[str, List[int]] = defaultdict(list)
        self.modifier_index: Dict[str, List[int]] = defaultdict(list)
        
        # Proximity mapping for efficient relationship detection
        self.proximity_map: Dict[int, List[int]] = defaultdict(list)
        
        # Category indexes for targeted assembly
        self.predicates_by_category: Dict[PredicateCategory, List[int]] = defaultdict(list)
        self.modifiers_by_type: Dict[str, List[int]] = defaultdict(list)
        
        # Performance tracking
        self._memory_usage = 0
        self._component_count = 0
    
    def add_subject(self, entity: SPOEntity) -> None:
        """Add a subject entity to the cache with indexing"""
        pos = entity.start_pos
        self.subjects[pos] = entity
        self.subject_index[entity.text.lower()].append(pos)
        self._update_proximity_map(pos)
        self._component_count += 1
    
    def add_predicate(self, predicate: SPOPredicate) -> None:
        """Add a predicate to the cache with category indexing"""
        pos = predicate.start_pos
        self.predicates[pos] = predicate
        self.predicate_index[predicate.text.lower()].append(pos)
        self.predicates_by_category[predicate.category].append(pos)
        self._update_proximity_map(pos)
        self._component_count += 1
    
    def add_object(self, entity: SPOEntity) -> None:
        """Add an object entity to the cache with indexing"""
        pos = entity.start_pos
        self.objects[pos] = entity
        self.object_index[entity.text.lower()].append(pos)
        self._update_proximity_map(pos)
        self._component_count += 1
    
    def add_modifier(self, modifier: SPOModifier) -> None:
        """Add a modifier to the cache with type indexing"""
        pos = modifier.start_pos
        self.modifiers[pos] = modifier
        self.modifier_index[modifier.text.lower()].append(pos)
        self.modifiers_by_type[modifier.modifier_type].append(pos)
        self._update_proximity_map(pos)
        self._component_count += 1
    
    def set_sentence_boundaries(self, boundaries: List[Tuple[int, int]]) -> None:
        """Set sentence boundaries for relationship scoping"""
        self.sentence_boundaries = boundaries
    
    def get_components_in_range(self, start: int, end: int) -> Dict[str, List]:
        """Get all components within a character range (e.g., sentence)"""
        components = {
            'subjects': [],
            'predicates': [],
            'objects': [],
            'modifiers': []
        }
        
        for pos, subject in self.subjects.items():
            if start <= pos <= end:
                components['subjects'].append(subject)
        
        for pos, predicate in self.predicates.items():
            if start <= pos <= end:
                components['predicates'].append(predicate)
        
        for pos, obj in self.objects.items():
            if start <= pos <= end:
                components['objects'].append(obj)
        
        for pos, modifier in self.modifiers.items():
            if start <= pos <= end:
                components['modifiers'].append(modifier)
        
        return components
    
    def get_nearby_components(self, position: int, window_size: int = 100) -> Dict[str, List]:
        """Get components within a window around a position"""
        start = max(0, position - window_size // 2)
        end = position + window_size // 2
        return self.get_components_in_range(start, end)
    
    def get_predicates_by_category(self, category: PredicateCategory) -> List[SPOPredicate]:
        """Get all predicates of a specific category"""
        positions = self.predicates_by_category.get(category, [])
        return [self.predicates[pos] for pos in positions]
    
    def get_modifiers_by_type(self, modifier_type: str) -> List[SPOModifier]:
        """Get all modifiers of a specific type"""
        positions = self.modifiers_by_type.get(modifier_type, [])
        return [self.modifiers[pos] for pos in positions]
    
    def find_entity_by_text(self, text: str, component_type: ComponentType) -> List[SPOEntity]:
        """Find entities by text content"""
        text_lower = text.lower()
        
        if component_type == ComponentType.SUBJECT:
            positions = self.subject_index.get(text_lower, [])
            return [self.subjects[pos] for pos in positions]
        elif component_type == ComponentType.OBJECT:
            positions = self.object_index.get(text_lower, [])
            return [self.objects[pos] for pos in positions]
        else:
            # Return both subjects and objects
            results = []
            positions = self.subject_index.get(text_lower, [])
            results.extend([self.subjects[pos] for pos in positions])
            positions = self.object_index.get(text_lower, [])
            results.extend([self.objects[pos] for pos in positions])
            return results
    
    def get_sentence_for_position(self, position: int) -> Optional[Tuple[int, int]]:
        """Get sentence boundaries containing a position"""
        for start, end in self.sentence_boundaries:
            if start <= position <= end:
                return (start, end)
        return None
    
    def _update_proximity_map(self, position: int, radius: int = 50) -> None:
        """Update proximity mapping for efficient relationship detection"""
        # Find nearby positions within radius
        nearby_positions = []
        
        # Check all component positions within radius
        all_positions = set()
        all_positions.update(self.subjects.keys())
        all_positions.update(self.predicates.keys())
        all_positions.update(self.objects.keys())
        all_positions.update(self.modifiers.keys())
        
        for pos in all_positions:
            if abs(pos - position) <= radius and pos != position:
                nearby_positions.append(pos)
        
        self.proximity_map[position] = nearby_positions
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Estimate memory usage of the cache"""
        subjects_size = sum(sys.getsizeof(entity) for entity in self.subjects.values())
        predicates_size = sum(sys.getsizeof(pred) for pred in self.predicates.values())
        objects_size = sum(sys.getsizeof(entity) for entity in self.objects.values())
        modifiers_size = sum(sys.getsizeof(mod) for mod in self.modifiers.values())
        
        # Index overhead
        index_size = (
            sys.getsizeof(self.subject_index) +
            sys.getsizeof(self.predicate_index) +
            sys.getsizeof(self.object_index) +
            sys.getsizeof(self.modifier_index) +
            sys.getsizeof(self.proximity_map) +
            sys.getsizeof(self.predicates_by_category) +
            sys.getsizeof(self.modifiers_by_type)
        )
        
        total_size = subjects_size + predicates_size + objects_size + modifiers_size + index_size
        
        return {
            'total_bytes': total_size,
            'total_kb': total_size / 1024,
            'components': {
                'subjects': len(self.subjects),
                'predicates': len(self.predicates),
                'objects': len(self.objects),
                'modifiers': len(self.modifiers)
            },
            'breakdown': {
                'subjects_kb': subjects_size / 1024,
                'predicates_kb': predicates_size / 1024,
                'objects_kb': objects_size / 1024,
                'modifiers_kb': modifiers_size / 1024,
                'indexes_kb': index_size / 1024
            }
        }
    
    def clear(self) -> None:
        """Clear all cached components and indexes"""
        self.subjects.clear()
        self.predicates.clear()
        self.objects.clear()
        self.modifiers.clear()
        self.sentence_boundaries.clear()
        
        self.subject_index.clear()
        self.predicate_index.clear()
        self.object_index.clear()
        self.modifier_index.clear()
        self.proximity_map.clear()
        
        self.predicates_by_category.clear()
        self.modifiers_by_type.clear()
        
        self._memory_usage = 0
        self._component_count = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring and debugging"""
        memory_info = self.get_memory_usage()
        
        return {
            'component_counts': memory_info['components'],
            'total_memory_kb': memory_info['total_kb'],
            'sentence_count': len(self.sentence_boundaries),
            'proximity_mappings': len(self.proximity_map),
            'predicate_categories': {cat.value: len(positions) 
                                   for cat, positions in self.predicates_by_category.items()},
            'modifier_types': dict(self.modifiers_by_type),
            'performance': {
                'total_components': self._component_count,
                'avg_components_per_sentence': (
                    self._component_count / len(self.sentence_boundaries) 
                    if self.sentence_boundaries else 0
                )
            }
        }