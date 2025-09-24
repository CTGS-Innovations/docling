"""
Semantic Fact Extractor for MVP-Fusion
Implements universal fact schema with typed facts for cross-domain knowledge extraction
Uses FLPC Rust regex + Aho-Corasick for high-performance semantic understanding
"""

# Always use standard Python re module - FastRegexEngine causes hanging
import re

# Import FastRegexEngine separately if needed for specific operations
try:
    from .fast_regex import FastRegexEngine
    _fast_regex_engine = FastRegexEngine()
    FAST_REGEX_AVAILABLE = True
except ImportError:
    _fast_regex_engine = None
    FAST_REGEX_AVAILABLE = False

# Try to import Aho-Corasick (if available)
try:
    from . import aho_corasick as ac
except ImportError:
    try:
        import aho_corasick as ac
    except ImportError:
        ac = None

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
import time
import yaml
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import centralized logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import get_fusion_logger

# Import FLPC engine for high-performance pattern matching (14.9x faster than re)
try:
    from fusion.flpc_engine import FLPCEngine
    FLPC_AVAILABLE = True
except ImportError:
    FLPC_AVAILABLE = False
    FLPCEngine = None

# Import conservative person entity extractor
try:
    from utils.person_entity_extractor import PersonEntityExtractor
    PERSON_EXTRACTOR_AVAILABLE = True
except ImportError:
    PERSON_EXTRACTOR_AVAILABLE = False
    PersonEntityExtractor = None

@dataclass
class SemanticFact:
    """Base class for all semantic facts"""
    fact_type: str
    confidence: float
    span: Dict[str, int]
    raw_text: str
    normalized_entities: Dict[str, Any] = field(default_factory=dict)
    entity_ids: Dict[str, str] = field(default_factory=dict)

@dataclass
class RegulationCitation(SemanticFact):
    """Regulation/code citation with context"""
    regulation_id: str = ""
    issuing_authority: str = ""
    subject_area: str = ""
    canonical_name: str = ""
    
@dataclass
class Requirement(SemanticFact):
    """Rule, constraint, or obligation"""
    requirement_text: str = ""
    subject: str = ""
    modality: str = ""  # must, shall, should, may
    conditions: List[str] = field(default_factory=list)
    
@dataclass
class FinancialImpact(SemanticFact):
    """Financial amounts with context and impact"""
    amount: float = 0.0
    currency: str = "USD"
    impact_type: str = ""  # cost, saving, revenue, penalty
    subject: str = ""
    timeframe: Optional[str] = None
    
@dataclass
class MeasurementRequirement(SemanticFact):
    """Technical measurements with requirements"""
    value: float = 0.0
    unit: str = ""
    measurement_type: str = ""  # distance, weight, time, temperature
    requirement_context: str = ""
    tolerance: Optional[str] = None
    
@dataclass
class ContactInfo(SemanticFact):
    """Contact information for organizations/people"""
    entity_name: str = ""
    contact_type: str = ""  # phone, email, address, website
    contact_value: str = ""
    canonical_entity_id: str = ""
    
@dataclass
class EventFact(SemanticFact):
    """Event with participants, date, and context"""
    event_type: str = ""
    participants: List[str] = field(default_factory=list)
    date: Optional[str] = None
    location: Optional[str] = None
    
@dataclass
class ActionFact(SemanticFact):
    """Subject-verb-object action statements"""
    subject: str = ""
    action_verb: str = ""
    object: str = ""
    modifiers: List[str] = field(default_factory=list)

@dataclass
class PersonFact(SemanticFact):
    """Conservative person entity with high-accuracy validation"""
    person_name: str = ""
    role_context: str = ""
    organization_affiliation: str = ""
    name_components: Dict[str, str] = field(default_factory=dict)  # first, last names
    validation_evidence: List[str] = field(default_factory=list)
    ambiguity_score: float = 0.0
    
@dataclass
class RegulatoryAuthorityFact(SemanticFact):
    """Government agencies and regulatory bodies with their authority scope"""
    organization_name: str = ""
    full_name: str = ""
    authority_type: str = ""  # federal_agency, state_agency, regulatory_body
    regulatory_scope: str = ""  # workplace_safety, environmental, financial
    jurisdiction: str = ""  # federal, state, local
    key_regulations: List[str] = field(default_factory=list)
    
@dataclass 
class CompanyFact(SemanticFact):
    """Private companies and organizations with business context"""
    company_name: str = ""
    industry_sector: str = ""  # construction, manufacturing, technology
    organization_type: str = ""  # corporation, llc, partnership
    business_context: str = ""  # appears in safety context, regulatory context
    
@dataclass
class GeographicFact(SemanticFact): 
    """Locations with geographic and regulatory context"""
    location_name: str = ""
    location_type: str = ""  # state, city, region, country
    regulatory_context: str = ""  # subject to OSHA regulations, state jurisdiction
    jurisdiction_level: str = ""  # federal, state, local

@dataclass
class CausalFact(SemanticFact):
    """Cause and effect relationships"""
    cause: str = ""
    effect: str = ""
    strength: str = ""  # strong, moderate, weak
    evidence_type: str = ""

class SemanticFactExtractor:
    """
    Universal fact extractor using FLPC + Aho-Corasick for cross-domain knowledge
    Implements fact assembly pipeline: entities → normalized entities → typed facts
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_fusion_logger(__name__)
        self.config = config or {}
        self.canonical_map = self._build_canonical_map()
        self.fact_patterns = self._build_fact_patterns()
        self.aho_corasick = self._build_normalizer()
        
        # Initialize FLPC engine for high-performance pattern matching (Rule #12)
        self.flpc_engine = None
        if FLPC_AVAILABLE:
            try:
                self.flpc_engine = FLPCEngine(self.config)
                self.logger.config("🚀 FLPC engine initialized for 14.9x faster pattern matching")
            except Exception as e:
                self.logger.config(f"⚠️ FLPC engine failed to initialize: {e}")
                self.flpc_engine = None
        else:
            self.logger.config("⚠️ FLPC not available - falling back to Python regex (40x slower)")
        
        # Initialize conservative person extractor if available
        self.person_extractor = None
        if PERSON_EXTRACTOR_AVAILABLE and config:
            corpus_config = config.get('corpus', {})
            try:
                self.person_extractor = PersonEntityExtractor(
                    first_names_path=Path(corpus_config.get('first_names_path')) if corpus_config.get('first_names_path') else None,
                    last_names_path=Path(corpus_config.get('last_names_path')) if corpus_config.get('last_names_path') else None,
                    organizations_path=Path(corpus_config.get('organizations_path')) if corpus_config.get('organizations_path') else None,
                    min_confidence=corpus_config.get('person_min_confidence', 0.7)
                )
                self.logger.entity("✅ Conservative person extractor initialized with corpus")
            except Exception as e:
                self.logger.logger.warning(f"⚠️ Could not initialize person extractor: {e}")
                self.person_extractor = None
        elif PERSON_EXTRACTOR_AVAILABLE:
            # Initialize with default settings (no corpus files)
            self.person_extractor = PersonEntityExtractor(min_confidence=0.7)
            self.logger.entity("✅ Conservative person extractor initialized (no corpus)")
        
    def _build_canonical_map(self) -> Dict[str, Dict[str, str]]:
        """Build canonical normalization mapping for entities"""
        return {
            # Government agencies
            "OSHA": {
                "canonical_name": "Occupational Safety and Health Administration",
                "entity_id": "Q192334",
                "domain": "safety_regulatory"
            },
            "EPA": {
                "canonical_name": "Environmental Protection Agency", 
                "entity_id": "Q311670",
                "domain": "environmental_regulatory"
            },
            "DOL": {
                "canonical_name": "Department of Labor",
                "entity_id": "Q217810", 
                "domain": "labor_regulatory"
            },
            "FDA": {
                "canonical_name": "Food and Drug Administration",
                "entity_id": "Q204711",
                "domain": "health_regulatory"
            },
            
            # Regulation types
            "CFR": {
                "canonical_name": "Code of Federal Regulations",
                "entity_id": "CFR",
                "domain": "regulatory_code"
            },
            "USC": {
                "canonical_name": "United States Code", 
                "entity_id": "USC",
                "domain": "legal_code"
            },
            "ISO": {
                "canonical_name": "International Organization for Standardization",
                "entity_id": "Q15028",
                "domain": "international_standard"
            },
            "ANSI": {
                "canonical_name": "American National Standards Institute",
                "entity_id": "Q217628",
                "domain": "national_standard"
            },
            
            # Common business entities
            "LLC": {
                "canonical_name": "Limited Liability Company",
                "entity_id": "LLC",
                "domain": "business_entity"
            },
            "Inc": {
                "canonical_name": "Incorporated",
                "entity_id": "INC", 
                "domain": "business_entity"
            },
            "Corp": {
                "canonical_name": "Corporation",
                "entity_id": "CORP",
                "domain": "business_entity"
            }
        }
    
    def _build_fact_patterns(self) -> Dict[str, List[str]]:
        """Build FLPC regex patterns for fact extraction"""
        return {
            'RegulationCitation': [
                r'(\d+\s+CFR\s+[\d\.\-]+)',  # "29 CFR 1926.1050-1060"
                r'(\w+)\s+(\d+\s+CFR\s+[\d\.]+)',  # "OSHA 29 CFR 1926.1050"
                r'(ISO\s+\d+(?::\d+)?)',  # "ISO 9001:2015"
                r'(ANSI\s+[A-Z]\d+(?:\.\d+)*)',  # "ANSI A14.3"
                r'(\d+\s+USC\s+[\d\.]+)',  # "29 USC 651"
                r'(Section\s+[\d\.]+(?:\([a-z]\))?)',  # "Section 5(a)(1)"
                r'(\d{4}\.\d+)',  # "1926.1050" (OSHA style)
                r'(Subpart\s+[A-Z])',  # "Subpart L"
            ],
            
            'Requirement': [
                r'(must|shall|required|mandatory)\s+(.+)',
                r'(should|recommended|advised)\s+(.+)', 
                r'(may|optional|permitted)\s+(.+)',
                r'(prohibited|forbidden|not\s+allowed)\s+(.+)',
            ],
            
            'FinancialImpact': [
                r'\$[\d,]+(?:\.\d{2})?\s*(?:billion|million|thousand)?\s*(?:cost|expense|fee)',
                r'\$[\d,]+(?:\.\d{2})?\s*(?:billion|million|thousand)?\s*(?:saving|saved|benefit)',
                r'\$[\d,]+(?:\.\d{2})?\s*(?:billion|million|thousand)?\s*(?:revenue|income|earnings)',
                r'\$[\d,]+(?:\.\d{2})?\s*(?:billion|million|thousand)?\s*(?:penalty|fine|violation)',
            ],
            
            'MeasurementRequirement': [
                r'(\d+(?:\.\d+)?)\s*(inches?|feet?|yards?|meters?|cm|mm)\s*(?:maximum|minimum|exactly|at\s+least|no\s+more\s+than)',
                r'(\d+(?:\.\d+)?)\s*(pounds?|lbs?|kg|grams?)\s*(?:maximum|minimum|exactly|at\s+least|no\s+more\s+than)',
                r'(\d+(?:\.\d+)?)\s*(?:degrees?\s*)?(?:fahrenheit|celsius|F|C)\s*(?:maximum|minimum|exactly)',
                r'(\d+(?:\.\d+)?)\s*(seconds?|minutes?|hours?|days?)\s*(?:maximum|minimum|exactly|at\s+least|no\s+more\s+than)',
            ],
            
            'ContactInfo': [
                r'(\d{3}[-\.\s]?\d{3}[-\.\s]?\d{4})',  # Phone numbers
                r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Email
                r'(https?://[^\s]+)',  # URLs
                r'(\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd))',  # Addresses
            ],
            
            'ActionFact': [
                # Capture complete noun phrases as subjects (not fragments)
                r'([A-Z][\w\s]+?(?:system|process|method|approach|technique|model|framework|algorithm|tool|service|department|agency|administration|organization|company|entity)s?)\s+(requires?|enforces?|provides?|maintains?|conducts?|issues?)\s+(.+?)(?=\.|,|;)',
                r'([A-Z][\w\s]+?(?:system|process|method|approach|technique|model|framework|algorithm|tool|service|department|agency|administration|organization|company|entity)s?)\s+(prevents?|reduces?|increases?|improves?|eliminates?|enhances?|optimizes?)\s+(.+?)(?=\.|,|;)',
                r'([A-Z][\w\s]+?(?:system|process|method|approach|technique|model|framework|algorithm|tool|service|department|agency|administration|organization|company|entity)s?)\s+(applies?\s+to|governs?|regulates?|oversees?|manages?|controls?)\s+(.+?)(?=\.|,|;)',
                # Capture "The/This/That X" patterns
                r'(?:The|This|That|These|Those|Our|Their)\s+([\w\s]+?)\s+(requires?|enforces?|provides?|maintains?|conducts?|issues?|prevents?|reduces?|increases?|improves?|eliminates?)\s+(.+?)(?=\.|,|;)',
                # Capture pronoun references if clear
                r'(It|They|He|She)\s+(requires?|enforces?|provides?|maintains?|conducts?|issues?|prevents?|reduces?|increases?|improves?|eliminates?)\s+(.+?)(?=\.|,|;)',
            ],
            
            'CausalFact': [
                r'(.+?)\s+(?:causes?|leads?\s+to|results?\s+in)\s+(.+?)(?=\.|,|;)',
                r'(.+?)\s+(?:prevents?|reduces?|eliminates?)\s+(.+?)(?=\.|,|;)',
                r'(?:due\s+to|because\s+of|as\s+a\s+result\s+of)\s+(.+?),\s*(.+?)(?=\.|;)',
            ]
        }
    
    def _build_normalizer(self):
        """Build Aho-Corasick automaton for entity normalization"""
        if ac and FLPC_AVAILABLE:
            try:
                automaton = ac.Automaton()
                for entity, info in self.canonical_map.items():
                    automaton.add_word(entity, (entity, info))
                automaton.make_automaton()
                return automaton
            except:
                return None
        else:
            # Aho-Corasick not available, will use fallback in _normalize_entities
            return None
    
    def _normalize_entities(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Normalize entities using Aho-Corasick for canonical forms"""
        normalized = {}
        
        if self.aho_corasick:
            # Use Aho-Corasick for fast normalization
            for end_index, (original, info) in self.aho_corasick.iter(text):
                start_index = end_index - len(original) + 1
                normalized[original] = {
                    'canonical_name': info['canonical_name'],
                    'entity_id': info['entity_id'],
                    'domain': info['domain'],
                    'span': {'start': start_index, 'end': end_index + 1}
                }
        else:
            # Fallback to simple mapping
            for entity, info in self.canonical_map.items():
                if entity in text:
                    normalized[entity] = info
                    
        return normalized
    
    def _extract_regulation_citations(self, text: str, normalized_entities: Dict) -> List[RegulationCitation]:
        """Extract regulation citations using FLPC for 14.9x performance (Rule #12)"""
        facts = []
        
        # Use FLPC engine if available, otherwise fallback to Python regex
        if self.flpc_engine:
            try:
                # Use FLPC for high-performance pattern matching
                flpc_results = self.flpc_engine.extract_entities(text, pattern_set="regulation")
                regulation_matches = flpc_results.get('entities', {}).get('regulation', [])
                
                for match_info in regulation_matches:
                    raw_text = match_info.get('text', '')
                    start = match_info.get('start', 0)
                    end = match_info.get('end', len(raw_text))
                    
                    # Determine authority and regulation
                    if 'CFR' in raw_text:
                        authority = 'Federal Government'
                        reg_id = raw_text
                    elif 'ISO' in raw_text:
                        authority = 'International Organization for Standardization'
                        reg_id = raw_text
                    elif 'ANSI' in raw_text:
                        authority = 'American National Standards Institute'
                        reg_id = raw_text
                    else:
                        authority = 'Unknown'
                        reg_id = raw_text
                    
                    fact = RegulationCitation(
                        fact_type='RegulationCitation',
                        confidence=0.7,
                        span={'start': start, 'end': end},
                        raw_text=raw_text,
                        regulation_id=reg_id,
                        issuing_authority=authority,
                        subject_area='',
                        normalized_entities=normalized_entities
                    )
                    facts.append(fact)
                    
            except Exception as e:
                self.logger.semantics(f"⚠️ FLPC regulation extraction failed: {e}")
                # Fallback to manual pattern matching
                facts = self._extract_regulation_citations_fallback(text, normalized_entities)
        else:
            # Fallback to Python regex (40x slower)
            facts = self._extract_regulation_citations_fallback(text, normalized_entities)
            
        return facts
    
    def _extract_regulation_citations_fallback(self, text: str, normalized_entities: Dict) -> List[RegulationCitation]:
        """Fallback regulation extraction using Python regex (for when FLPC unavailable)"""
        facts = []
        
        for pattern in self.fact_patterns['RegulationCitation']:
            try:
                for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
                    raw_text = match.group(0)
                    
                    # Determine authority and regulation
                    if 'CFR' in raw_text:
                        authority = 'Federal Government'
                        reg_id = raw_text
                    elif 'ISO' in raw_text:
                        authority = 'International Organization for Standardization'
                        reg_id = raw_text
                    elif 'ANSI' in raw_text:
                        authority = 'American National Standards Institute'
                        reg_id = raw_text
                    else:
                        authority = 'Unknown'
                        reg_id = raw_text
                    
                    fact = RegulationCitation(
                        fact_type='RegulationCitation',
                        confidence=0.7,
                        span={'start': match.start(), 'end': match.end()},
                        raw_text=raw_text,
                        regulation_id=reg_id,
                        issuing_authority=authority,
                        subject_area='',
                        normalized_entities=normalized_entities
                    )
                    facts.append(fact)
            except Exception as e:
                self.logger.semantics(f"Pattern {pattern} failed: {e}")
                continue
                
        return facts
    
    def _split_into_sentences(self, text: str) -> List[Tuple[str, int]]:
        """Split text into sentences using simple string operations (Rule #12 compliant)"""
        sentences = []
        
        # Simple sentence boundary detection without regex
        sentence_endings = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        
        current_pos = 0
        
        while current_pos < len(text):
            # Find next sentence boundary
            next_boundary = len(text)
            boundary_len = 0
            
            for ending in sentence_endings:
                pos = text.find(ending, current_pos)
                if pos != -1 and pos < next_boundary:
                    next_boundary = pos + 1  # Include punctuation
                    boundary_len = len(ending)
            
            # Extract sentence
            sentence_text = text[current_pos:next_boundary].strip()
            
            if len(sentence_text) > 10:  # Skip very short fragments
                sentences.append((sentence_text, current_pos))
            
            # Move to next sentence
            if next_boundary >= len(text):
                # No more boundaries found - we're done
                break
            
            current_pos = next_boundary + boundary_len - 1
            
            # Skip whitespace
            while current_pos < len(text) and text[current_pos].isspace():
                current_pos += 1
        
        # Handle case where no boundaries found (single sentence)
        if not sentences and len(text.strip()) > 10:
            sentences.append((text.strip(), 0))
        
        return sentences
    
    def _extract_requirements(self, text: str, normalized_entities: Dict) -> List[Requirement]:
        """Extract requirements as structured facts - sentence-by-sentence processing"""
        facts = []
        
        # Split text into sentences using simple sentence boundaries
        sentences = self._split_into_sentences(text)
        
        for sentence_text, sentence_start in sentences:
            for pattern in self.fact_patterns['Requirement']:
                try:
                    for match in re.finditer(pattern, sentence_text):
                        modality = match.group(1).lower()
                        requirement_text = match.group(2).strip()
                        
                        # Classify modality strength
                        if modality in ['must', 'shall', 'required', 'mandatory']:
                            modality_type = 'mandatory'
                        elif modality in ['should', 'recommended', 'advised']:
                            modality_type = 'recommended'
                        elif modality in ['may', 'optional', 'permitted']:
                            modality_type = 'optional'
                        else:
                            modality_type = 'prohibited'
                        
                        fact = Requirement(
                            fact_type='Requirement',
                            confidence=0.65,  # Lowered from 0.85
                            span={'start': sentence_start + match.start(), 'end': sentence_start + match.end()},
                            raw_text=match.group(0),
                            requirement_text=requirement_text,
                            subject='',
                            modality=modality_type,
                            normalized_entities=normalized_entities
                        )
                        facts.append(fact)
                except:
                    continue
                
        return facts
    
    def _extract_financial_impacts(self, text: str, normalized_entities: Dict) -> List[FinancialImpact]:
        """Extract financial impacts as structured facts"""
        facts = []
        
        for pattern in self.fact_patterns['FinancialImpact']:
            try:
                for match in re.finditer(pattern, text, 0):
                    raw_text = match.group(0)
                    
                    # Extract amount
                    amount_match = re.search(r'\$[\d,]+(?:\.\d{2})?', raw_text)
                    if amount_match:
                        amount_str = amount_match.group(0).replace('$', '').replace(',', '')
                        amount = float(amount_str)
                    else:
                        amount = 0.0
                    
                    # Determine impact type
                    if any(word in raw_text.lower() for word in ['cost', 'expense', 'fee']):
                        impact_type = 'cost'
                    elif any(word in raw_text.lower() for word in ['saving', 'saved', 'benefit']):
                        impact_type = 'saving'
                    elif any(word in raw_text.lower() for word in ['revenue', 'income', 'earnings']):
                        impact_type = 'revenue'
                    elif any(word in raw_text.lower() for word in ['penalty', 'fine', 'violation']):
                        impact_type = 'penalty'
                    else:
                        impact_type = 'unknown'
                    
                    fact = FinancialImpact(
                        fact_type='FinancialImpact',
                        confidence=0.6,  # Lowered from 0.8
                        span={'start': match.start(), 'end': match.end()},
                        raw_text=raw_text,
                        amount=amount,
                        currency='USD',
                        impact_type=impact_type,
                        subject='',
                        normalized_entities=normalized_entities
                    )
                    facts.append(fact)
            except:
                continue
                
        return facts
    
    def _extract_conservative_person_facts(self, text: str, normalized_entities: Dict) -> List[PersonFact]:
        """Extract person facts using conservative validation"""
        facts = []
        
        if not self.person_extractor:
            self.logger.logger.debug("⚠️ Person extractor not available, skipping person fact extraction")
            return facts
        
        try:
            # Use the conservative person extractor
            persons = self.person_extractor.extract_persons(text)
            
            for person in persons:
                # Extract name components
                tokens = person['text'].split()
                name_components = {}
                if len(tokens) >= 2:
                    name_components['first_name'] = tokens[0]
                    name_components['last_name'] = tokens[-1]
                    if len(tokens) > 2:
                        name_components['middle_names'] = ' '.join(tokens[1:-1])
                elif len(tokens) == 1:
                    name_components['single_name'] = tokens[0]
                
                # Create person fact
                fact = PersonFact(
                    fact_type='PersonFact',
                    confidence=person['confidence'],
                    span={'start': person['position'], 'end': person['position'] + len(person['text'])},
                    raw_text=person['text'],
                    person_name=person['text'],
                    role_context=self._extract_role_context_from_person(person, text),
                    organization_affiliation=self._extract_org_context_from_person(person, text),
                    name_components=name_components,
                    validation_evidence=person.get('evidence', []),
                    ambiguity_score=1.0 - person['confidence'],  # Higher ambiguity = lower confidence
                    normalized_entities=normalized_entities
                )
                facts.append(fact)
                
            self.logger.logger.debug(f"✅ Extracted {len(facts)} conservative person facts")
            
        except Exception as e:
            self.logger.logger.error(f"❌ Error in conservative person extraction: {e}")
            
        return facts
    
    def _extract_role_context_from_person(self, person: Dict, text: str) -> str:
        """Extract role context for a person from the surrounding text"""
        context = person.get('context', '')
        if not context:
            return ""
        
        # Look for role indicators
        role_patterns = [
            r'(CEO|CTO|CFO|COO|President|Director|Manager|Supervisor|Coordinator)',
            r'(Founder|Co-founder|Co-Founder)',
            r'(Professor|Dr\.|Doctor|Ph\.D)',
            r'(Inspector|Investigator|Agent|Officer)',
            r'(Engineer|Scientist|Researcher|Analyst)'
        ]
        
        for pattern in role_patterns:
            match = re.search(pattern, context, 0)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_org_context_from_person(self, person: Dict, text: str) -> str:
        """Extract organization context for a person"""
        context = person.get('context', '')
        if not context:
            return ""
        
        # Look for organization indicators
        org_patterns = [
            r'(OSHA|EPA|FDA|NIOSH|DOL)',  # Government agencies
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Corporation|Company))',  # Companies
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:University|Institute|College))',  # Educational
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Department|Agency|Administration))'  # Government
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        
        return ""
    
    def _extract_action_facts(self, text: str, normalized_entities: Dict) -> List[ActionFact]:
        """Extract action facts (subject-verb-object) with quality validation"""
        facts = []
        
        # Words that indicate incomplete subjects
        incomplete_subject_markers = {
            'such', 'as', 'like', 'including', 'with', 'without', 'for', 'to', 
            'from', 'by', 'of', 'in', 'on', 'at', 'the', 'a', 'an'
        }
        
        for pattern in self.fact_patterns['ActionFact']:
            try:
                for match in re.finditer(pattern, text, 0):
                    subject = match.group(1).strip()
                    action_verb = match.group(2).strip()
                    object_text = match.group(3).strip()
                    
                    # Quality validation: Skip if subject is incomplete or too short
                    subject_words = subject.split()
                    if len(subject_words) < 2:  # Single word subjects are usually poor
                        continue
                    
                    # Check if subject starts or ends with incomplete markers
                    if subject_words[0].lower() in incomplete_subject_markers:
                        continue
                    if subject_words[-1].lower() in incomplete_subject_markers:
                        continue
                        
                    # Skip if subject is mostly function words
                    content_words = [w for w in subject_words if w.lower() not in incomplete_subject_markers]
                    if len(content_words) < len(subject_words) * 0.5:  # Less than 50% content words
                        continue
                    
                    # Extract modifiers from surrounding context
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    context = text[context_start:context_end]
                    
                    # Look for modifying phrases
                    modifiers = []
                    modifier_patterns = [
                        r'(?:in|at|on|during|through|via|using|with)\s+[^,\.;]+',
                        r'(?:for|to|from|by)\s+[^,\.;]+',
                        r'(?:when|while|if|unless|although|because)\s+[^,\.;]+'
                    ]
                    
                    for mod_pattern in modifier_patterns:
                        mod_matches = re.findall(mod_pattern, context, re.IGNORECASE)
                        modifiers.extend([m.strip() for m in mod_matches[:2]])  # Limit to 2 modifiers per pattern
                    
                    # Calculate confidence based on quality
                    confidence = 0.75
                    if len(subject_words) >= 3 and len(content_words) >= 2:
                        confidence = 0.85
                    if modifiers:
                        confidence += 0.1
                    
                    fact = ActionFact(
                        fact_type='ActionFact',
                        confidence=min(confidence, 0.95),
                        span={'start': match.start(), 'end': match.end()},
                        raw_text=match.group(0),
                        subject=subject,
                        action_verb=action_verb,
                        object=object_text,
                        modifiers=modifiers[:3],  # Limit to 3 most relevant modifiers
                        normalized_entities=normalized_entities
                    )
                    facts.append(fact)
            except:
                continue
                
        return facts
    
    def _parse_yaml_markdown(self, text: str) -> Tuple[Dict, str]:
        """Parse YAML front matter and markdown content from the text"""
        self.logger.logger.debug(f"🔧 Parsing text: {len(text)} characters, starts with: '{text[:50]}...'")
        
        # Split on YAML delimiters
        if text.strip().startswith('---'):
            parts = text.split('---', 2)
            self.logger.logger.debug(f"📄 Found {len(parts)} parts after splitting on '---'")
            if len(parts) >= 3:
                try:
                    yaml_content = parts[1].strip()
                    markdown_content = parts[2].strip()
                    self.logger.logger.debug(f"📄 YAML section: {len(yaml_content)} chars")
                    self.logger.logger.debug(f"📝 Markdown section: {len(markdown_content)} chars")
                    yaml_data = yaml.safe_load(yaml_content)
                    self.logger.logger.debug(f"✅ YAML parsed successfully: {list(yaml_data.keys()) if yaml_data else 'Empty'}")
                    return yaml_data or {}, markdown_content
                except yaml.YAMLError as e:
                    self.logger.logger.error(f"❌ YAML parsing error: {e}")
                    return {}, text
        
        # No YAML front matter found, treat entire text as markdown
        self.logger.logger.debug("⚠️  No YAML front matter found (doesn't start with '---')")
        return {}, text
    
    def _normalize_yaml_entities(self, existing_entities: Dict) -> Dict[str, Dict[str, Any]]:
        """Normalize entities that are already extracted in YAML format"""
        normalized = {}
        
        # Process each entity type from YAML
        for entity_type, entities in existing_entities.items():
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        # Entity with span information
                        entity_value = entity.get('value', entity.get('text', ''))
                        if entity_value and entity_value in self.canonical_map:
                            canonical_info = self.canonical_map[entity_value]
                            normalized[entity_value] = {
                                'canonical_name': canonical_info['canonical_name'],
                                'entity_id': canonical_info['entity_id'],
                                'domain': canonical_info['domain'],
                                'span': entity.get('span', {}),
                                'type': entity.get('type', entity_type)
                            }
                    elif isinstance(entity, str):
                        # Simple string entity
                        if entity in self.canonical_map:
                            canonical_info = self.canonical_map[entity]
                            normalized[entity] = {
                                'canonical_name': canonical_info['canonical_name'],
                                'entity_id': canonical_info['entity_id'],
                                'domain': canonical_info['domain'],
                                'type': entity_type
                            }
        
        return normalized
    
    def _process_person_entity_parallel(self, entity: Dict, entity_type: str, markdown_content: str, worker_id: int) -> Optional[Dict]:
        """Process a single person entity with worker tracking"""
        from utils.worker_utils import set_worker_id
        set_worker_id(f"Person-{worker_id}")
        
        return self._create_intelligent_semantic_fact(entity_type, entity, markdown_content)
    
    def _promote_yaml_entities_to_facts(self, existing_entities: Dict, markdown_content: str) -> Dict[str, List]:
        """Dynamic promotion of any YAML entities to structured semantic facts"""
        promoted_facts = {}
        
        # Collect entity counts for structured logging
        entity_counts = {}
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
            
            if len(entities) > 0:
                entity_counts[entity_type] = len(entities)
            promoted_facts[entity_type] = []
            
            # Use parallel processing for person entities to improve performance
            if entity_type == 'person' and len(entities) > 4:  # Only parallelize if worth the overhead
                person_start_time = time.perf_counter()
                max_workers = min(4, len(entities))  # Cap at 4 workers for person processing
                self.logger.logger.debug(f"🔧 Using {max_workers} parallel workers for {len(entities)} person entities")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all person entity processing tasks
                    future_to_entity = {}
                    for i, entity in enumerate(entities):
                        if isinstance(entity, dict):
                            worker_id = (i % max_workers) + 1
                            future = executor.submit(self._process_person_entity_parallel, entity, entity_type, markdown_content, worker_id)
                            future_to_entity[future] = entity
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_entity):
                        entity = future_to_entity[future]
                        try:
                            semantic_fact = future.result()
                            if semantic_fact:
                                promoted_facts[entity_type].append(semantic_fact)
                            else:
                                # Log rejected person entities for visibility
                                self.logger.logger.debug(f"🚫 Filtered out false person: '{entity.get('value', 'unknown')}'")
                        except Exception as e:
                            self.logger.logger.warning(f"⚠️ Error processing person entity {entity.get('value', 'unknown')}: {e}")
                
                person_duration = (time.perf_counter() - person_start_time) * 1000
                self.logger.logger.debug(f"✅ Parallel person processing completed in {person_duration:.1f}ms ({len(entities)} entities)")
            else:
                # Sequential processing for non-person entities or small person lists
                for entity in entities:
                    if isinstance(entity, dict):
                        # Create semantic fact based on entity type
                        semantic_fact = self._create_intelligent_semantic_fact(entity_type, entity, markdown_content)
                        if semantic_fact:  # Only add non-None facts
                            promoted_facts[entity_type].append(semantic_fact)
                        elif entity_type == 'person':
                            # Log rejected person entities for visibility
                            self.logger.logger.debug(f"🚫 Filtered out false person: '{entity.get('value', 'unknown')}'")
        
        # Remove empty fact type lists
        promoted_facts = {k: v for k, v in promoted_facts.items() if v}
        
        # Structured entity logging - one line summary
        if entity_counts:
            entity_summary = ", ".join([f"{entity_type}:{count}" for entity_type, count in entity_counts.items()])
            self.logger.logger.debug(f"📊 Global entities: {entity_summary}")
        
        total_promoted = sum(len(facts) for facts in promoted_facts.values())
        self.logger.entity(f"✅ Total facts promoted: {total_promoted}")
        
        return promoted_facts
    
    def _universal_text_clean(self, text: str) -> str:
        """Universal text cleaning: replace newlines with spaces, normalize whitespace"""
        if not text:
            return ""
        
        # Replace single and multiple newlines with single space
        import re
        # Replace any sequence of newlines and whitespace with single space
        cleaned = re.sub(r'\s*\n\s*', ' ', str(text))
        # Normalize multiple spaces to single space
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Strip leading/trailing whitespace
        return cleaned.strip()
    
    def _create_intelligent_semantic_fact(self, entity_type: str, entity: Dict, context: str) -> Optional[Dict]:
        """Create meaningful semantic facts based on entity type and context analysis"""
        # EFFICIENCY: Early validation - check if entity has valid content before expensive processing
        raw_value = entity.get('value', entity.get('text', ''))
        if not raw_value or not raw_value.strip():
            return None
            
        # Apply universal text cleaning to all text fields
        raw_text = self._universal_text_clean(raw_value)
        canonical_name = self._universal_text_clean(self._get_canonical_name(raw_value, entity_type))
        
        # Filter out meaningless entities
        if self._is_meaningless_entity(raw_text, entity_type):
            return None
            
        # Create intelligent facts based on entity type and context
        fact = None
        if entity_type == 'org':
            fact = self._create_organization_fact(raw_text, canonical_name, entity, context)
        elif entity_type == 'gpe' or entity_type == 'location':
            fact = self._create_geographic_fact(raw_text, canonical_name, entity, context)
        elif entity_type == 'person':
            fact = self._create_person_context_fact(raw_text, canonical_name, entity, context)
        else:
            # For other entity types, create minimal contextual facts
            fact = self._create_contextual_fact(entity_type, raw_text, canonical_name, entity, context)
        
        # Filter out facts with no meaningful context
        if fact:
            context = fact.get('context_summary', '')
            if not context or context == 'No specific context found' or context.strip() == '':
                return None
            
        return fact
    
    def _is_meaningless_entity(self, text: str, entity_type: str) -> bool:
        """Filter out meaningless entities that shouldn't become facts"""
        meaningless_words = {
            'place', 'time', 'work', 'part', 'way', 'day', 'year', 'area', 'case', 
            'hand', 'side', 'fact', 'point', 'right', 'thing', 'world', 'life',
            'system', 'group', 'number', 'part', 'water', 'course', 'state'
        }
        
        # Filter very short or meaningless organization names
        if entity_type == 'org' and (len(text) < 3 or text.lower() in meaningless_words):
            return True
            
        # Filter generic location words  
        if entity_type in ['gpe', 'location'] and text.lower() in meaningless_words:
            return True
            
        return False
    
    def _create_organization_fact(self, raw_text: str, canonical_name: str, entity: Dict, context: str) -> Dict:
        """Create intelligent organization facts with regulatory/business context"""
        # Detect if this is a regulatory authority
        regulatory_keywords = ['administration', 'agency', 'bureau', 'commission', 'department', 'authority']
        is_regulatory = any(keyword in raw_text.lower() for keyword in regulatory_keywords)
        
        if is_regulatory or 'OSHA' in raw_text or 'EPA' in raw_text:
            return {
                'fact_type': 'RegulatoryAuthorityFact',
                'confidence': 0.9,
                'span': entity.get('span', {}),
                'raw_text': raw_text,
                'organization_name': canonical_name,
                'full_name': self._expand_regulatory_acronym(raw_text),
                'authority_type': self._classify_authority_type(raw_text),
                'regulatory_scope': self._extract_regulatory_scope(context, raw_text),
                'jurisdiction': self._determine_jurisdiction(raw_text),
                'extraction_layer': 'intelligent_analysis'
            }
        else:
            return {
                'fact_type': 'CompanyFact', 
                'confidence': 0.85,
                'span': entity.get('span', {}),
                'raw_text': raw_text,
                'company_name': canonical_name,
                'industry_sector': self._classify_industry_sector(context, raw_text),
                'business_context': self._extract_business_context(context, raw_text),
                'extraction_layer': 'intelligent_analysis'
            }
    
    def _create_geographic_fact(self, raw_text: str, canonical_name: str, entity: Dict, context: str) -> Dict:
        """Create intelligent geographic facts with jurisdictional context"""
        return {
            'fact_type': 'GeographicFact',
            'confidence': 0.85, 
            'span': entity.get('span', {}),
            'raw_text': raw_text,
            'location_name': canonical_name,
            'location_type': self._classify_location_type(raw_text),
            'regulatory_context': self._extract_regulatory_context(context, raw_text),
            'jurisdiction_level': self._determine_geographic_jurisdiction(raw_text),
            'extraction_layer': 'intelligent_analysis'
        }
        
    def _create_person_context_fact(self, raw_text: str, canonical_name: str, entity: Dict, context: str) -> Dict:
        """Create intelligent person facts with professional context"""
        return {
            'fact_type': 'PersonFact',
            'confidence': 0.8,
            'span': entity.get('span', {}),
            'raw_text': raw_text,
            'person_name': canonical_name,
            'professional_role': self._extract_professional_role(context, raw_text),
            'organizational_affiliation': self._extract_organizational_context(context, raw_text),
            'expertise_domain': self._classify_expertise_domain(context, raw_text),
            'extraction_layer': 'intelligent_analysis'
        }
        
    def _create_contextual_fact(self, entity_type: str, raw_text: str, canonical_name: str, entity: Dict, context: str) -> Dict:
        """Create contextual facts for other entity types"""
        return {
            'fact_type': f'{entity_type.title()}ContextFact',
            'confidence': 0.6,  # Lowered from 0.8 to get more facts
            'span': entity.get('span', {}), 
            'raw_text': raw_text,
            'canonical_name': canonical_name,
            'context_summary': self._extract_context_summary(context, raw_text),
            'extraction_layer': 'intelligent_analysis'
        }
        
    # Helper methods for context analysis
    def _expand_regulatory_acronym(self, text: str) -> str:
        """Expand common regulatory acronyms"""
        expansions = {
            'OSHA': 'Occupational Safety and Health Administration',
            'EPA': 'Environmental Protection Agency', 
            'NIOSH': 'National Institute for Occupational Safety and Health',
            'DOL': 'Department of Labor'
        }
        return expansions.get(text, text)
        
    def _classify_authority_type(self, text: str) -> str:
        """Classify the type of regulatory authority"""
        if 'administration' in text.lower():
            return 'federal_administration'
        elif 'agency' in text.lower():
            return 'federal_agency'
        elif 'department' in text.lower():
            return 'federal_department'
        else:
            return 'regulatory_body'
            
    def _extract_regulatory_scope(self, context: str, org_name: str) -> str:
        """Extract what this organization regulates based on context"""
        if 'safety' in context.lower() or 'OSHA' in org_name:
            return 'workplace_safety'
        elif 'environment' in context.lower() or 'EPA' in org_name:
            return 'environmental_protection'
        else:
            return 'general_regulatory'
            
    def _determine_jurisdiction(self, text: str) -> str:
        """Determine jurisdiction level"""
        return 'federal'  # Most regulatory agencies are federal
        
    def _classify_industry_sector(self, context: str, company: str) -> str:
        """Classify industry sector based on context"""
        if 'construction' in context.lower() or 'building' in context.lower():
            return 'construction'
        elif 'manufacturing' in context.lower():
            return 'manufacturing'
        else:
            return 'general_business'
            
    def _extract_business_context(self, context: str, company: str) -> str:
        """Extract business context"""
        if 'safety' in context.lower():
            return 'safety_context'
        elif 'regulation' in context.lower():
            return 'regulatory_context'
        else:
            return 'business_context'
            
    def _classify_location_type(self, location: str) -> str:
        """Classify type of location"""
        if len(location) == 2 and location.isupper():
            return 'state_abbreviation'
        elif 'county' in location.lower():
            return 'county'
        elif 'city' in location.lower():
            return 'city'
        else:
            return 'general_location'
            
    def _extract_regulatory_context(self, context: str, location: str) -> str:
        """Extract regulatory context for location"""
        if 'OSHA' in context or 'federal' in context.lower():
            return 'federal_jurisdiction'
        else:
            return 'state_local_jurisdiction'
            
    def _determine_geographic_jurisdiction(self, location: str) -> str:
        """Determine jurisdiction level for geographic entity"""
        if len(location) == 2 and location.isupper():
            return 'state'
        else:
            return 'local'
            
    def _extract_context_summary(self, context: str, entity: str) -> str:
        """Extract clean, readable sentence containing the entity (no markup or tags)"""
        # First, clean the context of all processing artifacts using string operations
        cleaned_context = context
        
        # Remove entity tags like ||UC Berkeley||org110|| using string replacement
        while '||' in cleaned_context:
            start = cleaned_context.find('||')
            if start == -1:
                break
            
            # Find the content and end tag
            content_start = start + 2
            content_end = cleaned_context.find('||', content_start)
            if content_end == -1:
                break
            
            # Find the closing tag marker (like org110||)
            final_end = cleaned_context.find('||', content_end + 2)
            if final_end == -1:
                final_end = content_end + 2
            else:
                final_end += 2
            
            # Extract the clean content and replace the tagged version
            content = cleaned_context[content_start:content_end]
            cleaned_context = cleaned_context[:start] + content + cleaned_context[final_end:]
        
        # Remove markdown formatting using string operations
        # Remove **bold**
        while '**' in cleaned_context:
            start = cleaned_context.find('**')
            end = cleaned_context.find('**', start + 2)
            if start == -1 or end == -1:
                break
            content = cleaned_context[start + 2:end]
            cleaned_context = cleaned_context[:start] + content + cleaned_context[end + 2:]
        
        # Remove *italic*
        while '*' in cleaned_context:
            start = cleaned_context.find('*')
            end = cleaned_context.find('*', start + 1)
            if start == -1 or end == -1:
                break
            content = cleaned_context[start + 1:end]
            cleaned_context = cleaned_context[:start] + content + cleaned_context[end + 1:]
        
        # Remove markdown headers and page markers
        lines = cleaned_context.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Skip headers and page markers
            if line.startswith('#') or line.startswith('## Page') or line.startswith('I '):
                continue
            if line:
                cleaned_lines.append(line)
        
        # Rejoin and clean whitespace
        cleaned_context = ' '.join(' '.join(cleaned_lines).split())
        
        # Find sentences containing the entity
        entity_lower = entity.lower()
        
        # Better sentence splitting - look for complete sentences with proper boundaries
        sentences = []
        
        # Split by sentence endings followed by capital letters or common sentence starters
        potential_sentences = []
        current = ""
        
        i = 0
        while i < len(cleaned_context):
            char = cleaned_context[i]
            current += char
            
            # Check for sentence ending
            if char in '.!?':
                # Look ahead to see if this is a real sentence ending
                next_chars = cleaned_context[i+1:i+4] if i+1 < len(cleaned_context) else ""
                
                # Real sentence ending if followed by space + capital letter or end of text
                if (len(next_chars) >= 2 and next_chars[0] == ' ' and next_chars[1].isupper()) or i+1 >= len(cleaned_context):
                    # Make sure sentence is substantial (not just abbreviations)
                    if len(current.strip()) > 20:  # Minimum meaningful sentence length
                        potential_sentences.append(current.strip())
                        current = ""
                # Skip common abbreviations that shouldn't split sentences
                elif any(abbrev in current[-10:].lower() for abbrev in ['dr.', 'mr.', 'mrs.', 'vs.', 'etc.', 'inc.', 'ltd.']):
                    pass  # Continue building sentence
                else:
                    # Check if we have a meaningful sentence boundary
                    if len(current.strip()) > 15:
                        potential_sentences.append(current.strip())
                        current = ""
            
            i += 1
        
        # Add any remaining content as a sentence if substantial
        if current.strip() and len(current.strip()) > 15:
            potential_sentences.append(current.strip())
        
        sentences = potential_sentences
        
        # Find the best sentence containing the entity
        best_sentence = None
        for sentence in sentences:
            if entity_lower in sentence.lower():
                # Clean the sentence
                clean_sentence = sentence.strip()
                # Ensure proper ending
                if clean_sentence and clean_sentence[-1] not in '.!?':
                    clean_sentence += '.'
                # Prefer longer, more informative sentences
                if not best_sentence or len(clean_sentence) > len(best_sentence):
                    best_sentence = clean_sentence
        
        if best_sentence:
            return best_sentence
        
        # Fallback: create a complete sentence window around the entity
        if entity_lower in cleaned_context.lower():
            pos = cleaned_context.lower().find(entity_lower)
            
            # Find the start of the sentence containing the entity
            sentence_start = 0
            for i in range(pos - 1, -1, -1):
                if cleaned_context[i] in '.!?' and i > 0:
                    # Check if this is a real sentence boundary
                    if i + 1 < len(cleaned_context) and cleaned_context[i + 1] == ' ':
                        sentence_start = i + 2  # Start after ". "
                        break
            
            # Find the end of the sentence containing the entity
            sentence_end = len(cleaned_context)
            for i in range(pos + len(entity), len(cleaned_context)):
                if cleaned_context[i] in '.!?':
                    # Check if this is a real sentence boundary
                    if i + 1 >= len(cleaned_context) or (cleaned_context[i + 1] == ' ' and 
                        i + 2 < len(cleaned_context) and cleaned_context[i + 2].isupper()):
                        sentence_end = i + 1
                        break
            
            context_window = cleaned_context[sentence_start:sentence_end].strip()
            
            # If we got a very short fragment, expand to get more context
            if len(context_window) < 30:
                # Get a larger window but try to end at sentence boundaries
                start = max(0, pos - 200)
                end = min(len(cleaned_context), pos + len(entity) + 200)
                
                # Try to find sentence boundaries in this larger window
                larger_window = cleaned_context[start:end]
                
                # Find the last complete sentence in this window
                last_period = larger_window.rfind('.')
                if last_period > len(entity) + 20:  # Make sure we have substantial content
                    context_window = larger_window[:last_period + 1].strip()
                else:
                    context_window = larger_window.strip()
                    if context_window and context_window[-1] not in '.!?':
                        context_window += '.'
            
            if context_window:
                return context_window
        
        return 'No specific context found'
        
    def _extract_professional_role(self, context: str, person_name: str) -> str:
        """Extract professional role for person entity"""
        role_patterns = ['CEO', 'CTO', 'researcher', 'professor', 'scientist', 'engineer', 'manager', 'director']
        context_lower = context.lower()
        
        for role in role_patterns:
            if role.lower() in context_lower:
                return role
        return 'unknown'
    
    def _extract_organizational_context(self, context: str, person_name: str) -> str:
        """Extract organizational affiliation for person entity"""
        # Simple pattern matching for common organizational indicators
        org_patterns = ['University', 'Institute', 'Corporation', 'Company', 'Lab', 'Laboratory']
        for pattern in org_patterns:
            if pattern.lower() in context.lower():
                return pattern
        return 'unknown'
    
    def _classify_expertise_domain(self, context: str, person_name: str) -> str:
        """Classify expertise domain for person entity"""
        domain_keywords = {
            'machine_learning': ['neural', 'learning', 'AI', 'artificial intelligence'],
            'software_engineering': ['software', 'programming', 'development'],
            'research': ['research', 'study', 'analysis'],
            'business': ['business', 'management', 'executive']
        }
        
        context_lower = context.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword.lower() in context_lower for keyword in keywords):
                return domain
        return 'general'
        
    def _create_intelligent_semantic_fact_body(self, entity_type: str, entity: Dict, markdown_content: str) -> Dict:
        """Create intelligent semantic fact body"""
        # Add entity-specific semantic enrichment
        if entity_type == 'money':
            financial_context = self._universal_text_clean(self._extract_financial_context(entity, context))
            base_data.update({
                'amount': self._parse_money_amount(entity.get('value', '')),
                'currency': self._detect_currency(entity.get('value', '')),
                'financial_context': financial_context
            })
        elif entity_type == 'regulation':
            base_data.update({
                'regulation_id': entity.get('value', ''),
                'issuing_authority': self._determine_authority(entity.get('value', '')),
                'regulatory_domain': self._classify_regulation_domain(entity.get('value', '')),
                'compliance_level': self._assess_compliance_level(entity.get('value', ''))
            })
        elif entity_type == 'person':
            # Process person entities that have already been validated
            person_name = entity.get('value', '')
            person_start_time = time.perf_counter()
            from utils.worker_utils import get_worker_prefix
            self.logger.logger.debug(f"{get_worker_prefix()} ✅ Creating semantic fact for validated person: '{person_name}'")
            
            # Extract role and organization efficiently - use existing data first
            try:
                t1 = time.perf_counter()
                
                # EFFICIENCY RULE: Use existing entity data first (already extracted via FLPC)
                person_role = entity.get('role')
                person_org = entity.get('organization')
                
                # Only do expensive re-extraction if data is missing
                if not person_role or not person_org:
                    # Use singleton comprehensive extractor for missing data only
                    if not hasattr(self, '_comprehensive_extractor'):
                        from knowledge.extractors.comprehensive_entity_extractor import ComprehensiveEntityExtractor
                        self._comprehensive_extractor = ComprehensiveEntityExtractor()
                    comprehensive_extractor = self._comprehensive_extractor
                    
                    t2 = time.perf_counter()
                    
                    # Only extract missing role
                    if not person_role:
                        extracted_role = comprehensive_extractor._extract_role_from_context(context, person_name)
                        person_role = extracted_role
                        
                    # Only extract missing organization  
                    if not person_org:
                        extracted_org = comprehensive_extractor._extract_organization_from_context(context)
                        person_org = extracted_org
                        
                    t3 = time.perf_counter()
                    
                    # Log only when expensive re-extraction occurs
                    reextraction_time = (t3 - t2) * 1000
                    if reextraction_time > 10:
                        self.logger.logger.debug(f"🔍 '{person_name}' re-extraction: {reextraction_time:.1f}ms (missing data)")
                else:
                    # Log efficient path
                    efficient_time = (time.perf_counter() - t1) * 1000
                    if efficient_time < 1:
                        self.logger.logger.debug(f"⚡ '{person_name}' used existing data: {efficient_time:.2f}ms")
                
            except Exception as e:
                self.logger.logger.debug(f"Fallback to basic role extraction: {e}")
                person_role = entity.get('role')
                person_org = entity.get('organization')
            
            # Extract context for the person
            t5 = time.perf_counter()
            person_context = self._extract_role_context_from_person(entity, context)
            t6 = time.perf_counter()
            context_time = (t6 - t5) * 1000
            if context_time > 10:
                self.logger.logger.debug(f"🔍 '{person_name}' context extraction: {context_time:.1f}ms")
            
            base_data.update({
                'person_name': person_name,
                'person_role': person_role,  # Now uses improved extraction
                'person_organization': person_org,  # Now uses improved extraction
                'person_context': person_context
            })
            
            # Log timing for person processing
            person_duration = (time.perf_counter() - person_start_time) * 1000
            from utils.worker_utils import get_worker_prefix
            self.logger.logger.debug(f"{get_worker_prefix()} ⏱️  Person '{person_name}' processed in {person_duration:.1f}ms")
        elif entity_type == 'organization':
            base_data.update({
                'organization_name': entity.get('value', ''),
                'organization_type': self._classify_organization_type(entity.get('value', '')),
                'industry_context': self._extract_industry_context(entity, context)
            })
        elif entity_type == 'phone':
            base_data.update({
                'phone_number': entity.get('value', ''),
                'contact_type': 'phone',
                'formatted_number': self._format_phone_number(entity.get('value', ''))
            })
        elif entity_type == 'url':
            base_data.update({
                'url': entity.get('value', ''),
                'domain': self._extract_domain(entity.get('value', '')),
                'link_type': self._classify_url_type(entity.get('value', ''))
            })
        elif entity_type == 'measurement':
            measurement_context = self._universal_text_clean(self._extract_measurement_context(entity, context))
            base_data.update({
                'measurement_value': self._extract_measurement_value(entity.get('value', '')),
                'unit': self._extract_measurement_unit(entity.get('value', '')),
                'measurement_context': measurement_context
            })
        elif entity_type == 'date':
            temporal_context = self._universal_text_clean(self._extract_temporal_context(entity, context))
            base_data.update({
                'date_value': entity.get('value', ''),
                'date_format': self._detect_date_format(entity.get('value', '')),
                'temporal_context': temporal_context
            })
        
        return base_data
    
    def _determine_authority(self, regulation_text: str) -> str:
        """Determine issuing authority from regulation text"""
        if 'CFR' in regulation_text:
            return 'Federal Government'
        elif 'OSHA' in regulation_text:
            return 'Occupational Safety and Health Administration'
        elif 'ISO' in regulation_text:
            return 'International Organization for Standardization'
        elif 'ANSI' in regulation_text:
            return 'American National Standards Institute'
        else:
            return 'Unknown'
    
    def _parse_money_amount(self, amount_text: str) -> float:
        """Parse money amount from text"""
        try:
            # Remove currency symbols and commas
            cleaned = amount_text.replace('$', '').replace(',', '').replace('€', '').replace('£', '')
            return float(cleaned)
        except:
            return 0.0
    
    # Dynamic semantic enrichment helper methods
    def _get_canonical_name(self, value: str, entity_type: str) -> str:
        """Get canonical name from mapping or return original"""
        if value in self.canonical_map:
            return self.canonical_map[value]['canonical_name']
        return value
    
    def _detect_currency(self, amount_text: str) -> str:
        """Detect currency from amount text"""
        if '$' in amount_text:
            return 'USD'
        elif '€' in amount_text:
            return 'EUR'
        elif '£' in amount_text:
            return 'GBP'
        return 'USD'  # Default
    
    def _extract_financial_context(self, entity: Dict, context: str) -> str:
        """Extract context using complete sentence boundaries"""
        span = entity.get('span', {})
        if not span or not context:
            return ""
            
        entity_start = span.get('start', 0)
        entity_end = span.get('end', 0)
        
        # Find the sentence containing the entity by walking character by character
        # Find start of sentence containing entity
        sentence_start = entity_start
        while sentence_start > 0:
            if context[sentence_start - 1] in '.!?':
                # Found sentence boundary, skip whitespace to find actual start
                while sentence_start < len(context) and context[sentence_start].isspace():
                    sentence_start += 1
                # If we hit a paragraph break (double newline), look for the start of current paragraph
                if '\n\n' in context[sentence_start:entity_start]:
                    # Find the start of the current paragraph
                    para_start = context.rfind('\n\n', sentence_start, entity_start)
                    if para_start != -1:
                        sentence_start = para_start + 2
                        while sentence_start < len(context) and context[sentence_start].isspace():
                            sentence_start += 1
                break
            sentence_start -= 1
        
        # Find end of sentence containing entity
        sentence_end = entity_end
        while sentence_end < len(context):
            if context[sentence_end] in '.!?':
                sentence_end += 1  # Include the punctuation
                break
            sentence_end += 1
            
        # Extract the complete sentence
        if sentence_start < sentence_end:
            sentence = context[sentence_start:sentence_end].strip()
            # Make sure we got a proper sentence (starts with capital letter)
            if sentence and sentence[0].isupper():
                return sentence
        
        # Fallback: return a reasonable window around the entity
        window_start = max(0, entity_start - 50)
        window_end = min(len(context), entity_end + 50)
        return context[window_start:window_end].strip()
    
    def _classify_regulation_domain(self, regulation_text: str) -> str:
        """Classify the domain of a regulation"""
        if any(word in regulation_text.upper() for word in ['OSHA', 'SAFETY', 'HEALTH']):
            return 'occupational_safety'
        elif 'CFR' in regulation_text:
            return 'federal_regulation'
        elif 'ISO' in regulation_text:
            return 'international_standard'
        return 'general'
    
    def _assess_compliance_level(self, regulation_text: str) -> str:
        """Assess compliance level requirement"""
        if any(word in regulation_text.lower() for word in ['must', 'shall', 'required']):
            return 'mandatory'
        elif any(word in regulation_text.lower() for word in ['should', 'recommended']):
            return 'recommended'
        return 'informational'
    
    
    def _find_organization_context(self, entity: Dict, context: str) -> str:
        """Find organization affiliation for person"""
        # Look for organization patterns near person mention
        org_patterns = ['Inc', 'LLC', 'Corp', 'Company', 'Agency', 'Department']
        for pattern in org_patterns:
            if pattern in context:
                return pattern
        return ""
    
    def _classify_organization_type(self, org_name: str) -> str:
        """Classify organization type"""
        if any(word in org_name for word in ['Inc', 'LLC', 'Corp', 'Company']):
            return 'private_company'
        elif any(word in org_name for word in ['Department', 'Agency', 'Administration']):
            return 'government_agency'
        elif any(word in org_name for word in ['University', 'Institute', 'College']):
            return 'educational'
        return 'organization'
    
    def _extract_industry_context(self, entity: Dict, context: str) -> str:
        """Extract industry context for organization"""
        industries = ['construction', 'manufacturing', 'healthcare', 'technology', 'finance']
        for industry in industries:
            if industry in context.lower():
                return industry
        return ""
    
    def _format_phone_number(self, phone: str) -> str:
        """Format phone number consistently"""
        # Simple formatting - could be enhanced
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return url
    
    def _classify_url_type(self, url: str) -> str:
        """Classify URL type"""
        if 'gov' in url:
            return 'government'
        elif 'edu' in url:
            return 'educational'
        elif 'org' in url:
            return 'organization'
        return 'general'
    
    def _extract_measurement_value(self, measurement: str) -> str:
        """Extract numeric value from measurement"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', measurement)
        return match.group(1) if match else ""
    
    def _extract_measurement_unit(self, measurement: str) -> str:
        """Extract unit from measurement"""
        units = ['inches', 'feet', 'meters', 'cm', 'mm', 'pounds', 'kg', 'degrees']
        for unit in units:
            if unit in measurement.lower():
                return unit
        return ""
    
    def _extract_measurement_context(self, entity: Dict, context: str) -> str:
        """Extract context around measurement"""
        return self._extract_financial_context(entity, context)  # Reuse logic
    
    def _detect_date_format(self, date_text: str) -> str:
        """Detect date format"""
        if '/' in date_text:
            return 'MM/DD/YYYY'
        elif '-' in date_text:
            return 'YYYY-MM-DD'
        return 'unknown'
    
    def _extract_temporal_context(self, entity: Dict, context: str) -> str:
        """Extract temporal context around date"""
        return self._extract_financial_context(entity, context)  # Reuse logic
    
    def _is_likely_false_person_name(self, name: str) -> bool:
        """Detect likely false positive person names"""
        name_lower = name.lower()
        
        # Document structure elements
        document_fragments = {
            'general requirements', 'introduction working', 'contents introduction',
            'rules this', 'health act', 'labor occupational', 'health administration',
            'health review', 'specific types', 'portable ladders', 'fixed ladders',
            'ladder safety', 'defective ladders', 'stairways used', 'during construction',
            'temporary stairs', 'stair rails', 'training requirements', 'health program',
            'management guidelines', 'state programs', 'consultation services',
            'voluntary protection', 'strategic partnership', 'alliance program',
            'electronic information', 'further assistance', 'regional offices'
        }
        
        # Equipment and structural elements
        equipment_terms = {
            'all ladders', 'ladders all', 'ladders the', 'stairways the',
            'handrails requirements', 'midrails midrails', 'safety devices',
            'mounting ladder', 'related support', 'do not'
        }
        
        # Organizational fragments and addresses
        org_fragments = {
            'health achievement', 'recognition program', 'federal register',
            'the federal', 'the occupational', 'training institute',
            'education centers', 'consultation program', 'publications office',
            'constitution avenue', 'federal building', 'varick street',
            'the curtis', 'independence mall', 'west suite', 'west philadelphia',
            'south arlington', 'heights road', 'expert advisors',
            'electronic compliance', 'assistance tools', 'technical links',
            'government printing', 'forsyth street', 'south dearborn',
            'griffin street', 'city center', 'main street', 'kansas city',
            'american samoa', 'northern mariana', 'stevenson street',
            'san francisco', 'third avenue', 'area offices', 'state plans'
        }
        
        # Check against all known false positive patterns
        all_false_patterns = document_fragments | equipment_terms | org_fragments
        
        if name_lower in all_false_patterns:
            return True
            
        # Additional heuristic checks
        # Names that are clearly procedural/document terms
        if any(word in name_lower for word in ['requirements', 'guidelines', 'procedures', 'regulations']):
            return True
            
        # Names that are clearly addresses/locations without person context
        if any(word in name_lower for word in ['street', 'avenue', 'building', 'center', 'office']):
            return True
            
        # Names that are equipment or technical terms
        if any(word in name_lower for word in ['ladder', 'stair', 'rail', 'device', 'system']):
            return True
            
        # Names that are procedural terms
        if any(word in name_lower for word in ['program', 'service', 'assistance', 'consultation']):
            return True
            
        return False
    
    def _extract_semantic_relationships(self, markdown_content: str, facts: Dict) -> List[Dict]:
        """Extract semantic relationships between entities"""
        relationships = []
        # Simple relationship extraction - could be enhanced
        # This is where we'd find connections between entities
        return relationships
    
    def _apply_entity_normalization_and_filtering(self, all_facts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply normalization and minimum occurrence threshold filtering to reduce noise
        """
        
        # Step 1: Define normalization mappings for common variants
        normalization_map = {
            # OSHA variants
            "OSHA": ["The OSHA Training Institute", "OSHA Training Institute", "Training Institute"],
            "Occupational Safety and Health Administration": ["Occupational Safety", "Health Administration"],
            
            # Date formatting variants  
            "March 15, 1991": ["March 15,1991", "March 15 1991"],
            "January 26, 1989": ["January 26,1989", "January 26 1989"],
            
            # Location variants
            "New York, NY": ["New York"],
            "Washington, DC": ["Washington D.C.", "Washington"],
            
            # Remove obvious fragments
            "_FRAGMENTS_": ["Rules This", "Labor Occupational", "Health Act", "Introduction Working", "General Requirements", "Contents Introduction", "All Ladders"]
        }
        
        # Step 2: Define minimum occurrence thresholds by entity type
        min_thresholds = {
            "people": 2,        # Must appear 2+ times (filters out name fragments)
            "person": 2,        # Must appear 2+ times
            "organizations": 2, # Must appear 2+ times (filters out partial org names)
            "org": 2,          # Must appear 2+ times
            "locations": 2,     # Must appear 2+ times (filters out random place mentions)
            "loc": 2,          # Must appear 2+ times
            "phone": 1,         # Keep all (usually accurate when found)
            "measurement": 1,   # Keep all (usually accurate)
            "regulations": 1,   # Keep all (usually important)
            "regulation": 1,    # Keep all (usually important)
            "date": 1,         # Keep all (usually relevant)
            "money": 1,        # Keep all (usually important)
            "percent": 1,      # Keep all (usually relevant)
            "percentages": 1,  # Keep all (usually relevant)
            "url": 1,          # Keep all (usually important)
            "gpe": 1,          # Keep all (geopolitical entities usually relevant)
            "financial": 1,    # Keep all (usually important)
            "conservative_persons": 1,  # Keep all conservative person facts (already validated)
            "personfact": 1,   # Keep all person facts
            "validatedpersonfact": 1,  # Keep all validated person facts
            "unvalidatedpersonfact": 1  # Keep all unvalidated person facts (for analysis)
        }
        
        # Step 3: Build frequency map with normalization
        entity_frequencies = {}
        entity_to_canonical = {}
        
        for fact_type, facts in all_facts.items():
            if not isinstance(facts, list):
                continue
                
            for fact in facts:
                canonical_name = fact.get('canonical_name', '').strip()
                entity_type = fact.get('entity_type', '').lower()
                
                # Skip empty names
                if not canonical_name:
                    continue
                
                # Remove obvious fragments
                if canonical_name in normalization_map.get('_FRAGMENTS_', []):
                    continue
                
                # Apply normalization
                normalized_name = canonical_name
                for canonical, variants in normalization_map.items():
                    if canonical == '_FRAGMENTS_':
                        continue
                    if canonical_name in variants:
                        normalized_name = canonical
                        break
                
                # Track frequency
                key = (normalized_name, entity_type)
                entity_frequencies[key] = entity_frequencies.get(key, 0) + 1
                entity_to_canonical[canonical_name] = normalized_name
        
        # Step 4: Filter facts based on frequency thresholds
        filtered_facts = {}
        removed_counts = {}
        
        for fact_type, facts in all_facts.items():
            if not isinstance(facts, list):
                # Keep non-list items as-is (like metadata)
                filtered_facts[fact_type] = facts
                continue
            
            # Special handling for conservative person facts - always keep them
            if fact_type == 'conservative_persons':
                self.logger.logger.debug(f"🎯 Preserving {len(facts)} conservative person facts (already validated)")
                filtered_facts[fact_type] = facts
                continue
                
            filtered_list = []
            
            for fact in facts:
                canonical_name = fact.get('canonical_name', '').strip()
                entity_type = fact.get('entity_type', '').lower()
                fact_type_lower = fact.get('fact_type', '').lower()
                
                # Special handling for person facts - use different criteria
                if 'person' in fact_type_lower or entity_type == 'person':
                    # Person facts use conservative validation results
                    if fact.get('conservative_validation') is True:
                        # Validated person - keep regardless of frequency
                        fact['validation_status'] = 'conservative_validated'
                        filtered_list.append(fact)
                        continue
                    elif fact.get('conservative_validation') is False:
                        # Failed validation - mark but keep for analysis
                        fact['validation_status'] = 'conservative_rejected'
                        fact['confidence'] *= 0.3  # Heavily penalize
                        filtered_list.append(fact)
                        continue
                
                # Skip empty names for other types
                if not canonical_name:
                    continue
                
                # Skip fragments
                if canonical_name in normalization_map.get('_FRAGMENTS_', []):
                    removed_counts[f"{entity_type}_fragments"] = removed_counts.get(f"{entity_type}_fragments", 0) + 1
                    continue
                
                # Get normalized name and frequency
                normalized_name = entity_to_canonical.get(canonical_name, canonical_name)
                key = (normalized_name, entity_type)
                frequency = entity_frequencies.get(key, 0)
                
                # Check minimum threshold
                min_threshold = min_thresholds.get(entity_type, 1)
                
                if frequency >= min_threshold:
                    # Update fact with normalized name
                    fact['canonical_name'] = normalized_name
                    fact['frequency_score'] = frequency
                    filtered_list.append(fact)
                else:
                    removed_counts[f"{entity_type}_low_frequency"] = removed_counts.get(f"{entity_type}_low_frequency", 0) + 1
            
            if filtered_list:
                # Sort by frequency (highest first), but put validated persons first
                filtered_list.sort(key=lambda x: (
                    1 if x.get('validation_status') == 'conservative_validated' else 0,
                    x.get('frequency_score', 0)
                ), reverse=True)
                filtered_facts[fact_type] = filtered_list
        
        # Step 5: Log filtering results
        total_removed = sum(removed_counts.values())
        self.logger.logger.debug(f"🧹 Filtered out {total_removed} noisy entities:")
        for category, count in removed_counts.items():
            self.logger.logger.debug(f"   - {category}: {count} entities")
        
        # Show top entities by type
        self.logger.logger.debug("🏆 Top entities after filtering:")
        for fact_type, facts in filtered_facts.items():
            if isinstance(facts, list) and facts:
                entity_type = facts[0].get('entity_type', 'unknown')
                top_3 = [(f.get('canonical_name', ''), f.get('frequency_score', 0)) for f in facts[:3]]
                self.logger.logger.debug(f"   - {entity_type}: {top_3}")
        
        return filtered_facts
    
    def extract_semantic_facts(self, text: str) -> Dict[str, Any]:
        """
        Main extraction method: Parse YAML + markdown → promote entities to structured facts
        Returns comprehensive semantic fact graph
        """
        self.logger.entity("🧠 Starting semantic fact extraction...")
        
        # Step 1: Parse YAML front matter and markdown content
        yaml_data, markdown_content = self._parse_yaml_markdown(text)
        self.logger.logger.debug(f"📄 Parsed YAML: {len(yaml_data)} top-level keys found")
        self.logger.logger.debug(f"📝 Markdown content: {len(markdown_content)} characters")
        
        # Step 2: Get existing entities from YAML (already extracted)
        existing_entities = yaml_data.get('classification', {}).get('universal_entities', {})
        if not existing_entities:
            # Fallback to global_entities if structure is different
            existing_entities = yaml_data.get('global_entities', {})
        if not existing_entities:
            # Fallback to raw_entities structure (modern format)
            existing_entities = yaml_data.get('raw_entities', {})
        
        self.logger.logger.debug(f"🔍 Found entities in YAML: {list(existing_entities.keys()) if existing_entities else 'None'}")
        if existing_entities:
            for entity_type, entities in existing_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                self.logger.logger.debug(f"   - {entity_type}: {count} entities")
        else:
            self.logger.logger.debug("   ⚠️  No entities found in YAML structure")
        
        # Step 3: Normalize entities from YAML
        normalized_entities = self._normalize_yaml_entities(existing_entities)
        self.logger.logger.debug(f"🔄 Normalized {len(normalized_entities)} entities from YAML")
        
        # Step 4: Promote existing YAML entities to structured facts (primary method)
        self.logger.logger.debug("⬆️  Promoting YAML entities to structured facts...")
        all_facts = self._promote_yaml_entities_to_facts(existing_entities, markdown_content)
        
        # Step 4.5: Extract conservative person facts from full text (additional validation)
        if self.person_extractor and markdown_content:
            self.logger.logger.debug("👥 Extracting conservative person facts from markdown...")
            conservative_person_facts = self._extract_conservative_person_facts(markdown_content, normalized_entities)
            if conservative_person_facts:
                all_facts['conservative_persons'] = conservative_person_facts
                self.logger.entity(f"✅ Found {len(conservative_person_facts)} conservative person facts")
        
        # Step 5: Apply normalization + threshold filtering to reduce noise
        self.logger.logger.debug("🧹 Applying normalization and threshold filtering...")
        all_facts = self._apply_entity_normalization_and_filtering(all_facts)
        
        # Step 6: Extract meaningful semantic facts from markdown content (regulations, requirements, financial impacts)
        self.logger.logger.debug("🔍 Extracting semantic facts from markdown content...")
        # Check if this is a regulatory/safety document for enhanced extraction
        domain_classification = yaml_data.get('domain_classification', {})
        top_domains = domain_classification.get('top_domains', [])
        top_doc_types = domain_classification.get('top_document_types', [])
        
        is_regulatory_document = (
            'safety_compliance' in top_domains or 
            'osha_report' in top_doc_types or 
            'regulation' in top_doc_types
        )
        # Skip expensive markdown search if already identified as regulatory
        if not is_regulatory_document:
            is_regulatory_document = 'OSHA' in markdown_content
        
        if is_regulatory_document:
            self.logger.logger.debug("🏛️ Regulatory document detected - enabling enhanced regulatory extraction")
        
        # Extract regulation citations (enhanced for regulatory docs)
        regulation_facts = self._extract_regulation_citations(markdown_content, normalized_entities)
        if regulation_facts:
            all_facts['regulation_citations'] = regulation_facts
            self.logger.logger.debug(f"   - regulation_citations: {len(regulation_facts)} regulatory citations found")
        
        # Extract requirements and rules (enhanced for regulatory docs)
        requirement_facts = self._extract_requirements(markdown_content, normalized_entities)
        if requirement_facts:
            all_facts['requirements'] = requirement_facts
            self.logger.logger.debug(f"   - requirements: {len(requirement_facts)} compliance requirements found")
        
        # Extract financial impacts
        financial_facts = self._extract_financial_impacts(markdown_content, normalized_entities)
        if financial_facts:
            all_facts['financial_impacts'] = financial_facts
            self.logger.logger.debug(f"   - financial_impacts: {len(financial_facts)} financial facts found")
        
        # Extract action facts (subject-verb-object relationships)
        action_facts = self._extract_action_facts(markdown_content, normalized_entities)
        if action_facts:
            all_facts['action_facts'] = action_facts
            self.logger.logger.debug(f"   - action_facts: {len(action_facts)} action relationships found")
        
        # Step 7: Extract additional semantic relationships from markdown content
        self.logger.logger.debug("🔍 Extracting semantic relationships from markdown content...")
        relationships = self._extract_semantic_relationships(markdown_content, all_facts)
        if relationships:
            all_facts['relationships'] = relationships
            self.logger.logger.debug(f"   - relationships: {len(relationships)} semantic relationships found")
        
        # Step 7: Build semantic summary
        total_facts = sum(len(facts) for facts in all_facts.values())
        self.logger.entity(f"✅ Total semantic facts extracted: {total_facts}")
        
        # Build semantic facts structure - handle dynamic fact types
        semantic_facts_output = {}
        
        # Process all fact types in all_facts
        for fact_type, facts in all_facts.items():
            if isinstance(facts, list) and facts:
                # Convert facts to serializable format
                processed_facts = []
                for fact in facts:
                    if hasattr(fact, '__dict__'):
                        # Convert dataclass to dict
                        fact_dict = {k: v for k, v in fact.__dict__.items() if not k.startswith('_')}
                    elif isinstance(fact, dict):
                        # Already a dict
                        fact_dict = fact
                    else:
                        # Convert to string representation
                        fact_dict = {'raw_text': str(fact), 'confidence': 0.5}
                    
                    processed_facts.append(fact_dict)
                
                semantic_facts_output[fact_type] = processed_facts
        
        result = {
            'semantic_facts': semantic_facts_output,
            'normalized_entities': normalized_entities,
            'semantic_summary': {
                'total_facts': total_facts,
                'fact_types': {k: len(v) for k, v in all_facts.items()},
                'extraction_engine': 'FLPC + Aho-Corasick Semantic',
                'performance_model': 'O(n) Linear Semantic Extraction',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return result
    
    def extract_semantic_facts_from_classification(self, classification_data: Dict, markdown_content: str) -> Dict[str, Any]:
        """
        Parallel processing method: Extract semantic facts from classification data + markdown content
        Uses existing entities from classification and markdown context for enrichment
        """
        self.logger.entity("🧠 Starting semantic fact extraction from classification data...")
        
        # Step 1: Get entities from classification structure (adapt to actual format)
        raw_entities = classification_data.get('raw_entities', {})
        
        # Handle both nested and flat raw_entities structure
        if 'global_entities' in raw_entities or 'domain_entities' in raw_entities:
            # Nested structure
            global_entities = raw_entities.get('global_entities', {})
            domain_entities = raw_entities.get('domain_entities', {})
        else:
            # Flat structure - treat all raw_entities as global for now
            global_entities = raw_entities
            domain_entities = {}
        
        # STRUCTURED ENTITY LOGGING RULE: 2-line summary format for each layer
        # Line 1: Global entities summary
        if global_entities:
            global_counts = []
            for entity_type, entities in global_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                if count > 0:
                    global_counts.append(f"{entity_type}:{count}")
            
            if global_counts:
                self.logger.logger.debug(f"📊 Global entities: {', '.join(global_counts)}")
            else:
                self.logger.logger.debug("📊 Global entities: none found")
        else:
            self.logger.logger.debug("📊 Global entities: none found")
        
        # Line 2: Domain entities summary  
        if domain_entities:
            domain_counts = []
            for entity_type, entities in domain_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                if count > 0:
                    domain_counts.append(f"{entity_type}:{count}")
            
            if domain_counts:
                self.logger.logger.debug(f"🎯 Domain entities: {', '.join(domain_counts)}")
            else:
                self.logger.logger.debug("🎯 Domain entities: none found")
        else:
            self.logger.logger.debug("🎯 Domain entities: none found")
        
        # Step 2: Normalize entities from both global and domain classifications
        global_normalized = self._normalize_classification_entities(global_entities)
        domain_normalized = self._normalize_classification_entities(domain_entities)
        
        # Combine normalized entities (maintaining source distinction)
        normalized_entities = {}
        for k, v in global_normalized.items():
            v['source'] = 'global'
            normalized_entities[f"global_{k}"] = v
        for k, v in domain_normalized.items():
            v['source'] = 'domain'
            normalized_entities[f"domain_{k}"] = v
            
        self.logger.logger.debug(f"🔄 Normalized {len(global_normalized)} global + {len(domain_normalized)} domain entities")
        
        # Step 3: Promote classification entities to structured facts (process both)
        self.logger.logger.debug("⬆️  Promoting classification entities to structured facts...")
        
        # Process global entities
        global_facts = self._promote_classification_entities_to_facts(global_entities, markdown_content, source="global")
        
        # Process domain entities  
        domain_facts = self._promote_classification_entities_to_facts(domain_entities, markdown_content, source="domain")
        
        # Combine all facts maintaining source distinction
        all_facts = {}
        
        # Add global facts
        for fact_type, facts in global_facts.items():
            all_facts[f"global_{fact_type}"] = facts
            
        # Add domain facts
        for fact_type, facts in domain_facts.items():
            all_facts[f"domain_{fact_type}"] = facts
        
        # Step 4: Extract additional semantic relationships from markdown content
        self.logger.logger.debug("🔍 Extracting semantic relationships from markdown content...")
        relationships = self._extract_semantic_relationships(markdown_content, all_facts)
        if relationships:
            all_facts['relationships'] = relationships
            self.logger.logger.debug(f"   - relationships: {len(relationships)} semantic relationships found")
        
        # Step 5: Build semantic summary
        total_facts = sum(len(facts) for facts in all_facts.values())
        self.logger.entity(f"✅ Total semantic facts extracted: {total_facts}")
        
        result = {
            'semantic_facts': all_facts,
            'normalized_entities': normalized_entities,
            'semantic_summary': {
                'total_facts': total_facts,
                'fact_types': {k: len(v) for k, v in all_facts.items()},
                'extraction_engine': 'FLPC + Classification Parallel Processing',
                'performance_model': 'O(n) Linear Semantic Extraction',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return result
    
    def _normalize_classification_entities(self, existing_entities: Dict) -> Dict[str, Dict[str, Any]]:
        """Normalize entities from classification data structure"""
        normalized = {}
        
        # Process each entity type from classification
        for entity_type, entities in existing_entities.items():
            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        # Entity with span information (standard format)
                        entity_value = entity.get('value', entity.get('text', ''))
                        if entity_value and entity_value in self.canonical_map:
                            canonical_info = self.canonical_map[entity_value]
                            normalized[entity_value] = {
                                'canonical_name': canonical_info['canonical_name'],
                                'entity_id': canonical_info['entity_id'],
                                'domain': canonical_info['domain'],
                                'span': entity.get('span', {}),
                                'type': entity.get('type', entity_type)
                            }
        
        return normalized
    
    def _process_classification_person_entity_parallel(self, entity: Dict, entity_type: str, markdown_content: str, source: str, worker_id: int) -> Optional[Dict]:
        """Process a single classification person entity with worker tracking"""
        from utils.worker_utils import set_worker_id
        set_worker_id(f"ClassPerson-{worker_id}")
        
        semantic_fact = self._create_intelligent_semantic_fact(entity_type, entity, markdown_content)
        if semantic_fact:
            # Add source information to semantic fact
            semantic_fact['extraction_source'] = source
            semantic_fact['fact_type'] = f"{source.title()}{entity_type.title()}Fact"
        return semantic_fact
    
    def _promote_classification_entities_to_facts(self, existing_entities: Dict, markdown_content: str, source: str = "unknown") -> Dict[str, List]:
        """Dynamic promotion of classification entities to structured semantic facts"""
        promoted_facts = {}
        
        # Collect entity counts for structured logging
        entity_counts = {}
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
            
            if len(entities) > 0:
                entity_counts[entity_type] = len(entities)
            promoted_facts[entity_type] = []
            
            # Use parallel processing for person entities to improve performance
            if entity_type == 'person' and len(entities) > 4:  # Only parallelize if worth the overhead
                person_start_time = time.perf_counter()
                max_workers = min(4, len(entities))  # Cap at 4 workers for person processing
                self.logger.logger.debug(f"🔧 Using {max_workers} parallel workers for {len(entities)} {source} person entities")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all person entity processing tasks
                    future_to_entity = {}
                    for i, entity in enumerate(entities):
                        if isinstance(entity, dict):
                            worker_id = (i % max_workers) + 1
                            future = executor.submit(self._process_classification_person_entity_parallel, entity, entity_type, markdown_content, source, worker_id)
                            future_to_entity[future] = entity
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_entity):
                        entity = future_to_entity[future]
                        try:
                            semantic_fact = future.result()
                            if semantic_fact:
                                promoted_facts[entity_type].append(semantic_fact)
                        except Exception as e:
                            self.logger.logger.warning(f"⚠️ Error processing {source} person entity {entity.get('value', 'unknown')}: {e}")
                
                person_duration = (time.perf_counter() - person_start_time) * 1000
                self.logger.logger.debug(f"✅ Parallel {source} person processing completed in {person_duration:.1f}ms ({len(entities)} entities)")
            else:
                # Sequential processing for non-person entities or small person lists
                for entity in entities:
                    if isinstance(entity, dict):
                        # Create semantic fact based on entity type
                        semantic_fact = self._create_intelligent_semantic_fact(entity_type, entity, markdown_content)
                        if semantic_fact:
                            # Add source information to semantic fact
                            semantic_fact['extraction_source'] = source
                            semantic_fact['fact_type'] = f"{source.title()}{entity_type.title()}Fact"
                            promoted_facts[entity_type].append(semantic_fact)
        
        # Structured entity logging - one line summary
        if entity_counts:
            entity_summary = ", ".join([f"{entity_type}:{count}" for entity_type, count in entity_counts.items()])
            self.logger.logger.debug(f"🎯 Domain entities: {entity_summary}")
        
        total_promoted = sum(len(facts) for facts in promoted_facts.values())
        self.logger.entity(f"✅ Total {source} facts promoted: {total_promoted}")
        
        return promoted_facts


if __name__ == "__main__":
    # Test semantic fact extraction
    test_text = """
    OSHA requires fall protection at heights over 6 feet. The regulation 29 CFR 1926.501 
    mandates that employers must provide safety equipment. Companies should invest in 
    training programs. The average cost of compliance is $42,000 per workplace.
    Proper safety equipment saves $4 for every $1 invested. ISO 14122 provides 
    international safety standards. Contact OSHA at (202) 693-1999 for guidance.
    Safety violations may result in penalties up to $136,532.
    """
    
    extractor = SemanticFactExtractor()
    results = extractor.extract_semantic_facts(test_text)
    
    # Test function - keep as print statements for testing
    print("=== SEMANTIC FACT EXTRACTION ===")
    print(json.dumps(results, indent=2))
    print(f"\n✅ Total semantic facts: {results['semantic_summary']['total_facts']}")
    print(f"✅ Fact breakdown: {results['semantic_summary']['fact_types']}")
    print(f"✅ Normalized entities: {len(results['normalized_entities'])}")