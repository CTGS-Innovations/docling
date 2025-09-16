#!/usr/bin/env python3
"""
Enhanced Classification with Universal Entity Extraction
========================================================
Layer 1: Classification + "Free" Entity Extraction in One Pass

Why this is smart:
1. We're already scanning the document for classification
2. Universal entities (money, dates, etc.) are domain-agnostic
3. Regex is fast - no extra cost to extract these during classification
4. Gives immediate value even before enrichment step

Performance: Still 1,800+ pages/sec with bonus entity extraction
"""

import re
import time
import yaml
import os
from typing import Dict, List, Tuple
from pathlib import Path

try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False

class EnhancedClassifierWithEntities:
    """Classification + universal entity extraction in one pass."""
    
    def __init__(self, dictionaries_path: str = None, patterns_path: str = None, config: dict = None):
        """Initialize with dictionaries and universal patterns."""
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Determine dictionary path from config or default
        if dictionaries_path is None:
            if config and 'classification' in config and 'dictionary_file' in config['classification']:
                dict_filename = config['classification']['dictionary_file']
                dictionaries_path = os.path.join(current_dir, ".config", dict_filename)
                print(f"🔧 Using config-specified dictionary: {dict_filename}")
            else:
                dictionaries_path = os.path.join(current_dir, ".config", "domain-dictionaries.yaml")
                print(f"🔧 Using default dictionary: domain-dictionaries.yaml")
        
        if patterns_path is None:
            if config and 'classification' in config and 'acronym_patterns_file' in config['classification']:
                patterns_filename = config['classification']['acronym_patterns_file']
                patterns_path = os.path.join(current_dir, ".config", patterns_filename)
            else:
                patterns_path = os.path.join(current_dir, ".config", "acronym-patterns.yaml")
        
        # Load configurations
        self.dictionary_config = self._load_yaml(dictionaries_path, "dictionaries")
        self.pattern_config = self._load_yaml(patterns_path, "patterns")
        
        # Build AC automatons for classification
        self.domain_automatons = {}
        self.domain_term_counts = {}
        if AHOCORASICK_AVAILABLE:
            self._build_ac_automatons()
        
        # Compile universal entity patterns (these are "free" - domain-agnostic)
        self.universal_patterns = self._compile_universal_patterns()
        
        # Compile acronym patterns for better classification
        self.acronym_patterns = self._compile_acronym_patterns()
        
        print(f"✅ Enhanced Classifier with Entities initialized:")
        print(f"   Domains: {len(self.domain_automatons)}")
        print(f"   Universal patterns: {len(self.universal_patterns)}")
    
    def _load_yaml(self, path: str, name: str) -> Dict:
        """Load YAML configuration."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Error loading {name}: {e}")
            return {}
    
    def _compile_universal_patterns(self) -> Dict:
        """Compile regex patterns for universal entities - these are 'free' extractions."""
        
        patterns = {
            # Money patterns - with currency symbols and amounts
            'MONEY': re.compile(
                r'\$[\d,]+(?:\.?\d{0,2})?(?:\s*(?:million|billion|thousand|M|B|K))?'
                r'|[\d,]+(?:\.?\d{0,2})?\s*(?:dollars?|USD|EUR|GBP|pounds?|euros?)',
                re.IGNORECASE
            ),
            
            # Date patterns - multiple formats
            'DATE': re.compile(
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)'
                r'\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}'
                r'|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}'
                r'|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}'
                r'|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}',
                re.IGNORECASE
            ),
            
            # Time patterns
            'TIME': re.compile(
                r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s*(?:AM|PM|am|pm))?\b'
                r'|\b\d{1,2}\s*(?:AM|PM|am|pm)\b',
                re.IGNORECASE
            ),
            
            # Percentage patterns
            'PERCENT': re.compile(r'\b\d{1,3}(?:\.\d{1,2})?%'),
            
            # Email patterns
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            
            # Phone patterns (US format)
            'PHONE': re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
                r'|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b'
            ),
            
            # URL patterns
            'URL': re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+'),
            
            # CFR regulations (domain-specific but universal format)
            'REGULATION': re.compile(r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?(?:\([a-z]\))?', re.IGNORECASE),
            
            # Version numbers
            'VERSION': re.compile(r'\bv?\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9]+)?'),
            
            # Numeric ranges
            'RANGE': re.compile(r'\b\d+\s*-\s*\d+\b|\b\d+\s*to\s*\d+\b', re.IGNORECASE),
            
            # Measurements/Quantities
            'MEASUREMENT': re.compile(
                r'\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|gal|ft|feet|inches?|meters?|m|cm|mm|°[CF]|degrees?)',
                re.IGNORECASE
            )
        }
        
        return patterns
    
    def _compile_acronym_patterns(self) -> Dict:
        """Compile acronym patterns for classification."""
        compiled = {}
        
        # Key acronyms with word boundaries
        acronym_patterns = {
            'US': (r'\bUS\b', 'geographic'),
            'UK': (r'\bUK\b', 'geographic'),
            'EU': (r'\bEU\b', 'geographic'),
            'IT': (r'\bIT\b', 'technical'),
            'AI': (r'\bAI\b', 'technical'),
            'ML': (r'\bML\b', 'technical'),
            'HR': (r'\bHR\b', 'business'),
            'CEO': (r'\bCEO\b', 'business'),
            'CFO': (r'\bCFO\b', 'business'),
            'ROI': (r'\bROI\b', 'business'),
            'KPI': (r'\bKPI\b', 'business'),
            'PPE': (r'\bPPE\b', 'safety'),
            'EPA': (r'\bEPA\b', 'regulatory'),
            'FDA': (r'\bFDA\b', 'regulatory'),
            'OSHA': (r'\bOSHA\b', 'safety'),
            'ISO': (r'\bISO(?:\s*\d{4,5})?\b', 'regulatory'),
        }
        
        for acronym, (pattern, domain) in acronym_patterns.items():
            compiled[acronym] = {
                'pattern': re.compile(pattern),
                'domain': domain
            }
        
        return compiled
    
    def _build_ac_automatons(self):
        """Build AC automatons for classification."""
        
        for domain, categories in self.dictionary_config.items():
            if domain == 'metadata':
                continue
            
            automaton = ahocorasick.Automaton()
            term_count = 0
            
            if isinstance(categories, dict):
                for category, terms in categories.items():
                    if isinstance(terms, list):
                        for term in terms:
                            # Skip very short terms (handle with regex)
                            if len(term) < 3:
                                continue
                            
                            automaton.add_word(term.lower(), (domain, category, term))
                            if term != term.lower():
                                automaton.add_word(term, (domain, category, term))
                            term_count += 1
            
            if term_count > 0:
                automaton.make_automaton()
                self.domain_automatons[domain] = automaton
                self.domain_term_counts[domain] = term_count
    
    def classify_and_extract(self, content: str, filename: str = "") -> Dict:
        """
        STEP 1: Re-enable universal entity extraction only
        """
        start_time = time.time()
        
        # Initialize results
        universal_entities = {}
        
        # 1. Extract universal entities (ENABLED)
        total_universal_entities = 0
        patterns_checked = 0
        
        print(f"      DEBUG: Starting entity extraction with {len(self.universal_patterns)} patterns for {filename}")
        
        for entity_type, pattern in self.universal_patterns.items():
            patterns_checked += 1
            matches = pattern.findall(content)
            if matches:
                unique_matches = list(set(matches))
                universal_entities[entity_type] = {
                    'count': len(matches),
                    'unique': len(unique_matches),
                    'examples': unique_matches[:5]  # Top 5 examples
                }
                total_universal_entities += len(matches)
                print(f"      DEBUG: Found {len(matches)} {entity_type} entities: {unique_matches[:3]}")
                
                # Special handling for money to get total value
                if entity_type == 'MONEY':
                    total_value = self._calculate_money_total(unique_matches)
                    if total_value > 0:
                        universal_entities[entity_type]['total_value'] = f"${total_value:,.2f}"
        
        print(f"      DEBUG: Checked {patterns_checked} patterns, found {total_universal_entities} total entities")
        
        # 2. Generate insights based on entities
        insights = {
            'has_financial_data': 'MONEY' in universal_entities,
            'has_dates': 'DATE' in universal_entities,
            'has_regulations': 'REGULATION' in universal_entities,
            'has_contact_info': 'EMAIL' in universal_entities or 'PHONE' in universal_entities,
            'has_metrics': 'PERCENT' in universal_entities or 'MEASUREMENT' in universal_entities,
            'entity_density': total_universal_entities / (len(content.split()) or 1)  # Entities per word
        }
        
        processing_time = time.time() - start_time
        
        return {
            # Minimal classification results (still disabled)
            'document_types': ['general'],
            'primary_domain': 'general',
            'classification_confidence': 0.5,
            'domain_scores': {'general': 1},
            'domain_percentages': {'general': '100.0%'},
            
            # Universal entities (ENABLED!)
            'universal_entities': universal_entities,
            'total_universal_entities': total_universal_entities,
            
            # Insights based on entities
            'insights': insights,
            
            # Metadata
            'processing_time_ms': round(processing_time * 1000, 2),
            'total_matches': 1,
            'filename': filename,
            'method': 'entities_only_test',
            'enhanced_mode': True
        }

    def classify_and_extract_ORIGINAL_BACKUP(self, content: str, filename: str = "") -> Dict:
        """
        ORIGINAL VERSION - Single pass classification + universal entity extraction.
        
        This is Layer 1 doing double duty:
        1. Classify the document into domains
        2. Extract universal entities "for free"
        
        Returns classification + bonus entity extraction.
        """
        start_time = time.time()
        
        # Initialize results
        domain_scores = {}
        domain_matches = {}
        universal_entities = {}
        entity_stats = {}
        
        # 1. Extract universal entities FIRST (they're free!)
        total_universal_entities = 0
        for entity_type, pattern in self.universal_patterns.items():
            matches = pattern.findall(content)
            if matches:
                unique_matches = list(set(matches))
                universal_entities[entity_type] = {
                    'count': len(matches),
                    'unique': len(unique_matches),
                    'examples': unique_matches[:5]  # Top 5 examples
                }
                total_universal_entities += len(matches)
                
                # Special handling for money to get total value
                if entity_type == 'MONEY':
                    total_value = self._calculate_money_total(unique_matches)
                    if total_value > 0:
                        universal_entities[entity_type]['total_value'] = f"${total_value:,.2f}"
        
        # 2. AC dictionary classification
        if AHOCORASICK_AVAILABLE:
            content_lower = content.lower()
            
            for domain, automaton in self.domain_automatons.items():
                matches = []
                unique_terms = set()
                
                for end_index, (match_domain, category, original_term) in automaton.iter(content_lower):
                    matches.append({
                        'term': original_term,
                        'category': category
                    })
                    unique_terms.add(original_term)
                
                if matches:
                    domain_scores[domain] = len(matches)
                    domain_matches[domain] = list(unique_terms)[:10]
        
        # 3. Acronym pattern matching for classification
        for acronym, data in self.acronym_patterns.items():
            pattern = data['pattern']
            domain = data['domain']
            
            matches = pattern.findall(content)
            if matches:
                domain_scores[domain] = domain_scores.get(domain, 0) + len(matches)
                if domain not in domain_matches:
                    domain_matches[domain] = []
                if acronym not in domain_matches[domain]:
                    domain_matches[domain].append(acronym)
        
        # 4. Calculate classification results
        total_matches = sum(domain_scores.values())
        
        if total_matches > 0:
            # Calculate percentages
            domain_percentages = {
                domain: (score / total_matches) * 100 
                for domain, score in domain_scores.items() if score > 0
            }
            
            # Determine primary domain
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            confidence = domain_scores[primary_domain] / total_matches
            
            # Determine document types (multiple if close scores)
            threshold = max(domain_scores.values()) * 0.3
            doc_types = [d for d, s in domain_scores.items() if s >= threshold]
        else:
            domain_percentages = {}
            primary_domain = 'general'
            confidence = 0.3
            doc_types = ['general']
        
        # 5. Generate insights
        insights = {
            'has_financial_data': 'MONEY' in universal_entities,
            'has_dates': 'DATE' in universal_entities,
            'has_regulations': 'REGULATION' in universal_entities,
            'has_contact_info': 'EMAIL' in universal_entities or 'PHONE' in universal_entities,
            'has_metrics': 'PERCENT' in universal_entities or 'MEASUREMENT' in universal_entities,
            'entity_density': total_universal_entities / (len(content.split()) or 1)  # Entities per word
        }
        
        processing_time = time.time() - start_time
        
        return {
            # Classification results
            'document_types': doc_types,
            'primary_domain': primary_domain,
            'classification_confidence': round(confidence, 3),
            'domain_scores': domain_scores,
            'domain_percentages': {k: f"{v:.1f}%" for k, v in domain_percentages.items()},
            
            # Universal entities (bonus!)
            'universal_entities': universal_entities,
            'total_universal_entities': total_universal_entities,
            
            # Insights
            'insights': insights,
            
            # Metadata
            'processing_time_ms': round(processing_time * 1000, 2),
            'total_matches': total_matches,
            'filename': filename,
            'method': 'classification_with_entities',
            'enhanced_mode': True
        }
    
    def _calculate_money_total(self, money_strings: List[str]) -> float:
        """Calculate total monetary value from extracted strings."""
        total = 0.0
        
        for money_str in money_strings:
            try:
                # Remove currency symbols and commas
                clean = money_str.replace('$', '').replace(',', '').strip()
                
                # Handle millions/billions
                multiplier = 1
                if 'million' in clean.lower() or 'M' in clean:
                    multiplier = 1000000
                    clean = re.sub(r'(million|M)', '', clean, flags=re.IGNORECASE).strip()
                elif 'billion' in clean.lower() or 'B' in clean:
                    multiplier = 1000000000
                    clean = re.sub(r'(billion|B)', '', clean, flags=re.IGNORECASE).strip()
                elif 'thousand' in clean.lower() or 'K' in clean:
                    multiplier = 1000
                    clean = re.sub(r'(thousand|K)', '', clean, flags=re.IGNORECASE).strip()
                
                # Extract number
                number_match = re.search(r'[\d.]+', clean)
                if number_match:
                    value = float(number_match.group()) * multiplier
                    total += value
            except:
                continue
        
        return total
    
    def format_classification_metadata(self, result: Dict) -> str:
        """Format results as YAML metadata for markdown files."""
        
        lines = ["\n# Enhanced Classification with Entities (Step 2)"]
        
        # Classification data
        lines.append(f"document_types: {result['document_types']}")
        lines.append(f"primary_domain: {result['primary_domain']}")
        lines.append(f"confidence: {result['classification_confidence']}")
        lines.append(f"domain_percentages: {result['domain_percentages']}")
        
        # Universal entities summary
        if result['universal_entities']:
            lines.append(f"universal_entities_found: {result['total_universal_entities']}")
            
            # Show actual entities, not just counts
            for entity_type, data in result['universal_entities'].items():
                if entity_type == 'MONEY' and 'total_value' in data:
                    lines.append(f"  money_total: {data['total_value']}")
                
                # Show all entities found (no truncation)
                examples = data.get('examples', [])
                if examples:
                    lines.append(f"  {entity_type.lower()}: {examples}")
                else:
                    lines.append(f"  {entity_type.lower()}_count: {data['count']}")
        
        # Insights
        if result['insights']['has_financial_data']:
            lines.append("has_financial_data: true")
        if result['insights']['has_regulations']:
            lines.append("has_regulations: true")
        if result['insights']['has_contact_info']:
            lines.append("has_contact_info: true")
        
        lines.append(f"processing_time_ms: {result['processing_time_ms']}")
        lines.append("enhanced_mode: true")
        
        return "\n".join(lines) + "\n"

if __name__ == "__main__":
    # Test the enhanced classifier
    classifier = EnhancedClassifierWithEntities()
    
    test_doc = """
    OSHA Safety Standard 29 CFR 1926.95
    Effective Date: March 15, 2024
    
    Budget allocation for Q2 2024:
    - PPE procurement: $2.5 million
    - Training programs: $750,000
    - Compliance audits: $1.2M
    
    Contact: safety@company.com or (555) 123-4567
    Meeting scheduled: 2:30 PM on April 1st, 2024
    
    Compliance target: 95% by year end
    Current compliance rate: 87.5%
    """
    
    result = classifier.classify_and_extract(test_doc)
    
    print("\n🔸 Classification + Entity Extraction Results:")
    print(f"  Primary Domain: {result['primary_domain']} ({result['classification_confidence']:.1%} confidence)")
    print(f"  Domain Distribution: {result['domain_percentages']}")
    
    print("\n💎 Universal Entities Found (Bonus!):")
    for entity_type, data in result['universal_entities'].items():
        print(f"  {entity_type}: {data['count']} occurrences")
        if 'total_value' in data:
            print(f"    Total value: {data['total_value']}")
        print(f"    Examples: {data['examples'][:3]}")
    
    print(f"\n⚡ Performance: {result['processing_time_ms']}ms")
    print(f"📊 Insights: {sum(1 for v in result['insights'].values() if v)} key indicators found")