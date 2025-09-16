#!/usr/bin/env python3
"""
Aho-Corasick Pattern Matching Engine for AI Agent Knowledge Feeding
==================================================================
High-performance pattern matching for 25 domains optimized for AI consumption.
Target: 25ms → 5ms performance improvement over regex.
"""

import time
import yaml
import ahocorasick
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict


class AhoCorasickKnowledgeEngine:
    """
    High-performance Aho-Corasick engine for AI-optimized domain classification.
    
    Architecture:
    - Single automaton for all 25 domains
    - Weighted scoring for domain confidence
    - Entity extraction with domain context
    - Optimized for AI agent knowledge feeding
    """
    
    def __init__(self, patterns_file: str = "knowledge/ai_domain_patterns.yaml"):
        self.patterns_file = patterns_file
        self.domain_patterns = {}
        self.domain_weights = {}
        self.entity_patterns = {}
        
        # Aho-Corasick automatons
        self.domain_automaton = None
        self.entity_automaton = None
        
        # Performance tracking
        self.build_time_ms = 0
        self.last_search_time_ms = 0
        
        # Load and build automatons
        self._load_patterns()
        self._build_automatons()
        
    def _load_patterns(self):
        """Load domain patterns from YAML configuration"""
        patterns_path = Path(self.patterns_file)
        if not patterns_path.exists():
            raise FileNotFoundError(f"Patterns file not found: {self.patterns_file}")
            
        with open(patterns_path, 'r') as f:
            config = yaml.safe_load(f)
            
        domains_config = config.get('domains', {})
        
        for domain_name, domain_config in domains_config.items():
            # Store domain keywords with weights
            keywords = domain_config.get('keywords', {})
            self.domain_patterns[domain_name] = keywords
            self.domain_weights[domain_name] = domain_config.get('weight', 1.0)
            
            # Store entity patterns
            entities = domain_config.get('entities', {})
            self.entity_patterns[domain_name] = entities
            
        print(f"📚 Loaded {len(self.domain_patterns)} domains with {sum(len(kw) for kw in self.domain_patterns.values())} total patterns")
        
    def _build_automatons(self):
        """Build Aho-Corasick automatons for domains and entities"""
        build_start = time.perf_counter()
        
        # Build domain classification automaton
        self.domain_automaton = ahocorasick.Automaton()
        pattern_id = 0
        
        for domain_name, keywords in self.domain_patterns.items():
            for keyword, weight in keywords.items():
                # Store pattern with domain and weight info
                pattern_info = {
                    'domain': domain_name,
                    'keyword': keyword,
                    'weight': weight,
                    'domain_weight': self.domain_weights[domain_name]
                }
                self.domain_automaton.add_word(keyword.lower(), (pattern_id, pattern_info))
                pattern_id += 1
        
        self.domain_automaton.make_automaton()
        
        # Build entity extraction automaton
        self.entity_automaton = ahocorasick.Automaton()
        entity_id = 0
        
        for domain_name, entity_categories in self.entity_patterns.items():
            for category_name, entity_list in entity_categories.items():
                for entity in entity_list:
                    entity_info = {
                        'domain': domain_name,
                        'category': category_name,
                        'entity': entity
                    }
                    self.entity_automaton.add_word(entity.lower(), (entity_id, entity_info))
                    entity_id += 1
        
        self.entity_automaton.make_automaton()
        
        self.build_time_ms = (time.perf_counter() - build_start) * 1000
        
        print(f"⚡ Built Aho-Corasick automatons: {self.build_time_ms:.2f}ms")
        print(f"   📊 Domain patterns: {pattern_id} total")
        print(f"   🔍 Entity patterns: {entity_id} total")
        
    def classify_domains(self, content: str) -> Dict[str, float]:
        """
        Fast domain classification using Aho-Corasick pattern matching.
        Returns domain confidence scores optimized for AI agents.
        """
        search_start = time.perf_counter()
        content_lower = content.lower()
        
        # Track domain hits and weights
        domain_hits = defaultdict(float)
        total_weighted_hits = 0
        
        # Single pass through content with Aho-Corasick
        for end_index, (pattern_id, pattern_info) in self.domain_automaton.iter(content_lower):
            domain = pattern_info['domain']
            keyword_weight = pattern_info['weight']
            domain_weight = pattern_info['domain_weight']
            
            # Weighted scoring: keyword_weight * domain_weight
            hit_score = keyword_weight * domain_weight
            domain_hits[domain] += hit_score
            total_weighted_hits += hit_score
        
        # Convert to percentages
        domain_scores = {}
        if total_weighted_hits > 0:
            for domain, score in domain_hits.items():
                percentage = (score / total_weighted_hits) * 100
                domain_scores[domain] = round(percentage, 1)
        else:
            domain_scores['general'] = 100.0
            
        # Sort by confidence (highest first)
        domain_scores = dict(sorted(domain_scores.items(), key=lambda x: x[1], reverse=True))
        
        self.last_search_time_ms = (time.perf_counter() - search_start) * 1000
        
        return domain_scores
        
    def extract_entities(self, content: str, target_domains: List[str] = None) -> Dict[str, List[str]]:
        """
        Extract entities using Aho-Corasick, optionally filtered by domains.
        Optimized for AI agent knowledge context.
        """
        content_lower = content.lower()
        
        # Track found entities by category
        entity_hits = defaultdict(set)
        
        # Single pass entity extraction
        for end_index, (entity_id, entity_info) in self.entity_automaton.iter(content_lower):
            domain = entity_info['domain']
            category = entity_info['category']
            entity = entity_info['entity']
            
            # Filter by target domains if specified
            if target_domains and domain not in target_domains:
                continue
                
            entity_hits[category].add(entity)
        
        # Convert to lists with limits (for AI agent consumption)
        result = {}
        for category, entities in entity_hits.items():
            entity_list = list(entities)[:10]  # Limit for AI processing
            if entity_list:
                result[category] = entity_list
                
        return result
        
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        return {
            'build_time_ms': self.build_time_ms,
            'last_search_time_ms': self.last_search_time_ms,
            'total_domain_patterns': sum(len(kw) for kw in self.domain_patterns.values()),
            'total_entity_patterns': sum(len(entities) for domain_entities in self.entity_patterns.values() 
                                       for entities in domain_entities.values()),
            'domains_loaded': len(self.domain_patterns),
            'memory_efficient': True,
            'ai_optimized': True
        }
        
    def benchmark_vs_regex(self, test_content: str, iterations: int = 100) -> Dict[str, Any]:
        """
        Benchmark Aho-Corasick vs regex performance.
        Target: 25ms → 5ms improvement
        """
        import re
        
        # Aho-Corasick timing
        ac_times = []
        for i in range(iterations):
            start = time.perf_counter()
            ac_result = self.classify_domains(test_content)
            ac_times.append((time.perf_counter() - start) * 1000)
        
        # Regex timing (simulate current approach)
        regex_times = []
        for i in range(iterations):
            start = time.perf_counter()
            
            # Simulate regex-based classification
            content_lower = test_content.lower()
            domain_hits = defaultdict(int)
            
            for domain_name, keywords in self.domain_patterns.items():
                for keyword, weight in keywords.items():
                    # Simple regex search
                    if keyword in content_lower:
                        domain_hits[domain_name] += int(weight)
            
            regex_times.append((time.perf_counter() - start) * 1000)
        
        avg_ac_time = sum(ac_times) / len(ac_times)
        avg_regex_time = sum(regex_times) / len(regex_times)
        improvement = ((avg_regex_time - avg_ac_time) / avg_regex_time) * 100
        
        return {
            'aho_corasick_avg_ms': round(avg_ac_time, 3),
            'regex_avg_ms': round(avg_regex_time, 3),
            'performance_improvement_percent': round(improvement, 1),
            'speed_multiplier': round(avg_regex_time / avg_ac_time, 1),
            'target_achieved': avg_ac_time < 5.0,  # Target: <5ms
            'iterations': iterations
        }


class AhoCorasickLayeredClassifier:
    """
    Integration layer for Aho-Corasick engine with existing layered classification.
    Replaces regex patterns in Layers 3-5 with high-performance AC automaton.
    """
    
    def __init__(self, patterns_file: str = "knowledge/ai_domain_patterns.yaml"):
        self.ac_engine = AhoCorasickKnowledgeEngine(patterns_file)
        
    def layer3_domain_classification_ac(self, content: str) -> Dict[str, Any]:
        """
        Layer 3: High-performance domain classification using Aho-Corasick.
        Replaces regex-based _classify_domains_with_scores method.
        """
        start_time = time.perf_counter()
        
        # Use Aho-Corasick for domain classification
        domain_scores = self.ac_engine.classify_domains(content)
        
        # Determine primary domain and confidence
        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k]) if domain_scores else 'general'
        primary_domain_confidence = domain_scores.get(primary_domain, 0)
        
        # Domain-based routing decisions
        routing_decisions = {
            'skip_entity_extraction': primary_domain_confidence < 20.0,
            'enable_deep_domain_extraction': primary_domain_confidence >= 60.0,
            'domain_specialization_route': primary_domain if primary_domain_confidence >= 40.0 else 'general'
        }
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return {
            'domains': domain_scores,
            'primary_domain': primary_domain,
            'primary_domain_confidence': primary_domain_confidence,
            'domain_routing': routing_decisions,
            'classification_method': 'aho_corasick',
            'processing_time_ms': round(processing_time, 3),
            'ai_optimized': True
        }
        
    def layer5_deep_domain_entities_ac(self, content: str, domain_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Layer 5: High-performance deep domain entity extraction using Aho-Corasick.
        AI-optimized entity extraction based on domain context.
        """
        start_time = time.perf_counter()
        
        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k])
        
        # Extract entities for top domains (AI agent context)
        top_domains = [domain for domain, score in list(domain_scores.items())[:3]]  # Top 3 domains
        deep_entities = self.ac_engine.extract_entities(content, target_domains=top_domains)
        
        total_deep_entities = sum(len(v) for v in deep_entities.values())
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return {
            'deep_domain_entities': deep_entities,
            'deep_domain_specialization': primary_domain,
            'deep_entities_found': total_deep_entities,
            'domain_expertise_applied': True,
            'target_domains': top_domains,
            'extraction_method': 'aho_corasick',
            'processing_time_ms': round(processing_time, 3),
            'ai_agent_ready': True
        }