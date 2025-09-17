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
    
    def __init__(self):
        self.canonical_map = self._build_canonical_map()
        self.fact_patterns = self._build_fact_patterns()
        self.aho_corasick = self._build_normalizer()
        
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
        print(f"🔧 Parsing text: {len(text)} characters, starts with: '{text[:50]}...'")
        
        # Split on YAML delimiters
        if text.strip().startswith('---'):
            parts = text.split('---', 2)
            print(f"📄 Found {len(parts)} parts after splitting on '---'")
            if len(parts) >= 3:
                try:
                    yaml_content = parts[1].strip()
                    markdown_content = parts[2].strip()
                    print(f"📄 YAML section: {len(yaml_content)} chars")
                    print(f"📝 Markdown section: {len(markdown_content)} chars")
                    yaml_data = yaml.safe_load(yaml_content)
                    print(f"✅ YAML parsed successfully: {list(yaml_data.keys()) if yaml_data else 'Empty'}")
                    return yaml_data or {}, markdown_content
                except yaml.YAMLError as e:
                    print(f"❌ YAML parsing error: {e}")
                    return {}, text
        
        # No YAML front matter found, treat entire text as markdown
        print("⚠️  No YAML front matter found (doesn't start with '---')")
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
        
        print(f"🔄 Dynamically promoting entities: {list(existing_entities.keys())}")
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
                
            print(f"   Processing {entity_type}: {len(entities)} entities")
            promoted_facts[entity_type] = []
            
            for entity in entities:
                if isinstance(entity, dict):
                    # Create semantic fact based on entity type
                    semantic_fact = self._create_dynamic_semantic_fact(entity_type, entity, markdown_content)
                    if semantic_fact:
                        promoted_facts[entity_type].append(semantic_fact)
        
        total_promoted = sum(len(facts) for facts in promoted_facts.values())
        print(f"✅ Total facts promoted: {total_promoted}")
        
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
            base_data.update({
                'person_name': entity.get('value', ''),
                'role_context': self._extract_role_context(entity, context),
                'organization_affiliation': self._find_organization_context(entity, context)
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
        """Extract financial context around money entity"""
        span = entity.get('span', {})
        if span and context:
            start = max(0, span.get('start', 0) - 100)
            end = min(len(context), span.get('end', 0) + 100)
            return context[start:end].strip()
        return ""
    
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
    
    def _extract_role_context(self, entity: Dict, context: str) -> str:
        """Extract role context for person entities"""
        # Simple role extraction - could be enhanced
        roles = ['director', 'manager', 'supervisor', 'worker', 'inspector', 'ceo', 'president']
        for role in roles:
            if role in context.lower():
                return role
        return ""
    
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
            "financial": 1     # Keep all (usually important)
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
            
            filtered_list = []
            
            for fact in facts:
                canonical_name = fact.get('canonical_name', '').strip()
                entity_type = fact.get('entity_type', '').lower()
                
                # Skip empty names
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
                # Sort by frequency (highest first)
                filtered_list.sort(key=lambda x: x.get('frequency_score', 0), reverse=True)
                filtered_facts[fact_type] = filtered_list
        
        # Step 5: Log filtering results
        total_removed = sum(removed_counts.values())
        print(f"🧹 Filtered out {total_removed} noisy entities:")
        for category, count in removed_counts.items():
            print(f"   - {category}: {count} entities")
        
        # Show top entities by type
        print("🏆 Top entities after filtering:")
        for fact_type, facts in filtered_facts.items():
            if isinstance(facts, list) and facts:
                entity_type = facts[0].get('entity_type', 'unknown')
                top_3 = [(f.get('canonical_name', ''), f.get('frequency_score', 0)) for f in facts[:3]]
                print(f"   - {entity_type}: {top_3}")
        
        return filtered_facts
    
    def extract_semantic_facts(self, text: str) -> Dict[str, Any]:
        """
        Main extraction method: Parse YAML + markdown → promote entities to structured facts
        Returns comprehensive semantic fact graph
        """
        print("🧠 Starting semantic fact extraction...")
        
        # Step 1: Parse YAML front matter and markdown content
        yaml_data, markdown_content = self._parse_yaml_markdown(text)
        print(f"📄 Parsed YAML: {len(yaml_data)} top-level keys found")
        print(f"📝 Markdown content: {len(markdown_content)} characters")
        
        # Step 2: Get existing entities from YAML (already extracted)
        existing_entities = yaml_data.get('classification', {}).get('universal_entities', {})
        if not existing_entities:
            # Fallback to global_entities if structure is different
            existing_entities = yaml_data.get('global_entities', {})
        
        print(f"🔍 Found entities in YAML: {list(existing_entities.keys()) if existing_entities else 'None'}")
        if existing_entities:
            for entity_type, entities in existing_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                print(f"   - {entity_type}: {count} entities")
        else:
            print("   ⚠️  No entities found in YAML structure")
        
        # Step 3: Normalize entities from YAML
        normalized_entities = self._normalize_yaml_entities(existing_entities)
        print(f"🔄 Normalized {len(normalized_entities)} entities from YAML")
        
        # Step 4: Promote existing YAML entities to structured facts (primary method)
        print("⬆️  Promoting YAML entities to structured facts...")
        all_facts = self._promote_yaml_entities_to_facts(existing_entities, markdown_content)
        
        # Step 5: Apply normalization + threshold filtering to reduce noise
        print("🧹 Applying normalization and threshold filtering...")
        all_facts = self._apply_entity_normalization_and_filtering(all_facts)
        
        # Step 6: Extract additional semantic relationships from markdown content
        print("🔍 Extracting semantic relationships from markdown content...")
        relationships = self._extract_semantic_relationships(markdown_content, all_facts)
        if relationships:
            all_facts['relationships'] = relationships
            print(f"   - relationships: {len(relationships)} semantic relationships found")
        
        # Step 7: Build semantic summary
        total_facts = sum(len(facts) for facts in all_facts.values())
        print(f"✅ Total semantic facts extracted: {total_facts}")
        
        result = {
            'semantic_facts': {
                'regulation_citations': [
                    {
                        'regulation_id': f.regulation_id,
                        'authority': f.issuing_authority,
                        'raw_text': f.raw_text,
                        'span': f.span,
                        'confidence': f.confidence
                    }
                    for f in all_facts['regulation_citations']
                ],
                'requirements': [
                    {
                        'requirement': f.requirement_text,
                        'modality': f.modality,
                        'raw_text': f.raw_text,
                        'span': f.span,
                        'confidence': f.confidence
                    }
                    for f in all_facts['requirements']
                ],
                'financial_impacts': [
                    {
                        'amount': f.amount,
                        'currency': f.currency,
                        'impact_type': f.impact_type,
                        'raw_text': f.raw_text,
                        'span': f.span,
                        'confidence': f.confidence
                    }
                    for f in all_facts['financial_impacts']
                ],
                'action_facts': [
                    {
                        'subject': f.subject,
                        'action': f.action_verb,
                        'object': f.object,
                        'raw_text': f.raw_text,
                        'span': f.span,
                        'confidence': f.confidence
                    }
                    for f in all_facts['action_facts']
                ]
            },
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
        print("🧠 Starting semantic fact extraction from classification data...")
        
        # Step 1: Get ALL entities from classification structure (both global and domain)
        entities_section = classification_data.get('entities', {})
        global_entities = entities_section.get('global_entities', {})
        domain_entities = entities_section.get('domain_entities', {})
        
        print(f"🔍 Found entity sections in classification:")
        print(f"   📊 Global entities: {list(global_entities.keys()) if global_entities else 'None'}")
        print(f"   🎯 Domain entities: {list(domain_entities.keys()) if domain_entities else 'None'}")
        
        # Log entity counts for visibility
        if global_entities:
            for entity_type, entities in global_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                print(f"      - global_{entity_type}: {count} entities")
        
        if domain_entities:
            for entity_type, entities in domain_entities.items():
                count = len(entities) if isinstance(entities, list) else 1
                print(f"      - domain_{entity_type}: {count} entities")
        
        if not global_entities and not domain_entities:
            print("   ⚠️  No entities found in classification structure")
        
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
            
        print(f"🔄 Normalized {len(global_normalized)} global + {len(domain_normalized)} domain entities")
        
        # Step 3: Promote classification entities to structured facts (process both)
        print("⬆️  Promoting classification entities to structured facts...")
        
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
        print("🔍 Extracting semantic relationships from markdown content...")
        relationships = self._extract_semantic_relationships(markdown_content, all_facts)
        if relationships:
            all_facts['relationships'] = relationships
            print(f"   - relationships: {len(relationships)} semantic relationships found")
        
        # Step 5: Build semantic summary
        total_facts = sum(len(facts) for facts in all_facts.values())
        print(f"✅ Total semantic facts extracted: {total_facts}")
        
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
        
        print(f"🔄 Dynamically promoting {source} entities: {list(existing_entities.keys())}")
        
        for entity_type, entities in existing_entities.items():
            if not isinstance(entities, list):
                continue
                
            print(f"   Processing {source}_{entity_type}: {len(entities)} entities")
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
        print(f"✅ Total {source} facts promoted: {total_promoted}")
        
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
    
    print("=== SEMANTIC FACT EXTRACTION ===")
    print(json.dumps(results, indent=2))
    print(f"\n✅ Total semantic facts: {results['semantic_summary']['total_facts']}")
    print(f"✅ Fact breakdown: {results['semantic_summary']['fact_types']}")
    print(f"✅ Normalized entities: {len(results['normalized_entities'])}")