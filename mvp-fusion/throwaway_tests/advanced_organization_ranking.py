#!/usr/bin/env python3
"""
Advanced Organization Ranking System with Multi-Entity Context & SPO Integration
================================================================================
Enhanced ranking system that uses:
1. Nearby entity analysis (PERSON, GPE, etc.)
2. SPO (Subject-Predicate-Object) relationships  
3. Corpus cleaning recommendations
4. Cross-entity validation

Example scenarios that boost confidence:
- "John Smith, CEO of Apple" (PERSON + title + ORG)
- "Apple Inc. headquarters in Cupertino" (ORG + GPE)
- SPO: "Apple -> headquartered_in -> California"
"""

import re
from typing import Dict, List, Tuple, Any, Set
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EntityMatch:
    """Generic entity match container"""
    text: str
    start: int
    end: int
    entity_type: str  # 'ORG', 'PERSON', 'GPE', 'LOC', etc.
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)


@dataclass
class SPOTriple:
    """Subject-Predicate-Object relationship"""
    subject: str
    predicate: str
    object: str
    confidence: float
    subject_span: Tuple[int, int] = None
    object_span: Tuple[int, int] = None


class AdvancedOrganizationRanking:
    """
    Multi-entity context-aware organization ranking system.
    Integrates entity proximity and SPO relationships for validation.
    """
    
    def __init__(self):
        # Core blacklists (expanded)
        self.blacklist_words = {
            'here', 'there', 'where', 'when', 'what', 'how', 'why',
            'market', 'industry', 'business', 'service', 'services',  
            'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'in', 'on',
            'social', 'global', 'local', 'national', 'international',
            'world', 'system', 'platform', 'network', 'way', 'fire', 'complex',
            'element', 'state', 'government', 'public', 'private', 'general'
        }
        
        self.blacklist_patterns = {
            'the u', 'the us', 'the uk', 'the eu', 'the market', 'the industry',
            'the business', 'the service', 'the group', 'the team', 'the way',
            'the fire', 'the complex', 'global market', 'the system'
        }
        
        # Organization indicators
        self.org_suffixes = {
            'inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 'co', 'company',
            'group', 'holdings', 'enterprises', 'solutions', 'systems', 'technologies'
        }
        
        # Title/role words that indicate organization context
        self.org_role_indicators = {
            'ceo', 'president', 'director', 'manager', 'founder', 'executive',
            'chairman', 'cto', 'cfo', 'vice president', 'vp', 'head of',
            'chief', 'partner', 'associate', 'consultant', 'advisor'
        }
        
        # Predicates that indicate organization relationships
        self.org_predicates = {
            'works_for', 'employed_by', 'ceo_of', 'president_of', 'founded',
            'headquartered_in', 'located_in', 'based_in', 'operates_in',
            'acquired', 'merged_with', 'partnership_with', 'invested_in'
        }
        
        # Location/business context words
        self.business_context = {
            'headquarters', 'office', 'branch', 'facility', 'campus', 'building',
            'founded', 'established', 'incorporated', 'acquired', 'merged'
        }
    
    def analyze_entity_proximity(self, org_match: EntityMatch, all_entities: List[EntityMatch], 
                                proximity_window: int = 100) -> Dict[str, Any]:
        """
        Analyze nearby entities to validate organization legitimacy.
        
        Args:
            org_match: The organization match to validate
            all_entities: All detected entities in the document
            proximity_window: Character distance to consider "nearby"
            
        Returns:
            Dict with proximity analysis results
        """
        nearby_entities = []
        evidence = []
        confidence_boost = 0.0
        
        org_center = (org_match.start + org_match.end) // 2
        
        for entity in all_entities:
            if entity.entity_type == 'ORG' or entity == org_match:
                continue
                
            entity_center = (entity.start + entity.end) // 2
            distance = abs(org_center - entity_center)
            
            if distance <= proximity_window:
                nearby_entities.append(entity)
                
                # PERSON entities nearby often validate organizations
                if entity.entity_type == 'PERSON':
                    confidence_boost += 0.15
                    evidence.append(f'nearby_person_{entity.text}')
                
                # GPE (locations) validate business presence
                elif entity.entity_type == 'GPE':
                    confidence_boost += 0.10
                    evidence.append(f'nearby_location_{entity.text}')
                
                # Other organizations suggest business context
                elif entity.entity_type == 'ORG':
                    confidence_boost += 0.05
                    evidence.append(f'nearby_organization')
        
        return {
            'nearby_entities': nearby_entities,
            'confidence_boost': min(confidence_boost, 0.3),  # Cap boost
            'evidence': evidence,
            'entity_count_by_type': self._count_entities_by_type(nearby_entities)
        }
    
    def analyze_spo_relationships(self, org_match: EntityMatch, spo_triples: List[SPOTriple]) -> Dict[str, Any]:
        """
        Analyze SPO relationships that mention the potential organization.
        
        Args:
            org_match: The organization match to validate
            spo_triples: List of Subject-Predicate-Object relationships
            
        Returns:
            Dict with SPO analysis results
        """
        relevant_triples = []
        evidence = []
        confidence_boost = 0.0
        
        org_text_lower = org_match.text.lower()
        
        for triple in spo_triples:
            # Check if organization appears in subject or object
            in_subject = org_text_lower in triple.subject.lower()
            in_object = org_text_lower in triple.object.lower()
            
            if in_subject or in_object:
                relevant_triples.append(triple)
                
                # Organization-validating predicates
                if triple.predicate in self.org_predicates:
                    confidence_boost += 0.20
                    evidence.append(f'spo_org_predicate_{triple.predicate}')
                
                # Person-organization relationships
                if in_object and any(role in triple.predicate.lower() for role in self.org_role_indicators):
                    confidence_boost += 0.25
                    evidence.append(f'spo_person_role_{triple.predicate}')
                
                # Location-organization relationships  
                if 'located' in triple.predicate or 'headquarters' in triple.predicate:
                    confidence_boost += 0.15
                    evidence.append(f'spo_location_relation_{triple.predicate}')
        
        return {
            'relevant_triples': relevant_triples,
            'confidence_boost': min(confidence_boost, 0.4),  # Cap boost
            'evidence': evidence,
            'triple_count': len(relevant_triples)
        }
    
    def analyze_context_roles_and_titles(self, text: str, org_match: EntityMatch, window: int = 50) -> Dict[str, Any]:
        """
        Look for role/title indicators near the organization mention.
        """
        start_pos = max(0, org_match.start - window)
        end_pos = min(len(text), org_match.end + window)
        context = text[start_pos:end_pos].lower()
        
        evidence = []
        confidence_boost = 0.0
        
        # Look for organizational roles/titles
        for role in self.org_role_indicators:
            if role in context:
                confidence_boost += 0.20
                evidence.append(f'context_role_{role}')
                break  # Only count once
        
        # Look for business context words
        for word in self.business_context:
            if word in context:
                confidence_boost += 0.10
                evidence.append(f'business_context_{word}')
                break  # Only count once
        
        return {
            'confidence_boost': min(confidence_boost, 0.3),
            'evidence': evidence,
            'context_analyzed': context[max(0, org_match.start-start_pos-10):org_match.end-start_pos+10]
        }
    
    def rank_organization_with_context(self, text: str, org_match: EntityMatch, 
                                     all_entities: List[EntityMatch], 
                                     spo_triples: List[SPOTriple] = None) -> EntityMatch:
        """
        Enhanced organization ranking using multi-entity context and SPO relationships.
        """
        org_text_lower = org_match.text.lower().strip()
        
        # Start with basic analysis
        evidence = []
        confidence = 0.0
        
        # BLACKLIST CHECK
        if org_text_lower in self.blacklist_words or org_text_lower in self.blacklist_patterns:
            org_match.confidence = 0.0
            org_match.evidence = ['blacklisted_word']
            return org_match
        
        # FRAGMENT CHECK
        if len(org_text_lower) <= 2:
            org_match.confidence = 0.0
            org_match.evidence = ['too_short']
            return org_match
        
        # BASE CONFIDENCE
        word_count = len(org_match.text.split())
        if word_count == 1:
            confidence = 0.2  # Low base for single words
        else:
            confidence = 0.6  # Higher base for multi-word
            evidence.append('multi_word')
        
        # CAPITALIZATION
        if org_match.text[0].isupper():
            confidence += 0.15
            evidence.append('capitalized')
        
        # ORGANIZATION SUFFIXES
        for suffix in self.org_suffixes:
            if org_text_lower.endswith(suffix):
                confidence += 0.25
                evidence.append(f'org_suffix_{suffix}')
                break
        
        # ENTITY PROXIMITY ANALYSIS
        proximity_analysis = self.analyze_entity_proximity(org_match, all_entities)
        confidence += proximity_analysis['confidence_boost']
        evidence.extend(proximity_analysis['evidence'])
        
        # CONTEXT ROLES/TITLES ANALYSIS  
        context_analysis = self.analyze_context_roles_and_titles(text, org_match)
        confidence += context_analysis['confidence_boost']
        evidence.extend(context_analysis['evidence'])
        
        # SPO RELATIONSHIP ANALYSIS
        if spo_triples:
            spo_analysis = self.analyze_spo_relationships(org_match, spo_triples)
            confidence += spo_analysis['confidence_boost']
            evidence.extend(spo_analysis['evidence'])
        
        # FINAL ADJUSTMENTS
        confidence = min(confidence, 0.95)
        confidence = max(confidence, 0.0)
        
        org_match.confidence = confidence
        org_match.evidence = evidence
        
        return org_match
    
    def _count_entities_by_type(self, entities: List[EntityMatch]) -> Dict[str, int]:
        """Count entities by type for analysis"""
        counts = {}
        for entity in entities:
            counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
        return counts
    
    def generate_corpus_cleaning_report(self, corpus_file: str) -> Dict[str, Any]:
        """
        Generate recommendations for cleaning the organization corpus.
        """
        if not Path(corpus_file).exists():
            return {'error': 'Corpus file not found'}
        
        with open(corpus_file, 'r') as f:
            lines = f.readlines()
        
        flagged_words = []
        for i, line in enumerate(lines):
            word = line.strip().lower()
            if word in self.blacklist_words or word in self.blacklist_patterns:
                flagged_words.append({'line': i+1, 'word': word, 'reason': 'common_word'})
            elif len(word) <= 2:
                flagged_words.append({'line': i+1, 'word': word, 'reason': 'too_short'})
            elif word in ['and', 'or', 'the', 'of', 'in', 'at', 'on', 'for', 'with']:
                flagged_words.append({'line': i+1, 'word': word, 'reason': 'stop_word'})
        
        return {
            'total_lines': len(lines),
            'flagged_count': len(flagged_words),
            'flagged_words': flagged_words,
            'cleanup_percentage': round((len(flagged_words) / len(lines)) * 100, 2)
        }


# EXAMPLE USAGE WITH REALISTIC SCENARIOS
if __name__ == "__main__":
    ranker = AdvancedOrganizationRanking()
    
    # Test text with rich entity context
    test_text = """
    John Smith, CEO of Apple Inc., announced today that the company's headquarters 
    in Cupertino, California will expand. Microsoft Corporation and Google are also 
    major players in the industry. The market for smartphones continues to grow.
    Here we see strong partnerships between Tesla and SpaceX, both founded by Elon Musk.
    """
    
    # Simulate detected entities (what pipeline would provide)
    all_entities = [
        EntityMatch("John Smith", 5, 15, "PERSON"),
        EntityMatch("Apple Inc.", 24, 34, "ORG"),
        EntityMatch("Cupertino", 85, 94, "GPE"),
        EntityMatch("California", 96, 106, "GPE"),
        EntityMatch("Microsoft Corporation", 120, 141, "ORG"),
        EntityMatch("Google", 146, 152, "ORG"),
        EntityMatch("the market", 175, 185, "ORG"),  # False positive
        EntityMatch("industry", 220, 228, "ORG"),   # False positive
        EntityMatch("Tesla", 280, 285, "ORG"),
        EntityMatch("SpaceX", 290, 296, "ORG"),
        EntityMatch("Elon Musk", 315, 324, "PERSON"),
        EntityMatch("Here", 250, 254, "ORG")        # False positive
    ]
    
    # Simulate SPO relationships (what semantic analysis would provide)  
    spo_triples = [
        SPOTriple("John Smith", "ceo_of", "Apple Inc.", 0.9),
        SPOTriple("Apple Inc.", "headquartered_in", "Cupertino", 0.85),
        SPOTriple("Tesla", "founded_by", "Elon Musk", 0.9),
        SPOTriple("SpaceX", "founded_by", "Elon Musk", 0.9),
    ]
    
    print("ADVANCED ORGANIZATION RANKING WITH CONTEXT:")
    print("=" * 60)
    
    # Test only ORG entities
    org_entities = [e for e in all_entities if e.entity_type == "ORG"]
    
    for org_entity in org_entities:
        enhanced_match = ranker.rank_organization_with_context(
            test_text, org_entity, all_entities, spo_triples
        )
        
        print(f"Text: '{enhanced_match.text}'")
        print(f"Confidence: {enhanced_match.confidence:.3f}")
        print(f"Evidence: {', '.join(enhanced_match.evidence)}")
        print("-" * 40)
    
    print("\nHIGH CONFIDENCE ORGANIZATIONS (>= 0.5):")
    high_conf = [e for e in org_entities if ranker.rank_organization_with_context(test_text, e, all_entities, spo_triples).confidence >= 0.5]
    for org in high_conf:
        ranked = ranker.rank_organization_with_context(test_text, org, all_entities, spo_triples)
        print(f"✓ '{ranked.text}' (confidence: {ranked.confidence:.3f})")
    
    # Test corpus cleaning
    print(f"\nCORPUS CLEANING ANALYSIS:")
    print("-" * 30)
    corpus_path = "/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data/org/single_word_organizations.txt"
    if Path(corpus_path).exists():
        cleaning_report = ranker.generate_corpus_cleaning_report(corpus_path)
        print(f"Total words in corpus: {cleaning_report['total_lines']}")
        print(f"Words flagged for removal: {cleaning_report['flagged_count']}")
        print(f"Cleanup percentage: {cleaning_report['cleanup_percentage']}%")
        print("\nSample flagged words:")
        for word_info in cleaning_report['flagged_words'][:10]:
            print(f"  Line {word_info['line']}: '{word_info['word']}' ({word_info['reason']})")
    else:
        print("Corpus file not found for analysis")