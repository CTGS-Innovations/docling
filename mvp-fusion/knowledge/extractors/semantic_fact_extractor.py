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
        """Promote existing YAML entities to structured semantic facts"""
        promoted_facts = {
            'regulation_citations': [],
            'requirements': [],
            'financial_impacts': [],
            'action_facts': []
        }
        
        # Promote regulation entities to RegulationCitation facts
        regulations = existing_entities.get('regulation', [])
        for reg in regulations:
            if isinstance(reg, dict):
                fact = RegulationCitation(
                    fact_type='RegulationCitation',
                    confidence=0.9,
                    span=reg.get('span', {}),
                    raw_text=reg.get('value', reg.get('text', '')),
                    regulation_id=reg.get('value', reg.get('text', '')),
                    issuing_authority=self._determine_authority(reg.get('value', '')),
                    subject_area='safety_compliance'
                )
                promoted_facts['regulation_citations'].append(fact)
        
        # Promote money entities to FinancialImpact facts
        money_entities = existing_entities.get('money', [])
        for money in money_entities:
            if isinstance(money, dict):
                amount_text = money.get('value', money.get('text', ''))
                amount = self._parse_money_amount(amount_text)
                fact = FinancialImpact(
                    fact_type='FinancialImpact',
                    confidence=0.8,
                    span=money.get('span', {}),
                    raw_text=amount_text,
                    amount=amount,
                    currency='USD',
                    impact_type='cost',  # Default, could be refined
                    subject='compliance'
                )
                promoted_facts['financial_impacts'].append(fact)
        
        return promoted_facts
    
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
        
        # Step 4: Extract additional semantic facts from markdown content
        print("🔍 Extracting facts from markdown content...")
        all_facts = {
            'regulation_citations': self._extract_regulation_citations(markdown_content, normalized_entities),
            'requirements': self._extract_requirements(markdown_content, normalized_entities),
            'financial_impacts': self._extract_financial_impacts(markdown_content, normalized_entities),
            'action_facts': self._extract_action_facts(markdown_content, normalized_entities)
        }
        
        for fact_type, facts in all_facts.items():
            print(f"   - {fact_type}: {len(facts)} facts from markdown")
        
        # Step 5: Promote existing YAML entities to structured facts
        print("⬆️  Promoting YAML entities to structured facts...")
        promoted_facts = self._promote_yaml_entities_to_facts(existing_entities, markdown_content)
        
        for fact_type, facts in promoted_facts.items():
            print(f"   - {fact_type}: {len(facts)} facts promoted from YAML")
        
        # Step 6: Merge promoted facts with extracted facts
        for fact_type, facts in promoted_facts.items():
            if fact_type in all_facts:
                all_facts[fact_type].extend(facts)
            else:
                all_facts[fact_type] = facts
        
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