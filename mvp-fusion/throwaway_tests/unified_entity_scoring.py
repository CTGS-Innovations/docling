#!/usr/bin/env python3
"""
Unified Entity Scoring System for ORG and GPE
==============================================
Character-length sensitive scoring with evidence requirements.

SCORING PHILOSOPHY:
- Short words (<5 chars) need STRONG evidence to be valid
- Medium words (5-8 chars) need MODERATE evidence  
- Long words (>8 chars) are more likely legitimate
- Multi-word entities get higher base confidence
- Context validation is crucial for all entities

Example scoring:
- "US" (2 chars): Needs 3+ pieces of evidence  
- "Apple" (5 chars): Needs 2+ pieces of evidence
- "Microsoft" (9 chars): Needs 1+ piece of evidence
- "Apple Inc." (multi-word): Lower evidence threshold
"""

import re
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class EntityType(Enum):
    ORG = "ORG"
    GPE = "GPE" 
    PERSON = "PERSON"
    LOC = "LOC"


@dataclass 
class ScoredEntity:
    """Entity with comprehensive scoring metadata"""
    text: str
    start: int
    end: int
    entity_type: EntityType
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    character_length: int = 0
    word_count: int = 0
    evidence_score: float = 0.0
    meets_threshold: bool = False


class UnifiedEntityScoring:
    """
    Unified scoring system for ORG and GPE entities with character-length sensitivity.
    """
    
    def __init__(self):
        # Character length thresholds and requirements
        self.char_thresholds = {
            'very_short': 3,    # ≤3 chars: US, UK, EU (need VERY strong evidence)
            'short': 5,         # ≤5 chars: Apple, Intel (need strong evidence)
            'medium': 8,        # ≤8 chars: Microsoft (moderate evidence)
            'long': 12          # >8 chars: likely legitimate (minimal evidence)
        }
        
        # Evidence requirements by character length and entity type
        self.evidence_requirements = {
            'ORG': {
                'very_short': 3,    # ORG data is noisy - need 3+ pieces
                'short': 2,         # Need 2+ pieces of evidence  
                'medium': 1,        # Need 1+ piece of evidence
                'long': 0           # No strict evidence requirement
            },
            'GPE': {
                'very_short': 2,    # GPE data is cleaner - only need 2+ pieces
                'short': 1,         # Need 1+ piece of evidence (lower than ORG)
                'medium': 0,        # No evidence requirement (trust the data)
                'long': 0           # No strict evidence requirement
            }
        }
        
        # Base confidence by character length and word count  
        self.base_confidence = {
            'ORG': {
                'very_short_single': 0.05,    # "US" - very low base
                'short_single': 0.15,         # "Apple" - low base
                'medium_single': 0.25,        # "Microsoft" - moderate base
                'long_single': 0.40,          # "International" - higher base
                'multi_word': 0.60            # "Apple Inc." - high base
            },
            'GPE': {
                'very_short_single': 0.20,    # "US" - higher trust in GPE data
                'short_single': 0.30,         # "Texas" - higher base than ORG
                'medium_single': 0.45,        # "Seattle" - higher base
                'long_single': 0.60,          # "California" - much higher base
                'multi_word': 0.70            # "New York" - higher than ORG
            }
        }
        
        # Common blacklisted words (expanded)
        self.blacklist_words = {
            # ORG blacklist
            'here', 'there', 'where', 'when', 'what', 'how', 'why',
            'market', 'industry', 'business', 'service', 'group', 'team',
            'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'in', 'on',
            'social', 'global', 'local', 'way', 'fire', 'complex', 'element', 'state',
            
            # GPE blacklist (different focus)
            'north', 'south', 'east', 'west', 'center', 'central', 'main', 'new', 'old'
        }
        
        # Phrase patterns (multi-word blacklists)
        self.blacklist_phrases = {
            'the market', 'the industry', 'the business', 'the service',
            'the group', 'the team', 'the way', 'the fire', 'the complex',
            'the u', 'the us', 'the uk', 'the eu', 'global market',
            'the system', 'the platform', 'the network', 'the world'
        }
        
        # Entity-specific validation
        self.org_suffixes = {
            'inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 'co', 'company',
            'group', 'holdings', 'enterprises', 'solutions', 'systems', 'technologies'
        }
        
        # GPE-specific indicators  
        self.gpe_indicators = {
            'city', 'county', 'state', 'province', 'country', 'nation', 'territory',
            'republic', 'kingdom', 'federation', 'union', 'district', 'region'
        }
        
        self.gpe_suffixes = {
            'ville', 'town', 'city', 'burg', 'field', 'wood', 'land', 'stan'
        }
        
        # Role/context indicators
        self.org_role_words = {
            'ceo', 'president', 'director', 'manager', 'founder', 'executive',
            'chairman', 'cto', 'cfo', 'head', 'chief', 'partner'
        }
        
        self.gpe_context_words = {
            'located', 'based', 'headquarters', 'capital', 'government', 'mayor',
            'population', 'residents', 'citizens', 'border', 'boundary'
        }
    
    def get_character_category(self, text: str) -> str:
        """Categorize entity by character length"""
        length = len(text)
        if length <= self.char_thresholds['very_short']:
            return 'very_short'
        elif length <= self.char_thresholds['short']:
            return 'short' 
        elif length <= self.char_thresholds['medium']:
            return 'medium'
        else:
            return 'long'
    
    def calculate_base_confidence(self, text: str, entity_type: EntityType) -> Tuple[float, str]:
        """Calculate base confidence based on character length, word count, and entity type"""
        word_count = len(text.split())
        char_category = self.get_character_category(text)
        entity_key = entity_type.value
        
        if word_count > 1:
            base_conf = self.base_confidence[entity_key]['multi_word']
            confidence_type = 'multi_word'
        else:
            base_conf = self.base_confidence[entity_key][f'{char_category}_single']
            confidence_type = f'{char_category}_single'
            
        return base_conf, confidence_type
    
    def analyze_organization_evidence(self, text: str, full_text: str, start: int, end: int,
                                    nearby_entities: List[ScoredEntity]) -> Tuple[float, List[str]]:
        """Analyze ORG-specific evidence"""
        evidence = []
        evidence_score = 0.0
        text_lower = text.lower()
        
        # Capitalization
        if text[0].isupper():
            evidence_score += 0.15
            evidence.append('capitalized')
        
        # Organization suffixes
        for suffix in self.org_suffixes:
            if text_lower.endswith(suffix):
                evidence_score += 0.25
                evidence.append(f'org_suffix_{suffix}')
                break
        
        # Context window analysis
        window = 50
        context_start = max(0, start - window)
        context_end = min(len(full_text), end + window)
        context = full_text[context_start:context_end].lower()
        
        # Role/title context
        for role in self.org_role_words:
            if role in context:
                evidence_score += 0.20
                evidence.append(f'role_context_{role}')
                break
        
        # Nearby entity analysis
        for entity in nearby_entities:
            distance = abs((start + end) // 2 - (entity.start + entity.end) // 2)
            if distance <= 100:  # Within 100 characters
                if entity.entity_type == EntityType.PERSON:
                    evidence_score += 0.15
                    evidence.append(f'nearby_person')
                elif entity.entity_type == EntityType.GPE:
                    evidence_score += 0.10
                    evidence.append(f'nearby_location')
        
        return evidence_score, evidence
    
    def analyze_gpe_evidence(self, text: str, full_text: str, start: int, end: int,
                           nearby_entities: List[ScoredEntity]) -> Tuple[float, List[str]]:
        """Analyze GPE-specific evidence"""
        evidence = []
        evidence_score = 0.0
        text_lower = text.lower()
        
        # Capitalization (very important for places)
        if text[0].isupper():
            evidence_score += 0.20  # Higher weight than ORG
            evidence.append('capitalized')
        
        # GPE suffixes
        for suffix in self.gpe_suffixes:
            if text_lower.endswith(suffix):
                evidence_score += 0.25
                evidence.append(f'gpe_suffix_{suffix}')
                break
        
        # Context analysis
        window = 50
        context_start = max(0, start - window)
        context_end = min(len(full_text), end + window)
        context = full_text[context_start:context_end].lower()
        
        # Geographic context words
        for word in self.gpe_context_words:
            if word in context:
                evidence_score += 0.15
                evidence.append(f'geo_context_{word}')
                break
        
        # Geographic indicators
        for indicator in self.gpe_indicators:
            if indicator in context:
                evidence_score += 0.10
                evidence.append(f'geo_indicator_{indicator}')
                break
        
        # Nearby entities
        for entity in nearby_entities:
            distance = abs((start + end) // 2 - (entity.start + entity.end) // 2)
            if distance <= 100:
                if entity.entity_type == EntityType.ORG:
                    evidence_score += 0.10
                    evidence.append(f'nearby_organization')
                elif entity.entity_type == EntityType.PERSON:
                    evidence_score += 0.05
                    evidence.append(f'nearby_person')
        
        return evidence_score, evidence
    
    def score_entity(self, text: str, start: int, end: int, entity_type: EntityType,
                   full_text: str, nearby_entities: List[ScoredEntity] = None) -> ScoredEntity:
        """
        Comprehensive entity scoring with character-length sensitivity.
        """
        if nearby_entities is None:
            nearby_entities = []
            
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Create base entity
        entity = ScoredEntity(
            text=text_clean,
            start=start,
            end=end,
            entity_type=entity_type,
            character_length=len(text_clean),
            word_count=len(text_clean.split())
        )
        
        # Blacklist check (words and phrases)
        if text_lower in self.blacklist_words or text_lower in self.blacklist_phrases:
            entity.confidence = 0.0
            entity.evidence = ['blacklisted']
            entity.meets_threshold = False
            return entity
        
        # Character length category
        char_category = self.get_character_category(text_clean)
        
        # Base confidence
        base_confidence, confidence_type = self.calculate_base_confidence(text_clean, entity_type)
        
        # Entity-specific evidence analysis
        if entity_type == EntityType.ORG:
            evidence_score, evidence = self.analyze_organization_evidence(
                text_clean, full_text, start, end, nearby_entities
            )
        elif entity_type == EntityType.GPE:
            evidence_score, evidence = self.analyze_gpe_evidence(
                text_clean, full_text, start, end, nearby_entities
            )
        else:
            evidence_score, evidence = 0.0, []
        
        # Calculate final confidence
        final_confidence = min(base_confidence + evidence_score, 0.95)
        
        # Evidence threshold check (entity-type specific)
        entity_key = entity_type.value
        required_evidence = self.evidence_requirements[entity_key].get(char_category, 0)
        evidence_count = len(evidence)
        meets_threshold = evidence_count >= required_evidence
        
        # Apply threshold penalty for insufficient evidence
        if not meets_threshold and char_category in ['very_short', 'short']:
            final_confidence *= 0.3  # Heavy penalty for short words with insufficient evidence
        
        entity.confidence = final_confidence
        entity.evidence = evidence + [f'base_{confidence_type}']
        entity.evidence_score = evidence_score
        entity.meets_threshold = meets_threshold
        
        return entity
    
    def filter_by_threshold(self, entities: List[ScoredEntity], min_confidence: float = 0.4) -> List[ScoredEntity]:
        """Filter entities by confidence threshold"""
        return [e for e in entities if e.confidence >= min_confidence]


# EXAMPLE USAGE WITH CHARACTER LENGTH SENSITIVITY
if __name__ == "__main__":
    scorer = UnifiedEntityScoring()
    
    test_text = """
    The US Department of Justice and EU regulations affect Apple Inc. and Google.
    Microsoft Corporation is based in Seattle, Washington. Tesla operates in California.
    Here we see the market growth in Asia. The complex industry standards apply.
    """
    
    # Test entities with various character lengths
    test_entities = [
        # Very short (≤3 chars) - need 3+ evidence pieces
        ("US", 4, 6, EntityType.GPE),
        ("EU", 31, 33, EntityType.GPE),
        
        # Short (≤5 chars) - need 2+ evidence pieces  
        ("Apple", 50, 55, EntityType.ORG),
        ("Tesla", 140, 145, EntityType.ORG),
        ("Asia", 220, 224, EntityType.GPE),
        
        # Medium (≤8 chars) - need 1+ evidence piece
        ("Google", 66, 72, EntityType.ORG),
        ("Seattle", 105, 112, EntityType.GPE),
        
        # Long (>8 chars) - minimal evidence needed
        ("Microsoft Corporation", 74, 96, EntityType.ORG),
        ("Washington", 114, 124, EntityType.GPE),
        ("California", 160, 170, EntityType.GPE),
        
        # Problematic cases
        ("the market", 185, 195, EntityType.ORG),
        ("industry", 215, 223, EntityType.ORG),
        ("Here", 175, 179, EntityType.ORG)
    ]
    
    print("UNIFIED ENTITY SCORING RESULTS:")
    print("=" * 70)
    print(f"{'Entity':<20} {'Type':<5} {'Chars':<6} {'Confidence':<12} {'Threshold':<10} {'Evidence'}")
    print("-" * 70)
    
    scored_entities = []
    for text, start, end, entity_type in test_entities:
        scored = scorer.score_entity(text, start, end, entity_type, test_text)
        scored_entities.append(scored)
        
        threshold_status = "✓" if scored.meets_threshold else "✗"
        evidence_summary = f"{len(scored.evidence)-1} pieces"  # -1 for base confidence
        
        print(f"{scored.text:<20} {scored.entity_type.value:<5} {scored.character_length:<6} "
              f"{scored.confidence:<12.3f} {threshold_status:<10} {evidence_summary}")
    
    print(f"\nCHARACTER LENGTH ANALYSIS:")
    print("-" * 40)
    
    by_length = {}
    for entity in scored_entities:
        cat = scorer.get_character_category(entity.text)
        if cat not in by_length:
            by_length[cat] = []
        by_length[cat].append(entity)
    
    for category, entities in by_length.items():
        avg_conf = sum(e.confidence for e in entities) / len(entities)
        threshold_met = sum(1 for e in entities if e.meets_threshold)
        print(f"{category.upper():<12}: {len(entities)} entities, avg confidence: {avg_conf:.3f}, "
              f"threshold met: {threshold_met}/{len(entities)}")
    
    print(f"\nHIGH CONFIDENCE ENTITIES (≥0.4):")
    high_conf = scorer.filter_by_threshold(scored_entities, 0.4)
    for entity in high_conf:
        print(f"✓ {entity.text} ({entity.entity_type.value}): {entity.confidence:.3f}")