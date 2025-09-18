#!/usr/bin/env python3
"""
Enhanced Entity Disambiguation Module
======================================
Foundation for accurate semantic fact extraction through proper entity classification.

This module provides context-aware disambiguation between persons and organizations,
which is critical for generating accurate, atomic facts from documents.
"""

import re
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import Counter
import logging
from pathlib import Path

# Get fusion logger
from .logging_config import get_fusion_logger

@dataclass
class EntityContext:
    """Captures contextual information around an entity mention"""
    entity_text: str
    entity_type: str  # Original classification (PERSON, ORG, etc.)
    left_context: str  # 50 chars before entity
    right_context: str  # 50 chars after entity
    sentence: str  # Full sentence containing entity
    span: Tuple[int, int]  # Character position in document
    confidence: float = 0.5
    
@dataclass 
class DisambiguatedEntity:
    """Enhanced entity with disambiguation and normalization"""
    original_text: str
    normalized_text: str  # Standardized form
    entity_type: str  # PERSON, ORG, LOCATION, etc.
    entity_subtype: Optional[str] = None  # CEO, FOUNDER, COMPANY, STARTUP, etc.
    confidence: float = 0.5
    contexts: List[EntityContext] = field(default_factory=list)
    aliases: Set[str] = field(default_factory=set)
    relationships: Dict[str, str] = field(default_factory=dict)  # e.g., {"employee_of": "OpenAI"}
    
class EntityDisambiguator:
    """
    Advanced entity disambiguation using corpus-based validation and contextual patterns.
    
    Key capabilities:
    1. Corpus-based name/company validation using Aho-Corasick for O(n) performance
    2. Person vs Organization disambiguation using context + corpus validation
    3. Entity normalization and deduplication
    4. Role and relationship extraction
    5. High-confidence scoring based on corpus matches + context
    """
    
    # Class variable to control "once per class" logging
    _validation_logged = False
    
    def __init__(self, corpus_dir: Optional[Path] = None):
        self.logger = get_fusion_logger(__name__)
        
        # Initialize corpus validator for high-confidence entity recognition
        try:
            # Try absolute import first
            from knowledge.corpus.entity_corpus_builder import CorpusValidator
            self.corpus_validator = CorpusValidator(corpus_dir)
            self.has_corpus = True
            
            # Log corpus statistics
            stats = self.corpus_validator.get_corpus_stats()
            self.logger.entity(f"✅ Loaded entity corpus: {stats['total_first_names']} first names, "
                             f"{stats['total_last_names']} last names, {stats['total_companies']} companies")
            self.logger.entity(f"   Investors: {stats['total_vc_firms']} VC firms, {stats['total_pe_firms']} PE firms")
            self.logger.entity(f"   Aho-Corasick: {'✅ Available' if stats['uses_ahocorasick'] else '❌ Not available'}")
            
        except ImportError:
            try:
                # Try relative import
                from ..knowledge.corpus.entity_corpus_builder import CorpusValidator
                self.corpus_validator = CorpusValidator(corpus_dir)
                self.has_corpus = True
                
                # Log corpus statistics
                stats = self.corpus_validator.get_corpus_stats()
                self.logger.entity(f"✅ Loaded entity corpus: {stats['total_first_names']} first names, "
                                 f"{stats['total_last_names']} last names, {stats['total_companies']} companies")
                
            except ImportError:
                self.logger.logger.warning("⚠️  Corpus validator not available, falling back to basic patterns")
                self.corpus_validator = None
                self.has_corpus = False
        
        # Person indicators (strongly suggest PERSON entity)
        self.person_indicators = {
            'titles': ['mr', 'mrs', 'ms', 'dr', 'prof', 'professor', 'sir', 'dame', 'lord', 'lady'],
            'roles': ['ceo', 'cto', 'cfo', 'founder', 'co-founder', 'president', 'director', 
                     'manager', 'engineer', 'developer', 'analyst', 'consultant', 'advisor',
                     'chairman', 'vice president', 'vp', 'svp', 'evp', 'partner', 'principal'],
            'actions': ['said', 'says', 'stated', 'announced', 'believes', 'thinks', 'founded',
                       'created', 'built', 'leads', 'manages', 'joined', 'left', 'resigned'],
            'possessives': ["'s", 'his', 'her', 'their']
        }
        
        # Organization indicators (strongly suggest ORG entity)
        self.org_indicators = {
            'suffixes': ['inc', 'corp', 'corporation', 'llc', 'ltd', 'limited', 'company', 'co',
                        'group', 'holdings', 'partners', 'associates', 'solutions', 'systems',
                        'technologies', 'tech', 'labs', 'research', 'institute', 'university',
                        'college', 'bank', 'capital', 'ventures', 'fund', 'foundation'],
            'prefixes': ['the', 'at'],  # "at Google", "The Microsoft Corporation"
            'contexts': ['acquired', 'acquires', 'merged', 'partnered', 'invested', 'raised',
                        'valued at', 'headquartered', 'based in', 'offices in', 'employees']
        }
        
        # Mixed signals (could be either)
        self.ambiguous_patterns = [
            'apple',  # Apple Inc. vs person named Apple
            'ford',   # Ford Motor vs Harrison Ford
            'wells',  # Wells Fargo vs person named Wells
            'chase',  # JPMorgan Chase vs person named Chase
            'stanley' # Morgan Stanley vs person named Stanley
        ]
        
    def disambiguate_entities(self, entities: Dict[str, List], content: str) -> Dict[str, List[DisambiguatedEntity]]:
        """
        Main disambiguation pipeline.
        
        Args:
            entities: Raw entities from extraction {"person": [...], "org": [...], ...}
            content: Full document content for context analysis
            
        Returns:
            Dictionary of disambiguated entities by type
        """
        disambiguated = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'other': []
        }
        
        # Process persons with disambiguation
        if 'person' in entities:
            for entity in entities['person']:
                disamb_entity = self._disambiguate_person(entity, content)
                if disamb_entity.entity_type == 'PERSON':
                    disambiguated['persons'].append(disamb_entity)
                else:
                    disambiguated['organizations'].append(disamb_entity)
        
        # Process organizations with disambiguation
        if 'org' in entities:
            for entity in entities['org']:
                disamb_entity = self._disambiguate_org(entity, content)
                if disamb_entity.entity_type == 'ORG':
                    disambiguated['organizations'].append(disamb_entity)
                else:
                    disambiguated['persons'].append(disamb_entity)
        
        # Normalize and deduplicate
        disambiguated = self._normalize_and_deduplicate(disambiguated)
        
        # Extract relationships between entities
        self._extract_relationships(disambiguated, content)
        
        return disambiguated
    
    def _disambiguate_person(self, entity_data: Dict, content: str) -> DisambiguatedEntity:
        """
        Disambiguate a potential person entity using corpus + context.
        
        Uses corpus validation for high confidence + contextual clues for edge cases.
        """
        entity_text = entity_data.get('value', entity_data) if isinstance(entity_data, dict) else str(entity_data)
        span = entity_data.get('span', {}) if isinstance(entity_data, dict) else {}
        
        # Extract context around entity
        context = self._extract_context(entity_text, content, span)
        
        # Start with corpus-based validation if available
        person_score = 0.1  # Base score
        org_score = 0.1
        entity_subtype = None
        corpus_details = {}
        
        if self.has_corpus and self.corpus_validator:
            # High-confidence corpus validation
            person_confidence, person_details = self.corpus_validator.validate_person_name(entity_text)
            org_confidence, org_details = self.corpus_validator.validate_company_name(entity_text)
            
            corpus_details = {'person_details': person_details, 'org_details': org_details}
            
            # Corpus validation is primary signal
            person_score = person_confidence
            org_score = org_confidence
            
            # Extract subtype from corpus details
            if person_details.get('is_known_angel'):
                entity_subtype = 'ANGEL_INVESTOR'
            elif org_details.get('company_type'):
                entity_subtype = org_details['company_type'].upper()
            
            # "Once per class" validation logging to reduce spam
            if not EntityDisambiguator._validation_logged:
                self.logger.entity(f"🔍 Corpus validation active: Person vs Org disambiguation")
                EntityDisambiguator._validation_logged = True
        
        # Enhance with contextual clues
        lower_context = context.sentence.lower()
        lower_entity = entity_text.lower()
        
        # Title check (Mr., Dr., etc.) - strong person indicator
        for title in self.person_indicators['titles']:
            if f"{title}. {lower_entity}" in lower_context or f"{title} {lower_entity}" in lower_context:
                person_score = max(person_score, 0.8)  # Strong override
                break
        
        # Role check (CEO, founder, etc.) - strong person indicator
        for role in self.person_indicators['roles']:
            if f"{lower_entity}, {role}" in lower_context or f"{role} {lower_entity}" in lower_context:
                person_score = max(person_score, 0.8)
                entity_subtype = entity_subtype or role.upper()
                break
        
        # Action verb check (said, founded, etc.) - moderate person indicator
        for action in self.person_indicators['actions']:
            if f"{lower_entity} {action}" in lower_context:
                person_score += 0.15
                break
        
        # Check for strong organization indicators that override corpus
        for suffix in self.org_indicators['suffixes']:
            if (lower_entity.endswith(f" {suffix}") or 
                lower_entity.endswith(f" {suffix}.") or
                lower_entity.endswith(f"_{suffix}")):  # Handle underscores
                org_score = max(org_score, 0.85)  # Strong override
                entity_subtype = 'CORPORATION'
                break
        
        # Organizational context patterns
        for org_context in self.org_indicators['contexts']:
            if org_context in lower_context:
                org_score += 0.1
                break
        
        # Edge case: detect "Company Name Inc" patterns
        if ' inc' in lower_entity or ' corp' in lower_entity or ' llc' in lower_entity:
            org_score = max(org_score, 0.9)
            entity_subtype = 'CORPORATION'
        
        # Determine final type based on scores
        if org_score > person_score:
            entity_type = 'ORG'
            confidence = min(org_score, 1.0)
        else:
            entity_type = 'PERSON'
            confidence = min(person_score, 1.0)
        
        # Create disambiguated entity
        disamb = DisambiguatedEntity(
            original_text=entity_text,
            normalized_text=self._normalize_entity_text(entity_text),
            entity_type=entity_type,
            entity_subtype=entity_subtype,
            confidence=confidence
        )
        disamb.contexts.append(context)
        
        # Store corpus validation details for debugging
        if corpus_details:
            disamb.relationships['corpus_validation'] = str(corpus_details)
        
        return disamb
    
    def _disambiguate_org(self, entity_data: Dict, content: str) -> DisambiguatedEntity:
        """
        Disambiguate a potential organization entity using corpus + context.
        
        Uses corpus validation for known companies/investors + contextual patterns.
        """
        entity_text = entity_data.get('value', entity_data) if isinstance(entity_data, dict) else str(entity_data)
        span = entity_data.get('span', {}) if isinstance(entity_data, dict) else {}
        
        # Extract context
        context = self._extract_context(entity_text, content, span)
        
        # Start with corpus-based validation
        org_score = 0.1  # Base score
        person_score = 0.1
        entity_subtype = None
        corpus_details = {}
        
        if self.has_corpus and self.corpus_validator:
            # High-confidence corpus validation
            org_confidence, org_details = self.corpus_validator.validate_company_name(entity_text)
            person_confidence, person_details = self.corpus_validator.validate_person_name(entity_text)
            
            corpus_details = {'org_details': org_details, 'person_details': person_details}
            
            # Corpus validation is primary signal
            org_score = org_confidence
            person_score = person_confidence
            
            # Extract detailed subtype from corpus
            if org_details.get('is_vc_firm'):
                entity_subtype = 'VC_FIRM'
            elif org_details.get('is_pe_firm'):
                entity_subtype = 'PE_FIRM'
            elif org_details.get('is_accelerator'):
                entity_subtype = 'ACCELERATOR'
            elif org_details.get('is_university'):
                entity_subtype = 'UNIVERSITY'
            elif org_details.get('is_government'):
                entity_subtype = 'GOVERNMENT'
            elif org_details.get('is_known_company'):
                entity_subtype = 'CORPORATION'
            
            # Validation logging already shown once per class instance
        
        # Enhance with contextual patterns
        lower_context = context.sentence.lower()
        lower_entity = entity_text.lower()
        
        # Check organization indicators
        for suffix in self.org_indicators['suffixes']:
            if suffix in lower_entity:
                org_score = max(org_score, 0.8)
                if not entity_subtype:  # Only set if not already determined by corpus
                    if 'tech' in suffix or 'systems' in suffix:
                        entity_subtype = 'TECH_COMPANY'
                    elif 'capital' in suffix or 'ventures' in suffix:
                        entity_subtype = 'INVESTOR'
                    elif 'university' in suffix or 'college' in suffix:
                        entity_subtype = 'UNIVERSITY'
                    else:
                        entity_subtype = 'CORPORATION'
                break
        
        # Check organizational contexts
        for org_context in self.org_indicators['contexts']:
            if org_context in lower_context:
                org_score += 0.1
                break
        
        # Check if it might be a person despite initial classification
        # This handles cases where corpus says "company" but context suggests person
        name_parts = entity_text.split()
        if len(name_parts) == 2:
            # Could be First Last name - check if corpus has no strong company signals
            if (name_parts[0][0].isupper() and name_parts[1][0].isupper() and
                not any(suffix in lower_entity for suffix in self.org_indicators['suffixes']) and
                not corpus_details.get('org_details', {}).get('is_known_company', False)):
                
                # Additional person context checks
                for action in self.person_indicators['actions']:
                    if f"{lower_entity} {action}" in lower_context:
                        person_score = max(person_score, 0.7)
                        break
                
                for role in self.person_indicators['roles']:
                    if f"{lower_entity}, {role}" in lower_context or f"{role} {lower_entity}" in lower_context:
                        person_score = max(person_score, 0.8)
                        entity_subtype = role.upper()
                        break
        
        # Determine final type
        if person_score > org_score:
            entity_type = 'PERSON'
            confidence = min(person_score, 1.0)
        else:
            entity_type = 'ORG'
            confidence = min(org_score, 1.0)
        
        # Create disambiguated entity
        disamb = DisambiguatedEntity(
            original_text=entity_text,
            normalized_text=self._normalize_entity_text(entity_text),
            entity_type=entity_type,
            entity_subtype=entity_subtype,
            confidence=confidence
        )
        disamb.contexts.append(context)
        
        # Store corpus validation details for debugging
        if corpus_details:
            disamb.relationships['corpus_validation'] = str(corpus_details)
        
        return disamb
    
    def _extract_context(self, entity_text: str, content: str, span: Dict) -> EntityContext:
        """Extract contextual information around an entity mention."""
        # Use span if available, otherwise search for entity
        if span and 'start' in span and 'end' in span:
            start = span['start']
            end = span['end']
        else:
            # Find entity in content
            match = re.search(re.escape(entity_text), content, re.IGNORECASE)
            if match:
                start = match.start()
                end = match.end()
            else:
                start = 0
                end = len(entity_text)
        
        # Extract surrounding context
        left_boundary = max(0, start - 50)
        right_boundary = min(len(content), end + 50)
        
        left_context = content[left_boundary:start].strip()
        right_context = content[end:right_boundary].strip()
        
        # Extract full sentence
        sentence_start = content.rfind('.', 0, start) + 1 if content.rfind('.', 0, start) != -1 else 0
        sentence_end = content.find('.', end)
        sentence_end = sentence_end + 1 if sentence_end != -1 else len(content)
        sentence = content[sentence_start:sentence_end].strip()
        
        return EntityContext(
            entity_text=entity_text,
            entity_type='UNKNOWN',
            left_context=left_context,
            right_context=right_context,
            sentence=sentence,
            span=(start, end)
        )
    
    def _normalize_entity_text(self, text: str) -> str:
        """
        Normalize entity text for deduplication.
        
        Examples:
        - "Apple Inc." -> "Apple Inc"
        - "mr. john smith" -> "John Smith"
        - "THE MICROSOFT CORPORATION" -> "Microsoft Corporation"
        """
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove titles
        for title in self.person_indicators['titles']:
            pattern = rf'\b{title}\.?\s+'
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove 'The' prefix for organizations
        if text.lower().startswith('the '):
            text = text[4:]
        
        # Normalize case (Title Case for names/orgs)
        text = ' '.join(word.capitalize() for word in text.split())
        
        # Remove trailing punctuation
        text = text.rstrip('.,;:')
        
        return text
    
    def _normalize_and_deduplicate(self, entities: Dict) -> Dict:
        """
        Normalize entities and merge duplicates.
        
        Combines different mentions of the same entity and tracks aliases.
        """
        for entity_type, entity_list in entities.items():
            if not entity_list:
                continue
            
            # Group by normalized text
            normalized_groups = {}
            for entity in entity_list:
                norm_text = entity.normalized_text.lower()
                if norm_text not in normalized_groups:
                    normalized_groups[norm_text] = []
                normalized_groups[norm_text].append(entity)
            
            # Merge entities with same normalized form
            merged_entities = []
            for norm_text, group in normalized_groups.items():
                if len(group) == 1:
                    merged_entities.append(group[0])
                else:
                    # Merge multiple mentions
                    primary = group[0]
                    for other in group[1:]:
                        # Add aliases
                        if other.original_text != primary.original_text:
                            primary.aliases.add(other.original_text)
                        # Combine contexts
                        primary.contexts.extend(other.contexts)
                        # Update confidence (average)
                        primary.confidence = (primary.confidence + other.confidence) / 2
                    merged_entities.append(primary)
            
            entities[entity_type] = merged_entities
        
        return entities
    
    def _extract_relationships(self, entities: Dict, content: str) -> None:
        """
        Extract relationships between entities.
        
        Identifies patterns like:
        - "John Smith, CEO of Apple"
        - "Google acquired DeepMind"
        - "Sarah Johnson joined Microsoft"
        """
        all_persons = entities.get('persons', [])
        all_orgs = entities.get('organizations', [])
        
        content_lower = content.lower()
        
        # Extract person-organization relationships
        for person in all_persons:
            person_text = person.normalized_text.lower()
            
            # Check for role patterns
            for org in all_orgs:
                org_text = org.normalized_text.lower()
                
                # Pattern: "Person, Role at/of Organization"
                patterns = [
                    rf"{person_text},?\s+\w+\s+(?:at|of)\s+{org_text}",
                    rf"{person_text}\s+(?:joined|left|leads|manages|founded)\s+{org_text}",
                    rf"{org_text}'s\s+\w+\s+{person_text}",  # "Apple's CEO Tim Cook"
                ]
                
                for pattern in patterns:
                    if re.search(pattern, content_lower):
                        person.relationships['affiliated_with'] = org.normalized_text
                        org.relationships[f'has_person_{person.normalized_text}'] = person.normalized_text
                        break
        
        # Extract organization-organization relationships  
        for org1 in all_orgs:
            org1_text = org1.normalized_text.lower()
            for org2 in all_orgs:
                if org1 == org2:
                    continue
                org2_text = org2.normalized_text.lower()
                
                # Acquisition pattern
                if re.search(rf"{org1_text}\s+(?:acquired|acquires|bought)\s+{org2_text}", content_lower):
                    org1.relationships['acquired'] = org2.normalized_text
                    org2.relationships['acquired_by'] = org1.normalized_text
                
                # Partnership pattern
                if re.search(rf"{org1_text}\s+(?:partnered|partners)\s+with\s+{org2_text}", content_lower):
                    org1.relationships['partner'] = org2.normalized_text
                    org2.relationships['partner'] = org1.normalized_text
    
    def generate_entity_summary(self, entities: Dict) -> Dict:
        """
        Generate a summary of disambiguated entities for logging/debugging.
        """
        summary = {
            'total_persons': len(entities.get('persons', [])),
            'total_organizations': len(entities.get('organizations', [])),
            'high_confidence_persons': sum(1 for p in entities.get('persons', []) if p.confidence > 0.7),
            'high_confidence_orgs': sum(1 for o in entities.get('organizations', []) if o.confidence > 0.7),
            'entities_with_relationships': sum(1 for e in entities.get('persons', []) + entities.get('organizations', []) if e.relationships),
            'entities_with_subtypes': sum(1 for e in entities.get('persons', []) + entities.get('organizations', []) if e.entity_subtype)
        }
        return summary