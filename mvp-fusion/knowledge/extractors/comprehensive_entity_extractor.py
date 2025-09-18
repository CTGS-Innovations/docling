"""
Comprehensive Entity & Relationship Extractor for Scout MVP-Fusion
Extracts ALL named entities, relationships, and quantifiable data
Uses FLPC Rust regex for maximum performance across all patterns
"""

try:
    from . import fast_regex as re  # MVP-Fusion standard: FLPC Rust regex
except ImportError:
    import sys
    sys.path.insert(0, '.')
    import fast_regex as re
    
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import sys
from pathlib import Path

# Import centralized logging
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.logging_config import get_fusion_logger

# Import conservative person extractor
try:
    from utils.person_entity_extractor import PersonEntityExtractor
    CONSERVATIVE_PERSON_AVAILABLE = True
except ImportError:
    CONSERVATIVE_PERSON_AVAILABLE = False

@dataclass
class MoneyEntity:
    """Financial amounts with context"""
    amount: str
    currency: str
    context: str
    normalized_value: float

@dataclass
class PercentageEntity:
    """Percentages with what they measure"""
    value: float
    subject: str
    context: str
    trend: Optional[str] = None  # increase, decrease, stable

@dataclass
class MeasurementEntity:
    """Any measurement with units"""
    value: str
    unit: str
    category: str  # distance, weight, time, temperature, etc.
    imperial_metric_pair: Optional[str] = None

@dataclass
class DateTimeEntity:
    """Dates, times, and periods"""
    text: str
    type: str  # date, time, duration, period
    normalized: Optional[str] = None

@dataclass
class OrganizationEntity:
    """Organizations, companies, agencies"""
    name: str
    type: str  # government, company, nonprofit, etc.
    acronym: Optional[str] = None
    references: List[str] = field(default_factory=list)

@dataclass
class PersonEntity:
    """People mentioned in text"""
    full_name: str
    role: Optional[str] = None
    organization: Optional[str] = None

@dataclass
class LocationEntity:
    """Geographic locations"""
    name: str
    type: str  # country, state, city, address, etc.
    context: str

@dataclass
class RegulatoryEntity:
    """Regulations, standards, laws"""
    identifier: str
    type: str  # OSHA, CFR, ISO, ANSI, etc.
    title: Optional[str] = None
    section: Optional[str] = None

@dataclass
class StatisticEntity:
    """Statistical data points"""
    value: str
    metric: str
    comparison: Optional[str] = None
    time_period: Optional[str] = None

@dataclass
class RelationshipEntity:
    """Relationships between entities"""
    entity1: str
    entity1_type: str
    relationship: str
    entity2: str
    entity2_type: str
    confidence: float

class ComprehensiveEntityExtractor:
    """
    Extracts ALL entities and relationships using FLPC Rust regex
    Maximizes information extraction from any document
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_fusion_logger(__name__)
        # All patterns use FLPC Rust regex for performance
        self._initialize_patterns()
        
        # Initialize conservative person extractor
        self.person_extractor = None
        if CONSERVATIVE_PERSON_AVAILABLE:
            try:
                # Try to load with corpus configuration
                corpus_config = config.get('corpus', {}) if config else {}
                
                # Load corpus files if paths are provided
                first_names_path = corpus_config.get('first_names_path')
                last_names_path = corpus_config.get('last_names_path')
                organizations_path = corpus_config.get('organizations_path')
                
                # Convert string paths to Path objects
                first_names_path = Path(first_names_path) if first_names_path else None
                last_names_path = Path(last_names_path) if last_names_path else None
                organizations_path = Path(organizations_path) if organizations_path else None
                
                self.person_extractor = PersonEntityExtractor(
                    first_names_path=first_names_path,
                    last_names_path=last_names_path,  
                    organizations_path=organizations_path,
                    min_confidence=corpus_config.get('person_min_confidence', 0.7)
                )
                
                # Load default corpus if no paths provided
                if not any([first_names_path, last_names_path]):
                    self._load_default_corpus()
                    
                self.logger.logger.debug("✅ Conservative person extractor initialized")
            except Exception as e:
                self.logger.logger.warning(f"⚠️ Could not initialize conservative person extractor: {e}")
                self.person_extractor = None
    
    def _load_default_corpus(self):
        """Load default corpus from foundation data files"""
        try:
            base_dir = Path(__file__).parent.parent / 'corpus' / 'foundation_data'
            
            # Load first names
            first_names_file = base_dir / 'first_names_top.txt'
            if first_names_file.exists():
                with open(first_names_file, 'r') as f:
                    self.person_extractor.first_names = {line.strip().lower() for line in f if line.strip()}
                self.logger.logger.debug(f"Loaded {len(self.person_extractor.first_names)} first names")
            
            # Load last names  
            last_names_file = base_dir / 'last_names_top.txt'
            if last_names_file.exists():
                with open(last_names_file, 'r') as f:
                    self.person_extractor.last_names = {line.strip().lower() for line in f if line.strip()}
                self.logger.logger.debug(f"Loaded {len(self.person_extractor.last_names)} last names")
                
        except Exception as e:
            self.logger.logger.warning(f"Could not load default corpus: {e}")
    
    def _clean_context(self, context: str) -> str:
        """Clean context text by normalizing whitespace, removing line breaks, and handling unicode"""
        if not context:
            return ""
        
        # Clean up unicode and special characters for clean text output
        try:
            # Replace common problematic unicode sequences with readable equivalents
            context = context.replace('\\u2014', '—')  # em-dash
            context = context.replace('\\u2013', '–')  # en-dash
            context = context.replace('\\u2019', "'")  # right single quote
            context = context.replace('\\u201c', '"')  # left double quote
            context = context.replace('\\u201d', '"')  # right double quote
            
            # Remove any remaining escape sequences that could cause encoding issues
            import re
            context = re.sub(r'\\x[0-9a-fA-F]{2}', ' ', context)  # Remove \xXX sequences
            context = re.sub(r'\\u[0-9a-fA-F]{4}', ' ', context)  # Remove \uXXXX sequences
            
        except:
            pass  # Keep original if processing fails
            
        # Replace multiple whitespace chars (including newlines) with single space
        cleaned = ' '.join(context.split()).strip()
        
        # Limit context length to prevent excessive output, but break at word boundaries
        if len(cleaned) > 200:
            # Find the last space before the 200 char limit to avoid cutting mid-word
            truncated = cleaned[:200]
            last_space = truncated.rfind(' ')
            if last_space > 150:  # Only break at word boundary if it's reasonably close
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."
        
        return cleaned
    
    def _is_valid_entity(self, entity_text: str) -> bool:
        """Validate entity to filter out malformed entries with formatting issues"""
        if not entity_text or len(entity_text.strip()) < 2:
            return False
        
        # Filter out entities that are mostly whitespace or formatting
        if len(entity_text.strip()) / len(entity_text) < 0.5:
            return False
            
        # Filter out entities with excessive special characters
        special_char_count = sum(1 for c in entity_text if not c.isalnum() and c not in ' .-')
        if special_char_count > len(entity_text) * 0.3:
            return False
            
        # Filter out single characters or very short nonsense
        if len(entity_text.strip()) < 3 and not entity_text.strip().isupper():
            return False
            
        return True
    
    def _initialize_patterns(self):
        """Initialize all extraction patterns"""
        
        # Money patterns - comprehensive currency support
        self.money_patterns = [
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:billion|million|thousand|hundred))?',  # $1,234.56 million
            r'USD\s*[\d,]+(?:\.\d{2})?',  # USD 1234.56
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|cents?)',  # 100 dollars
            r'€[\d,]+(?:\.\d{2})?',  # €1,234.56
            r'£[\d,]+(?:\.\d{2})?',  # £1,234.56
            r'¥[\d,]+',  # ¥1234
        ]
        
        # Percentage patterns
        self.percentage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)',  # 15.5% or 15.5 percent
            r'(\d+(?:\.\d+)?)\s*(?:percentage|pct)',  # 15.5 percentage
            r'(\d+)-(\d+)\s*(?:percent|%)',  # 10-15%
            r'(\d+(?:\.\d+)?)\s*%\s*(?:increase|decrease|growth|decline)',  # 5% increase
        ]
        
        # Measurement patterns - comprehensive units
        self.measurement_patterns = [
            # Distance
            r'(\d+(?:\.\d+)?)\s*(inches?|feet?|yards?|miles?|meters?|kilometers?|cm|mm|km|m)\b',
            # Weight
            r'(\d+(?:\.\d+)?)\s*(pounds?|lbs?|ounces?|oz|tons?|kilograms?|kg|grams?|g)\b',
            # Time
            r'(\d+(?:\.\d+)?)\s*(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b',
            # Temperature
            r'(\d+(?:\.\d+)?)\s*(?:degrees?\s*)?(?:fahrenheit|celsius|F|C)\b',
            # Area/Volume
            r'(\d+(?:\.\d+)?)\s*(?:square|cubic|sq|cu)\s*(feet?|meters?|inches?)',
        ]
        
        # Date/Time patterns
        self.datetime_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2023-12-31
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # 12/31/2023
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',  # January 1, 2023
            r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?',  # 12:30 PM
            r'(?:Q[1-4]|first|second|third|fourth)\s+quarter\s+\d{4}',  # Q1 2023
            r'(?:fiscal|calendar)\s+year\s+\d{4}',  # fiscal year 2023
        ]
        
        # Organization patterns
        self.organization_patterns = [
            r'(?:OSHA|EPA|FDA|CDC|NIOSH|ANSI|ISO|NFPA|ASTM)\b',  # Regulatory bodies
            r'(?:Inc|LLC|Ltd|Corp|Corporation|Company|Co\.?)\b',  # Company suffixes
            r'(?:Department|Agency|Administration|Commission|Bureau)\s+of\s+[A-Z][a-z]+',  # Government
            r'(?:University|Institute|Center|Foundation)\s+(?:of\s+)?[A-Z][a-z]+',  # Educational
            r'[A-Z][A-Z]+(?:\s+[A-Z][A-Z]+)*',  # Acronyms (IBM, DOL, etc.)
        ]
        
        # Person patterns (challenging but attempting)
        self.person_patterns = [
            r'(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*',  # Titled names
            r'[A-Z][a-z]+\s+[A-Z]\.\s+[A-Z][a-z]+',  # John Q. Public
            r'[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+(?:Jr\.|Sr\.|III|IV))?',  # Full names with suffix
        ]
        
        # Generate location patterns from centralized geographic data
        self.location_patterns = self._build_location_patterns()
        
        # Regulatory/Standard patterns
        self.regulatory_patterns = [
            r'OSHA\s+\d+(?:[-\.]\w+)*',  # OSHA 3124-12R
            r'\d+\s+CFR\s+[\d\.]+',  # 29 CFR 1926.501
            r'ISO\s+\d+(?::\d+)?',  # ISO 9001:2015
            r'ANSI\s+[A-Z]\d+(?:\.\d+)*',  # ANSI A14.3
            r'NFPA\s+\d+',  # NFPA 70
            r'Section\s+[\d\.]+(?:\([a-z]\))?',  # Section 5(a)(1)
            r'Part\s+\d+',  # Part 1926
            r'Subpart\s+[A-Z]',  # Subpart M
        ]
        
        # Statistical patterns
        self.statistical_patterns = [
            r'(\d+(?:,\d+)?)\s+(?:injuries|fatalities|accidents|incidents)\s+(?:per|annually)',
            r'(\d+(?:\.\d+)?)\s*(?:times|x)\s+(?:more|less|higher|lower)',
            r'(?:average|median|mean)\s+(?:of\s+)?(\d+(?:\.\d+)?)',
            r'(\d+)\s+out\s+of\s+(\d+)',
            r'(\d+(?:\.\d+)?)\s+per\s+(\d+(?:,\d+)?)',
        ]
        
        # Relationship indicator words
        self.relationship_indicators = {
            'requires': 'requirement',
            'must': 'obligation',
            'causes': 'causation',
            'prevents': 'prevention',
            'leads to': 'consequence',
            'results in': 'result',
            'depends on': 'dependency',
            'applies to': 'application',
            'exempt from': 'exemption',
            'responsible for': 'responsibility',
        }
    
    def extract_money(self, text: str) -> List[MoneyEntity]:
        """Extract all monetary values"""
        entities = []
        
        for pattern in self.money_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context
                start = max(0, match.start(0) - 50)
                end = min(len(text), match.end(0) + 50)
                context = self._clean_context(text[start:end])
                
                # Parse amount and currency
                amount_text = match.group(0)
                currency = 'USD' if '$' in amount_text else 'OTHER'
                
                # Normalize value
                normalized = self._normalize_money(amount_text)
                
                entity = MoneyEntity(
                    amount=amount_text,
                    currency=currency,
                    context=context,
                    normalized_value=normalized
                )
                entities.append(entity)
        
        return entities
    
    def extract_percentages(self, text: str) -> List[PercentageEntity]:
        """Extract all percentage values"""
        entities = []
        
        for pattern in self.percentage_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get context
                start = max(0, match.start(0) - 50)
                end = min(len(text), match.end(0) + 50)
                context = self._clean_context(text[start:end])
                
                # Extract value
                try:
                    value = float(match.group(1))
                except:
                    value = 0.0
                
                # Determine trend
                trend = None
                if 'increase' in context.lower():
                    trend = 'increase'
                elif 'decrease' in context.lower() or 'decline' in context.lower():
                    trend = 'decrease'
                
                # Find subject
                subject = self._extract_percentage_subject(context)
                
                entity = PercentageEntity(
                    value=value,
                    subject=subject,
                    context=context,
                    trend=trend
                )
                entities.append(entity)
        
        return entities
    
    def extract_measurements(self, text: str) -> List[MeasurementEntity]:
        """Extract all measurements with units"""
        entities = []
        seen = set()  # Avoid duplicates
        
        for pattern in self.measurement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                measurement_text = match.group(0)
                
                if measurement_text not in seen:
                    seen.add(measurement_text)
                    
                    # Parse measurement components
                    try:
                        value = match.group(1)
                        unit = match.group(2) if len(match.groups()) >= 2 else ""
                    except:
                        value = measurement_text
                        unit = ""
                    
                    category = self._categorize_measurement(unit)
                    
                    # Check for imperial/metric pairs
                    start = match.start(0)
                    end = match.end(0) + 20
                    following = text[end:min(len(text), end+50)]
                    pair = None
                    if '(' in following:
                        pair_match = re.search(r'\(([^)]+)\)', following)
                        if pair_match:
                            pair = pair_match.group(1)
                    
                    entity = MeasurementEntity(
                        value=value,
                        unit=unit,
                        category=category,
                        imperial_metric_pair=pair
                    )
                    entities.append(entity)
        
        return entities
    
    def extract_organizations(self, text: str) -> List[OrganizationEntity]:
        """Extract organizations and agencies"""
        entities = []
        seen = set()
        
        for pattern in self.organization_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                org_name = match.group(0)
                
                # Clean the organization name to remove line breaks
                clean_org_name = self._clean_context(org_name)
                
                if (clean_org_name not in seen and len(clean_org_name) > 2 and 
                    self._is_valid_entity(clean_org_name)):  # Filter out malformed entities
                    seen.add(clean_org_name)
                    org_name = clean_org_name
                    
                    # Determine type
                    org_type = self._categorize_organization(org_name)
                    
                    # Check if it's an acronym
                    acronym = org_name if org_name.isupper() and len(org_name) <= 10 else None
                    
                    entity = OrganizationEntity(
                        name=org_name,
                        type=org_type,
                        acronym=acronym
                    )
                    entities.append(entity)
        
        return entities
    
    def extract_people(self, text: str) -> List[PersonEntity]:
        """Extract person names using conservative validation"""
        entities = []
        
        # Use conservative person extractor if available
        if self.person_extractor:
            try:
                conservative_persons = self.person_extractor.extract_persons(text)
                self.logger.logger.debug(f"🎯 Conservative person extractor found {len(conservative_persons)} validated persons")
                
                for person in conservative_persons:
                    # Extract role from context
                    role = self._extract_role(person.get('context', ''))
                    
                    entity = PersonEntity(
                        full_name=person['text'],
                        role=role,
                        organization=None  # Could be enhanced
                    )
                    entities.append(entity)
                    
                return entities
                
            except Exception as e:
                self.logger.logger.warning(f"Conservative person extraction failed: {e}")
                # Fall back to original method below
        
        # Fallback to original regex-based method (with minimal filtering)
        self.logger.logger.debug("🔄 Falling back to regex-based person extraction")
        seen = set()
        
        for pattern in self.person_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(0)
                
                # Clean the name to remove line breaks
                clean_name = self._clean_context(name)
                
                # Apply very strict filtering to reduce false positives
                if clean_name not in seen and not self._is_false_positive_name(clean_name):
                    seen.add(clean_name)
                    name = clean_name
                    
                    # Try to extract role from context
                    start = max(0, match.start(0) - 50)
                    end = min(len(text), match.end(0) + 50)
                    context = self._clean_context(text[start:end])
                    role = self._extract_role(context)
                    
                    entity = PersonEntity(
                        full_name=name,
                        role=role,
                        organization=None  # Could be enhanced
                    )
                    entities.append(entity)
        
        return entities
    
    def extract_locations(self, text: str) -> List[LocationEntity]:
        """Extract geographic locations"""
        entities = []
        seen = set()
        
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                location = match.group(0)
                
                # Clean the location name to remove line breaks
                clean_location = self._clean_context(location)
                
                if clean_location not in seen:
                    seen.add(clean_location)
                    location = clean_location
                    
                    # Get context
                    start = max(0, match.start(0) - 30)
                    end = min(len(text), match.end(0) + 30)
                    context = self._clean_context(text[start:end])
                    
                    # Categorize location
                    loc_type = self._categorize_location(location)
                    
                    entity = LocationEntity(
                        name=location,
                        type=loc_type,
                        context=context
                    )
                    entities.append(entity)
        
        return entities
    
    def extract_regulations(self, text: str) -> List[RegulatoryEntity]:
        """Extract regulatory references"""
        entities = []
        
        for pattern in self.regulatory_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                identifier = self._clean_context(match.group(0))
                
                # Determine type
                reg_type = identifier.split()[0] if ' ' in identifier else identifier[:4]
                
                entity = RegulatoryEntity(
                    identifier=identifier,
                    type=reg_type,
                    title=None,
                    section=None
                )
                entities.append(entity)
        
        return entities
    
    def extract_statistics(self, text: str) -> List[StatisticEntity]:
        """Extract statistical information"""
        entities = []
        
        for pattern in self.statistical_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get full context
                start = max(0, match.start(0) - 50)
                end = min(len(text), match.end(0) + 50)
                context = self._clean_context(text[start:end])
                
                entity = StatisticEntity(
                    value=match.group(0),
                    metric=self._extract_metric(context),
                    comparison=self._extract_comparison(context),
                    time_period=self._extract_time_period(context)
                )
                entities.append(entity)
        
        return entities
    
    def extract_relationships(self, text: str, entities: Dict[str, List]) -> List[RelationshipEntity]:
        """Extract relationships between entities"""
        relationships = []
        
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            # Look for relationship indicators
            for indicator, rel_type in self.relationship_indicators.items():
                if indicator in sentence.lower():
                    # Find entities in this sentence
                    sentence_entities = self._find_entities_in_sentence(sentence, entities)
                    
                    # Create relationships between entities
                    if len(sentence_entities) >= 2:
                        for i in range(len(sentence_entities) - 1):
                            rel = RelationshipEntity(
                                entity1=sentence_entities[i]['name'],
                                entity1_type=sentence_entities[i]['type'],
                                relationship=rel_type,
                                entity2=sentence_entities[i+1]['name'],
                                entity2_type=sentence_entities[i+1]['type'],
                                confidence=0.7
                            )
                            relationships.append(rel)
        
        return relationships
    
    def extract_all_entities(self, text: str, global_entities: Dict = None) -> Dict[str, Any]:
        """
        Enrich global entities with domain-specific context and extract domain-specific entities.
        
        Architecture:
        - ENRICHMENT: Use global_entities (Core 8) as foundation and enrich with roles/context
        - DOMAIN EXTRACTION: Extract domain-specific entities (money, percentages, etc.)
        - NO RE-DETECTION: Don't duplicate global entity detection
        """
        if global_entities:
            self.logger.logger.debug("🎯 ENRICHMENT MODE: Enriching global entities with domain context...")
        else:
            self.logger.logger.debug("⚠️ FALLBACK MODE: No global entities provided, extracting all entities...")
        
        # ENRICHMENT: Process global entities if provided
        enriched_people = []
        enriched_organizations = []
        enriched_locations = []
        
        if global_entities:
            # Enrich global people entities with roles and context
            global_people = global_entities.get('people', [])
            self.logger.logger.debug(f"🔄 Enriching {len(global_people)} global people entities...")
            
            for person_entity in global_people:
                enriched_person = self._enrich_person_entity(person_entity, text)
                if enriched_person:
                    enriched_people.append(enriched_person)
            
            # Enrich global organizations with additional context
            global_orgs = global_entities.get('organizations', [])
            for org_entity in global_orgs:
                enriched_org = self._enrich_organization_entity(org_entity, text)
                if enriched_org:
                    enriched_organizations.append(enriched_org)
                    
            # Enrich global locations with additional context
            global_locations = global_entities.get('locations', [])
            for loc_entity in global_locations:
                enriched_loc = self._enrich_location_entity(loc_entity, text)
                if enriched_loc:
                    enriched_locations.append(enriched_loc)
        
        # DOMAIN EXTRACTION: Extract domain-specific entities (not part of Core 8)
        all_entities = {
            'money': self.extract_money(text),
            'percentages': self.extract_percentages(text),
            'measurements': self.extract_measurements(text),
            'regulations': self.extract_regulations(text),
            'statistics': self.extract_statistics(text),
            # Use enriched entities or fallback to extraction if no global entities
            'people': enriched_people if global_entities else self.extract_people(text),
            'organizations': enriched_organizations if global_entities else self.extract_organizations(text),
            'locations': enriched_locations if global_entities else self.extract_locations(text)
        }
        
        # Extract relationships
        relationships = self.extract_relationships(text, all_entities)
        
        # Convert to JSON-serializable format
        result = {
            'entities': {
                'financial': [
                    {
                        'amount': m.amount,
                        'currency': m.currency,
                        'normalized': m.normalized_value,
                        'context': self._clean_context(m.context)
                    }
                    for m in all_entities['money']
                ],
                'percentages': [
                    {
                        **{
                            'value': p.value,
                            'subject': p.subject,
                            'context': self._clean_context(p.context)
                        },
                        **({"trend": p.trend} if p.trend else {})
                    }
                    for p in all_entities['percentages']
                ],
                'measurements': [
                    {
                        'value': m.value,
                        'unit': m.unit,
                        'category': m.category,
                        'pair': m.imperial_metric_pair
                    }
                    for m in all_entities['measurements']
                ],
                'organizations': [
                    {
                        **{
                            'name': self._clean_context(o.name),
                            'type': o.type
                        },
                        **({"acronym": o.acronym} if o.acronym else {})
                    }
                    for o in all_entities['organizations']
                ],
                'people': [
                    {
                        **{"name": self._clean_context(p.full_name)},
                        **({"role": p.role} if p.role else {})
                    }
                    for p in all_entities['people']
                ],
                'locations': [
                    {
                        'name': l.name,
                        'type': l.type
                    }
                    for l in all_entities['locations']
                ],
                'regulations': [
                    {
                        'id': r.identifier,
                        'type': r.type
                    }
                    for r in all_entities['regulations']
                ],
                'statistics': [
                    {
                        'value': s.value,
                        'metric': s.metric,
                        'comparison': s.comparison,
                        'period': s.time_period
                    }
                    for s in all_entities['statistics']
                ]
            },
            'relationships': [
                {
                    'from': r.entity1,
                    'from_type': r.entity1_type,
                    'relation': r.relationship,
                    'to': r.entity2,
                    'to_type': r.entity2_type,
                    'confidence': r.confidence
                }
                for r in relationships
            ],
            'summary': {
                'total_entities': sum(len(v) for v in all_entities.values()),
                'total_relationships': len(relationships),
                'entity_types': {k: len(v) for k, v in all_entities.items()},
                'extraction_engine': 'FLPC Rust Regex',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return result
    
    # Helper methods
    def _normalize_money(self, amount_text: str) -> float:
        """Convert money text to float"""
        # Remove currency symbols and commas
        cleaned = amount_text.replace('$', '').replace(',', '').replace('€', '').replace('£', '').replace('¥', '')
        
        # Handle millions/billions
        multiplier = 1
        if 'billion' in cleaned.lower():
            multiplier = 1_000_000_000
            cleaned = cleaned.lower().replace('billion', '').strip()
        elif 'million' in cleaned.lower():
            multiplier = 1_000_000
            cleaned = cleaned.lower().replace('million', '').strip()
        elif 'thousand' in cleaned.lower():
            multiplier = 1_000
            cleaned = cleaned.lower().replace('thousand', '').strip()
        
        try:
            return float(cleaned) * multiplier
        except:
            return 0.0
    
    def _extract_percentage_subject(self, context: str) -> str:
        """Extract what a percentage refers to"""
        subjects = ['workers', 'injuries', 'costs', 'time', 'projects', 'companies', 'compliance']
        for subject in subjects:
            if subject in context.lower():
                return subject
        return 'unspecified'
    
    def _categorize_measurement(self, unit: str) -> str:
        """Categorize measurement type"""
        unit_lower = unit.lower()
        if any(u in unit_lower for u in ['inch', 'feet', 'yard', 'mile', 'meter', 'km', 'cm', 'mm']):
            return 'distance'
        elif any(u in unit_lower for u in ['pound', 'lb', 'ounce', 'oz', 'ton', 'kilogram', 'kg', 'gram']):
            return 'weight'
        elif any(u in unit_lower for u in ['second', 'minute', 'hour', 'day', 'week', 'month', 'year']):
            return 'time'
        elif any(u in unit_lower for u in ['degree', 'fahrenheit', 'celsius']):
            return 'temperature'
        elif any(u in unit_lower for u in ['square', 'cubic', 'sq', 'cu']):
            return 'area_volume'
        return 'other'
    
    def _categorize_organization(self, name: str) -> str:
        """Categorize organization type"""
        if any(gov in name for gov in ['Department', 'Agency', 'Administration', 'Commission']):
            return 'government'
        elif any(edu in name for edu in ['University', 'Institute', 'College']):
            return 'educational'
        elif any(reg in name for reg in ['OSHA', 'EPA', 'FDA', 'ISO', 'ANSI']):
            return 'regulatory'
        elif any(corp in name for corp in ['Inc', 'LLC', 'Ltd', 'Corp']):
            return 'company'
        return 'organization'
    
    def _is_false_positive_name(self, name: str) -> bool:
        """Filter out false positive names"""
        false_positives = ['United States', 'New York', 'General', 'Major', 'Senior', 'Junior']
        return name in false_positives
    
    def _extract_role(self, context: str) -> Optional[str]:
        """Extract person's role from context"""
        roles = ['director', 'manager', 'supervisor', 'inspector', 'worker', 'contractor', 'president', 'ceo']
        for role in roles:
            if role in context.lower():
                return role
        return None
    
    def _build_location_patterns(self) -> List[str]:
        """Build location regex patterns from centralized geographic data"""
        try:
            from knowledge.corpus.geographic_data import get_geographic_data
            
            geo_data = get_geographic_data()
            
            # Build regex patterns from centralized data
            # Note: For very large lists, we use simplified patterns to avoid regex complexity
            patterns = [
                # Address patterns
                r'\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)',
                
                # Use simplified geographic patterns to avoid massive regex
                # The actual classification will be done by the _categorize_location method
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # General location pattern
            ]
            
            return patterns
            
        except ImportError:
            # Fallback to basic patterns if centralized data unavailable
            return [
                r'(?:United States|Canada|Mexico|UK|EU|China|Japan)',
                r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',
                r'\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)',
            ]
    
    def _categorize_location(self, location: str) -> str:
        """Categorize location type using centralized geographic data"""
        # Import centralized geographic data
        from knowledge.corpus.geographic_data import get_geographic_data
        
        geo_data = get_geographic_data()
        return geo_data.classify_location(location)
    
    def _extract_metric(self, context: str) -> str:
        """Extract what is being measured"""
        metrics = ['injuries', 'fatalities', 'accidents', 'costs', 'time', 'productivity']
        for metric in metrics:
            if metric in context.lower():
                return metric
        return 'unspecified'
    
    def _extract_comparison(self, context: str) -> Optional[str]:
        """Extract comparison information"""
        if 'more than' in context.lower():
            return 'greater_than'
        elif 'less than' in context.lower():
            return 'less_than'
        elif 'equal to' in context.lower():
            return 'equal_to'
        return None
    
    def _extract_time_period(self, context: str) -> Optional[str]:
        """Extract time period from context"""
        periods = ['annually', 'yearly', 'monthly', 'weekly', 'daily', 'per year', 'per month']
        for period in periods:
            if period in context.lower():
                return period
        return None
    
    def _find_entities_in_sentence(self, sentence: str, entities: Dict) -> List[Dict]:
        """Find which entities appear in a sentence"""
        found = []
        
        # Check each entity type
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                # Get entity name based on type
                if entity_type == 'money':
                    name = entity.amount
                elif entity_type == 'organizations':
                    name = entity.name
                elif entity_type == 'regulations':
                    name = entity.identifier
                else:
                    continue
                
                if name in sentence:
                    found.append({'name': name, 'type': entity_type})
        
        return found

    def _enrich_person_entity(self, person_entity: Dict, text: str) -> Dict:
        """
        Enrich a global person entity with role and organizational context.
        
        Uses entity span information for precise context extraction.
        """
        try:
            # Extract person name and span information
            person_name = person_entity.get('value', person_entity.get('text', ''))
            start_pos = person_entity.get('start', 0)
            end_pos = person_entity.get('end', len(person_name))
            
            # Get expanded context around the person mention
            context_start = max(0, start_pos - 100)
            context_end = min(len(text), end_pos + 100)
            context = text[context_start:context_end]
            
            # Extract role information from context
            role = self._extract_role_from_context(context, person_name)
            
            # Extract organizational affiliation
            organization = self._extract_organization_from_context(context)
            
            # Clean context for output
            clean_context = self._clean_context(context)
            
            return {
                'name': self._clean_context(person_name),
                'role': role,
                'organization': organization,
                'context': clean_context,
                'span': {'start': start_pos, 'end': end_pos}
            }
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to enrich person entity {person_entity}: {e}")
            return None

    def _enrich_organization_entity(self, org_entity: Dict, text: str) -> Dict:
        """
        Enrich a global organization entity with type and context information.
        """
        try:
            org_name = org_entity.get('value', org_entity.get('text', ''))
            start_pos = org_entity.get('start', 0)
            end_pos = org_entity.get('end', len(org_name))
            
            # Get context around organization mention
            context_start = max(0, start_pos - 80)
            context_end = min(len(text), end_pos + 80)
            context = text[context_start:context_end]
            
            # Determine organization type and add context
            org_type = self._categorize_organization(org_name)
            acronym = org_name if org_name.isupper() and len(org_name) <= 10 else None
            
            return {
                'name': self._clean_context(org_name),
                'type': org_type,
                'acronym': acronym,
                'context': self._clean_context(context),
                'span': {'start': start_pos, 'end': end_pos}
            }
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to enrich organization entity {org_entity}: {e}")
            return None

    def _enrich_location_entity(self, location_entity: Dict, text: str) -> Dict:
        """
        Enrich a global location entity with type and context information.
        """
        try:
            location_name = location_entity.get('value', location_entity.get('text', ''))
            start_pos = location_entity.get('start', 0)
            end_pos = location_entity.get('end', len(location_name))
            
            # Get context around location mention
            context_start = max(0, start_pos - 60)
            context_end = min(len(text), end_pos + 60)
            context = text[context_start:context_end]
            
            # Categorize location type
            loc_type = self._categorize_location(location_name)
            
            return {
                'name': self._clean_context(location_name),
                'type': loc_type,
                'context': self._clean_context(context),
                'span': {'start': start_pos, 'end': end_pos}
            }
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to enrich location entity {location_entity}: {e}")
            return None

    def _extract_role_from_context(self, context: str, person_name: str) -> Optional[str]:
        """
        Extract professional role or title from context around a person's name.
        
        Looks for role indicators before and after the person's name.
        """
        context_lower = context.lower()
        
        # Common role patterns - look for these near the person's name
        role_patterns = [
            # Executive roles
            r'(?:chief|senior|executive|deputy|assistant)\s+(?:executive\s+officer|officer|manager|director)',
            r'(?:president|ceo|cto|cfo|coo|chairman|chairwoman)',
            
            # Management roles  
            r'(?:director|manager|supervisor|superintendent|foreman|lead|coordinator)',
            r'(?:project|site|safety|operations|quality|plant)\s+(?:manager|director|supervisor)',
            
            # Professional titles
            r'(?:engineer|inspector|specialist|analyst|consultant|advisor|representative)',
            r'(?:safety|compliance|risk|quality|environmental)\s+(?:engineer|inspector|specialist|officer)',
            
            # Government/regulatory roles
            r'(?:administrator|commissioner|secretary|assistant\s+secretary|deputy)',
            r'(?:compliance|enforcement|regulatory)\s+(?:officer|specialist|inspector)',
            
            # Worker classifications
            r'(?:contractor|subcontractor|employee|worker|operator|technician)',
            r'(?:construction|maintenance|production|assembly)\s+(?:worker|operator|technician)'
        ]
        
        # Look for role patterns in context
        for pattern in role_patterns:
            matches = re.finditer(pattern, context_lower)
            for match in matches:
                # Check if role is reasonably close to person name (within 50 characters)
                role_pos = match.start()
                person_pos = context_lower.find(person_name.lower())
                
                if person_pos != -1 and abs(role_pos - person_pos) <= 50:
                    role = match.group(0)
                    # Clean up and capitalize properly
                    return ' '.join(word.capitalize() for word in role.split())
        
        # Look for simpler role indicators
        simple_roles = ['director', 'manager', 'supervisor', 'inspector', 'worker', 'contractor', 
                       'president', 'ceo', 'administrator', 'officer', 'engineer', 'specialist']
        
        for role in simple_roles:
            if role in context_lower:
                # Check proximity to person name
                role_pos = context_lower.find(role)
                person_pos = context_lower.find(person_name.lower())
                
                if person_pos != -1 and abs(role_pos - person_pos) <= 30:
                    return role.capitalize()
        
        return None

    def _extract_organization_from_context(self, context: str) -> Optional[str]:
        """
        Extract organizational affiliation from context.
        
        Looks for organization indicators in the context.
        """
        context_lower = context.lower()
        
        # Common organization indicators
        org_patterns = [
            r'(?:at|with|for|from)\s+([A-Z][A-Za-z\s&]+(?:Inc|LLC|Ltd|Corp|Corporation|Company|Co\.?))',
            r'(?:department|agency|administration|commission|bureau)\s+of\s+([A-Za-z\s]+)',
            r'(OSHA|EPA|FDA|CDC|NIOSH|ANSI|ISO|NFPA|ASTM)',
            r'([A-Z][A-Za-z\s]+)\s+(?:department|division|office|unit)'
        ]
        
        for pattern in org_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                org = match.group(1) if len(match.groups()) >= 1 else match.group(0)
                if len(org.strip()) > 2:
                    return self._clean_context(org.strip())
        
        return None


if __name__ == "__main__":
    # Test with OSHA document text
    test_text = """
    Working on and around stairways and ladders is hazardous. Stairways and ladders are major
    sources of injuries and fatalities among construction workers for example, and many of the 
    injuries are serious enough to require time off the job. OSHA rules apply to all stairways 
    and ladders used in construction, alteration, repair, painting, decorating and demolition.
    When there is a break in elevation of 19 inches (48 cm) or more and no ramp, runway,
    embankment or personnel hoist is available, employers must provide a stairway or ladder
    at all worker points of access. OSHA 3124-12R 2003. The standards are found in 29 CFR 1926.
    Studies show that 65% of fall injuries could be prevented with proper safety equipment.
    The average cost of a workplace injury is $42,000. Fall protection systems cost between 
    $500 and $1,500 per worker. Companies can save up to 40% on insurance premiums with 
    proper safety programs. The Department of Labor reports over 100,000 ladder injuries annually.
    ISO 14122 provides international standards for industrial stairs.
    """
    
    extractor = ComprehensiveEntityExtractor()
    results = extractor.extract_all_entities(test_text)
    
    print("=== COMPREHENSIVE ENTITY EXTRACTION ===")
    print(json.dumps(results, indent=2))
    print(f"\n✅ Total entities extracted: {results['summary']['total_entities']}")
    print(f"✅ Entity breakdown: {results['summary']['entity_types']}")
    print(f"✅ Relationships found: {results['summary']['total_relationships']}")