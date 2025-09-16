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
    
    def __init__(self, config_dir: str = "knowledge"):
        self.config_dir = Path(config_dir)
        self.domain_patterns = {}
        self.domain_weights = {}
        self.document_type_patterns = {}
        self.document_type_weights = {}
        self.entity_patterns = {}
        
        # Aho-Corasick automatons
        self.domain_automaton = None
        self.document_type_automaton = None
        self.entity_automaton = None
        
        # Performance tracking
        self.build_time_ms = 0
        self.last_search_time_ms = 0
        
        # Load and build automatons
        self._load_modular_patterns()
        self._build_automatons()
        
    def _load_modular_patterns(self):
        """Load patterns from modular configuration files"""
        total_domain_patterns = 0
        total_doctype_patterns = 0
        total_entity_patterns = 0
        
        # Load domain patterns from all domain files
        domains_dir = self.config_dir / "domains"
        if domains_dir.exists():
            for domain_file in domains_dir.glob("*.yaml"):
                with open(domain_file, 'r') as f:
                    domain_config = yaml.safe_load(f)
                
                for domain_name, domain_data in domain_config.items():
                    keywords = domain_data.get('keywords', {})
                    self.domain_patterns[domain_name] = keywords
                    self.domain_weights[domain_name] = domain_data.get('weight', 1.0)
                    total_domain_patterns += len(keywords)
                    
                    # Store entity patterns
                    entities = domain_data.get('entities', {})
                    if entities:
                        self.entity_patterns[domain_name] = entities
                        total_entity_patterns += sum(len(e) if isinstance(e, list) else 1 for e in entities.values())
        
        # Load document type patterns from all document type files  
        doctypes_dir = self.config_dir / "document_types"
        if doctypes_dir.exists():
            for doctype_file in doctypes_dir.glob("*.yaml"):
                with open(doctype_file, 'r') as f:
                    doctype_config = yaml.safe_load(f)
                
                for doctype_name, doctype_data in doctype_config.items():
                    keywords = doctype_data.get('keywords', {})
                    self.document_type_patterns[doctype_name] = keywords
                    self.document_type_weights[doctype_name] = doctype_data.get('weight', 1.0)
                    total_doctype_patterns += len(keywords)
        
        # Load universal entity patterns
        entities_dir = self.config_dir / "entities"
        if entities_dir.exists():
            for entity_file in entities_dir.glob("*.yaml"):
                with open(entity_file, 'r') as f:
                    entity_config = yaml.safe_load(f)
                
                for category_name, category_data in entity_config.items():
                    self.entity_patterns[category_name] = category_data
                    if isinstance(category_data, dict):
                        total_entity_patterns += sum(len(e) if isinstance(e, list) else 1 for e in category_data.values())
        
        print(f"📚 Loaded modular patterns:")
        print(f"   🏛️  Domains: {len(self.domain_patterns)} ({total_domain_patterns} keywords)")
        print(f"   📄 Document Types: {len(self.document_type_patterns)} ({total_doctype_patterns} keywords)")
        print(f"   🔍 Entity Categories: {len(self.entity_patterns)} ({total_entity_patterns} total patterns)")
        
    def _build_automatons(self):
        """Build Aho-Corasick automatons for domains, document types, and entities"""
        build_start = time.perf_counter()
        
        # Build domain classification automaton
        self.domain_automaton = ahocorasick.Automaton()
        domain_pattern_id = 0
        
        for domain_name, keywords in self.domain_patterns.items():
            for keyword, weight in keywords.items():
                pattern_info = {
                    'type': 'domain',
                    'name': domain_name,
                    'keyword': keyword,
                    'weight': weight,
                    'base_weight': self.domain_weights[domain_name]
                }
                self.domain_automaton.add_word(keyword.lower(), (domain_pattern_id, pattern_info))
                domain_pattern_id += 1
        
        self.domain_automaton.make_automaton()
        
        # Build document type classification automaton
        self.document_type_automaton = ahocorasick.Automaton()
        doctype_pattern_id = 0
        
        for doctype_name, keywords in self.document_type_patterns.items():
            for keyword, weight in keywords.items():
                pattern_info = {
                    'type': 'document_type',
                    'name': doctype_name,
                    'keyword': keyword,
                    'weight': weight,
                    'base_weight': self.document_type_weights[doctype_name]
                }
                self.document_type_automaton.add_word(keyword.lower(), (doctype_pattern_id, pattern_info))
                doctype_pattern_id += 1
        
        self.document_type_automaton.make_automaton()
        
        # Build entity extraction automaton
        self.entity_automaton = ahocorasick.Automaton()
        entity_id = 0
        
        for domain_name, entity_categories in self.entity_patterns.items():
            for category_name, entity_list in entity_categories.items():
                if isinstance(entity_list, list):
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
        
        print(f"⚡ Built modular Aho-Corasick automatons: {self.build_time_ms:.2f}ms")
        print(f"   🏛️  Domain patterns: {domain_pattern_id}")
        print(f"   📄 Document type patterns: {doctype_pattern_id}")
        print(f"   🔍 Entity patterns: {entity_id}")
        
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
            domain = pattern_info['name']
            keyword_weight = pattern_info['weight']
            domain_weight = pattern_info['base_weight']
            
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
        
    def classify_document_types(self, content: str) -> Dict[str, float]:
        """
        Fast document type classification using Aho-Corasick pattern matching.
        Returns document type confidence scores optimized for AI agents.
        """
        content_lower = content.lower()
        
        # Track document type hits and weights
        doctype_hits = defaultdict(float)
        total_weighted_hits = 0
        
        # Single pass through content with Aho-Corasick
        for end_index, (pattern_id, pattern_info) in self.document_type_automaton.iter(content_lower):
            doctype = pattern_info['name']
            keyword_weight = pattern_info['weight']
            doctype_weight = pattern_info['base_weight']
            
            # Weighted scoring: keyword_weight * doctype_weight
            hit_score = keyword_weight * doctype_weight
            doctype_hits[doctype] += hit_score
            total_weighted_hits += hit_score
        
        # Convert to percentages
        doctype_scores = {}
        if total_weighted_hits > 0:
            for doctype, score in doctype_hits.items():
                percentage = (score / total_weighted_hits) * 100
                doctype_scores[doctype] = round(percentage, 1)
        else:
            doctype_scores['document'] = 100.0
            
        # Sort by confidence (highest first)
        doctype_scores = dict(sorted(doctype_scores.items(), key=lambda x: x[1], reverse=True))
        
        return doctype_scores
        
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
    
    def __init__(self, config_dir: str = "knowledge"):
        self.ac_engine = AhoCorasickKnowledgeEngine(config_dir)
        
    def layer3_domain_classification_ac(self, content: str) -> Dict[str, Any]:
        """
        Layer 3: High-performance domain + document type classification using Aho-Corasick.
        Replaces regex-based classification with modular patterns.
        """
        start_time = time.perf_counter()
        
        # Use Aho-Corasick for both domain and document type classification
        domain_scores = self.ac_engine.classify_domains(content)
        document_type_scores = self.ac_engine.classify_document_types(content)
        
        # Determine primary domain and confidence
        primary_domain = max(domain_scores.keys(), key=lambda k: domain_scores[k]) if domain_scores else 'general'
        primary_domain_confidence = domain_scores.get(primary_domain, 0)
        
        # Determine primary document type
        primary_document_type = max(document_type_scores.keys(), key=lambda k: document_type_scores[k]) if document_type_scores else 'document'
        primary_doctype_confidence = document_type_scores.get(primary_document_type, 0)
        
        # Domain-based routing decisions
        routing_decisions = {
            'skip_entity_extraction': primary_domain_confidence < 20.0,
            'enable_deep_domain_extraction': primary_domain_confidence >= 60.0,
            'domain_specialization_route': primary_domain if primary_domain_confidence >= 40.0 else 'general'
        }
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        return {
            'domains': domain_scores,
            'document_types': document_type_scores,
            'primary_domain': primary_domain,
            'primary_domain_confidence': primary_domain_confidence,
            'primary_document_type': primary_document_type,
            'primary_doctype_confidence': primary_doctype_confidence,
            'domain_routing': routing_decisions,
            'classification_method': 'aho_corasick_modular',
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