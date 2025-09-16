#!/usr/bin/env python3
"""
Enhanced Classification Module
===============================
High-performance document classification using regex patterns
inspired by the 1,717 pages/sec benchmark results.

Key Improvements:
1. Pre-compiled regex patterns for 2,000+ pages/sec performance
2. Pattern-based document type detection  
3. Multi-domain scoring with confidence metrics
4. Domain-specific pattern libraries
"""

import re
import time
import yaml
import os
from typing import Dict, List, Tuple, Set
from pathlib import Path

class EnhancedClassifier:
    """High-performance document classifier using compiled regex patterns."""
    
    def __init__(self, config_path: str = None):
        """Initialize with patterns loaded from configuration files."""
        
        # Load patterns from config file
        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, ".config", "regex-patterns.yaml")
        
        self.config_path = config_path
        self.pattern_config = self._load_pattern_config()
        
        # Compile all patterns for maximum speed
        self.compiled_patterns = self._compile_patterns()
    
    def _load_pattern_config(self) -> Dict:
        """Load pattern configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ Pattern config file not found: {self.config_path}")
            print("⚠️ Using fallback hardcoded patterns")
            return self._get_fallback_patterns()
        except yaml.YAMLError as e:
            print(f"⚠️ Error parsing pattern config: {e}")
            return self._get_fallback_patterns()
    
    def _compile_patterns(self) -> Dict:
        """Compile all regex patterns from configuration for maximum performance."""
        compiled = {}
        
        # Compile classification patterns by domain
        if 'classification_patterns' in self.pattern_config:
            for domain, patterns in self.pattern_config['classification_patterns'].items():
                compiled[domain] = {}
                for pattern_name, pattern_data in patterns.items():
                    pattern_str = pattern_data['pattern']
                    flags_str = pattern_data.get('flags', 'NONE')
                    
                    # Convert flags string to re flags
                    flags = 0
                    if 'IGNORECASE' in flags_str:
                        flags |= re.IGNORECASE
                    if 'MULTILINE' in flags_str:
                        flags |= re.MULTILINE
                    if 'DOTALL' in flags_str:
                        flags |= re.DOTALL
                    
                    compiled[domain][pattern_name] = {
                        'pattern': re.compile(pattern_str, flags),
                        'weight': pattern_data.get('weight', 1),
                        'description': pattern_data.get('description', '')
                    }
        
        # Compile structure patterns
        if 'structure_patterns' in self.pattern_config:
            compiled['structure'] = {}
            for pattern_name, pattern_data in self.pattern_config['structure_patterns'].items():
                pattern_str = pattern_data['pattern']
                flags = re.IGNORECASE if pattern_data.get('flags', 'IGNORECASE') == 'IGNORECASE' else 0
                compiled['structure'][pattern_name] = re.compile(pattern_str, flags)
        
        return compiled
    
    def _get_fallback_patterns(self) -> Dict:
        """Fallback patterns if config file is not available."""
        return {
            'classification_patterns': {
                'safety': {
                    'hazard_indicators': {
                        'pattern': r'\b(?:hazard|risk|danger|unsafe|accident|injury|fatality)\b',
                        'flags': 'IGNORECASE',
                        'weight': 2
                    }
                },
                'technical': {
                    'programming': {
                        'pattern': r'\b(?:function|class|algorithm|API|database|framework)\b',
                        'flags': 'IGNORECASE', 
                        'weight': 2
                    }
                }
            },
            'structure_patterns': {
                'report': {
                    'pattern': r'\b(?:report|summary|findings|analysis)\b',
                    'flags': 'IGNORECASE'
                }
            }
        }
    
    def classify_document(self, content: str, filename: str = "") -> Dict:
        """
        Classify document using high-performance regex patterns.
        
        Returns:
            Dict with classification results including confidence scores,
            primary domain, document types, and pattern match details.
        """
        start_time = time.time()
        
        # Score each domain using loaded patterns
        domain_scores = {}
        pattern_matches = {}
        
        for domain, patterns in self.compiled_patterns.items():
            if domain == 'structure':  # Handle structure patterns separately
                continue
                
            total_score = 0
            domain_pattern_matches = {}
            
            for pattern_name, pattern_data in patterns.items():
                pattern = pattern_data['pattern']
                weight = pattern_data['weight']
                
                matches = pattern.findall(content)
                match_count = len(matches)
                weighted_score = match_count * weight
                total_score += weighted_score
                
                if matches:
                    domain_pattern_matches[pattern_name] = {
                        'count': match_count,
                        'weight': weight,
                        'weighted_score': weighted_score,
                        'matches': matches[:10],  # Limit to first 10 for performance
                        'description': pattern_data['description']
                    }
            
            domain_scores[domain] = total_score
            if domain_pattern_matches:
                pattern_matches[domain] = domain_pattern_matches
        
        # Calculate document structure score using loaded patterns
        structure_scores = {}
        if 'structure' in self.compiled_patterns:
            for struct_type, pattern in self.compiled_patterns['structure'].items():
                matches = pattern.findall(content)
                if matches:
                    structure_scores[struct_type] = len(matches)
        
        # Determine primary domain and confidence
        if not domain_scores or max(domain_scores.values()) == 0:
            primary_domain = 'general'
            confidence = 0.5
            doc_types = ['general']
        else:
            # Calculate normalized scores (percentage of total matches)
            total_score = sum(domain_scores.values())
            normalized_scores = {domain: (score / total_score) * 100 
                               for domain, score in domain_scores.items() if score > 0}
            
            # Primary domain is highest scoring
            primary_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
            
            # Confidence based on dominance of primary domain
            primary_percentage = normalized_scores.get(primary_domain, 0)
            confidence = min(primary_percentage / 100, 1.0)
            
            # Multi-domain classification if scores are close
            doc_types = []
            threshold = max(domain_scores.values()) * 0.3  # 30% of max score
            
            for domain, score in domain_scores.items():
                if score >= threshold:
                    doc_types.append(domain)
            
            if not doc_types:
                doc_types = [primary_domain]
        
        # Add document structure types
        if structure_scores:
            primary_structure = max(structure_scores.items(), key=lambda x: x[1])[0]
            if primary_structure not in doc_types:
                doc_types.append(primary_structure)
        
        # Calculate processing speed
        processing_time = time.time() - start_time
        
        return {
            'document_types': doc_types,
            'primary_domain': primary_domain,
            'classification_confidence': round(confidence, 3),
            'domain_scores': domain_scores,
            'domain_percentages': {domain: f"{percentage:.1f}%" 
                                 for domain, percentage in normalized_scores.items()} if 'normalized_scores' in locals() else {},
            'structure_types': structure_scores,
            'pattern_matches': pattern_matches,
            'processing_time_ms': round(processing_time * 1000, 2),
            'filename': filename
        }
    
    def get_domain_insights(self, classification_result: Dict) -> Dict:
        """
        Extract domain-specific insights from pattern matches.
        
        Returns actionable insights for each detected domain.
        """
        insights = {}
        pattern_matches = classification_result.get('pattern_matches', {})
        
        for domain, matches in pattern_matches.items():
            domain_insights = {}
            
            if domain == 'safety':
                if 'hazard_indicators' in matches:
                    domain_insights['hazard_level'] = 'high' if matches['hazard_indicators']['count'] > 5 else 'medium'
                if 'osha_specific' in matches:
                    domain_insights['regulatory_scope'] = 'OSHA regulated'
                if 'ppe_mentions' in matches:
                    domain_insights['safety_equipment'] = 'PPE required'
                    
            elif domain == 'technical':
                if 'programming' in matches:
                    domain_insights['tech_category'] = 'software development'
                if 'data_science' in matches:
                    domain_insights['tech_category'] = 'data science/ML'
                if 'infrastructure' in matches:
                    domain_insights['tech_category'] = 'infrastructure/DevOps'
                    
            elif domain == 'regulatory':
                if 'regulations' in matches:
                    domain_insights['regulatory_type'] = 'CFR/Federal regulations'
                if 'enforcement' in matches:
                    domain_insights['enforcement_risk'] = 'penalties mentioned'
            
            if domain_insights:
                insights[domain] = domain_insights
        
        return insights

def benchmark_classification_speed(classifier: EnhancedClassifier, test_documents: List[str]) -> Dict:
    """
    Benchmark classification speed across multiple documents.
    
    Returns performance metrics including pages/sec.
    """
    start_time = time.time()
    
    total_documents = len(test_documents)
    successful_classifications = 0
    total_pattern_matches = 0
    
    for doc_content in test_documents:
        try:
            result = classifier.classify_document(doc_content)
            successful_classifications += 1
            total_pattern_matches += sum(result.get('domain_scores', {}).values())
        except Exception as e:
            print(f"Classification error: {e}")
    
    total_time = time.time() - start_time
    pages_per_sec = successful_classifications / total_time if total_time > 0 else 0
    
    return {
        'total_documents': total_documents,
        'successful_classifications': successful_classifications,
        'total_time_seconds': round(total_time, 3),
        'pages_per_second': round(pages_per_sec, 1),
        'average_time_per_doc_ms': round((total_time / total_documents) * 1000, 2) if total_documents > 0 else 0,
        'total_pattern_matches': total_pattern_matches,
        'target_performance': '2000+ pages/sec',
        'performance_vs_target': f"{((pages_per_sec / 2000) * 100):.1f}%" if pages_per_sec > 0 else "0%"
    }

if __name__ == "__main__":
    # Example usage and speed test
    classifier = EnhancedClassifier()
    
    # Test document
    test_doc = """
    OSHA Safety Standard 29 CFR 1926.95
    
    Personal Protective Equipment (PPE) Requirements for Construction
    
    All workers must wear appropriate safety helmets, harnesses, and respirators
    when working at heights exceeding 6 feet. Chemical exposure requires
    additional ventilation and protective equipment.
    
    Hazard assessment must be conducted before work begins. Any violations
    will result in citations and penalties as per Department of Labor guidelines.
    """
    
    result = classifier.classify_document(test_doc, "osha_ppe_standard.md")
    insights = classifier.get_domain_insights(result)
    
    print("🔸 Enhanced Classification Results:")
    print(f"  Primary Domain: {result['primary_domain']}")
    print(f"  Document Types: {result['document_types']}")
    print(f"  Confidence: {result['classification_confidence']}")
    print(f"  Processing Time: {result['processing_time_ms']}ms")
    print(f"  Domain Insights: {insights}")