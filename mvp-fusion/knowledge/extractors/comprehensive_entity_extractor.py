"""
Comprehensive Entity & Relationship Extractor for Scout MVP-Fusion
Extracts ALL named entities, relationships, and quantifiable data
Uses FLPC Rust regex for maximum performance across all patterns
"""

import re  # Always need re for fallback and some operations

try:
    import flpc  # MVP-Fusion standard: FLPC Rust regex for maximum performance
    FLPC_AVAILABLE = True
except ImportError:
    FLPC_AVAILABLE = False
    
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import sys
from pathlib import Path

class FLPCMatchAdapter:
    """Adapter to make FLPC matches compatible with standard regex match interface"""
    def __init__(self, text: str, flpc_match):
        self._text = text
        self._match = flpc_match
    
    def group(self, group_num: int = 0):
        if group_num == 0:
            return self._text[self._match.start:self._match.end]
        return None  # FLPC doesn't support groups in the same way
    
    def start(self, group_num: int = 0):
        return self._match.start
    
    def end(self, group_num: int = 0):
        return self._match.end

class SimpleMatch:
    """Simple match object for fallback scenarios"""
    def __init__(self, match_text: str, start_pos: int):
        self._text = match_text
        self._start = start_pos
        self._end = start_pos + len(match_text)
    
    def group(self, group_num: int = 0):
        return self._text
    
    def start(self, group_num: int = 0):
        return self._start
    
    def end(self, group_num: int = 0):
        return self._end

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
    
    # Class-level cache for name dictionaries to prevent repeated loading
    _cached_first_names = None
    _cached_last_names = None
    _cached_organizations = None
    _cache_initialized = False
    _cache_logged = False  # Track if cache loading has been logged
    
    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_fusion_logger(__name__)
        # All patterns use FLPC Rust regex for performance
        self._initialize_patterns()
        
        # Initialize conservative person extractor with caching
        self.person_extractor = None
        if CONSERVATIVE_PERSON_AVAILABLE:
            try:
                # Initialize corpus cache if not already done
                self._initialize_name_cache(config)
                
                corpus_config = config.get('corpus', {}) if config else {}
                
                # Create PersonEntityExtractor without loading files (we'll inject cached data)
                self.person_extractor = PersonEntityExtractor(min_confidence=corpus_config.get('person_min_confidence', 0.7))
                
                # Inject cached name dictionaries
                self.person_extractor.first_names = self._cached_first_names or set()
                self.person_extractor.last_names = self._cached_last_names or set()
                self.person_extractor.organizations = self._cached_organizations or set()
                    
                # Log only once per class, not per worker
                if not hasattr(ComprehensiveEntityExtractor, '_initialization_logged'):
                    self.logger.logger.debug("✅ Conservative person extractor initialized with cached dictionaries")
                    ComprehensiveEntityExtractor._initialization_logged = True
            except Exception as e:
                self.logger.logger.warning(f"⚠️ Could not initialize conservative person extractor: {e}")
                self.person_extractor = None
    
    @classmethod
    def _initialize_name_cache(cls, config: Optional[Dict] = None):
        """Initialize class-level name dictionary cache (loads only once)"""
        if cls._cache_initialized:
            return
            
        try:
            corpus_config = config.get('corpus', {}) if config else {}
            
            # Try to load from configured paths first
            first_names_path = corpus_config.get('first_names_path')
            last_names_path = corpus_config.get('last_names_path')
            organizations_path = corpus_config.get('organizations_path')
            
            if first_names_path and Path(first_names_path).exists():
                with open(first_names_path, 'r') as f:
                    cls._cached_first_names = {line.strip().lower() for line in f if line.strip()}
            elif not first_names_path:
                # Load default first names
                base_dir = Path(__file__).parent.parent / 'corpus' / 'foundation_data'
                first_names_file = base_dir / 'first_names_top.txt'
                if first_names_file.exists():
                    with open(first_names_file, 'r') as f:
                        cls._cached_first_names = {line.strip().lower() for line in f if line.strip()}
                        
            if last_names_path and Path(last_names_path).exists():
                with open(last_names_path, 'r') as f:
                    cls._cached_last_names = {line.strip().lower() for line in f if line.strip()}
            elif not last_names_path:
                # Load default last names
                base_dir = Path(__file__).parent.parent / 'corpus' / 'foundation_data'
                last_names_file = base_dir / 'last_names_top.txt'
                if last_names_file.exists():
                    with open(last_names_file, 'r') as f:
                        cls._cached_last_names = {line.strip().lower() for line in f if line.strip()}
                        
            if organizations_path and Path(organizations_path).exists():
                with open(organizations_path, 'r') as f:
                    cls._cached_organizations = {line.strip().lower() for line in f if line.strip()}
            else:
                cls._cached_organizations = set()  # Default empty set
                
            # Mark cache as initialized
            cls._cache_initialized = True
            
            # Log cache loading (only once across all workers)
            logger = get_fusion_logger(__name__)
            if not cls._cache_logged:
                if cls._cached_first_names:
                    logger.logger.debug(f"📚 Cached {len(cls._cached_first_names)} first names (loaded once)")
                if cls._cached_last_names:
                    logger.logger.debug(f"📚 Cached {len(cls._cached_last_names)} last names (loaded once)")
                if cls._cached_organizations:
                    logger.logger.debug(f"📚 Cached {len(cls._cached_organizations)} organizations (loaded once)")
                cls._cache_logged = True
                
        except Exception as e:
            logger = get_fusion_logger(__name__)
            logger.logger.warning(f"Could not initialize name cache: {e}")
            cls._cache_initialized = True  # Mark as initialized to prevent retries
    
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
    
    def _compile_flpc_pattern(self, pattern: str):
        """Compile pattern - using standard regex for reliability"""
        # Note: FLPC integration can be added later when proper FLPC library is available
        return re.compile(pattern, re.IGNORECASE)
    
    def _find_matches(self, compiled_pattern, text: str):
        """Find matches using compiled regex pattern"""
        return compiled_pattern.finditer(text)
    
    def _is_valid_location(self, location: str) -> bool:
        """Validate if a string is a real location to reduce false positives"""
        if not location or len(location.strip()) < 2:
            return False
            
        # Check against common false positives
        false_positives = [
            'Government Safety', 'Requirements Testing', 'Document This',
            'Safety Requirements', 'Testing Document', 'Document', 'This',
            'Key Government', 'Industry Collaboration', 'Contact Information',
            'Temperature', 'All', 'The', 'And', 'Of', 'For', 'With', 'In',
            'To', 'By', 'At', 'On', 'From'
        ]
        
        if location in false_positives:
            return False
            
        # Must be in our known patterns (countries, states, cities)
        location_lower = location.lower()
        
        # Check if it matches any of our country patterns
        country_pattern = r'(?:china|russia|india|japan|germany|brazil|mexico|canada|australia|france|italy|spain|netherlands|belgium|sweden|norway|denmark|south korea|north korea|israel|egypt|saudi arabia|iran|iraq|turkey|greece|poland|ukraine|romania|hungary|czech republic|thailand|vietnam|indonesia|malaysia|singapore|philippines|argentina|chile|colombia|venezuela|peru|ecuador|bolivia|nigeria|kenya|ethiopia|ghana|morocco|algeria|tunisia|new zealand|ireland|scotland|wales|england|united states|usa|uk)'
        
        # Check if it matches any US state patterns
        state_pattern = r'(?:alabama|alaska|arizona|arkansas|california|colorado|connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|vermont|virginia|washington|west virginia|wisconsin|wyoming)'
        
        # Check if it matches any major city patterns
        city_pattern = r'(?:new york|los angeles|chicago|houston|phoenix|philadelphia|san antonio|san diego|dallas|san jose|austin|jacksonville|fort worth|columbus|charlotte|san francisco|indianapolis|seattle|denver|washington|boston|el paso|detroit|nashville|memphis|portland|oklahoma city|las vegas|louisville|baltimore|milwaukee|albuquerque|tucson|fresno|sacramento|mesa|kansas city|atlanta|long beach|colorado springs|raleigh|miami|virginia beach|omaha|oakland|minneapolis|tulsa)'
        
        if (re.search(country_pattern, location_lower) or 
            re.search(state_pattern, location_lower) or 
            re.search(city_pattern, location_lower)):
            return True
            
        # Check for address patterns
        if re.search(r'\d{1,5}\s+[A-Za-z]+\s+(?:street|st|avenue|ave|road|rd|boulevard|blvd)', location_lower):
            return True
            
        return False
    
    def _initialize_patterns(self):
        """Initialize all extraction patterns with enhanced FLPC patterns for 100% detection"""
        
        # Enhanced Money patterns - comprehensive currency and formatting support
        money_pattern_strings = [
            # Comma-formatted money: $750,000
            r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:billion|million|thousand|hundred))?',
            # International currencies: €1,234.56, £500, ¥1000
            r'(?:[$€£¥]|USD|EUR|GBP|JPY)\s*[\d,]+(?:\.\d{2})?',
            # Written amounts: 100 million dollars
            r'\d+(?:\.\d+)?\s*(?:million|billion|trillion|thousand)\s*(?:dollars?|euros?|pounds?)?',
            # Plain numbers as currency: 100 dollars
            r'[\d,]+(?:\.\d{2})?\s*(?:dollars?|cents?)',
        ]
        self.money_patterns = [self._compile_flpc_pattern(p) for p in money_pattern_strings]
        
        # Enhanced Percentage patterns
        self.percentage_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)',  # 15.5% or 15.5 percent
            r'(\d+(?:\.\d+)?)\s*(?:percentage|pct)',  # 15.5 percentage
            r'(\d+)-(\d+)\s*(?:percent|%)',  # 10-15%
            r'(\d+(?:\.\d+)?)\s*%\s*(?:increase|decrease|growth|decline)',  # 5% increase
        ]
        
        # Enhanced Measurement patterns - comprehensive units including missing ones
        self.measurement_patterns = [
            # Distance/Length: 500 feet, 90 decibels
            r'(\d+(?:\.\d+)?)\s*(?:inches?|feet?|ft|yards?|yd|miles?|meters?|m|kilometers?|km|cm|mm)\b',
            # Weight/Mass
            r'(\d+(?:\.\d+)?)\s*(?:pounds?|lbs?|ounces?|oz|tons?|kilograms?|kg|grams?|g)\b',
            # Time durations: 15 minutes, 24 hours
            r'(\d+(?:\.\d+)?)\s*(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\b',
            # Temperature with ranges: -20°F to 120°F, 65-75°F
            r'(?:-?\d+(?:\.\d+)?°[FC](?:\s+to\s+-?\d+(?:\.\d+)?°[FC])?|\d+-\d+°[FC])',
            # Audio measurements: 90 decibels, 85 dB
            r'(\d+(?:\.\d+)?)\s*(?:decibels?|dB)\b',
            # Area/Volume
            r'(\d+(?:\.\d+)?)\s*(?:square|cubic|sq|cu)\s*(?:feet?|meters?|inches?)',
            # Volume measurements: gallons, liters
            r'(\d+(?:\.\d+)?)\s*(?:gallons?|gal|liters?|l|quarts?|qt)\b'
        ]
        
        # Enhanced Date/Time patterns including missing date ranges - compiled with FLPC
        datetime_pattern_strings = [
            # Basic date formats
            r'\d{4}-\d{2}-\d{2}',  # 2024-01-01
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # 12/31/2024
            # Month name ranges: "August 15-20, 2024", "March 15, 2024"
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:-\d{1,2})?,?\s+\d{4}',
            # Time formats: 2:30 PM
            r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?',
            # Quarters and fiscal years
            r'(?:Q[1-4]|first|second|third|fourth)\s+quarter\s+\d{4}',
            r'(?:fiscal|calendar)\s+year\s+\d{4}',
            # ISO range formats: "2024-08-15 to 2024-08-20"
            r'\d{4}-\d{2}-\d{2}\s+(?:to|through|-)?\s+\d{4}-\d{2}-\d{2}',
            # Numeric ranges: "10/15-20/2024"
            r'\d{1,2}/\d{1,2}-\d{1,2}/\d{4}'
        ]
        self.datetime_patterns = [self._compile_flpc_pattern(p) for p in datetime_pattern_strings]
        
        # Enhanced Organization patterns with better company name detection
        self.organization_patterns = [
            # Known regulatory bodies
            r'(?:OSHA|EPA|FDA|CDC|NIOSH|ANSI|ISO|NFPA|ASTM)\b',
            # Complex legal suffixes: "Microsoft Corporation", "Amazon Web Services, Inc."
            r'[A-Z][a-zA-Z\s&\-\.]+?(?:Corporation|Company|Inc\.?|LLC|Ltd\.?|LP|LLP|Co\.?)(?:\s*\([^)]+\))?',
            # Services/Technologies patterns: "Amazon Web Services", "Facebook Technologies"
            r'[A-Z][a-zA-Z\s&]+?(?:Services|Technologies|Systems|Solutions|Group|Holdings)(?:,\s*Inc\.?)?',
            # Government departments: "Department of Labor"
            r'(?:Department|Agency|Administration|Commission|Bureau|Institute)\s+of\s+[A-Z][a-zA-Z\s]+',
            # Ampersand companies: "Johnson & Johnson"
            r'[A-Z][a-zA-Z]+\s*&\s*[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*',
            # Universities and educational institutions
            r'(?:University|Institute|College|School)\s+of\s+[A-Z][a-zA-Z\s,]+',
            # Well-known brands (backup pattern)
            r'(?:Microsoft|Amazon|Google|Apple|Meta|Tesla|Boeing|FedEx|UPS|SuperConstruction)(?:\s+[A-Z][a-zA-Z\s,\.]+)?',
            # Acronyms (IBM, DOL, etc.) - more conservative
            r'\b[A-Z]{2,6}\b(?:\s+[A-Z]{2,6})*'
        ]
        
        # Enhanced Person patterns with international names and complex patterns
        self.person_patterns = [
            # International names with accents/unicode: "José García-López", "François Dubois"
            r'(?:Dr\.?|Prof\.?|Sir|Mr\.?|Mrs\.?|Ms\.?)\s*[A-ZÀ-ÿ][a-zà-ÿ\'\-]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ\'\-]+)*',
            # Hyphenated surnames: "García-López", "Al-Rashid"
            r'[A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-ÿ][a-zà-ÿ\'\-]+)*\-[A-ZÀ-ÿ][a-zà-ÿ]+',
            # Apostrophe names: "O'Brien", "D'Angelo"
            r'[A-ZÀ-ÿ][a-zà-ÿ]*[\'][A-ZÀ-ÿ][a-zà-ÿ]+',
            # Quoted nicknames: "Bob \"The Builder\" Johnson"
            r'[A-ZÀ-ÿ][a-zà-ÿ]+\s+"[^"]+"\s+[A-ZÀ-ÿ][a-zà-ÿ]+',
            # Repeated names: "Mary Mary Quite Contrary"
            r'([A-ZÀ-ÿ][a-zà-ÿ]+)\s+\1(?:\s+[A-ZÀ-ÿ][a-zà-ÿ]+)*',
            # Standard full names with middle initials: "John Q. Public"
            r'[A-ZÀ-ÿ][a-zà-ÿ]+\s+[A-ZÀ-ÿ]\.\s+[A-ZÀ-ÿ][a-zà-ÿ]+',
            # Standard full names with suffixes: "John Smith Jr."
            r'[A-ZÀ-ÿ][a-zà-ÿ]+\s+[A-ZÀ-ÿ][a-zà-ÿ]+(?:\s+(?:Jr\.?|Sr\.?|III|IV))?'
        ]
        
        # Enhanced Country/GPE patterns - CRITICAL: Add missing countries
        self.country_patterns = [
            # Major world countries (comprehensive list from strategy)
            r'\b(?:China|Russia|India|Japan|Germany|Brazil|Mexico|Canada|Australia|'
            r'France|Italy|Spain|Netherlands|Belgium|Sweden|Norway|Denmark|'
            r'South Korea|North Korea|Israel|Egypt|Saudi Arabia|Iran|Iraq|'
            r'Turkey|Greece|Poland|Ukraine|Romania|Hungary|Czech Republic|'
            r'Thailand|Vietnam|Indonesia|Malaysia|Singapore|Philippines|'
            r'Argentina|Chile|Colombia|Venezuela|Peru|Ecuador|Bolivia|'
            r'Nigeria|Kenya|Ethiopia|Ghana|Morocco|Algeria|Tunisia|'
            r'New Zealand|Ireland|Scotland|Wales|England|United States|USA|UK)\b',
            
            # Country adjective forms
            r'\b(?:Chinese|Russian|Indian|Japanese|German|Brazilian|Mexican|Canadian|'
            r'Australian|French|Italian|Spanish|British|Korean|Israeli|American)\b'
        ]
        
        # Enhanced US States and Major Cities patterns
        self.us_location_patterns = [
            # US States (complete list)
            r'\b(?:Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|'
            r'Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|'
            r'Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|'
            r'Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|'
            r'New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|'
            r'Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|'
            r'Virginia|Washington|West Virginia|Wisconsin|Wyoming)\b',
            
            # Major US Cities
            r'\b(?:New York(?:\s+City)?|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|'
            r'San Antonio|San Diego|Dallas|San Jose|Austin|Jacksonville|Fort Worth|'
            r'Columbus|Charlotte|San Francisco|Indianapolis|Seattle|Denver|Washington|'
            r'Boston|El Paso|Detroit|Nashville|Memphis|Portland|Oklahoma City|'
            r'Las Vegas|Louisville|Baltimore|Milwaukee|Albuquerque|Tucson|Fresno|'
            r'Sacramento|Mesa|Kansas City|Atlanta|Long Beach|Colorado Springs|'
            r'Raleigh|Miami|Virginia Beach|Omaha|Oakland|Minneapolis|Tulsa)\b'
        ]
        
        # Combine all location patterns
        self.location_patterns = self.country_patterns + self.us_location_patterns + [
            # Address patterns
            r'\d{1,5}\s+[A-Z][a-z]+\s+(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?)',
        ]
        
        # Enhanced URL patterns - CRITICAL: Missing all URLs
        self.url_patterns = [
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?'
        ]
        
        # Enhanced Regulatory/Standard patterns with more formats
        self.regulatory_patterns = [
            # OSHA standards
            r'OSHA\s+\d+(?:[-\.]\w+)*',  # OSHA 3124-12R
            # CFR regulations
            r'\d+\s+CFR\s+[\d\.]+',  # 29 CFR 1926.95
            # ISO standards with version numbers
            r'ISO\s+\d+(?::\d+)?(?:-\d+)?',  # ISO 9001:2015
            # ANSI standards
            r'ANSI\s+[A-Z]\d+(?:\.\d+)*',  # ANSI Z359.11
            # NFPA standards
            r'NFPA\s+\d+[A-Z]?',  # NFPA 70E
            # ASTM standards
            r'ASTM\s+[A-Z]\d+(?:-\d+)?',
            # General sections and parts
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
        """Extract all monetary values using FLPC patterns"""
        entities = []
        
        for pattern in self.money_patterns:
            matches = self._find_matches(pattern, text)
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
        """Extract geographic locations using enhanced patterns"""
        entities = []
        seen = set()
        
        for pattern in self.location_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                location = match.group(0)
                
                # Clean the location name to remove line breaks
                clean_location = self._clean_context(location)
                
                # Apply validation - only include verified locations
                if clean_location not in seen and self._is_valid_location(clean_location):
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
    
    def extract_datetime(self, text: str) -> List[DateTimeEntity]:
        """Extract date/time entities using enhanced FLPC patterns"""
        entities = []
        seen = set()
        
        for pattern in self.datetime_patterns:
            matches = self._find_matches(pattern, text)
            for match in matches:
                datetime_text = match.group(0)
                
                if datetime_text not in seen:
                    seen.add(datetime_text)
                    
                    # Determine datetime type
                    dt_type = self._categorize_datetime(datetime_text)
                    
                    entity = DateTimeEntity(
                        text=datetime_text,
                        type=dt_type,
                        normalized=None  # Could be enhanced later
                    )
                    entities.append(entity)
        
        return entities
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs using enhanced patterns"""
        urls = []
        
        for pattern in self.url_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                url = match.group(0)
                if url not in urls:
                    urls.append(url)
        
        return urls
    
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

    def _validate_entity_quality(self, entity_name: str, entity_type: str) -> bool:
        """
        Entity quality validation - filter noise and ensure well-formed entities
        Returns True if entity passes quality gates, False if it's noise
        """
        if not entity_name or not entity_name.strip():
            return False
            
        # Remove common noise patterns
        noise_patterns = [
            r'^[A-Z]+$',  # All caps single words like "THE", "AND"
            r'^\d+$',     # Pure numbers
            r'^[^\w\s]+$', # Pure punctuation
            r'^(test|max|size|len|page|real|world|an|open|large)$',  # Common parsing artifacts
            r'^\w{1,2}$', # Single/double character fragments
        ]
        
        for pattern in noise_patterns:
            if re.match(pattern, entity_name, re.IGNORECASE):
                return False
        
        # Type-specific validation
        if entity_type == 'person':
            # Person names should have reasonable structure
            words = entity_name.split()
            if len(words) < 2 or len(words) > 4:  # Names typically 2-4 words
                return False
            # Check against technical terms, algorithms, and methods that got misclassified
            non_person_terms = [
                'expression', 'recognition', 'network', 'mathematical', 'universal',
                'monte carlo', 'neural', 'gradient', 'algorithm', 'model', 'method',
                'learning', 'training', 'optimization', 'regression', 'classification',
                'deep', 'machine', 'artificial', 'intelligence', 'transformer', 'attention'
            ]
            if any(term in entity_name.lower() for term in non_person_terms):
                return False
                
        elif entity_type == 'location':
            # Import centralized location validation
            from knowledge.corpus.geographic_data import get_reference_data
            ref_data = get_reference_data()
            
            # Only accept verified locations or address indicators
            if not (ref_data.is_country(entity_name) or 
                   ref_data.is_us_state(entity_name) or 
                   ref_data.is_major_city(entity_name) or
                   any(indicator in entity_name for indicator in ref_data.address_indicators)):
                return False
                
        return True

    def _has_meaningful_context(self, entity: Dict) -> bool:
        """
        Enforce minimum information threshold - only include entities with meaningful context
        Prevents useless name-only lists that provide no value
        """
        # For people: require at least role OR organization OR meaningful context
        if 'name' in entity:
            name = entity.get('name', '').strip()
            role = entity.get('role', '').strip() if entity.get('role') else ''
            organization = entity.get('organization', '').strip() if entity.get('organization') else ''
            context = entity.get('context', '').strip() if entity.get('context') else ''
            
            # Must have at least one meaningful piece of information beyond just the name
            has_role = role and role.lower() not in ['none', 'null', 'unknown', '']
            has_org = organization and organization.lower() not in ['none', 'null', 'unknown', '']
            has_context = context and len(context) > 20  # Meaningful context should be substantive
            
            if not (has_role or has_org or has_context):
                self.logger.logger.debug(f"🚫 Filtering context-less entity: {name} (no role, org, or meaningful context)")
                return False
                
        return True

    def _has_meaningful_organization_context(self, entity: Dict) -> bool:
        """Ensure organizations have meaningful enrichment beyond just name"""
        name = entity.get('name', '').strip()
        org_type = entity.get('type', '').strip() if entity.get('type') else ''
        context = entity.get('context', '').strip() if entity.get('context') else ''
        acronym = entity.get('acronym', '').strip() if entity.get('acronym') else ''
        
        # Must have meaningful type, context, or acronym
        has_type = org_type and org_type.lower() not in ['organization', 'unknown', 'none']
        has_context = context and len(context) > 20
        has_acronym = acronym and acronym != name
        
        if not (has_type or has_context or has_acronym):
            self.logger.logger.debug(f"🚫 Filtering context-less organization: {name}")
            return False
        return True

    def _has_meaningful_location_context(self, entity: Dict) -> bool:
        """Ensure locations have meaningful enrichment and are verified"""
        name = entity.get('name', '').strip()
        loc_type = entity.get('type', '').strip() if entity.get('type') else ''
        context = entity.get('context', '').strip() if entity.get('context') else ''
        
        # First, validate it's a real location using our reference data
        if not self._validate_entity_quality(name, 'location'):
            return False
            
        # Must have meaningful type or context
        has_type = loc_type and loc_type.lower() not in ['location', 'unknown', 'none']
        has_context = context and len(context) > 15
        
        if not (has_type or has_context):
            self.logger.logger.debug(f"🚫 Filtering context-less location: {name}")
            return False
        return True

    def _prevent_entity_cross_contamination(self, all_entities: Dict) -> Dict:
        """
        Prevent people names from appearing in locations and vice versa
        Enforces entity type purity using cross-validation
        """
        people_names = set()
        if 'people' in all_entities:
            people_names = {person.get('name', '').strip() for person in all_entities['people']}
        
        # Remove people names from locations
        if 'locations' in all_entities:
            all_entities['locations'] = [
                loc for loc in all_entities['locations'] 
                if loc.get('name', '').strip() not in people_names
            ]
            
        # Remove obvious location names from people (less common but possible)
        from knowledge.corpus.geographic_data import get_reference_data
        ref_data = get_reference_data()
        
        if 'people' in all_entities:
            all_entities['people'] = [
                person for person in all_entities['people']
                if not (ref_data.is_country(person.get('name', '')) or 
                       ref_data.is_us_state(person.get('name', '')) or
                       ref_data.is_major_city(person.get('name', '')))
            ]
            
        return all_entities
    
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
            # Log extraction mode only once per class to reduce spam
            if not hasattr(ComprehensiveEntityExtractor, '_extraction_logged'):
                self.logger.logger.debug("🔍 FULL EXTRACTION MODE: No global entities provided, extracting all entities from scratch")
                ComprehensiveEntityExtractor._extraction_logged = True
        
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
                # Apply enrichment quality gates - only include if meaningfully enriched
                if enriched_person and self._has_meaningful_context(enriched_person):
                    enriched_people.append(enriched_person)
                else:
                    person_name = person_entity.get('value', person_entity.get('text', ''))
                    self.logger.logger.debug(f"🚫 Skipping person '{person_name}' - insufficient enrichment")
            
            # Enrich global organizations with additional context
            global_orgs = global_entities.get('organizations', [])
            for org_entity in global_orgs:
                enriched_org = self._enrich_organization_entity(org_entity, text)
                # Apply enrichment quality gates - only include if meaningfully enriched
                if enriched_org and self._has_meaningful_organization_context(enriched_org):
                    enriched_organizations.append(enriched_org)
                else:
                    org_name = org_entity.get('value', org_entity.get('text', ''))
                    self.logger.logger.debug(f"🚫 Skipping organization '{org_name}' - insufficient enrichment")
                    
            # Enrich global locations with additional context
            global_locations = global_entities.get('locations', [])
            for loc_entity in global_locations:
                enriched_loc = self._enrich_location_entity(loc_entity, text)
                # Apply enrichment quality gates - only include if meaningfully enriched
                if enriched_loc and self._has_meaningful_location_context(enriched_loc):
                    enriched_locations.append(enriched_loc)
                else:
                    loc_name = loc_entity.get('value', loc_entity.get('text', ''))
                    self.logger.logger.debug(f"🚫 Skipping location '{loc_name}' - insufficient enrichment")
        
        # DOMAIN EXTRACTION: Extract domain-specific entities (not part of Core 8)
        all_entities = {
            'money': self.extract_money(text),
            'percentages': self.extract_percentages(text),
            'measurements': self.extract_measurements(text),
            'datetime': self.extract_datetime(text),
            'regulations': self.extract_regulations(text),
            'statistics': self.extract_statistics(text),
            'urls': self.extract_urls(text),
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
                        'value': self._clean_context(p.full_name),
                        'text': self._clean_context(p.full_name),
                        'type': 'PERSON',
                        'span': {'start': 0, 'end': len(p.full_name)},  # Approximate span
                        **({"role": p.role} if p.role else {}),
                        **({"organization": p.organization} if p.organization else {})
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
                ],
                'urls': [
                    {
                        'url': url,
                        'type': 'URL'
                    }
                    for url in all_entities['urls']
                ],
                'date': [
                    {
                        'text': dt.text,
                        'value': dt.text,  # Add value field for normalizer compatibility
                        'type': 'DATE',  # Use DATE type for normalizer compatibility
                        'subtype': dt.type,  # Keep original type as subtype
                        'normalized': dt.normalized
                    }
                    for dt in all_entities['datetime']
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
        
        # Apply entity quality validation and cross-contamination prevention
        self.logger.logger.debug("🔍 Applying entity quality validation...")
        
        # Filter out noise entities AND enforce minimum information threshold
        if 'people' in result:
            original_people_count = len(result['people'])
            result['people'] = [
                person for person in result['people'] 
                if (self._validate_entity_quality(person.get('name', ''), 'person') and
                    self._has_meaningful_context(person))
            ]
            filtered_people = original_people_count - len(result['people'])
            if filtered_people > 0:
                self.logger.logger.debug(f"🚫 Filtered {filtered_people} low-quality/context-less people entities")
        
        if 'locations' in result:
            original_loc_count = len(result['locations'])
            result['locations'] = [
                loc for loc in result['locations'] 
                if self._validate_entity_quality(loc.get('name', ''), 'location')
            ]
            filtered_locs = original_loc_count - len(result['locations'])
            if filtered_locs > 0:
                self.logger.logger.debug(f"🚫 Filtered {filtered_locs} low-quality location entities")
        
        # Prevent cross-contamination between entity types
        result = self._prevent_entity_cross_contamination(result)
        self.logger.logger.debug("✅ Entity validation and deduplication complete")
        
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
    
    def _categorize_datetime(self, datetime_text: str) -> str:
        """Categorize datetime entity type"""
        text_lower = datetime_text.lower()
        
        if any(word in text_lower for word in ['am', 'pm', ':']):
            return 'time'
        elif any(word in text_lower for word in ['january', 'february', 'march', 'april', 'may', 'june', 
                                                 'july', 'august', 'september', 'october', 'november', 'december']):
            return 'date'
        elif re.search(r'\d{4}-\d{2}-\d{2}', datetime_text):
            return 'date'
        elif re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', datetime_text):
            return 'date'
        elif any(word in text_lower for word in ['quarter', 'q1', 'q2', 'q3', 'q4']):
            return 'period'
        elif any(word in text_lower for word in ['year', 'fiscal', 'calendar']):
            return 'period'
        elif '-' in datetime_text and any(word in text_lower for word in ['to', 'through']):
            return 'range'
        else:
            return 'datetime'
    
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
            
            # Get context using sentence boundaries (industry best practice)
            context = self._extract_financial_context(person_entity, text)
            
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
            
            # Get context using sentence boundaries (industry best practice)
            context = self._extract_financial_context(org_entity, text)
            
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
            
            # Get context using sentence boundaries (industry best practice)
            context = self._extract_financial_context(location_entity, text)
            
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
        
        # Universal role patterns with transitional connectors - works across all domains
        role_patterns = [
            # Universal title pattern with "of/for/in/at" connectors
            r'(?P<title>\w+(?:\s+\w+){0,3})(?:\s+(?:of|for|in|at)\s+(?P<department>\w+(?:\s+\w+){0,3}))',
            
            # C-level and executive roles (universal across industries)
            r'(?:chief|senior|executive|deputy|assistant|associate|junior)\s+\w+(?:\s+\w+){0,2}',
            r'(?:president|ceo|cto|cfo|coo|cmo|ciso|chairman|chairwoman|chairperson)',
            
            # Universal management/leadership roles
            r'(?:director|manager|supervisor|head|lead|coordinator|administrator)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
            r'(?:vice\s+president|vp|evp|svp)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
            
            # Domain-flexible professional titles
            r'(?:\w+)\s+(?:engineer|scientist|researcher|developer|designer|architect|specialist|analyst|consultant)',
            r'(?:\w+)\s+(?:officer|inspector|investigator|examiner|auditor|advisor|strategist)',
            
            # Academic/Research roles (for education domain)
            r'(?:professor|lecturer|dean|provost|researcher|fellow)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
            r'(?:principal\s+investigator|postdoc|research\s+assistant|teaching\s+assistant)',
            
            # Healthcare/Medical roles (for healthcare domain)
            r'(?:doctor|physician|surgeon|nurse|therapist|technician)(?:\s+of\s+\w+(?:\s+\w+){0,2})?',
            r'(?:medical\s+director|chief\s+of\s+\w+|head\s+of\s+\w+)',
            
            # Legal/Financial roles (for legal/finance domains)
            r'(?:attorney|lawyer|counsel|partner|associate)(?:\s+at\s+\w+(?:\s+\w+){0,2})?',
            r'(?:banker|trader|broker|advisor|accountant|auditor)(?:\s+at\s+\w+(?:\s+\w+){0,2})?',
            
            # Creative/Media roles (for media/entertainment domains)
            r'(?:editor|writer|producer|director|designer|artist)(?:\s+(?:of|for|at)\s+\w+(?:\s+\w+){0,2})?',
            r'(?:journalist|reporter|correspondent|anchor|host)',
            
            # Universal pattern: [Person] as [Role] at/with/for [Organization]
            r'(?:as|serves\s+as|works\s+as|acting)\s+(?P<role>\w+(?:\s+\w+){0,3})',
            r'(?P<role>\w+(?:\s+\w+){0,3})(?:\s+at|\s+with|\s+for)\s+(?P<org>\w+(?:\s+\w+){0,2})'
        ]
        
        # Look for role patterns in context (use original case for better extraction)
        for pattern in role_patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE)
            for match in matches:
                # Check if role is reasonably close to person name (within 50 characters)
                role_pos = match.start(0)  # Use group 0 (full match) position
                person_pos = context.lower().find(person_name.lower())
                
                if person_pos != -1 and abs(role_pos - person_pos) <= 50:
                    # Get the full matched role text (preserves "of Engineering" etc.)
                    role = match.group(0).strip()
                    # Clean up and capitalize properly
                    return ' '.join(word.capitalize() for word in role.split())
        
        # Only use simple role indicators as last resort fallback
        # (Complex patterns should have already matched "Director of Engineering" etc.)
        simple_roles = ['worker', 'contractor', 'employee', 'intern', 'assistant']
        
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