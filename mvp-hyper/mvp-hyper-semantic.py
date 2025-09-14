#!/usr/bin/env python3
"""
MVP Hyper Semantic Extractor
============================
Local, CPU-based knowledge extraction system for MVP Hyper-Core.
Extracts structured facts, entities, and relationships from markdown using
regex, dictionaries, and lightweight NLP - no cloud APIs required.

Performance targets:
- Regex/Dictionary: 2,000-5,000 pages/sec
- spaCy small NLP: 30-100 pages/sec  
- FlashText lookup: 50,000+ matches/sec

Outputs structured metadata as .metadata.json files alongside processed documents.
"""

import re
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import hashlib
import collections
from decimal import Decimal

# Core processing libraries
try:
    import spacy
    from spacy import displacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    print("Warning: spaCy not available, NLP features disabled")

try:
    from flashtext import KeywordProcessor
    HAS_FLASHTEXT = True
except ImportError:
    HAS_FLASHTEXT = False

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


@dataclass
class ExtractedFact:
    """A structured fact extracted from text."""
    fact_id: str                    # Unique ID for this fact
    subject: str                    # Main entity (e.g., "HR1234")
    predicate: str                  # Relationship type (e.g., "appropriates_to")
    object: Optional[str] = None    # Target entity (e.g., "DOE")
    value: Optional[Union[str, int, float, Dict]] = None  # Associated value
    confidence: float = 0.0         # Extraction confidence (0-1)
    source_span: Tuple[int, int] = (0, 0)  # Character positions in source text
    extraction_method: str = "unknown"     # How this fact was extracted
    metadata: Dict[str, Any] = None        # Additional context


@dataclass
class ExtractedEntity:
    """A named entity extracted from text."""
    entity_id: str                  # Canonical ID
    text: str                       # Original text span
    entity_type: str                # PERSON, ORG, MONEY, DATE, etc.
    aliases: List[str] = None       # Alternative forms
    confidence: float = 0.0         # Recognition confidence
    source_span: Tuple[int, int] = (0, 0)
    metadata: Dict[str, Any] = None
    extraction_method: str = "unknown"  # How this entity was extracted


@dataclass
class SemanticMetadata:
    """Complete semantic metadata for a document."""
    document_path: str
    facts: List[ExtractedFact]
    entities: List[ExtractedEntity]
    relationships: List[Dict[str, Any]]
    extraction_stats: Dict[str, Any]
    processing_time: float
    timestamp: str
    file_hash: str


class EntityType(Enum):
    """Common entity types for extraction."""
    PERSON = "PERSON"
    ORGANIZATION = "ORG"
    MONEY = "MONEY"
    DATE = "DATE"
    BILL = "BILL"
    COMMITTEE = "COMMITTEE"
    LOCATION = "GPE"
    LAW = "LAW"
    VOTE = "VOTE"
    AMOUNT = "QUANTITY"


class FactType(Enum):
    """Common fact/relationship types."""
    INTRODUCED_BY = "introduced_by"
    SPONSORED_BY = "sponsored_by"
    APPROPRIATES_TO = "appropriates_to"
    PASSED_IN = "passed_in"
    VOTED_ON = "voted_on"
    REPORTED_BY = "reported_by"
    SIGNED_BY = "signed_by"
    ALLOCATED_TO = "allocated_to"
    APPOINTED_TO = "appointed_to"
    ASSOCIATED_WITH = "associated_with"


class MVPHyperSemanticExtractor:
    """Ultra-fast local knowledge extraction engine."""
    
    def __init__(self, 
                 enable_spacy: bool = True,
                 spacy_model: str = "en_core_web_sm",
                 cache_enabled: bool = True):
        
        self.enable_spacy = enable_spacy and HAS_SPACY
        self.cache_enabled = cache_enabled
        self.extraction_cache = {}
        
        # Initialize spaCy if available
        self.nlp = None
        if self.enable_spacy:
            try:
                self.nlp = spacy.load(spacy_model)
                # Disable unnecessary components for speed
                self.nlp.disable_pipes(["parser", "tagger", "lemmatizer"])
            except OSError:
                print(f"Warning: spaCy model '{spacy_model}' not found, using regex only")
                self.enable_spacy = False
        
        # Initialize FlashText processor
        self.keyword_processor = None
        if HAS_FLASHTEXT:
            self.keyword_processor = KeywordProcessor(case_sensitive=False)
            self._load_gazetteers()
        
        # Pre-compiled regex patterns for common extractions
        self.patterns = self._compile_extraction_patterns()
        
        # Entity gazetteers (can be expanded)
        self.gazetteers = self._load_entity_gazetteers()
    
    def _compile_extraction_patterns(self) -> Dict[str, re.Pattern]:
        """Compile high-performance regex patterns for domain-specific extractions."""
        
        return {
            # Legislative patterns
            'bill_ids': re.compile(r'\b([HS]\.?[RJ]\.?\s*\d+)\b', re.I),
            'congress_session': re.compile(r'\b(\d{2,3})(st|nd|rd|th)\s+Congress\b', re.I),
            
            # Money amounts
            'money': re.compile(r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(million|billion|trillion|M|B|T)?\b', re.I),
            'appropriation': re.compile(r'appropriat\w*\s+\$?([\d,]+(?:\.\d{2})?)\s*(million|billion|M|B)?\b', re.I),
            
            # Dates and times
            'dates': re.compile(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2}, \d{4}|January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b', re.I),
            'fiscal_year': re.compile(r'\bFY\s*(\d{4})\b', re.I),
            
            # Safety and regulatory patterns
            'osha_numbers': re.compile(r'\bOSHA\s+(\d+)[-.]?(\d+)?\b', re.I),
            'safety_requirements': re.compile(r'\b(must|shall|required to|should)\s+(.{10,100}?)(?:\.|\n)', re.I),
            'hazard_types': re.compile(r'\b(hazard|risk|danger|threat|violence|injury|accident|incident)\s*:?\s*([^.\n]{10,80})', re.I),
            'compliance_standards': re.compile(r'\b(standard|regulation|guideline|policy|procedure)\s+(\d+[-.]?\d*)\b', re.I),
            'safety_controls': re.compile(r'\b(control|prevent|protect|reduce|eliminate|mitigate)\s+(.{10,80})(?:by|through|with)', re.I),
            
            # Technical patterns
            'specifications': re.compile(r'\bspecification[s]?\s*:?\s*([^.\n]{10,100})', re.I),
            'procedures': re.compile(r'\bprocedure[s]?\s*:?\s*([^.\n]{10,100})', re.I),
            'requirements': re.compile(r'\brequirement[s]?\s*:?\s*([^.\n]{10,100})', re.I),
            
            # Business patterns
            'policies': re.compile(r'\bpolicy\s*:?\s*([^.\n]{10,100})', re.I),
            'objectives': re.compile(r'\bobjective[s]?\s*:?\s*([^.\n]{10,100})', re.I),
            'responsibilities': re.compile(r'\bresponsibilit[y|ies]+\s*:?\s*([^.\n]{10,100})', re.I),
            
            # Votes
            'vote_counts': re.compile(r'\b(\d+)[–-](\d+)\b'),
            'vote_results': re.compile(r'\bpassed.*?(\d+)[–-](\d+)\b', re.I),
            
            # People and titles
            'representatives': re.compile(r'\b(Rep\.|Representative|Sen\.|Senator)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(([DR])-([A-Z]{2})\)', re.I),
            'titles': re.compile(r'\b(Chairman|Chairwoman|Secretary|Director|Administrator|Commissioner)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.I),
            
            # Organizations and agencies
            'committees': re.compile(r'\b(Committee on|Subcommittee on)\s+([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+)*)\b'),
            'agencies': re.compile(r'\b(Department of|Agency|Bureau of|Office of)\s+([A-Z][a-z]+(?:\s+(?:and\s+)?[A-Z][a-z]+)*)\b'),
            'government_orgs': re.compile(r'\b(OSHA|EPA|FDA|CDC|NIH|DOL|HHS|NIOSH)\b'),
            
            # Actions and procedures
            'introduced': re.compile(r'\bintroduced\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},?\s+\d{4})\b', re.I),
            'reported': re.compile(r'\breported\s+by\s+(?:the\s+)?(.+?)\s+(?:on|and)\b', re.I),
            'passed': re.compile(r'\bpassed\s+(?:the\s+)?(House|Senate)(?:\s+with\s+a\s+vote\s+of\s+(\d+)[–-](\d+))?\b', re.I),
            
            # Email and contact info
            'emails': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
            'websites': re.compile(r'\bwww\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'),
        }
    
    def _load_entity_gazetteers(self) -> Dict[str, Set[str]]:
        """Load entity gazetteers for fast lookup."""
        
        return {
            'agencies': {
                'DOE', 'Department of Energy', 'Energy Department',
                'DOD', 'Department of Defense', 'Defense Department',
                'HHS', 'Department of Health and Human Services',
                'DOJ', 'Department of Justice', 'Justice Department',
                'DHS', 'Department of Homeland Security',
                'EPA', 'Environmental Protection Agency',
                'FDA', 'Food and Drug Administration',
                'CDC', 'Centers for Disease Control',
                'NIH', 'National Institutes of Health',
                'NASA', 'National Aeronautics and Space Administration',
                'DOT', 'Department of Transportation',
                'DOL', 'Department of Labor',
                'Treasury', 'Department of Treasury',
                'State', 'Department of State',
                'USDA', 'Department of Agriculture',
            },
            
            'committees': {
                'House Committee on Appropriations',
                'Senate Committee on Appropriations', 
                'House Committee on Energy and Commerce',
                'Senate Committee on Energy and Natural Resources',
                'House Committee on Ways and Means',
                'Senate Finance Committee',
                'House Committee on Armed Services',
                'Senate Armed Services Committee',
                'House Committee on Judiciary',
                'Senate Judiciary Committee',
            },
            
            'states': {
                'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
            }
        }
    
    def _load_gazetteers(self):
        """Load gazetteers into FlashText for ultra-fast lookup."""
        if not self.keyword_processor:
            return
        
        # Add agencies with aliases
        agencies = [
            ('Department of Energy', ['DOE', 'Energy Department']),
            ('Department of Defense', ['DOD', 'Defense Department', 'Pentagon']),
            ('Environmental Protection Agency', ['EPA']),
            ('Food and Drug Administration', ['FDA']),
            # Add more as needed
        ]
        
        for canonical, aliases in agencies:
            self.keyword_processor.add_keyword(canonical, canonical)
            for alias in aliases:
                self.keyword_processor.add_keyword(alias, canonical)
    
    def extract_semantic_metadata(self, file_path: Path, content: str) -> SemanticMetadata:
        """Extract comprehensive semantic metadata from document content."""
        
        start_time = time.time()
        
        # Generate cache key
        cache_key = self._generate_cache_key(file_path, content)
        if self.cache_enabled and cache_key in self.extraction_cache:
            cached = self.extraction_cache[cache_key]
            cached.processing_time = 0.0  # Cached result
            return cached
        
        # Initialize extraction containers
        facts = []
        entities = []
        relationships = []
        stats = {'extraction_methods_used': []}
        
        # 1. Fast regex extraction (2,000-5,000 pages/sec)
        regex_facts, regex_entities = self._extract_with_regex(content)
        facts.extend(regex_facts)
        entities.extend(regex_entities)
        stats['extraction_methods_used'].append('regex')
        stats['regex_facts'] = len(regex_facts)
        stats['regex_entities'] = len(regex_entities)
        
        # 2. FlashText dictionary lookup (50,000+ matches/sec)
        if self.keyword_processor:
            dict_entities = self._extract_with_dictionaries(content)
            entities.extend(dict_entities)
            stats['extraction_methods_used'].append('flashtext')
            stats['dict_entities'] = len(dict_entities)
        
        # 3. spaCy NLP extraction (30-100 pages/sec)
        if self.enable_spacy and self.nlp:
            nlp_facts, nlp_entities = self._extract_with_spacy(content)
            facts.extend(nlp_facts)
            entities.extend(nlp_entities)
            stats['extraction_methods_used'].append('spacy')
            stats['nlp_facts'] = len(nlp_facts)
            stats['nlp_entities'] = len(nlp_entities)
        
        # 4. Build relationships from facts
        relationships = self._build_relationships(facts)
        stats['relationships'] = len(relationships)
        
        # 5. Deduplicate and merge entities
        entities = self._deduplicate_entities(entities)
        stats['final_entities'] = len(entities)
        stats['final_facts'] = len(facts)
        
        processing_time = time.time() - start_time
        
        # Create metadata object
        metadata = SemanticMetadata(
            document_path=str(file_path),
            facts=facts,
            entities=entities,
            relationships=relationships,
            extraction_stats=stats,
            processing_time=processing_time,
            timestamp=datetime.now(timezone.utc).isoformat(),
            file_hash=cache_key[:16]
        )
        
        # Cache result
        if self.cache_enabled:
            self.extraction_cache[cache_key] = metadata
        
        return metadata
    
    def _extract_with_regex(self, content: str) -> Tuple[List[ExtractedFact], List[ExtractedEntity]]:
        """Ultra-fast regex-based extraction - 2,000-5,000 pages/sec with domain-specific patterns."""
        
        facts = []
        entities = []
        
        # First classify document type to determine extraction focus
        doc_type = self._classify_document_domain(content)
        
        # Common extractions for all document types
        
        # Extract government organizations
        for match in self.patterns['government_orgs'].finditer(content):
            org_name = match.group(1)
            entities.append(ExtractedEntity(
                entity_id=f"gov_org_{org_name.lower()}",
                text=match.group(0),
                entity_type=EntityType.ORGANIZATION.value,
                confidence=0.95,
                source_span=match.span(),
                metadata={'org_type': 'government', 'canonical_name': org_name},
                extraction_method="regex"
            ))
        
        # Extract dates
        for match in self.patterns['dates'].finditer(content):
            date_text = match.group(0)
            entities.append(ExtractedEntity(
                entity_id=f"date_{hash(date_text) % 10000}",
                text=date_text,
                entity_type=EntityType.DATE.value,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        # Extract websites and contact info
        for match in self.patterns['websites'].finditer(content):
            entities.append(ExtractedEntity(
                entity_id=f"website_{hash(match.group(0)) % 10000}",
                text=match.group(0),
                entity_type="WEBSITE",
                confidence=0.9,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        for match in self.patterns['phone'].finditer(content):
            phone = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
            entities.append(ExtractedEntity(
                entity_id=f"phone_{phone.replace('-', '')}",
                text=match.group(0),
                entity_type="PHONE",
                confidence=0.9,
                source_span=match.span(),
                metadata={'formatted_phone': phone},
                extraction_method="regex"
            ))
        
        # Domain-specific extractions based on document type
        if doc_type == "safety":
            self._extract_safety_facts(content, facts, entities)
        elif doc_type == "technical":
            self._extract_technical_facts(content, facts, entities)
        elif doc_type == "business":
            self._extract_business_facts(content, facts, entities)
        elif doc_type == "legislative":
            self._extract_legislative_facts(content, facts, entities)
        else:
            # General extraction for unknown types
            self._extract_general_facts(content, facts, entities)
        
        return facts, entities
    
    def _classify_document_domain(self, content: str) -> str:
        """Classify document domain to determine extraction patterns."""
        content_lower = content.lower()
        
        # Safety document indicators
        safety_keywords = ['osha', 'safety', 'hazard', 'workplace violence', 'injury', 'accident', 'ppe', 'occupational']
        safety_score = sum(1 for kw in safety_keywords if kw in content_lower)
        
        # Technical document indicators  
        tech_keywords = ['specification', 'procedure', 'technical', 'system', 'implementation', 'configuration']
        tech_score = sum(1 for kw in tech_keywords if kw in content_lower)
        
        # Business document indicators
        business_keywords = ['policy', 'strategy', 'business', 'management', 'corporate', 'objective']
        business_score = sum(1 for kw in business_keywords if kw in content_lower)
        
        # Legislative document indicators
        legislative_keywords = ['bill', 'congress', 'senate', 'house', 'appropriation', 'vote']
        legislative_score = sum(1 for kw in legislative_keywords if kw in content_lower)
        
        # Return the domain with highest score
        scores = {
            'safety': safety_score,
            'technical': tech_score, 
            'business': business_score,
            'legislative': legislative_score
        }
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _extract_safety_facts(self, content: str, facts: List[ExtractedFact], entities: List[ExtractedEntity]):
        """Extract safety-specific facts and entities."""
        
        # Extract OSHA numbers
        for match in self.patterns['osha_numbers'].finditer(content):
            osha_num = match.group(1)
            if match.group(2):
                osha_num += f"-{match.group(2)}"
            
            entities.append(ExtractedEntity(
                entity_id=f"osha_{osha_num}",
                text=match.group(0),
                entity_type="REGULATION",
                confidence=0.95,
                source_span=match.span(),
                metadata={'regulation_type': 'OSHA', 'number': osha_num},
                extraction_method="regex"
            ))
        
        # Extract safety requirements
        for match in self.patterns['safety_requirements'].finditer(content):
            requirement_text = match.group(2).strip()
            facts.append(ExtractedFact(
                fact_id=f"safety_req_{hash(requirement_text) % 10000}",
                subject="safety_compliance",
                predicate="requires",
                value=requirement_text,
                confidence=0.8,
                source_span=match.span(),
                metadata={'requirement_type': match.group(1).lower()},
                extraction_method="regex"
            ))
        
        # Extract hazard types
        for match in self.patterns['hazard_types'].finditer(content):
            hazard_type = match.group(1)
            description = match.group(2).strip()
            
            facts.append(ExtractedFact(
                fact_id=f"hazard_{hash(description) % 10000}",
                subject="workplace_safety",
                predicate="identifies_hazard",
                object=hazard_type,
                value=description,
                confidence=0.85,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        # Extract safety controls
        for match in self.patterns['safety_controls'].finditer(content):
            control_action = match.group(1)
            control_description = match.group(2).strip()
            
            facts.append(ExtractedFact(
                fact_id=f"control_{hash(control_description) % 10000}",
                subject="safety_control",
                predicate=f"control_action_{control_action.lower()}",
                value=control_description,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
    
    def _extract_technical_facts(self, content: str, facts: List[ExtractedFact], entities: List[ExtractedEntity]):
        """Extract technical document facts."""
        
        # Extract specifications
        for match in self.patterns['specifications'].finditer(content):
            spec_text = match.group(1).strip()
            facts.append(ExtractedFact(
                fact_id=f"spec_{hash(spec_text) % 10000}",
                subject="technical_specification",
                predicate="specifies",
                value=spec_text,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        # Extract procedures
        for match in self.patterns['procedures'].finditer(content):
            procedure_text = match.group(1).strip()
            facts.append(ExtractedFact(
                fact_id=f"proc_{hash(procedure_text) % 10000}",
                subject="technical_procedure",
                predicate="defines_procedure",
                value=procedure_text,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
    
    def _extract_business_facts(self, content: str, facts: List[ExtractedFact], entities: List[ExtractedEntity]):
        """Extract business document facts."""
        
        # Extract policies
        for match in self.patterns['policies'].finditer(content):
            policy_text = match.group(1).strip()
            facts.append(ExtractedFact(
                fact_id=f"policy_{hash(policy_text) % 10000}",
                subject="business_policy",
                predicate="establishes_policy",
                value=policy_text,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        # Extract objectives
        for match in self.patterns['objectives'].finditer(content):
            objective_text = match.group(1).strip()
            facts.append(ExtractedFact(
                fact_id=f"obj_{hash(objective_text) % 10000}",
                subject="business_objective",
                predicate="defines_objective",
                value=objective_text,
                confidence=0.8,
                source_span=match.span(),
                extraction_method="regex"
            ))
    
    def _extract_legislative_facts(self, content: str, facts: List[ExtractedFact], entities: List[ExtractedEntity]):
        """Extract legislative document facts."""
        
        # Extract bill information and related facts
        for match in self.patterns['bill_ids'].finditer(content):
            bill_id = match.group(1).upper().replace(' ', '').replace('.', '')
            entities.append(ExtractedEntity(
                entity_id=f"bill_{bill_id}",
                text=match.group(0),
                entity_type=EntityType.BILL.value,
                confidence=0.9,
                source_span=match.span(),
                extraction_method="regex"
            ))
        
        # Extract representatives and senators
        for match in self.patterns['representatives'].finditer(content):
            title = match.group(1)
            name = match.group(2)
            party = match.group(3)
            state = match.group(4)
            
            person_id = name.replace(' ', '_').lower()
            entities.append(ExtractedEntity(
                entity_id=f"person_{person_id}",
                text=match.group(0),
                entity_type=EntityType.PERSON.value,
                confidence=0.9,
                source_span=match.span(),
                metadata={
                    'title': title,
                    'party': party,
                    'state': state,
                    'name': name
                },
                extraction_method="regex"
            ))
    
    def _extract_general_facts(self, content: str, facts: List[ExtractedFact], entities: List[ExtractedEntity]):
        """Extract general facts when document type is unclear."""
        
        # Extract money amounts
        for match in self.patterns['money'].finditer(content):
            amount_str = match.group(1).replace(',', '')
            multiplier = match.group(2)
            
            try:
                amount = float(amount_str)
                if multiplier:
                    multipliers = {'million': 1e6, 'M': 1e6, 'billion': 1e9, 'B': 1e9, 'trillion': 1e12, 'T': 1e12}
                    amount *= multipliers.get(multiplier.lower(), 1)
                
                entities.append(ExtractedEntity(
                    entity_id=f"money_{int(amount)}",
                    text=match.group(0),
                    entity_type=EntityType.MONEY.value,
                    confidence=0.95,
                    source_span=match.span(),
                    metadata={'amount_usd': int(amount)},
                    extraction_method="regex"
                ))
            except ValueError:
                continue
        
        # Extract general requirements
        for match in self.patterns['requirements'].finditer(content):
            req_text = match.group(1).strip()
            facts.append(ExtractedFact(
                fact_id=f"req_{hash(req_text) % 10000}",
                subject="general_requirement",
                predicate="states_requirement",
                value=req_text,
                confidence=0.7,
                source_span=match.span(),
                extraction_method="regex"
            ))
    
    def _extract_with_dictionaries(self, content: str) -> List[ExtractedEntity]:
        """Ultra-fast dictionary lookup using FlashText - 50,000+ matches/sec."""
        
        entities = []
        
        if not self.keyword_processor:
            return entities
        
        # Extract all keyword matches with positions
        matches = self.keyword_processor.extract_keywords(content, span_info=True)
        
        for canonical_name, start_pos, end_pos in matches:
            # Determine entity type based on gazetteer
            entity_type = EntityType.ORGANIZATION.value  # Default
            
            if canonical_name in self.gazetteers['agencies']:
                entity_type = EntityType.ORGANIZATION.value
            elif canonical_name in self.gazetteers['committees']:
                entity_type = EntityType.COMMITTEE.value
            
            entity_id = canonical_name.lower().replace(' ', '_').replace('of', '').strip('_')
            
            entities.append(ExtractedEntity(
                entity_id=f"org_{entity_id}",
                text=content[start_pos:end_pos],
                entity_type=entity_type,
                confidence=0.9,
                source_span=(start_pos, end_pos),
                metadata={'canonical_name': canonical_name},
                extraction_method="flashtext"
            ))
        
        return entities
    
    def _extract_with_spacy(self, content: str) -> Tuple[List[ExtractedFact], List[ExtractedEntity]]:
        """NLP-based extraction using spaCy - 30-100 pages/sec."""
        
        facts = []
        entities = []
        
        if not self.nlp:
            return facts, entities
        
        # Process text with spaCy (chunked for memory efficiency)
        chunk_size = 10000  # Process in 10k character chunks
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            doc = self.nlp(chunk)
            
            # Extract named entities
            for ent in doc.ents:
                # Map spaCy entity types to our types
                entity_type_map = {
                    'PERSON': EntityType.PERSON.value,
                    'ORG': EntityType.ORGANIZATION.value,
                    'GPE': EntityType.LOCATION.value,
                    'MONEY': EntityType.MONEY.value,
                    'DATE': EntityType.DATE.value,
                }
                
                entity_type = entity_type_map.get(ent.label_, ent.label_)
                entity_id = ent.text.lower().replace(' ', '_')
                
                entities.append(ExtractedEntity(
                    entity_id=f"spacy_{entity_id}",
                    text=ent.text,
                    entity_type=entity_type,
                    confidence=0.7,  # spaCy confidence is typically lower than regex
                    source_span=(i + ent.start_char, i + ent.end_char),
                    metadata={'spacy_label': ent.label_},
                    extraction_method="spacy"
                ))
        
        return facts, entities
    
    def _build_relationships(self, facts: List[ExtractedFact]) -> List[Dict[str, Any]]:
        """Build relationship graph from extracted facts."""
        
        relationships = []
        
        # Group facts by subject to find related entities
        subject_facts = collections.defaultdict(list)
        for fact in facts:
            subject_facts[fact.subject].append(fact)
        
        # Create relationships between entities that share subjects
        for subject, subject_fact_list in subject_facts.items():
            if len(subject_fact_list) > 1:
                for i, fact1 in enumerate(subject_fact_list):
                    for fact2 in subject_fact_list[i+1:]:
                        relationships.append({
                            'source': fact1.fact_id,
                            'target': fact2.fact_id,
                            'relationship_type': 'co_referenced',
                            'subject': subject,
                            'confidence': min(fact1.confidence, fact2.confidence)
                        })
        
        return relationships
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities and merge similar ones."""
        
        if not entities:
            return entities
        
        # Simple deduplication by text similarity
        unique_entities = []
        seen_texts = set()
        
        for entity in entities:
            # Normalize text for comparison
            normalized_text = entity.text.lower().strip()
            
            if normalized_text not in seen_texts:
                seen_texts.add(normalized_text)
                unique_entities.append(entity)
            else:
                # Find existing entity and merge if confidence is higher
                for existing in unique_entities:
                    if existing.text.lower().strip() == normalized_text:
                        if entity.confidence > existing.confidence:
                            # Replace with higher confidence entity
                            idx = unique_entities.index(existing)
                            unique_entities[idx] = entity
                        break
        
        return unique_entities
    
    def _generate_cache_key(self, file_path: Path, content: str) -> str:
        """Generate cache key for extraction results."""
        key_string = f"{file_path.name}:{len(content)}:{content[:500]}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def save_metadata(self, metadata: SemanticMetadata, output_path: Optional[Path] = None) -> Path:
        """Save semantic metadata to .metadata.json file."""
        
        if output_path is None:
            # Generate sidecar filename
            source_path = Path(metadata.document_path)
            output_path = source_path.parent / f"{source_path.stem}.metadata.json"
        
        # Convert to JSON-serializable format
        metadata_dict = {
            'document_path': metadata.document_path,
            'facts': [asdict(fact) for fact in metadata.facts],
            'entities': [asdict(entity) for entity in metadata.entities],
            'relationships': metadata.relationships,
            'extraction_stats': metadata.extraction_stats,
            'processing_time': metadata.processing_time,
            'timestamp': metadata.timestamp,
            'file_hash': metadata.file_hash,
            'extraction_version': '1.0.0'
        }
        
        # Write JSON with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)
        
        return output_path


def extract_semantic_metadata_batch(input_dir: Path, 
                                   output_dir: Optional[Path] = None,
                                   file_pattern: str = "*.md",
                                   enable_spacy: bool = True) -> Dict[str, Any]:
    """Extract semantic metadata from all files in a directory."""
    
    if output_dir is None:
        output_dir = input_dir
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = MVPHyperSemanticExtractor(enable_spacy=enable_spacy)
    
    files = list(input_dir.glob(file_pattern))
    total_files = len(files)
    
    print(f"🧠 Extracting semantic metadata from {total_files} files...")
    
    results = {
        'total_files': total_files,
        'successful_extractions': 0,
        'total_facts': 0,
        'total_entities': 0,
        'total_processing_time': 0.0,
        'extraction_rate_pages_sec': 0.0,
        'errors': []
    }
    
    for i, file_path in enumerate(files, 1):
        try:
            # Read content
            content = file_path.read_text(encoding='utf-8')
            
            # Extract metadata
            metadata = extractor.extract_semantic_metadata(file_path, content)
            
            # Save to output directory
            if output_dir != input_dir:
                output_path = output_dir / f"{file_path.stem}.metadata.json"
            else:
                output_path = file_path.parent / f"{file_path.stem}.metadata.json"
            
            extractor.save_metadata(metadata, output_path)
            
            # Update stats
            results['successful_extractions'] += 1
            results['total_facts'] += len(metadata.facts)
            results['total_entities'] += len(metadata.entities)
            results['total_processing_time'] += metadata.processing_time
            
            # Progress feedback
            if i % 25 == 0:
                print(f"  [{i}/{total_files}] Processed {file_path.name}")
                print(f"    Facts: {len(metadata.facts)}, Entities: {len(metadata.entities)}")
        
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {e}"
            results['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    # Calculate final stats
    if results['total_processing_time'] > 0:
        # Estimate pages processed (250 words per page average)
        total_pages = sum(len(Path(input_dir / f).read_text().split()) // 250 or 1 
                         for f in [f.name for f in files])
        results['extraction_rate_pages_sec'] = total_pages / results['total_processing_time']
    
    print(f"\n✅ Semantic extraction complete!")
    print(f"📊 Processed: {results['successful_extractions']}/{results['total_files']} files")
    print(f"🔍 Extracted: {results['total_facts']} facts, {results['total_entities']} entities")
    print(f"⚡ Performance: {results['extraction_rate_pages_sec']:.1f} pages/sec")
    print(f"⏱️  Total time: {results['total_processing_time']:.2f}s")
    
    if results['errors']:
        print(f"⚠️  Errors: {len(results['errors'])}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mvp-hyper-semantic.py <input_dir> [output_dir] [--no-spacy]")
        print("Example: python mvp-hyper-semantic.py output/ semantic_output/")
        sys.exit(1)
    
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None
    enable_spacy = '--no-spacy' not in sys.argv
    
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)
    
    extract_semantic_metadata_batch(input_dir, output_dir, enable_spacy=enable_spacy)