#!/usr/bin/env python3
"""
Premium Entity Scoring System with Specialized Lists
====================================================
Enhanced scoring that includes:
1. Investor companies (1,324 entities) - high-value, immediate recognition
2. Unicorn companies (1,186 entities) - high-value, immediate recognition  
3. Sub-categorization metadata for source identification
4. Word boundary validation (whole words only)

PREMIUM ENTITY PHILOSOPHY:
- Investors & Unicorns get IMMEDIATE high confidence (0.8+)
- Must be whole words (not partial matches)
- Metadata tracks source: "investor_list" or "unicorn_list"
- Bypasses character length penalties
- Similar to GPE subcategorization approach
"""

import re
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class EntityType(Enum):
    ORG = "ORG"
    GPE = "GPE" 
    PERSON = "PERSON"
    LOC = "LOC"


@dataclass 
class PremiumEntity:
    """Entity with premium scoring and metadata"""
    text: str
    start: int
    end: int
    entity_type: EntityType
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    character_length: int = 0
    word_count: int = 0
    is_premium: bool = False
    premium_source: str = None  # "investor", "unicorn", "standard"
    subcategory: str = None


class PremiumEntityScoring:
    """
    Premium entity scoring with specialized high-value lists.
    """
    
    def __init__(self, corpus_base_path: str = "knowledge/corpus/foundation_data/org"):
        self.corpus_path = Path(corpus_base_path)
        
        # Load premium entity lists from org directory
        self.investors = self._load_entity_list("investors_2025_09_18.txt")
        self.unicorns = self._load_entity_list("unicorn_companies_2025_09_18.txt")
        
        print(f"Loaded {len(self.investors)} investors and {len(self.unicorns)} unicorns")
        
        # Premium entity confidence scores
        self.premium_confidence = {
            'investor': 0.85,    # High confidence for investors
            'unicorn': 0.90,     # Very high confidence for unicorns
        }
        
        # Standard scoring (from previous system)
        self.char_thresholds = {
            'very_short': 3,
            'short': 5,
            'medium': 8,
            'long': 12
        }
        
        self.evidence_requirements = {
            'ORG': {
                'very_short': 3,
                'short': 2,
                'medium': 1,
                'long': 0
            },
            'GPE': {
                'very_short': 2,
                'short': 1,
                'medium': 0,
                'long': 0
            }
        }
        
        self.base_confidence = {
            'ORG': {
                'very_short_single': 0.05,
                'short_single': 0.15,
                'medium_single': 0.25,
                'long_single': 0.40,
                'multi_word': 0.60
            },
            'GPE': {
                'very_short_single': 0.20,
                'short_single': 0.30,
                'medium_single': 0.45,
                'long_single': 0.60,
                'multi_word': 0.70
            }
        }
        
        # Blacklists
        self.blacklist_words = {
            'here', 'there', 'where', 'when', 'what', 'how', 'why',
            'market', 'industry', 'business', 'service', 'group', 'team',
            'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'in', 'on',
            'social', 'global', 'local', 'way', 'fire', 'complex', 'element', 'state'
        }
        
        self.blacklist_phrases = {
            'the market', 'the industry', 'the business', 'the service',
            'the group', 'the team', 'the way', 'the fire', 'the complex',
            'the u', 'the us', 'the uk', 'the eu', 'global market'
        }
    
    def _load_entity_list(self, filename: str) -> Set[str]:
        """Load entity list from file"""
        file_path = self.corpus_path / filename
        if not file_path.exists():
            print(f"Warning: {filename} not found at {file_path}")
            return set()
        
        entities = set()
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                entity = line.strip()
                if entity:
                    entities.add(entity.lower())  # Store lowercase for matching
        return entities
    
    def check_premium_entity(self, text: str, full_text: str, start: int, end: int) -> Tuple[bool, str, str]:
        """
        Check if entity is in premium lists with word boundary validation.
        
        Returns:
            (is_premium, source, subcategory)
        """
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Word boundary validation - ensure it's a complete word
        if not self._is_whole_word(full_text, start, end):
            return False, None, None
        
        # Check premium lists (prioritize unicorns if in both lists)
        if text_lower in self.unicorns:
            return True, "unicorn", "unicorn_company"
        elif text_lower in self.investors:
            return True, "investor", "investor_company"
        
        return False, None, None
    
    def _is_whole_word(self, full_text: str, start: int, end: int) -> bool:
        """
        Verify that the matched text is a complete word (not part of another word).
        """
        # Check character before start
        if start > 0 and full_text[start - 1].isalnum():
            return False
        
        # Check character after end
        if end < len(full_text) and full_text[end].isalnum():
            return False
        
        return True
    
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
    
    def score_entity_premium(self, text: str, start: int, end: int, entity_type: EntityType,
                           full_text: str, nearby_entities: List[PremiumEntity] = None) -> PremiumEntity:
        """
        Score entity with premium list recognition and metadata.
        """
        if nearby_entities is None:
            nearby_entities = []
            
        text_clean = text.strip()
        text_lower = text_clean.lower()
        
        # Create base entity
        entity = PremiumEntity(
            text=text_clean,
            start=start,
            end=end,
            entity_type=entity_type,
            character_length=len(text_clean),
            word_count=len(text_clean.split())
        )
        
        # PREMIUM ENTITY CHECK - Highest priority
        is_premium, premium_source, subcategory = self.check_premium_entity(text_clean, full_text, start, end)
        
        if is_premium:
            entity.confidence = self.premium_confidence[premium_source]
            entity.evidence = [f'premium_{premium_source}_list', 'whole_word_match']
            entity.is_premium = True
            entity.premium_source = premium_source
            entity.subcategory = subcategory
            return entity
        
        # BLACKLIST CHECK for non-premium entities
        if text_lower in self.blacklist_words or text_lower in self.blacklist_phrases:
            entity.confidence = 0.0
            entity.evidence = ['blacklisted']
            entity.premium_source = 'standard'
            return entity
        
        # STANDARD SCORING for non-premium entities
        char_category = self.get_character_category(text_clean)
        base_confidence, confidence_type = self.calculate_base_confidence(text_clean, entity_type)
        
        # Basic evidence (simplified for this example)
        evidence = []
        evidence_score = 0.0
        
        if text_clean[0].isupper():
            evidence_score += 0.15
            evidence.append('capitalized')
        
        # Apply evidence requirements
        entity_key = entity_type.value
        required_evidence = self.evidence_requirements[entity_key].get(char_category, 0)
        evidence_count = len(evidence)
        meets_threshold = evidence_count >= required_evidence
        
        # Calculate final confidence
        final_confidence = min(base_confidence + evidence_score, 0.95)
        
        # Apply threshold penalty for insufficient evidence
        if not meets_threshold and char_category in ['very_short', 'short']:
            final_confidence *= 0.3
        
        entity.confidence = final_confidence
        entity.evidence = evidence + [f'base_{confidence_type}']
        entity.premium_source = 'standard'
        
        return entity
    
    def batch_score_entities(self, entity_matches: List[Tuple[str, int, int, EntityType]], 
                           full_text: str) -> List[PremiumEntity]:
        """Score a batch of entity matches"""
        scored_entities = []
        
        for text, start, end, entity_type in entity_matches:
            scored = self.score_entity_premium(text, start, end, entity_type, full_text)
            scored_entities.append(scored)
        
        # Sort by confidence (highest first)
        scored_entities.sort(key=lambda x: x.confidence, reverse=True)
        return scored_entities
    
    def get_premium_stats(self) -> Dict[str, Any]:
        """Get statistics about premium entities"""
        return {
            'investors_count': len(self.investors),
            'unicorns_count': len(self.unicorns),
            'total_premium': len(self.investors) + len(self.unicorns),
            'sample_investors': list(self.investors)[:5] if self.investors else [],
            'sample_unicorns': list(self.unicorns)[:5] if self.unicorns else []
        }


# EXAMPLE USAGE WITH PREMIUM ENTITIES
if __name__ == "__main__":
    # Initialize with corpus path
    scorer = PremiumEntityScoring("/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data/org")
    
    # Test text with premium entities
    test_text = "Apple Inc. received funding from Sequoia Capital and a16z. The unicorn company Stripe is valued at $95 billion. Tesla and SpaceX are both founded by Elon Musk. Goldman Sachs invested in the startup. Here we see market growth."
    
    # Calculate correct positions for test entities
    entities_to_find = ["Apple Inc.", "Sequoia Capital", "a16z", "Stripe", "Tesla", "SpaceX", "Goldman Sachs", "market", "Here"]
    test_entities = []
    
    for entity_text in entities_to_find:
        start = test_text.find(entity_text)
        if start != -1:
            end = start + len(entity_text)
            test_entities.append((entity_text, start, end, EntityType.ORG))
        else:
            print(f"Warning: '{entity_text}' not found in test text")
    
    print("PREMIUM ENTITY SCORING RESULTS:")
    print("=" * 80)
    print(f"{'Entity':<20} {'Type':<5} {'Confidence':<12} {'Source':<12} {'Subcategory':<15} {'Evidence'}")
    print("-" * 80)
    
    scored_entities = scorer.batch_score_entities(test_entities, test_text)
    
    for entity in scored_entities:
        source_display = entity.premium_source or "standard"
        subcategory_display = entity.subcategory or "-"
        evidence_summary = f"{len(entity.evidence)} pieces"
        
        print(f"{entity.text:<20} {entity.entity_type.value:<5} {entity.confidence:<12.3f} "
              f"{source_display:<12} {subcategory_display:<15} {evidence_summary}")
    
    print(f"\nPREMIUM ENTITIES (≥0.8):")
    premium_entities = [e for e in scored_entities if e.confidence >= 0.8]
    for entity in premium_entities:
        print(f"✓ {entity.text} ({entity.premium_source}): {entity.confidence:.3f}")
    
    print(f"\nHIGH CONFIDENCE ENTITIES (≥0.4):")
    high_conf = [e for e in scored_entities if e.confidence >= 0.4]
    for entity in high_conf:
        print(f"• {entity.text}: {entity.confidence:.3f}")
    
    print(f"\nPREMIUM ENTITY STATISTICS:")
    stats = scorer.get_premium_stats()
    print(f"Investors loaded: {stats['investors_count']}")
    print(f"Unicorns loaded: {stats['unicorns_count']}")
    print(f"Total premium entities: {stats['total_premium']}")
    print(f"Sample investors: {', '.join(stats['sample_investors'])}")
    print(f"Sample unicorns: {', '.join(stats['sample_unicorns'])}")