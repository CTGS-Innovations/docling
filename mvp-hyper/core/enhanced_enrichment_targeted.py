#!/usr/bin/env python3
"""
Enhanced Targeted Enrichment using Aho-Corasick
================================================
Layer 2 of the efficient pipeline: Domain-specific deep extraction
based on classification results.

Uses classification insights to:
1. Focus on primary domain dictionaries
2. Include secondary domains if significant (>20%)
3. Skip irrelevant domains (<5%) to save cycles
4. Extract detailed entities only where relevant

Performance target: 1,500+ pages/sec with focused extraction
"""

import time
import yaml
import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path

try:
    import ahocorasick
    AHOCORASICK_AVAILABLE = True
except ImportError:
    AHOCORASICK_AVAILABLE = False
    print("⚠️ pyahocorasick not available for enrichment")

class TargetedEnrichment:
    """Targeted domain enrichment based on classification insights."""
    
    def __init__(self, dictionaries_config_path: str = None):
        """Initialize with domain dictionaries for targeted enrichment."""
        
        # Set default config path
        if dictionaries_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dictionaries_config_path = os.path.join(current_dir, ".config", "domain-dictionaries.yaml")
        
        self.dictionaries_config_path = dictionaries_config_path
        
        # Load dictionary configuration
        self.dictionary_config = self._load_dictionary_config()
        
        # Build automatons for each domain (but use selectively)
        self.domain_automatons = {}
        self.category_automatons = {}  # More granular automatons
        
        if AHOCORASICK_AVAILABLE:
            self._build_all_automatons()
            print(f"✅ Targeted Enrichment ready with {len(self.domain_automatons)} domain dictionaries")
        
        # Universal patterns for all domains
        self._compile_universal_patterns()
    
    def _load_dictionary_config(self) -> Dict:
        """Load domain dictionaries from configuration."""
        try:
            with open(self.dictionaries_config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️ Error loading dictionary config: {e}")
            return {}
    
    def _build_all_automatons(self):
        """Build automatons for all domains and categories."""
        
        for domain, categories in self.dictionary_config.items():
            if domain == 'metadata':
                continue
            
            # Build domain-level automaton
            domain_automaton = ahocorasick.Automaton()
            domain_term_count = 0
            
            # Also build category-level automatons for granular control
            if domain not in self.category_automatons:
                self.category_automatons[domain] = {}
            
            if isinstance(categories, dict):
                for category, terms in categories.items():
                    if isinstance(terms, list):
                        # Category-specific automaton
                        cat_automaton = ahocorasick.Automaton()
                        
                        for term in terms:
                            # Add to domain automaton
                            domain_automaton.add_word(term.lower(), (domain, category, term))
                            if term != term.lower():
                                domain_automaton.add_word(term, (domain, category, term))
                            
                            # Add to category automaton
                            cat_automaton.add_word(term.lower(), term)
                            if term != term.lower():
                                cat_automaton.add_word(term, term)
                            
                            domain_term_count += 1
                        
                        if domain_term_count > 0:
                            cat_automaton.make_automaton()
                            self.category_automatons[domain][category] = cat_automaton
            
            if domain_term_count > 0:
                domain_automaton.make_automaton()
                self.domain_automatons[domain] = domain_automaton
    
    def _compile_universal_patterns(self):
        """Compile regex patterns for universal entities."""
        self.universal_patterns = {
            'MONEY': re.compile(r'\$[0-9,]+(?:\.[0-9]{1,2})?(?:\s*(?:million|billion|thousand|M|B|K))?', re.IGNORECASE),
            'DATE': re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{1,2}-\d{1,2}', re.IGNORECASE),
            'PHONE': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'EMAIL': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'CFR_REGULATION': re.compile(r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?(?:\([a-z]\))?', re.IGNORECASE),
            'PERCENT': re.compile(r'\b\d{1,3}(?:\.\d+)?%')
        }
    
    def extract_entities_targeted(self, content: str, classification_result: Dict, 
                                 filename: str = "") -> Dict:
        """
        Extract entities using TARGETED approach based on classification.
        
        Layer 2: Deep extraction focused on relevant domains only.
        
        Args:
            content: Document content
            classification_result: Results from Layer 1 classification
            filename: Optional filename
            
        Returns:
            Detailed entity extraction focused on relevant domains
        """
        start_time = time.time()
        
        if not AHOCORASICK_AVAILABLE:
            return self._fallback_extraction(content, classification_result, filename)
        
        content_lower = content.lower()
        
        # Determine which domains to scan based on classification
        primary_domain = classification_result.get('primary_domain', 'general')
        domain_scores = classification_result.get('domain_scores', {})
        total_score = sum(domain_scores.values()) or 1
        
        # Decide which domains to process
        domains_to_scan = []
        domains_to_skip = []
        
        for domain, score in domain_scores.items():
            percentage = (score / total_score) * 100
            if percentage > 5:  # Only scan domains with >5% relevance
                domains_to_scan.append(domain)
            else:
                domains_to_skip.append(domain)
        
        # If no domains qualify, scan primary domain
        if not domains_to_scan and primary_domain != 'general':
            domains_to_scan = [primary_domain]
        elif not domains_to_scan:
            domains_to_scan = ['general'] if 'general' in self.domain_automatons else []
        
        # Extract entities from relevant domains only
        entities = {
            'targeted_domains': domains_to_scan,
            'skipped_domains': domains_to_skip,
            'domain_entities': {},
            'universal': {},
            'metadata': {}
        }
        
        total_entity_count = 0
        
        # 1. Extract from targeted domains only (EFFICIENCY!)
        for domain in domains_to_scan:
            if domain not in self.domain_automatons:
                continue
            
            automaton = self.domain_automatons[domain]
            domain_entities = {}
            
            # Find all matches for this domain
            for end_index, (match_domain, category, original_term) in automaton.iter(content_lower):
                if category not in domain_entities:
                    domain_entities[category] = {}
                
                if original_term not in domain_entities[category]:
                    domain_entities[category][original_term] = {
                        'count': 0,
                        'positions': []
                    }
                
                domain_entities[category][original_term]['count'] += 1
                domain_entities[category][original_term]['positions'].append(end_index)
                total_entity_count += 1
            
            if domain_entities:
                entities['domain_entities'][domain] = {
                    'categories': domain_entities,
                    'total_matches': sum(
                        sum(e['count'] for e in cat.values())
                        for cat in domain_entities.values()
                    ),
                    'unique_entities': sum(
                        len(cat) for cat in domain_entities.values()
                    )
                }
        
        # 2. Skip universal entities - already extracted in classification step
        # Universal entities (dates, money, etc.) are handled in classification
        # for entity_type, pattern in self.universal_patterns.items():
        #     matches = pattern.findall(content)
        #     if matches:
        #         unique_matches = list(set(matches))[:30]  # Limit to 30
        #         entities['universal'][entity_type] = {
        #             'count': len(matches),
        #             'unique_count': len(unique_matches),
        #             'examples': unique_matches[:10]
        #         }
        #         total_entity_count += len(matches)
        
        # 3. Metadata
        processing_time = time.time() - start_time
        entities['metadata'] = {
            'processing_time_ms': round(processing_time * 1000, 2),
            'total_entity_count': total_entity_count,
            'primary_domain': primary_domain,
            'domains_scanned': len(domains_to_scan),
            'domains_skipped': len(domains_to_skip),
            'efficiency_gain': f"{(len(domains_to_skip) / (len(domains_to_scan) + len(domains_to_skip)) * 100):.1f}%" if domains_to_scan or domains_to_skip else "0%",
            'filename': filename,
            'method': 'targeted_aho_corasick'
        }
        
        return entities
    
    def _fallback_extraction(self, content: str, classification_result: Dict, 
                            filename: str) -> Dict:
        """Fallback extraction without pyahocorasick."""
        import re
        
        # Basic regex extraction
        entities = {
            'targeted_domains': [classification_result.get('primary_domain', 'general')],
            'skipped_domains': [],
            'domain_entities': {},
            'universal': {},
            'metadata': {
                'method': 'fallback_regex',
                'processing_time_ms': 0,
                'total_entity_count': 0,
                'efficiency_gain': 'N/A (fallback mode)'
            }
        }
        
        # Extract domain-specific entities using basic regex (no universal - already done in Step 2)
        primary_domain = classification_result.get('primary_domain', 'general')
        
        # Focus on domain-specific extraction only
        if primary_domain == 'regulatory':
            # Regulatory-specific patterns
            regulatory_patterns = {
                'agencies': re.compile(r'\b(?:EPA|FDA|CDC|WHO|NIST|CPSC)\b'),
                'standards_orgs': re.compile(r'\b(?:ASTM|IEEE|ISO|ANSI|NFPA|UL)\b'),
                'cfr_regs': re.compile(r'\b\d{1,2}\s*CFR\s*\d{3,4}(?:\.\d+)?'),
                'iso_standards': re.compile(r'\bISO\s*\d{4,5}')
            }
            
            domain_entities = {}
            for category, pattern in regulatory_patterns.items():
                matches = pattern.findall(content)
                if matches:
                    domain_entities[category] = list(set(matches))
            
            if domain_entities:
                entities['domain_entities']['regulatory'] = {
                    'categories': domain_entities,
                    'unique_entities': sum(len(terms) for terms in domain_entities.values()),
                    'total_matches': sum(len(pattern.findall(content)) for pattern in regulatory_patterns.values())
                }
        
        elif primary_domain == 'technical':
            # Technical-specific patterns
            tech_patterns = {
                'frameworks': re.compile(r'\b(?:TensorFlow|PyTorch|React|Angular|Django|Flask)\b'),
                'languages': re.compile(r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+)\b'),
                'platforms': re.compile(r'\b(?:AWS|Azure|Docker|Kubernetes|GitHub)\b')
            }
            
            domain_entities = {}
            for category, pattern in tech_patterns.items():
                matches = pattern.findall(content)
                if matches:
                    domain_entities[category] = list(set(matches))
            
            if domain_entities:
                entities['domain_entities']['technical'] = {
                    'categories': domain_entities,
                    'unique_entities': sum(len(terms) for terms in domain_entities.values()),
                    'total_matches': sum(len(pattern.findall(content)) for pattern in tech_patterns.values())
                }
        
        # Update metadata
        entities['metadata']['total_entity_count'] = sum(
            data.get('total_matches', 0) for data in entities['domain_entities'].values()
        )
        
        return entities
    
    def format_enrichment_metadata(self, entities: Dict, classification_result: Dict) -> str:
        """
        Format enrichment results as YAML metadata for markdown files.
        
        Shows both classification and targeted enrichment results.
        """
        lines = ["\n# Targeted Enrichment (Step 3)"]
        
        # Show targeting efficiency
        lines.append(f"domains_scanned: {entities['targeted_domains']}")
        lines.append(f"domains_skipped: {entities['skipped_domains']}")
        lines.append(f"efficiency_gain: {entities['metadata']['efficiency_gain']}")
        
        # Show actual entities by domain
        if entities['domain_entities']:
            for domain, data in entities['domain_entities'].items():
                lines.append(f"{domain}_entities: {data['unique_entities']}")
                lines.append(f"{domain}_matches: {data['total_matches']}")
                
                # Show actual entities from top categories
                if 'categories' in data:
                    top_cats = sorted(data['categories'].items(), 
                                    key=lambda x: len(x[1]), reverse=True)[:3]
                    for cat, terms in top_cats:
                        unique_terms = list(set(terms))
                        lines.append(f"  {cat}: {unique_terms}")
        
        # Only show domain-specific results (universal entities already shown in Step 2)
        if entities['universal']:
            lines.append("# Note: Universal entities already extracted in Step 2 - focusing on domain-specific entities")
        
        # Performance
        lines.append(f"enrichment_time_ms: {entities['metadata']['processing_time_ms']}")
        lines.append(f"total_entities: {entities['metadata']['total_entity_count']}")
        
        return "\n".join(lines) + "\n"

def benchmark_targeted_enrichment(enrichment: TargetedEnrichment,
                                 test_documents: List[Tuple[str, Dict]]) -> Dict:
    """
    Benchmark targeted enrichment speed.
    
    Args:
        test_documents: List of (content, classification_result) tuples
    """
    start_time = time.time()
    
    total_documents = len(test_documents)
    successful_enrichments = 0
    total_entities = 0
    total_domains_skipped = 0
    
    for doc_content, classification in test_documents:
        try:
            result = enrichment.extract_entities_targeted(doc_content, classification)
            successful_enrichments += 1
            total_entities += result['metadata']['total_entity_count']
            total_domains_skipped += len(result.get('skipped_domains', []))
        except Exception as e:
            print(f"Enrichment error: {e}")
    
    total_time = time.time() - start_time
    pages_per_sec = successful_enrichments / total_time if total_time > 0 else 0
    
    return {
        'total_documents': total_documents,
        'successful_enrichments': successful_enrichments,
        'total_time_seconds': round(total_time, 3),
        'pages_per_second': round(pages_per_sec, 1),
        'total_entities_extracted': total_entities,
        'average_domains_skipped': total_domains_skipped / total_documents if total_documents > 0 else 0,
        'target_performance': '1500+ pages/sec',
        'performance_vs_target': f"{((pages_per_sec / 1500) * 100):.1f}%" if pages_per_sec > 0 else "0%"
    }

if __name__ == "__main__":
    # Example usage showing the layered approach
    from enhanced_classification_ac import AhoCorasickClassifier
    
    # Layer 1: Classification
    classifier = AhoCorasickClassifier()
    
    # Test document
    test_doc = """
    OSHA Safety Standard 29 CFR 1926.95
    
    Personal Protective Equipment Requirements
    
    All workers must wear hard hats, safety harnesses, and respirators
    when exposed to asbestos, lead, or chemical hazards. Fall protection
    is required for work at heights exceeding 6 feet.
    
    Contact: safety@company.com for more information.
    Budget: $2.5 million for safety equipment procurement.
    """
    
    # Layer 1: Classify to determine domains
    classification = classifier.classify_document(test_doc, "safety_doc.md")
    print("🔸 Layer 1 - Classification:")
    print(f"  Primary Domain: {classification['primary_domain']}")
    print(f"  Domain Distribution: {classification['domain_percentages']}")
    
    # Layer 2: Targeted enrichment based on classification
    enrichment = TargetedEnrichment()
    entities = enrichment.extract_entities_targeted(test_doc, classification, "safety_doc.md")
    
    print("\n🎯 Layer 2 - Targeted Enrichment:")
    print(f"  Domains Scanned: {entities['targeted_domains']}")
    print(f"  Domains Skipped: {entities['skipped_domains']}")
    print(f"  Efficiency Gain: {entities['metadata']['efficiency_gain']}")
    print(f"  Total Entities: {entities['metadata']['total_entity_count']}")
    print(f"  Processing Time: {entities['metadata']['processing_time_ms']}ms")