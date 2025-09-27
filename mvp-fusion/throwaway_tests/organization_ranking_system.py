#!/usr/bin/env python3
"""
Organization Entity Ranking System
==================================
Implements sophisticated context-aware ranking for organization entities
to reduce false positives from single-word matches.

Based on user requirements:
1. Single word matches should be LOW RANK by default
2. Require additional evidence for confidence boost:
   - Capitalization (first letter capitalized)
   - Suffixes (Inc, Corp, LLC, Ltd)
   - Context words (Company, Corporation, Group)
   - Multi-word patterns
3. Blacklist common words that shouldn't be organizations
"""

import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass


@dataclass
class OrganizationMatch:
    """Container for organization match with ranking metadata"""
    text: str
    start: int
    end: int
    confidence: float
    evidence: List[str]
    match_type: str  # 'single_word', 'multi_word', 'abbreviated'


class OrganizationRankingSystem:
    """
    Advanced ranking system for organization entity extraction.
    Reduces false positives through context analysis and evidence gathering.
    """
    
    def __init__(self):
        # Common words that should NOT be organizations (even if in corpus)
        self.blacklist_words = {
            'market', 'industry', 'business', 'company', 'service', 'services',
            'group', 'team', 'department', 'division', 'section', 'unit',
            'here', 'there', 'where', 'when', 'what', 'how', 'why',
            'the', 'and', 'or', 'but', 'for', 'with', 'by', 'at', 'in', 'on',
            'social', 'global', 'local', 'national', 'international',
            'public', 'private', 'personal', 'professional', 'commercial',
            'digital', 'online', 'virtual', 'physical', 'technical',
            'financial', 'economic', 'political', 'cultural', 'educational'
        }
        
        # Phrase patterns that should be rejected (includes "the X" patterns)
        self.blacklist_patterns = {
            'the market', 'the industry', 'the business', 'the company',
            'the service', 'the group', 'the team', 'the department',
            'the social', 'the global', 'the local', 'the national',
            'the u', 'the us', 'the uk', 'the eu',  # Fragments
            'the world', 'the system', 'the platform', 'the network',
            'the complex', 'the way', 'the fire', 'global market'
        }
        
        # Organization suffixes that boost confidence
        self.org_suffixes = {
            'inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 'co',
            'company', 'group', 'holdings', 'enterprises', 'solutions',
            'systems', 'technologies', 'partners', 'associates', 'consulting',
            'advisors', 'ventures', 'capital', 'investments', 'fund', 'funds'
        }
        
        # Context words that indicate organization nearby
        self.org_context_words = {
            'company', 'corporation', 'firm', 'business', 'enterprise',
            'organization', 'institution', 'agency', 'foundation', 'association',
            'partnership', 'consortium', 'alliance', 'coalition', 'union',
            'startup', 'venture', 'brand', 'manufacturer', 'provider'
        }
    
    def analyze_organization_match(self, text: str, match_text: str, start_pos: int, end_pos: int) -> OrganizationMatch:
        """
        Analyze a potential organization match and assign confidence ranking.
        
        Args:
            text: Full document text
            match_text: The matched organization text
            start_pos: Start position in text
            end_pos: End position in text
            
        Returns:
            OrganizationMatch with confidence score and evidence
        """
        match_text_lower = match_text.lower().strip()
        evidence = []
        confidence = 0.0
        
        # BLACKLIST CHECK - Immediate rejection
        if match_text_lower in self.blacklist_words or match_text_lower in self.blacklist_patterns:
            return OrganizationMatch(
                text=match_text,
                start=start_pos,
                end=end_pos,
                confidence=0.0,
                evidence=['blacklisted_word'],
                match_type='blacklisted'
            )
        
        # FRAGMENT CHECK - Reject obvious fragments
        if len(match_text_lower) <= 2:
            return OrganizationMatch(
                text=match_text,
                start=start_pos,
                end=end_pos,
                confidence=0.0,
                evidence=['too_short'],
                match_type='fragment'
            )
        
        # Determine match type
        word_count = len(match_text.split())
        if word_count == 1:
            match_type = 'single_word'
            confidence = 0.2  # Low starting confidence for single words
        else:
            match_type = 'multi_word'
            confidence = 0.6  # Higher starting confidence for multi-word
            evidence.append('multi_word_match')
        
        # CAPITALIZATION ANALYSIS
        if match_text[0].isupper():
            confidence += 0.2
            evidence.append('capitalized')
        
        if match_text.isupper() and len(match_text) > 2:
            confidence += 0.1
            evidence.append('all_caps_acronym')
        
        # SUFFIX ANALYSIS
        for suffix in self.org_suffixes:
            if match_text_lower.endswith(suffix):
                confidence += 0.3
                evidence.append(f'org_suffix_{suffix}')
                break
        
        # CONTEXT ANALYSIS - Look at surrounding words
        context_window = 50  # characters before and after
        before_start = max(0, start_pos - context_window)
        after_end = min(len(text), end_pos + context_window)
        
        context_before = text[before_start:start_pos].lower()
        context_after = text[end_pos:after_end].lower()
        full_context = context_before + " " + context_after
        
        # Check for organization context words
        for context_word in self.org_context_words:
            if context_word in full_context:
                confidence += 0.15
                evidence.append(f'context_word_{context_word}')
                break
        
        # PATTERN ANALYSIS
        # Check if preceded by "the" (often reduces legitimacy)
        if context_before.strip().endswith('the'):
            confidence -= 0.2
            evidence.append('preceded_by_the')
        
        # Check for organizational patterns (Inc., Corp., etc.)
        if re.search(r'\b(inc|corp|llc|ltd)\.?\s*$', context_after, re.IGNORECASE):
            confidence += 0.25
            evidence.append('followed_by_org_suffix')
        
        # FINAL CONFIDENCE ADJUSTMENTS
        # Cap confidence at reasonable levels
        confidence = min(confidence, 0.95)
        confidence = max(confidence, 0.0)
        
        return OrganizationMatch(
            text=match_text,
            start=start_pos,
            end=end_pos,
            confidence=confidence,
            evidence=evidence,
            match_type=match_type
        )
    
    def filter_organization_matches(self, matches: List[OrganizationMatch], min_confidence: float = 0.4) -> List[OrganizationMatch]:
        """
        Filter organization matches based on confidence threshold.
        
        Args:
            matches: List of OrganizationMatch objects
            min_confidence: Minimum confidence threshold (0.0 to 1.0)
            
        Returns:
            Filtered list of high-confidence matches
        """
        return [match for match in matches if match.confidence >= min_confidence]
    
    def rank_organizations(self, text: str, raw_matches: List[Tuple[str, int, int]]) -> List[OrganizationMatch]:
        """
        Take raw Aho-Corasick matches and apply sophisticated ranking.
        
        Args:
            text: Full document text
            raw_matches: List of (match_text, start_pos, end_pos) tuples
            
        Returns:
            List of ranked OrganizationMatch objects
        """
        ranked_matches = []
        
        for match_text, start_pos, end_pos in raw_matches:
            analyzed_match = self.analyze_organization_match(text, match_text, start_pos, end_pos)
            ranked_matches.append(analyzed_match)
        
        # Sort by confidence (highest first)
        ranked_matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return ranked_matches


# EXAMPLE USAGE
if __name__ == "__main__":
    ranking_system = OrganizationRankingSystem()
    
    # Test text with various organization mentions
    test_text = """
    Apple Inc. is a major technology company based in California. 
    The market for smartphones is competitive. Getty Images provides stock photos.
    Microsoft Corporation and Google are also major players in the industry.
    The U.S. Department of Justice investigated the case. Here we see growth.
    """
    
    # Simulate raw Aho-Corasick matches (what we currently get)
    raw_matches = [
        ("Apple Inc.", 5, 15),
        ("the market", 80, 90),
        ("Getty", 120, 125),
        ("Microsoft Corporation", 160, 180),
        ("Google", 185, 191),
        ("the U", 230, 235),
        ("industry", 270, 278),
        ("Here", 300, 304)
    ]
    
    # Apply ranking
    ranked_matches = ranking_system.rank_organizations(test_text, raw_matches)
    
    print("ORGANIZATION RANKING RESULTS:")
    print("=" * 50)
    
    for match in ranked_matches:
        print(f"Text: '{match.text}'")
        print(f"Confidence: {match.confidence:.2f}")
        print(f"Type: {match.match_type}")
        print(f"Evidence: {', '.join(match.evidence)}")
        print("-" * 30)
    
    print("\nHIGH CONFIDENCE MATCHES (>= 0.4):")
    high_confidence = ranking_system.filter_organization_matches(ranked_matches, 0.4)
    for match in high_confidence:
        print(f"✓ '{match.text}' (confidence: {match.confidence:.2f})")
    
    print("\nREJECTED MATCHES (< 0.4):")
    low_confidence = [m for m in ranked_matches if m.confidence < 0.4]
    for match in low_confidence:
        print(f"✗ '{match.text}' (confidence: {match.confidence:.2f}) - {', '.join(match.evidence)}")