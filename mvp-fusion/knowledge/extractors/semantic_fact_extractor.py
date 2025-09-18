"""
Semantic Fact Extractor for MVP-Fusion
Implements universal fact schema with typed facts for cross-domain knowledge extraction
Uses FLPC Rust regex + Aho-Corasick for high-performance semantic understanding
"""

try:
    from .fast_regex import FastRegexEngine
    # Use the existing fast_regex wrapper which handles FLPC + fallback
    _regex_engine = FastRegexEngine()
    # Create re-like interface
    re = _regex_engine
    FLPC_AVAILABLE = True
except ImportError:
    import re
    FLPC_AVAILABLE = False

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
import yaml
import sys
from pathlib import Path

# Import centralized logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import get_fusion_logger

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
        self.canonical_map = self._build_canonical_map()
        self.fact_patterns = self._build_fact_patterns()
        self.aho_corasick = self._build_normalizer()
        
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
                r'(\w+)\s+(\d+\s+CFR\s+[\d\.]+)',  # "OSHA 29 CFR 1926.1050"
                r'(ISO\s+\d+(?::\d+)?)',  # "ISO 9001:2015"
                r'(ANSI\s+[A-Z]\d+(?:\.\d+)*)',  # "ANSI A14.3"
                r'(\d+\s+USC\s+[\d\.]+)',  # "29 USC 651"
                r'(Section\s+[\d\.]+(?:\([a-z]\))?)',  # "Section 5(a)(1)"
            ],
            
            'Requirement': [
                r'(must|shall|required|mandatory)\s+(.+?)(?=\.|,|;)',
                r'(should|recommended|advised)\s+(.+?)(?=\.|,|;)', 
                r'(may|optional|permitted)\s+(.+?)(?=\.|,|;)',
                r'(prohibited|forbidden|not\s+allowed)\s+(.+?)(?=\.|,|;)',
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
                r'(\w+(?:\s+\w+)*)\s+(requires?|enforces?|provides?|maintains?|conducts?|issues?)\s+(.+?)(?=\.|,|;)',
                r'(\w+(?:\s+\w+)*)\s+(prevents?|reduces?|increases?|improves?|eliminates?)\s+(.+?)(?=\.|,|;)',
                r'(\w+(?:\s+\w+)*)\s+(applies?\s+to|governs?|regulates?|oversees?)\s+(.+?)(?=\.|,|;)',
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
        """Extract regulation citations as structured facts"""
        facts = []
        
        for pattern in self.fact_patterns['RegulationCitation']:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
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
                        confidence=0.9,
                        span={'start': match.start(), 'end': match.end()},
                        raw_text=raw_text,
                        regulation_id=reg_id,
                        issuing_authority=authority,
                        subject_area='',
                        normalized_entities=normalized_entities
                    )
                    facts.append(fact)
            except:
                continue
                
        return facts
    
    def _extract_requirements(self, text: str, normalized_entities: Dict) -> List[Requirement]:
        """Extract requirements as structured facts"""
        facts = []
        
        for pattern in self.fact_patterns['Requirement']:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
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
                        confidence=0.85,
                        span={'start': match.start(), 'end': match.end()},
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
                for match in re.finditer(pattern, text, re.IGNORECASE):
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
                        confidence=0.8,
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
            match = re.search(pattern, context, re.IGNORECASE)
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
        """Extract action facts (subject-verb-object)"""
        facts = []
        
        for pattern in self.fact_patterns['ActionFact']:
            try:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    subject = match.group(1).strip()
                    action_verb = match.group(2).strip()
                    object_text = match.group(3).strip()
                    
                    fact = ActionFact(
                        fact_type='ActionFact',
                        confidence=0.75,
                        span={'start': match.start(), 'end': match.end()},
                        raw_text=match.group(0),
                        subject=subject,
                        action_verb=action_verb,
                        object=object_text,
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
    
    def _promote_yaml_entities_to_facts(self, existing_entities: Dict, markdown_content: str) -> Dict[str, List]:
        """Dynamic promotion of any YAML entities to structured semantic facts"""
        promoted_facts = {}
        
        self.logger.logger.debug(f"🔄 Dynamically promoting entities: {list(existing_entities.keys())}")
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
                
            self.logger.logger.debug(f"   Processing {entity_type}: {len(entities)} entities")
            promoted_facts[entity_type] = []
            
            for entity in entities:
                if isinstance(entity, dict):
                    # Create semantic fact based on entity type
                    semantic_fact = self._create_dynamic_semantic_fact(entity_type, entity, markdown_content)
                    if semantic_fact:  # Only add non-None facts
                        promoted_facts[entity_type].append(semantic_fact)
                    elif entity_type == 'person':
                        # Log rejected person entities for visibility
                        self.logger.logger.debug(f"🚫 Filtered out false person: '{entity.get('value', 'unknown')}'")
        
        # Remove empty fact type lists
        promoted_facts = {k: v for k, v in promoted_facts.items() if v}
        
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
    
    def _create_dynamic_semantic_fact(self, entity_type: str, entity: Dict, context: str) -> Optional[Dict]:
        """Create semantic fact dynamically based on entity type"""
        # Apply universal text cleaning to all text fields
        raw_text = self._universal_text_clean(entity.get('value', entity.get('text', '')))
        canonical_name = self._universal_text_clean(self._get_canonical_name(entity.get('value', ''), entity_type))
        
        base_data = {
            'fact_type': f"{entity_type.title()}Fact",
            'confidence': 0.85,
            'span': entity.get('span', {}),
            'raw_text': raw_text,
            'entity_type': entity_type,
            'canonical_name': canonical_name,
            'extraction_layer': 'semantic_promotion'
        }
        
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
            self.logger.logger.debug(f"✅ Creating semantic fact for validated person: '{person_name}'")
            
            # Extract role and organization using improved comprehensive extraction
            try:
                from knowledge.extractors.comprehensive_entity_extractor import ComprehensiveEntityExtractor
                comprehensive_extractor = ComprehensiveEntityExtractor()
                
                # Use improved role extraction that handles transitional connectors
                extracted_role = comprehensive_extractor._extract_role_from_context(context, person_name)
                extracted_org = comprehensive_extractor._extract_organization_from_context(context)
                
                # Use extracted values or fall back to entity values
                person_role = extracted_role or entity.get('role')
                person_org = extracted_org or entity.get('organization')
                
            except Exception as e:
                self.logger.logger.debug(f"Fallback to basic role extraction: {e}")
                person_role = entity.get('role')
                person_org = entity.get('organization')
            
            # Extract context for the person
            person_context = self._extract_role_context_from_person(entity, context)
            
            base_data.update({
                'person_name': person_name,
                'person_role': person_role,  # Now uses improved extraction
                'person_organization': person_org,  # Now uses improved extraction
                'person_context': person_context
            })
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
        
        # Filter out empty facts to prevent data pollution
        if not raw_text.strip() and not canonical_name.strip():
            self.logger.logger.debug(f"🚫 Skipping empty {entity_type} fact with no content")
            return None
            
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
        """Extract financial context using sentence boundaries (industry best practice)"""
        span = entity.get('span', {})
        if not span or not context:
            return ""
            
        entity_start = span.get('start', 0)
        entity_end = span.get('end', 0)
        
        # Find sentence boundaries around the entity
        # Look backwards for sentence start
        sentence_start = max(0, entity_start - 200)
        for i in range(entity_start - 1, sentence_start, -1):
            if context[i] in '.!?':
                sentence_start = i + 1
                break
        
        # Look forwards for sentence end  
        sentence_end = min(len(context), entity_end + 200)
        for i in range(entity_end, sentence_end):
            if context[i] in '.!?':
                sentence_end = i + 1
                break
                
        # Extract complete sentences and clean up
        context_text = context[sentence_start:sentence_end].strip()
        
        # Remove partial sentences at start/end
        if not context_text.startswith(('.', '!', '?')):
            # Find first complete sentence
            first_sentence = context_text.find('. ')
            if first_sentence != -1:
                context_text = context_text[first_sentence + 2:]
        
        return context_text
    
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
        print("🔄 Normalizing entity variants...")
        
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
        
        self.logger.logger.debug(f"🔍 Found entities in YAML: {list(existing_entities.keys()) if existing_entities else 'None'}")
        if existing_entities:
            for entity_type, entities in existing_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                print(f"   - {entity_type}: {count} entities")
        else:
            print("   ⚠️  No entities found in YAML structure")
        
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
        
        # Step 6: Extract additional semantic relationships from markdown content
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
        
        # Step 1: Get ALL entities from classification structure (both global and domain)
        entities_section = classification_data.get('entities', {})
        global_entities = entities_section.get('global_entities', {})
        domain_entities = entities_section.get('domain_entities', {})
        
        self.logger.logger.debug(f"🔍 Found entity sections in classification:")
        self.logger.logger.debug(f"   📊 Global entities: {list(global_entities.keys()) if global_entities else 'None'}")
        self.logger.logger.debug(f"   🎯 Domain entities: {list(domain_entities.keys()) if domain_entities else 'None'}")
        
        # Log entity counts for visibility
        if global_entities:
            for entity_type, entities in global_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                self.logger.logger.debug(f"      - global_{entity_type}: {count} entities")
        
        if domain_entities:
            for entity_type, entities in domain_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                self.logger.logger.debug(f"      - domain_{entity_type}: {count} entities")
        
        if not global_entities and not domain_entities:
            self.logger.logger.debug("   ⚠️  No entities found in classification structure")
        
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
    
    def _promote_classification_entities_to_facts(self, existing_entities: Dict, markdown_content: str, source: str = "unknown") -> Dict[str, List]:
        """Dynamic promotion of classification entities to structured semantic facts"""
        promoted_facts = {}
        
        self.logger.logger.debug(f"🔄 Dynamically promoting {source} entities: {list(existing_entities.keys())}")
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
                
            self.logger.logger.debug(f"   Processing {source}_{entity_type}: {len(entities)} entities")
            promoted_facts[entity_type] = []
            
            for entity in entities:
                if isinstance(entity, dict):
                    # Create semantic fact based on entity type
                    semantic_fact = self._create_dynamic_semantic_fact(entity_type, entity, markdown_content)
                    if semantic_fact:
                        # Add source information to semantic fact
                        semantic_fact['extraction_source'] = source
                        semantic_fact['fact_type'] = f"{source.title()}{entity_type.title()}Fact"
                        promoted_facts[entity_type].append(semantic_fact)
        
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