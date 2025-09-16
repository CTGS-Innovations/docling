#!/usr/bin/env python3
"""
Enhanced Classification using Aho-Corasick (pyahocorasick)
===========================================================
High-performance document classification using dictionary-based domain detection.
Uses pyahocorasick to quickly identify document domains for targeted enrichment.

Layer 1 of the efficient pipeline:
1. Scan document with ALL domain dictionaries
2. Count hits per domain to determine primary domain(s)
3. Pass domain context to enrichment for focused extraction

Performance target: 1,816+ pages/sec (proven with pyahocorasick)
"""

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
    print("⚠️ pyahocorasick not available. Install with: pip install pyahocorasick")

class AhoCorasickClassifier:
    """High-performance document classifier using Aho-Corasick dictionary matching."""
    
    def __init__(self, dictionaries_config_path: str = None):
        """Initialize with domain dictionaries for classification."""
        
        # Set default config path
        if dictionaries_config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            dictionaries_config_path = os.path.join(current_dir, ".config", "domain-dictionaries.yaml")
        
        self.dictionaries_config_path = dictionaries_config_path
        
        # Load dictionary configuration
        self.dictionary_config = self._load_dictionary_config()
        
        # Build domain automatons for classification
        self.domain_automatons = {}
        self.domain_term_counts = {}
        
        if AHOCORASICK_AVAILABLE:
            self._build_domain_automatons()
            print(f"✅ AC Classifier initialized with {len(self.domain_automatons)} domains")
        else:
            print("⚠️ AC Classifier running in fallback mode without pyahocorasick")
    
    def _load_dictionary_config(self) -> Dict:
        """Load domain dictionaries from YAML configuration."""
        try:
            with open(self.dictionaries_config_path, 'r') as f:
                config = yaml.safe_load(f)
                print(f"✅ Loaded dictionary config: {self.dictionaries_config_path}")
                return config
        except FileNotFoundError:
            print(f"⚠️ Dictionary config not found: {self.dictionaries_config_path}")
            return self._get_fallback_dictionaries()
        except yaml.YAMLError as e:
            print(f"⚠️ Error parsing dictionary config: {e}")
            return self._get_fallback_dictionaries()
    
    def _get_fallback_dictionaries(self) -> Dict:
        """Minimal fallback dictionaries if config unavailable."""
        return {
            'safety': {
                'keywords': ['osha', 'safety', 'hazard', 'ppe', 'accident', 'injury'],
                'organizations': ['OSHA', 'NIOSH', 'EPA']
            },
            'technical': {
                'keywords': ['api', 'database', 'algorithm', 'code', 'function'],
                'languages': ['python', 'java', 'javascript']
            },
            'general': {
                'keywords': ['document', 'report', 'analysis', 'summary']
            }
        }
    
    def _build_domain_automatons(self):
        """Build Aho-Corasick automatons for each domain."""
        
        for domain, categories in self.dictionary_config.items():
            if domain == 'metadata':  # Skip metadata section
                continue
                
            # Create automaton for this domain
            automaton = ahocorasick.Automaton()
            term_count = 0
            
            # Add all terms from all categories in this domain
            if isinstance(categories, dict):
                for category, terms in categories.items():
                    if isinstance(terms, list):
                        for term in terms:
                            # Add both original and lowercase
                            automaton.add_word(term.lower(), (domain, category, term))
                            if term != term.lower():
                                automaton.add_word(term, (domain, category, term))
                            term_count += 1
            
            if term_count > 0:
                automaton.make_automaton()
                self.domain_automatons[domain] = automaton
                self.domain_term_counts[domain] = term_count
                print(f"  Built {domain} automaton: {term_count} terms")
    
    def classify_document(self, content: str, filename: str = "") -> Dict:
        """
        Classify document by counting domain-specific term matches.
        
        This is Layer 1: Quick scan with ALL domains to determine primary domain.
        
        Returns:
            Dict with classification results including:
            - primary_domain: The dominant domain
            - domain_scores: Raw match counts per domain
            - domain_percentages: Percentage distribution
            - confidence: Confidence in primary domain
            - top_matches: Examples of what was found
        """
        start_time = time.time()
        
        if not AHOCORASICK_AVAILABLE:
            return self._fallback_classification(content, filename)
        
        content_lower = content.lower()
        
        # Count matches per domain
        domain_scores = {}
        domain_matches = {}
        total_matches = 0
        
        for domain, automaton in self.domain_automatons.items():
            matches = []
            unique_terms = set()
            
            # Find all matches for this domain
            for end_index, (match_domain, category, original_term) in automaton.iter(content_lower):
                matches.append({
                    'term': original_term,
                    'category': category,
                    'position': end_index
                })
                unique_terms.add(original_term)
                total_matches += 1
            
            domain_scores[domain] = len(matches)
            
            # Store sample matches for reporting
            if matches:
                domain_matches[domain] = {
                    'total_hits': len(matches),
                    'unique_terms': len(unique_terms),
                    'sample_terms': list(unique_terms)[:10],  # First 10 unique terms
                    'categories': {}
                }
                
                # Count by category
                category_counts = {}
                for match in matches:
                    cat = match['category']
                    category_counts[cat] = category_counts.get(cat, 0) + 1
                
                domain_matches[domain]['categories'] = category_counts
        
        # Calculate domain percentages
        if total_matches > 0:
            domain_percentages = {
                domain: (score / total_matches) * 100 
                for domain, score in domain_scores.items() if score > 0
            }
        else:
            domain_percentages = {}
        
        # Determine primary domain
        if domain_scores:
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            
            # Calculate confidence based on dominance
            primary_score = domain_scores[primary_domain]
            if total_matches > 0:
                confidence = primary_score / total_matches
            else:
                confidence = 0.0
                
            # Adjust confidence based on absolute count
            if primary_score < 10:
                confidence *= 0.5  # Low confidence if few matches
            elif primary_score > 100:
                confidence = min(confidence * 1.2, 1.0)  # High confidence if many matches
        else:
            primary_domain = 'general'
            confidence = 0.3
        
        # Determine document types (can be multiple)
        doc_types = []
        threshold = max(domain_scores.values()) * 0.3 if domain_scores else 0
        
        for domain, score in domain_scores.items():
            if score >= threshold and score > 5:  # At least 5 matches
                doc_types.append(domain)
        
        if not doc_types:
            doc_types = ['general']
        
        # Calculate processing speed
        processing_time = time.time() - start_time
        
        return {
            'document_types': doc_types,
            'primary_domain': primary_domain,
            'classification_confidence': round(confidence, 3),
            'domain_scores': domain_scores,
            'domain_percentages': {k: f"{v:.1f}%" for k, v in domain_percentages.items()},
            'domain_matches': domain_matches,
            'total_matches': total_matches,
            'processing_time_ms': round(processing_time * 1000, 2),
            'filename': filename,
            'method': 'aho_corasick',
            'domains_scanned': len(self.domain_automatons),
            'terms_in_dictionaries': sum(self.domain_term_counts.values())
        }
    
    def _fallback_classification(self, content: str, filename: str) -> Dict:
        """Fallback classification without pyahocorasick."""
        content_lower = content.lower()
        
        # Simple keyword counting fallback
        domain_scores = {}
        
        for domain, categories in self.dictionary_config.items():
            if domain == 'metadata':
                continue
            
            score = 0
            if isinstance(categories, dict):
                for category, terms in categories.items():
                    if isinstance(terms, list):
                        for term in terms:
                            score += content_lower.count(term.lower())
            
            domain_scores[domain] = score
        
        total = sum(domain_scores.values()) or 1
        primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0] if domain_scores else 'general'
        
        return {
            'document_types': [primary_domain],
            'primary_domain': primary_domain,
            'classification_confidence': 0.5,
            'domain_scores': domain_scores,
            'domain_percentages': {k: f"{(v/total)*100:.1f}%" for k, v in domain_scores.items()},
            'method': 'fallback_keyword_count',
            'filename': filename
        }
    
    def get_classification_insights(self, classification_result: Dict) -> Dict:
        """
        Extract insights from classification for enrichment targeting.
        
        This helps Layer 2 (enrichment) know which domains to focus on.
        """
        insights = {
            'primary_domain': classification_result['primary_domain'],
            'secondary_domains': [],
            'skip_domains': [],
            'focus_categories': {}
        }
        
        # Identify secondary domains (>20% of matches)
        if 'domain_percentages' in classification_result:
            for domain, percentage in classification_result['domain_percentages'].items():
                percentage_val = float(percentage.rstrip('%'))
                if domain != insights['primary_domain'] and percentage_val > 20:
                    insights['secondary_domains'].append(domain)
                elif percentage_val < 5:
                    insights['skip_domains'].append(domain)
        
        # Identify top categories to focus on
        if 'domain_matches' in classification_result:
            primary_matches = classification_result['domain_matches'].get(insights['primary_domain'], {})
            if 'categories' in primary_matches:
                # Sort categories by match count
                sorted_cats = sorted(primary_matches['categories'].items(), 
                                   key=lambda x: x[1], reverse=True)
                insights['focus_categories'][insights['primary_domain']] = [
                    cat for cat, _ in sorted_cats[:5]  # Top 5 categories
                ]
        
        return insights

def benchmark_ac_classification(classifier: AhoCorasickClassifier, 
                               test_documents: List[str]) -> Dict:
    """
    Benchmark classification speed to validate 1,800+ pages/sec target.
    """
    start_time = time.time()
    
    total_documents = len(test_documents)
    successful_classifications = 0
    total_matches = 0
    
    for doc_content in test_documents:
        try:
            result = classifier.classify_document(doc_content)
            successful_classifications += 1
            total_matches += result.get('total_matches', 0)
        except Exception as e:
            print(f"Classification error: {e}")
    
    total_time = time.time() - start_time
    pages_per_sec = successful_classifications / total_time if total_time > 0 else 0
    
    return {
        'total_documents': total_documents,
        'successful_classifications': successful_classifications,
        'total_time_seconds': round(total_time, 3),
        'pages_per_second': round(pages_per_sec, 1),
        'total_matches': total_matches,
        'matches_per_second': round(total_matches / total_time, 1) if total_time > 0 else 0,
        'target_performance': '1800+ pages/sec',
        'performance_vs_target': f"{((pages_per_sec / 1800) * 100):.1f}%" if pages_per_sec > 0 else "0%",
        'pyahocorasick_available': AHOCORASICK_AVAILABLE
    }

if __name__ == "__main__":
    # Example usage
    classifier = AhoCorasickClassifier()
    
    # Test document
    test_doc = """
    OSHA Safety Standard 29 CFR 1926.95
    
    Personal Protective Equipment Requirements
    
    All workers must wear hard hats, safety harnesses, and respirators
    when exposed to asbestos, lead, or chemical hazards. Fall protection
    is required for work at heights exceeding 6 feet.
    
    The Department of Labor and NIOSH recommend following strict
    safety protocols to prevent workplace accidents and injuries.
    """
    
    result = classifier.classify_document(test_doc, "safety_standard.md")
    insights = classifier.get_classification_insights(result)
    
    print("\n🔸 AC Classification Results:")
    print(f"  Primary Domain: {result['primary_domain']}")
    print(f"  Confidence: {result['classification_confidence']}")
    print(f"  Domain Distribution: {result['domain_percentages']}")
    print(f"  Total Matches: {result['total_matches']}")
    print(f"  Processing Time: {result['processing_time_ms']}ms")
    
    print("\n🎯 Enrichment Targeting Insights:")
    print(f"  Focus on: {insights['primary_domain']} domain")
    print(f"  Secondary: {insights['secondary_domains']}")
    print(f"  Skip: {insights['skip_domains']}")