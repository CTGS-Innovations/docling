#!/usr/bin/env python3
"""
Enhanced Semantic Fact Extractor with Entity Disambiguation
=============================================================
Builds on the base semantic extractor to create more accurate, atomic facts
through proper entity disambiguation and normalization.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import re

# Import entity disambiguator
from .entity_disambiguator import EntityDisambiguator, DisambiguatedEntity

# Import base semantic extractor
sys.path.append(str(Path(__file__).parent.parent))
try:
    from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
except ImportError:
    SemanticFactExtractor = None

# Import logging
from .logging_config import get_fusion_logger

@dataclass
class AtomicFact:
    """
    Atomic, sourceable fact structure for founder intelligence.
    
    Each fact is a single, verifiable statement with clear attribution.
    """
    fact_id: str
    fact_type: str  # MarketSize, InvestmentRound, Acquisition, etc.
    subject: str  # Primary entity (normalized)
    subject_type: str  # PERSON, ORG, etc.
    predicate: str  # Action/relationship verb
    object: str  # Target of action/relationship
    object_type: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)  # Additional context
    source: Dict[str, Any] = field(default_factory=dict)  # Source location
    confidence: float = 0.5
    timestamp: Optional[str] = None
    
class EnhancedSemanticExtractor:
    """
    Enhanced semantic extraction with entity disambiguation.
    
    Key improvements:
    1. Uses disambiguated entities for accurate fact extraction
    2. Creates atomic facts (single subject-predicate-object)
    3. Normalizes entities across facts for better aggregation
    4. Tracks entity relationships and roles
    """
    
    def __init__(self):
        self.logger = get_fusion_logger(__name__)
        self.disambiguator = EntityDisambiguator()
        
        # Initialize base extractor if available
        if SemanticFactExtractor:
            self.base_extractor = SemanticFactExtractor()
        else:
            self.base_extractor = None
            self.logger.warning("Base SemanticFactExtractor not available")
        
        # Founder intelligence fact patterns
        self.fact_patterns = {
            'investment_round': [
                r'(?P<company>[\w\s]+)\s+(?:raised|raises|closed|closes)\s+\$?(?P<amount>[\d.,]+\s*[BMK]?)\s+(?:Series\s+)?(?P<round>[A-E]|seed|pre-seed)',
                r'(?P<investor>[\w\s]+)\s+(?:invested|invests)\s+\$?(?P<amount>[\d.,]+\s*[BMK]?)\s+in\s+(?P<company>[\w\s]+)',
            ],
            'acquisition': [
                r'(?P<acquirer>[\w\s]+)\s+(?:acquired|acquires|bought|buys)\s+(?P<target>[\w\s]+)\s+for\s+\$?(?P<amount>[\d.,]+\s*[BMK]?)',
                r'(?P<target>[\w\s]+)\s+(?:acquired|sold)\s+(?:by|to)\s+(?P<acquirer>[\w\s]+)',
            ],
            'market_size': [
                r'(?P<market>[\w\s]+)\s+market\s+(?:valued|worth)\s+(?:at\s+)?\$?(?P<size>[\d.,]+\s*[BMK]?)',
                r'\$?(?P<size>[\d.,]+\s*[BMK]?)\s+(?P<market>[\w\s]+)\s+market',
            ],
            'growth_metric': [
                r'(?P<subject>[\w\s]+)\s+(?:grew|growing)\s+(?P<rate>[\d.]+%)\s+(?:YoY|annually|per\s+year)',
                r'(?P<rate>[\d.]+%)\s+(?:growth|CAGR)\s+(?:for|in)\s+(?P<subject>[\w\s]+)',
            ],
            'leadership_change': [
                r'(?P<person>[\w\s]+)\s+(?:named|appointed|promoted)\s+(?:as\s+)?(?P<role>CEO|CTO|CFO|President|VP)\s+(?:of|at)\s+(?P<company>[\w\s]+)',
                r'(?P<company>[\w\s]+)\s+(?:hires|hired|appoints)\s+(?P<person>[\w\s]+)\s+as\s+(?P<role>[\w\s]+)',
            ],
            'product_launch': [
                r'(?P<company>[\w\s]+)\s+(?:launched|launches|released|releases)\s+(?P<product>[\w\s]+)',
                r'(?P<product>[\w\s]+)\s+(?:launched|released)\s+by\s+(?P<company>[\w\s]+)',
            ],
            'partnership': [
                r'(?P<company1>[\w\s]+)\s+(?:partners|partnered)\s+with\s+(?P<company2>[\w\s]+)',
                r'(?:partnership|collaboration)\s+between\s+(?P<company1>[\w\s]+)\s+and\s+(?P<company2>[\w\s]+)',
            ]
        }
    
    def extract_enhanced_facts(self, content: str, entities: Dict[str, List], 
                              classification_data: Dict = None) -> Dict[str, Any]:
        """
        Main extraction pipeline with entity disambiguation.
        
        Args:
            content: Document content
            entities: Raw entities from extraction
            classification_data: Document classification metadata
            
        Returns:
            Dictionary containing atomic facts and entity information
        """
        # Step 1: Disambiguate entities
        self.logger.entity("🔍 Disambiguating entities...")
        disambiguated = self.disambiguator.disambiguate_entities(entities, content)
        
        # Log disambiguation summary
        summary = self.disambiguator.generate_entity_summary(disambiguated)
        self.logger.entity(f"✅ Disambiguated: {summary['total_persons']} persons, {summary['total_organizations']} orgs")
        self.logger.entity(f"   High confidence: {summary['high_confidence_persons']} persons, {summary['high_confidence_orgs']} orgs")
        self.logger.entity(f"   With relationships: {summary['entities_with_relationships']} entities")
        
        # Step 2: Extract atomic facts using disambiguated entities
        atomic_facts = self._extract_atomic_facts(content, disambiguated)
        
        # Step 3: Extract founder intelligence facts
        founder_facts = self._extract_founder_facts(content, disambiguated)
        
        # Step 4: Normalize and deduplicate facts
        all_facts = atomic_facts + founder_facts
        normalized_facts = self._normalize_facts(all_facts, disambiguated)
        
        # Step 5: Build structured output
        result = {
            'entities': {
                'persons': [self._entity_to_dict(e) for e in disambiguated.get('persons', [])],
                'organizations': [self._entity_to_dict(e) for e in disambiguated.get('organizations', [])],
            },
            'entity_summary': summary,
            'facts': {
                'atomic_facts': [self._fact_to_dict(f) for f in normalized_facts],
                'total_facts': len(normalized_facts),
                'fact_types': self._count_fact_types(normalized_facts),
            },
            'founder_intelligence': self._organize_founder_intelligence(normalized_facts, disambiguated)
        }
        
        return result
    
    def _extract_atomic_facts(self, content: str, entities: Dict) -> List[AtomicFact]:
        """
        Extract basic atomic facts from content and entities.
        
        Creates simple subject-predicate-object triplets.
        """
        facts = []
        fact_counter = 0
        
        # Extract person-organization relationships
        for person in entities.get('persons', []):
            if person.relationships:
                for rel_type, rel_target in person.relationships.items():
                    fact = AtomicFact(
                        fact_id=f"fact_{fact_counter:04d}",
                        fact_type='PersonOrgRelation',
                        subject=person.normalized_text,
                        subject_type='PERSON',
                        predicate=rel_type.replace('_', ' '),
                        object=rel_target,
                        object_type='ORG',
                        confidence=person.confidence,
                        source={'extracted_from': 'entity_relationships'}
                    )
                    facts.append(fact)
                    fact_counter += 1
        
        # Extract organization relationships
        for org in entities.get('organizations', []):
            if org.relationships:
                for rel_type, rel_target in org.relationships.items():
                    # Skip reverse person relationships
                    if rel_type.startswith('has_person_'):
                        continue
                    
                    fact = AtomicFact(
                        fact_id=f"fact_{fact_counter:04d}",
                        fact_type='OrgRelation',
                        subject=org.normalized_text,
                        subject_type='ORG',
                        predicate=rel_type.replace('_', ' '),
                        object=rel_target,
                        object_type='ORG',
                        confidence=org.confidence,
                        source={'extracted_from': 'entity_relationships'}
                    )
                    facts.append(fact)
                    fact_counter += 1
        
        return facts
    
    def _extract_founder_facts(self, content: str, entities: Dict) -> List[AtomicFact]:
        """
        Extract founder-specific intelligence facts.
        
        Uses patterns for investment, acquisition, growth metrics, etc.
        """
        facts = []
        fact_counter = 1000  # Different range for founder facts
        
        # Build entity lookup for normalization
        entity_lookup = self._build_entity_lookup(entities)
        
        for fact_type, patterns in self.fact_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    fact = self._create_fact_from_match(
                        match, fact_type, entity_lookup, fact_counter
                    )
                    if fact:
                        facts.append(fact)
                        fact_counter += 1
        
        return facts
    
    def _create_fact_from_match(self, match, fact_type: str, 
                                entity_lookup: Dict, fact_id: int) -> Optional[AtomicFact]:
        """
        Create an atomic fact from a regex match.
        
        Normalizes entities and extracts context.
        """
        groups = match.groupdict()
        
        # Map fact types to extraction logic
        if fact_type == 'investment_round':
            if 'company' in groups and 'amount' in groups:
                company = self._normalize_with_lookup(groups['company'], entity_lookup, 'ORG')
                return AtomicFact(
                    fact_id=f"fact_{fact_id:04d}",
                    fact_type='InvestmentRound',
                    subject=company,
                    subject_type='ORG',
                    predicate='raised',
                    object=groups['amount'].strip(),
                    context={
                        'round': groups.get('round', '').strip(),
                        'investor': groups.get('investor', '').strip()
                    },
                    confidence=0.85,
                    source={'text': match.group(0), 'span': (match.start(), match.end())}
                )
        
        elif fact_type == 'acquisition':
            if 'acquirer' in groups and 'target' in groups:
                acquirer = self._normalize_with_lookup(groups['acquirer'], entity_lookup, 'ORG')
                target = self._normalize_with_lookup(groups['target'], entity_lookup, 'ORG')
                return AtomicFact(
                    fact_id=f"fact_{fact_id:04d}",
                    fact_type='Acquisition',
                    subject=acquirer,
                    subject_type='ORG',
                    predicate='acquired',
                    object=target,
                    object_type='ORG',
                    context={'amount': groups.get('amount', '').strip()},
                    confidence=0.9,
                    source={'text': match.group(0), 'span': (match.start(), match.end())}
                )
        
        elif fact_type == 'market_size':
            if 'market' in groups and 'size' in groups:
                return AtomicFact(
                    fact_id=f"fact_{fact_id:04d}",
                    fact_type='MarketSize',
                    subject=groups['market'].strip(),
                    subject_type='MARKET',
                    predicate='valued at',
                    object=groups['size'].strip(),
                    confidence=0.75,
                    source={'text': match.group(0), 'span': (match.start(), match.end())}
                )
        
        elif fact_type == 'leadership_change':
            if 'person' in groups and 'company' in groups and 'role' in groups:
                person = self._normalize_with_lookup(groups['person'], entity_lookup, 'PERSON')
                company = self._normalize_with_lookup(groups['company'], entity_lookup, 'ORG')
                return AtomicFact(
                    fact_id=f"fact_{fact_id:04d}",
                    fact_type='LeadershipChange',
                    subject=person,
                    subject_type='PERSON',
                    predicate='appointed as',
                    object=groups['role'].strip(),
                    context={'company': company},
                    confidence=0.85,
                    source={'text': match.group(0), 'span': (match.start(), match.end())}
                )
        
        elif fact_type == 'partnership':
            if 'company1' in groups and 'company2' in groups:
                company1 = self._normalize_with_lookup(groups['company1'], entity_lookup, 'ORG')
                company2 = self._normalize_with_lookup(groups['company2'], entity_lookup, 'ORG')
                return AtomicFact(
                    fact_id=f"fact_{fact_id:04d}",
                    fact_type='Partnership',
                    subject=company1,
                    subject_type='ORG',
                    predicate='partnered with',
                    object=company2,
                    object_type='ORG',
                    confidence=0.8,
                    source={'text': match.group(0), 'span': (match.start(), match.end())}
                )
        
        return None
    
    def _normalize_with_lookup(self, text: str, entity_lookup: Dict, expected_type: str) -> str:
        """
        Normalize entity text using disambiguated entity lookup.
        
        Returns normalized form if found, otherwise cleans the text.
        """
        text_lower = text.strip().lower()
        
        # Check if we have this entity in our lookup
        if text_lower in entity_lookup:
            entity = entity_lookup[text_lower]
            # Verify it's the expected type
            if entity.entity_type == expected_type:
                return entity.normalized_text
        
        # Not found - do basic normalization
        return ' '.join(text.strip().split())
    
    def _build_entity_lookup(self, entities: Dict) -> Dict[str, DisambiguatedEntity]:
        """
        Build lookup dictionary for quick entity normalization.
        
        Maps lowercase text to disambiguated entity objects.
        """
        lookup = {}
        
        for entity_list in entities.values():
            for entity in entity_list:
                # Add original text
                lookup[entity.original_text.lower()] = entity
                # Add normalized text
                lookup[entity.normalized_text.lower()] = entity
                # Add aliases
                for alias in entity.aliases:
                    lookup[alias.lower()] = entity
        
        return lookup
    
    def _normalize_facts(self, facts: List[AtomicFact], entities: Dict) -> List[AtomicFact]:
        """
        Normalize and deduplicate facts.
        
        Ensures consistent entity references across facts.
        """
        # Build entity lookup
        entity_lookup = self._build_entity_lookup(entities)
        
        # Normalize entity references in facts
        for fact in facts:
            # Normalize subject
            if fact.subject:
                subject_lower = fact.subject.lower()
                if subject_lower in entity_lookup:
                    entity = entity_lookup[subject_lower]
                    fact.subject = entity.normalized_text
                    fact.confidence = max(fact.confidence, entity.confidence)
            
            # Normalize object if it's an entity
            if fact.object and fact.object_type in ['PERSON', 'ORG']:
                object_lower = fact.object.lower()
                if object_lower in entity_lookup:
                    entity = entity_lookup[object_lower]
                    fact.object = entity.normalized_text
            
            # Normalize context entities
            if fact.context:
                for key, value in fact.context.items():
                    if isinstance(value, str):
                        value_lower = value.lower()
                        if value_lower in entity_lookup:
                            fact.context[key] = entity_lookup[value_lower].normalized_text
        
        # Remove duplicate facts
        seen = set()
        unique_facts = []
        for fact in facts:
            # Create fact signature
            signature = f"{fact.fact_type}:{fact.subject}:{fact.predicate}:{fact.object}"
            if signature not in seen:
                seen.add(signature)
                unique_facts.append(fact)
        
        return unique_facts
    
    def _organize_founder_intelligence(self, facts: List[AtomicFact], entities: Dict) -> Dict:
        """
        Organize facts into founder intelligence clusters.
        
        Groups facts by the 12 market intelligence areas.
        """
        clusters = {
            'market_opportunity': [],
            'capital_flows': [],
            'competitive_landscape': [],
            'user_pain_points': [],
            'technical_innovation': [],
            'talent_signals': [],
            'regulatory_landscape': [],
            'exit_landscape': [],
            'scaling_pathways': [],
            'partnership_ecosystem': [],
            'product_development': [],
            'operational_excellence': []
        }
        
        # Map fact types to clusters
        fact_mapping = {
            'MarketSize': 'market_opportunity',
            'InvestmentRound': 'capital_flows',
            'Acquisition': 'exit_landscape',
            'Partnership': 'partnership_ecosystem',
            'LeadershipChange': 'talent_signals',
            'ProductLaunch': 'product_development',
            'GrowthMetric': 'scaling_pathways',
        }
        
        for fact in facts:
            cluster = fact_mapping.get(fact.fact_type)
            if cluster and cluster in clusters:
                clusters[cluster].append(self._fact_to_dict(fact))
        
        # Add entity-based insights
        clusters['key_entities'] = {
            'top_persons': self._get_top_entities(entities.get('persons', []), 5),
            'top_organizations': self._get_top_entities(entities.get('organizations', []), 5)
        }
        
        return clusters
    
    def _get_top_entities(self, entities: List[DisambiguatedEntity], limit: int) -> List[Dict]:
        """Get top entities by confidence and relationship count."""
        # Sort by confidence and relationship count
        sorted_entities = sorted(
            entities,
            key=lambda e: (e.confidence, len(e.relationships)),
            reverse=True
        )[:limit]
        
        return [
            {
                'name': e.normalized_text,
                'type': e.entity_type,
                'subtype': e.entity_subtype,
                'confidence': e.confidence,
                'relationships': list(e.relationships.keys())
            }
            for e in sorted_entities
        ]
    
    def _entity_to_dict(self, entity: DisambiguatedEntity) -> Dict:
        """Convert entity to dictionary for JSON serialization."""
        return {
            'original_text': entity.original_text,
            'normalized_text': entity.normalized_text,
            'type': entity.entity_type,
            'subtype': entity.entity_subtype,
            'confidence': entity.confidence,
            'aliases': list(entity.aliases),
            'relationships': entity.relationships,
            'mention_count': len(entity.contexts)
        }
    
    def _fact_to_dict(self, fact: AtomicFact) -> Dict:
        """Convert fact to dictionary for JSON serialization."""
        return {
            'fact_id': fact.fact_id,
            'type': fact.fact_type,
            'subject': fact.subject,
            'subject_type': fact.subject_type,
            'predicate': fact.predicate,
            'object': fact.object,
            'object_type': fact.object_type,
            'context': fact.context,
            'confidence': fact.confidence,
            'source': fact.source
        }
    
    def _count_fact_types(self, facts: List[AtomicFact]) -> Dict[str, int]:
        """Count facts by type."""
        type_counts = {}
        for fact in facts:
            type_counts[fact.fact_type] = type_counts.get(fact.fact_type, 0) + 1
        return type_counts