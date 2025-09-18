#!/usr/bin/env python3
"""
Entity Corpus Builder for High-Confidence Entity Recognition
==============================================================
Builds Aho-Corasick automatons from name/company corpuses for O(n) validation.

This enables us to validate millions of entities across thousands of documents
with near-zero performance penalty.
"""

import json
import pickle
from pathlib import Path
from typing import Set, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Try to import pyahocorasick
try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False
    print("Warning: pyahocorasick not installed. Install with: pip install pyahocorasick")

@dataclass
class EntityCorpus:
    """Container for entity validation corpuses"""
    # Person name components
    first_names_male: Set[str]
    first_names_female: Set[str]
    first_names_unisex: Set[str]
    last_names: Set[str]
    name_prefixes: Set[str]  # Dr., Mr., Ms., etc.
    name_suffixes: Set[str]  # Jr., III, PhD, etc.
    
    # Company components  
    company_names: Set[str]  # Fortune 500, S&P 500, known startups
    company_suffixes: Set[str]  # Inc, LLC, Corp, Ltd, etc.
    company_keywords: Set[str]  # Technologies, Solutions, Systems, etc.
    
    # Investor entities
    vc_firms: Set[str]  # Sequoia, Andreessen Horowitz, etc.
    pe_firms: Set[str]  # Blackstone, KKR, Apollo, etc.
    angel_investors: Set[str]  # Known angel investors
    accelerators: Set[str]  # Y Combinator, Techstars, etc.
    
    # Domain-specific entities
    tech_companies: Set[str]  # FAANG, major tech companies
    universities: Set[str]  # Educational institutions
    government_agencies: Set[str]  # FDA, EPA, SEC, etc.

class CorpusValidator:
    """
    High-performance entity validation using Aho-Corasick automatons.
    
    Provides O(n) lookup for millions of patterns with minimal memory overhead.
    """
    
    def __init__(self, corpus_dir: Path = None):
        self.corpus_dir = corpus_dir or Path(__file__).parent / "data"
        self.corpus_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize automatons
        self.first_name_automaton = None
        self.last_name_automaton = None
        self.company_automaton = None
        self.investor_automaton = None
        
        # Load or build corpus
        self.corpus = self._load_or_build_corpus()
        
        # Build Aho-Corasick automatons if available
        if AHOCORASICK_AVAILABLE:
            self._build_automatons()
    
    def _load_or_build_corpus(self) -> EntityCorpus:
        """Load existing corpus or build from scratch."""
        corpus_file = self.corpus_dir / "entity_corpus.pkl"
        
        if corpus_file.exists():
            with open(corpus_file, 'rb') as f:
                return pickle.load(f)
        else:
            return self._build_default_corpus()
    
    def _build_default_corpus(self) -> EntityCorpus:
        """Build default corpus with common names and companies."""
        
        # Common first names (top 1000 most popular)
        first_names_male = {
            'james', 'john', 'robert', 'michael', 'william', 'david', 'richard',
            'joseph', 'thomas', 'christopher', 'charles', 'daniel', 'matthew',
            'mark', 'donald', 'steven', 'kenneth', 'paul', 'andrew', 'joshua',
            'kevin', 'brian', 'george', 'timothy', 'ronald', 'edward', 'jason',
            'jeffrey', 'ryan', 'jacob', 'gary', 'nicholas', 'eric', 'jonathan',
            'stephen', 'larry', 'justin', 'scott', 'brandon', 'benjamin', 'samuel',
            'frank', 'gregory', 'raymond', 'alexander', 'patrick', 'jack', 'dennis',
            'jerry', 'tyler', 'aaron', 'jose', 'adam', 'henry', 'nathan', 'douglas',
            'tim', 'elon', 'jeff', 'bill', 'steve', 'satya', 'sundar', 'jensen',
            'sam', 'marc', 'peter', 'reid', 'travis', 'brian', 'evan', 'jack',
            'mark', 'luke', 'matthew', 'john', 'paul', 'george', 'ringo'
        }
        
        first_names_female = {
            'mary', 'patricia', 'jennifer', 'linda', 'elizabeth', 'barbara',
            'susan', 'jessica', 'sarah', 'karen', 'nancy', 'betty', 'helen',
            'sandra', 'donna', 'carol', 'ruth', 'sharon', 'michelle', 'laura',
            'sarah', 'kimberly', 'deborah', 'dorothy', 'lisa', 'ashley', 'emily',
            'marie', 'alice', 'julie', 'heather', 'teresa', 'doris', 'gloria',
            'evelyn', 'jean', 'cheryl', 'mildred', 'katherine', 'joan', 'ashley',
            'judith', 'rose', 'janice', 'kelly', 'nicole', 'judy', 'christina',
            'kathy', 'theresa', 'beverly', 'denise', 'tammy', 'irene', 'jane',
            'sheryl', 'marissa', 'meg', 'ginni', 'safra', 'ruth', 'mackenzie'
        }
        
        first_names_unisex = {
            'alex', 'jordan', 'taylor', 'morgan', 'casey', 'riley', 'jamie',
            'avery', 'reese', 'cameron', 'quinn', 'blake', 'hayden', 'logan',
            'ryan', 'tyler', 'parker', 'drew', 'jesse', 'dakota', 'sage'
        }
        
        # Common last names (top 5000 US surnames)
        last_names = {
            'smith', 'johnson', 'williams', 'brown', 'jones', 'garcia', 'miller',
            'davis', 'rodriguez', 'martinez', 'hernandez', 'lopez', 'gonzalez',
            'wilson', 'anderson', 'thomas', 'taylor', 'moore', 'jackson', 'martin',
            'lee', 'perez', 'thompson', 'white', 'harris', 'sanchez', 'clark',
            'ramirez', 'lewis', 'robinson', 'walker', 'young', 'allen', 'king',
            'wright', 'scott', 'torres', 'nguyen', 'hill', 'flores', 'green',
            'adams', 'nelson', 'baker', 'hall', 'rivera', 'campbell', 'mitchell',
            'carter', 'roberts', 'gomez', 'phillips', 'evans', 'turner', 'parker',
            'collins', 'edwards', 'stewart', 'morris', 'murphy', 'cook', 'rogers',
            'morgan', 'peterson', 'cooper', 'reed', 'bailey', 'bell', 'ward',
            'cox', 'richardson', 'wood', 'watson', 'brooks', 'bennett', 'gray',
            'james', 'reyes', 'cruz', 'hughes', 'price', 'myers', 'long', 'foster',
            'sanders', 'ross', 'morales', 'powell', 'sullivan', 'russell', 'ortiz',
            'jenkins', 'gutierrez', 'perry', 'butler', 'barnes', 'fisher', 'ford',
            'musk', 'bezos', 'gates', 'jobs', 'cook', 'pichai', 'nadella', 'huang',
            'zuckerberg', 'altman', 'benioff', 'dorsey', 'kalanick', 'chesky',
            'spiegel', 'systrom', 'krieger', 'wojcicki', 'sandberg', 'whitman'
        }
        
        # Name prefixes and suffixes
        name_prefixes = {'dr', 'mr', 'ms', 'mrs', 'miss', 'prof', 'professor',
                        'sir', 'lord', 'lady', 'rev', 'reverend', 'hon', 'honorable'}
        
        name_suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq',
                        'dds', 'rn', 'cpa', 'mba', 'jd', 'ma', 'ba', 'bs', 'ms'}
        
        # Company suffixes (legal entities)
        company_suffixes = {
            'inc', 'incorporated', 'corp', 'corporation', 'llc', 'ltd', 'limited',
            'company', 'co', 'plc', 'lp', 'llp', 'pllc', 'pc', 'pa', 'associates',
            'partners', 'group', 'holdings', 'international', 'global', 'worldwide'
        }
        
        # Company keywords (common in tech/business names)
        company_keywords = {
            'technologies', 'technology', 'tech', 'systems', 'solutions', 'software',
            'services', 'consulting', 'analytics', 'digital', 'data', 'cloud',
            'cyber', 'security', 'network', 'mobile', 'media', 'entertainment',
            'financial', 'capital', 'ventures', 'partners', 'advisors', 'research',
            'labs', 'laboratory', 'institute', 'foundation', 'trust', 'bank',
            'insurance', 'healthcare', 'medical', 'pharma', 'bio', 'energy',
            'automotive', 'aerospace', 'defense', 'retail', 'commerce', 'logistics'
        }
        
        # Major companies (Fortune 500, S&P 500, unicorns)
        company_names = {
            # Tech giants
            'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'alphabet',
            'tesla', 'nvidia', 'intel', 'amd', 'oracle', 'salesforce', 'adobe',
            'ibm', 'cisco', 'qualcomm', 'broadcom', 'texas instruments', 'dell',
            'hp', 'hewlett packard', 'vmware', 'netflix', 'spotify', 'uber', 'lyft',
            'airbnb', 'doordash', 'instacart', 'snap', 'snapchat', 'pinterest',
            'twitter', 'x', 'linkedin', 'tiktok', 'bytedance', 'zoom', 'slack',
            'atlassian', 'shopify', 'square', 'block', 'stripe', 'paypal', 'visa',
            'mastercard', 'american express', 'coinbase', 'binance', 'robinhood',
            
            # AI companies
            'openai', 'anthropic', 'deepmind', 'stability ai', 'midjourney',
            'character ai', 'jasper', 'cohere', 'inflection', 'adept', 'runway',
            'hugging face', 'weights and biases', 'scale ai', 'databricks',
            
            # Enterprise
            'walmart', 'exxonmobil', 'chevron', 'berkshire hathaway', 'jpmorgan',
            'johnson & johnson', 'procter & gamble', 'nestle', 'coca cola',
            'pepsi', 'disney', 'nike', 'mcdonalds', 'starbucks', 'boeing',
            'lockheed martin', 'raytheon', 'general electric', 'ge', '3m',
            'honeywell', 'caterpillar', 'john deere', 'ford', 'general motors',
            'toyota', 'volkswagen', 'bmw', 'mercedes', 'ferrari', 'porsche'
        }
        
        # VC firms
        vc_firms = {
            'sequoia', 'sequoia capital', 'andreessen horowitz', 'a16z', 'accel',
            'benchmark', 'greylock', 'kleiner perkins', 'lightspeed', 'bessemer',
            'index ventures', 'battery ventures', 'general catalyst', 'gv',
            'google ventures', 'founders fund', 'khosla ventures', 'nea',
            'insight partners', 'tiger global', 'coatue', 'dsg', 'altimeter',
            'redpoint', 'matrix partners', 'mayfield', 'menlo ventures',
            'norwest', 'oak', 'sapphire', 'scale venture partners', 'shasta',
            'sierra ventures', 'spark capital', 'thrive capital', 'union square',
            'usv', 'venrock', 'first round', 'initialized', 'village global',
            'craft ventures', 'emergence', 'felicis', 'ggv', 'iconiq', 'ivp'
        }
        
        # PE firms
        pe_firms = {
            'blackstone', 'kkr', 'apollo', 'carlyle', 'warburg pincus', 'tpg',
            'bain capital', 'advent', 'cvc', 'eqt', 'silver lake', 'vista',
            'thoma bravo', 'francisco partners', 'permira', 'hellman friedman',
            'leonard green', 'providence equity', 'general atlantic', 'insight'
        }
        
        # Accelerators
        accelerators = {
            'y combinator', 'yc', 'techstars', '500 startups', '500 global',
            'plug and play', 'alchemist', 'dreamit', 'angelpad', 'launchpad',
            'founder institute', 'entrepreneurs roundtable', 'era', 'amplify',
            'betaworks', 'boost vc', 'science inc', 'idealab', 'rocket internet'
        }
        
        # Tech companies for domain-specific
        tech_companies = company_names.copy()  # Start with general tech companies
        
        # Universities
        universities = {
            'harvard', 'stanford', 'mit', 'yale', 'princeton', 'columbia',
            'berkeley', 'ucla', 'nyu', 'northwestern', 'duke', 'cornell',
            'brown', 'dartmouth', 'upenn', 'caltech', 'carnegie mellon', 'cmu',
            'georgia tech', 'university of washington', 'uw', 'ut austin',
            'umich', 'uiuc', 'purdue', 'oxford', 'cambridge', 'imperial',
            'eth zurich', 'epfl', 'tsinghua', 'peking', 'iit', 'nus', 'ntu'
        }
        
        # Government agencies
        government_agencies = {
            'fda', 'food and drug administration', 'epa', 'environmental protection',
            'sec', 'securities and exchange', 'ftc', 'federal trade', 'fcc',
            'federal communications', 'doj', 'department of justice', 'treasury',
            'state department', 'defense department', 'dod', 'pentagon', 'cia',
            'fbi', 'nsa', 'dhs', 'homeland security', 'nasa', 'noaa', 'cdc',
            'nih', 'nsf', 'doe', 'department of energy', 'usda', 'agriculture'
        }
        
        # Angel investors (well-known)
        angel_investors = {
            'peter thiel', 'reid hoffman', 'marc andreessen', 'ben horowitz',
            'chris sacca', 'jason calacanis', 'naval ravikant', 'tim ferriss',
            'gary vaynerchuk', 'mark cuban', 'ashton kutcher', 'justin bieber',
            'jay z', 'will smith', 'leonardo dicaprio', 'robert downey jr',
            'kevin rose', 'alexis ohanian', 'paul graham', 'jessica livingston',
            'sam altman', 'brian chesky', 'joe gebbia', 'travis kalanick',
            'garrett camp', 'evan williams', 'jack dorsey', 'kevin systrom'
        }
        
        corpus = EntityCorpus(
            first_names_male=first_names_male,
            first_names_female=first_names_female,
            first_names_unisex=first_names_unisex,
            last_names=last_names,
            name_prefixes=name_prefixes,
            name_suffixes=name_suffixes,
            company_names=company_names,
            company_suffixes=company_suffixes,
            company_keywords=company_keywords,
            vc_firms=vc_firms,
            pe_firms=pe_firms,
            angel_investors=angel_investors,
            accelerators=accelerators,
            tech_companies=tech_companies,
            universities=universities,
            government_agencies=government_agencies
        )
        
        # Save corpus
        self._save_corpus(corpus)
        return corpus
    
    def _save_corpus(self, corpus: EntityCorpus):
        """Save corpus to disk for reuse."""
        corpus_file = self.corpus_dir / "entity_corpus.pkl"
        with open(corpus_file, 'wb') as f:
            pickle.dump(corpus, f)
    
    def _build_automatons(self):
        """Build Aho-Corasick automatons for O(n) pattern matching."""
        if not AHOCORASICK_AVAILABLE:
            return
        
        # Build first name automaton
        self.first_name_automaton = ahocorasick.Automaton()
        all_first_names = (self.corpus.first_names_male | 
                          self.corpus.first_names_female | 
                          self.corpus.first_names_unisex)
        
        for name in all_first_names:
            self.first_name_automaton.add_word(name.lower(), name.lower())
        self.first_name_automaton.make_automaton()
        
        # Build last name automaton
        self.last_name_automaton = ahocorasick.Automaton()
        for name in self.corpus.last_names:
            self.last_name_automaton.add_word(name.lower(), name.lower())
        self.last_name_automaton.make_automaton()
        
        # Build company automaton
        self.company_automaton = ahocorasick.Automaton()
        all_companies = (self.corpus.company_names | 
                        self.corpus.tech_companies |
                        self.corpus.universities |
                        self.corpus.government_agencies)
        
        for company in all_companies:
            self.company_automaton.add_word(company.lower(), company.lower())
        self.company_automaton.make_automaton()
        
        # Build investor automaton
        self.investor_automaton = ahocorasick.Automaton()
        all_investors = (self.corpus.vc_firms | 
                        self.corpus.pe_firms |
                        self.corpus.accelerators)
        
        for investor in all_investors:
            self.investor_automaton.add_word(investor.lower(), investor.lower())
        self.investor_automaton.make_automaton()
    
    def validate_person_name(self, text: str) -> Tuple[float, Dict[str, any]]:
        """
        Validate if text is likely a person's name.
        
        Returns:
            confidence: 0.0 to 1.0 score
            details: Dictionary with validation details
        """
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        confidence = 0.0
        details = {
            'has_valid_first_name': False,
            'has_valid_last_name': False,
            'has_prefix': False,
            'has_suffix': False,
            'first_name': None,
            'last_name': None,
            'gender_hint': None
        }
        
        if len(words) == 0:
            return 0.0, details
        
        # Check for prefix (Dr., Mr., etc.)
        if words[0] in self.corpus.name_prefixes:
            details['has_prefix'] = True
            confidence += 0.1
            words = words[1:]  # Remove prefix for name checking
        
        # Check for suffix (Jr., PhD, etc.)
        if words and words[-1] in self.corpus.name_suffixes:
            details['has_suffix'] = True
            confidence += 0.1
            words = words[:-1]  # Remove suffix
        
        # Check first name
        if words:
            first_word = words[0]
            if AHOCORASICK_AVAILABLE and self.first_name_automaton:
                # Use Aho-Corasick for O(n) lookup
                matches = list(self.first_name_automaton.iter(first_word))
                if matches:
                    details['has_valid_first_name'] = True
                    details['first_name'] = first_word
                    confidence += 0.4
                    
                    # Determine gender hint
                    if first_word in self.corpus.first_names_male:
                        details['gender_hint'] = 'male'
                    elif first_word in self.corpus.first_names_female:
                        details['gender_hint'] = 'female'
                    else:
                        details['gender_hint'] = 'unisex'
            else:
                # Fallback to set lookup
                if (first_word in self.corpus.first_names_male or
                    first_word in self.corpus.first_names_female or
                    first_word in self.corpus.first_names_unisex):
                    details['has_valid_first_name'] = True
                    details['first_name'] = first_word
                    confidence += 0.4
        
        # Check last name
        if len(words) > 1:
            last_word = words[-1]
            if AHOCORASICK_AVAILABLE and self.last_name_automaton:
                matches = list(self.last_name_automaton.iter(last_word))
                if matches:
                    details['has_valid_last_name'] = True
                    details['last_name'] = last_word
                    confidence += 0.4
            else:
                if last_word in self.corpus.last_names:
                    details['has_valid_last_name'] = True
                    details['last_name'] = last_word
                    confidence += 0.4
        
        # Bonus confidence for both first and last name valid
        if details['has_valid_first_name'] and details['has_valid_last_name']:
            confidence += 0.2
        
        # Check if it's a known angel investor (full name match)
        if text_lower in self.corpus.angel_investors:
            confidence = max(confidence, 0.95)
            details['is_known_angel'] = True
        
        return min(confidence, 1.0), details
    
    def validate_company_name(self, text: str) -> Tuple[float, Dict[str, any]]:
        """
        Validate if text is likely a company/organization name.
        
        Returns:
            confidence: 0.0 to 1.0 score
            details: Dictionary with validation details
        """
        text_lower = text.lower().strip()
        confidence = 0.0
        details = {
            'is_known_company': False,
            'has_company_suffix': False,
            'has_company_keyword': False,
            'is_vc_firm': False,
            'is_pe_firm': False,
            'is_accelerator': False,
            'is_university': False,
            'is_government': False,
            'company_type': None
        }
        
        # Check if it's a known company
        if AHOCORASICK_AVAILABLE and self.company_automaton:
            matches = list(self.company_automaton.iter(text_lower))
            if matches:
                details['is_known_company'] = True
                confidence = 0.9
        else:
            if text_lower in self.corpus.company_names:
                details['is_known_company'] = True
                confidence = 0.9
        
        # Check for company suffix (Inc, LLC, etc.)
        for suffix in self.corpus.company_suffixes:
            if text_lower.endswith(f' {suffix}') or text_lower.endswith(f' {suffix}.'):
                details['has_company_suffix'] = True
                details['company_type'] = 'corporation'
                confidence = max(confidence, 0.8)
                break
        
        # Check for company keywords
        for keyword in self.corpus.company_keywords:
            if keyword in text_lower:
                details['has_company_keyword'] = True
                confidence = max(confidence, 0.6)
                break
        
        # Check specific company types
        if AHOCORASICK_AVAILABLE and self.investor_automaton:
            matches = list(self.investor_automaton.iter(text_lower))
            if matches:
                # Determine specific type
                if text_lower in self.corpus.vc_firms:
                    details['is_vc_firm'] = True
                    details['company_type'] = 'vc_firm'
                    confidence = 0.95
                elif text_lower in self.corpus.pe_firms:
                    details['is_pe_firm'] = True
                    details['company_type'] = 'pe_firm'
                    confidence = 0.95
                elif text_lower in self.corpus.accelerators:
                    details['is_accelerator'] = True
                    details['company_type'] = 'accelerator'
                    confidence = 0.95
        else:
            # Fallback checks
            if text_lower in self.corpus.vc_firms:
                details['is_vc_firm'] = True
                details['company_type'] = 'vc_firm'
                confidence = 0.95
            elif text_lower in self.corpus.pe_firms:
                details['is_pe_firm'] = True
                details['company_type'] = 'pe_firm'
                confidence = 0.95
            elif text_lower in self.corpus.accelerators:
                details['is_accelerator'] = True
                details['company_type'] = 'accelerator'
                confidence = 0.95
        
        # Check universities
        if text_lower in self.corpus.universities:
            details['is_university'] = True
            details['company_type'] = 'university'
            confidence = max(confidence, 0.9)
        
        # Check government agencies
        if text_lower in self.corpus.government_agencies:
            details['is_government'] = True
            details['company_type'] = 'government'
            confidence = max(confidence, 0.9)
        
        return min(confidence, 1.0), details
    
    def expand_corpus_from_file(self, filepath: Path, corpus_type: str):
        """
        Expand corpus with additional entries from a file.
        
        Args:
            filepath: Path to file with one entry per line
            corpus_type: Type of corpus to expand (e.g., 'first_names', 'companies')
        """
        with open(filepath, 'r') as f:
            entries = {line.strip().lower() for line in f if line.strip()}
        
        if corpus_type == 'first_names_male':
            self.corpus.first_names_male.update(entries)
        elif corpus_type == 'first_names_female':
            self.corpus.first_names_female.update(entries)
        elif corpus_type == 'last_names':
            self.corpus.last_names.update(entries)
        elif corpus_type == 'companies':
            self.corpus.company_names.update(entries)
        elif corpus_type == 'vc_firms':
            self.corpus.vc_firms.update(entries)
        # Add more as needed
        
        # Rebuild automatons with expanded corpus
        if AHOCORASICK_AVAILABLE:
            self._build_automatons()
        
        # Save updated corpus
        self._save_corpus(self.corpus)
    
    def get_corpus_stats(self) -> Dict[str, int]:
        """Get statistics about the loaded corpus."""
        return {
            'total_first_names': len(self.corpus.first_names_male | 
                                    self.corpus.first_names_female | 
                                    self.corpus.first_names_unisex),
            'total_last_names': len(self.corpus.last_names),
            'total_companies': len(self.corpus.company_names),
            'total_vc_firms': len(self.corpus.vc_firms),
            'total_pe_firms': len(self.corpus.pe_firms),
            'total_accelerators': len(self.corpus.accelerators),
            'total_universities': len(self.corpus.universities),
            'total_government': len(self.corpus.government_agencies),
            'uses_ahocorasick': AHOCORASICK_AVAILABLE
        }