#!/usr/bin/env python3
"""
Pattern Router - Smart Engine Selection
=======================================

Intelligent routing system that analyzes content and selects the optimal
processing engine combination for maximum performance while maintaining quality.

Routes based on:
- Content complexity analysis
- Pattern type distribution
- Performance requirements
- Quality thresholds
"""

import time
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter


class PatternRouter:
    """
    Smart pattern routing for optimal engine selection.
    
    Analyzes content to determine the best processing strategy:
    - Simple keywords -> Aho-Corasick (50M+ chars/sec)
    - Complex patterns -> FLPC Rust (69M chars/sec)
    - Mixed content -> Hybrid approach
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the pattern router."""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Routing configuration
        routing_config = config.get('fusion_engine', {}).get('routing', {})
        self.smart_routing = routing_config.get('smart_routing', True)
        self.keyword_threshold = routing_config.get('keyword_threshold', 0.8)
        self.complexity_threshold = routing_config.get('complexity_threshold', 0.3)
        self.early_termination = routing_config.get('early_termination', True)
        self.confidence_threshold = routing_config.get('confidence_threshold', 0.95)
        
        # Performance metrics
        self.metrics = {
            'routing_decisions': 0,
            'ac_selections': 0,
            'flpc_selections': 0,
            'hybrid_selections': 0,
            'routing_time': 0.0
        }
        
        # Content analysis patterns
        self.keyword_indicators = self._load_keyword_indicators()
        self.complexity_indicators = self._load_complexity_indicators()
        
        self.logger.info("Pattern router initialized with smart routing")
    
    def _load_keyword_indicators(self) -> List[str]:
        """Load indicators that suggest simple keyword matching is sufficient."""
        return [
            # Safety keywords
            'safety', 'osha', 'epa', 'hazard', 'risk', 'ppe',
            'regulation', 'compliance', 'standard', 'emergency',
            
            # Common organizations
            'niosh', 'fda', 'cdc', 'dot', 'faa', 'ansi', 'iso',
            
            # Simple workplace terms
            'training', 'procedure', 'policy', 'equipment',
            'worker', 'employee', 'supervisor', 'manager'
        ]
    
    def _load_complexity_indicators(self) -> List[str]:
        """Load indicators that suggest complex regex patterns are needed."""
        return [
            # Financial indicators
            '$', 'dollar', 'cost', 'price', 'budget', 'fee',
            
            # Date/time indicators
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'am', 'pm', 'time', 'schedule', 'deadline',
            
            # Contact information
            '@', '.com', '.org', '.gov', 'email', 'phone', 'contact',
            
            # Technical specifications
            'version', 'v.', 'specification', 'measurement', 'temperature',
            'pressure', 'weight', 'dimension', 'cfr', 'regulation'
        ]
    
    def route(self, text: str) -> Dict[str, Any]:
        """
        Analyze content and determine optimal processing strategy.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Routing decision with strategy, patterns, and confidence
        """
        start_time = time.time()
        
        try:
            # Perform content analysis
            analysis = self._analyze_content(text)
            
            # Make routing decision
            decision = self._make_routing_decision(analysis)
            
            # Add metadata
            decision['analysis'] = analysis
            decision['routing_time_ms'] = (time.time() - start_time) * 1000
            
            # Update metrics
            self._update_metrics(decision['strategy'])
            
            return decision
            
        except Exception as e:
            self.logger.error(f"Error in pattern routing: {e}")
            return self._fallback_decision()
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze content characteristics for routing decisions."""
        text_lower = text.lower()
        words = text_lower.split()
        
        # Basic statistics
        char_count = len(text)
        word_count = len(words)
        avg_word_length = sum(len(word) for word in words) / word_count if word_count > 0 else 0
        
        # Keyword analysis
        keyword_matches = sum(1 for word in words if word in self.keyword_indicators)
        keyword_density = keyword_matches / word_count if word_count > 0 else 0
        
        # Complexity analysis
        complexity_matches = sum(1 for indicator in self.complexity_indicators if indicator in text_lower)
        complexity_score = complexity_matches / len(self.complexity_indicators)
        
        # Pattern type detection
        pattern_types = self._detect_pattern_types(text)
        
        # Document type inference
        doc_type = self._infer_document_type(text_lower, pattern_types)
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'avg_word_length': avg_word_length,
            'keyword_density': keyword_density,
            'complexity_score': complexity_score,
            'pattern_types': pattern_types,
            'document_type': doc_type,
            'keyword_matches': keyword_matches,
            'complexity_matches': complexity_matches
        }
    
    def _detect_pattern_types(self, text: str) -> Dict[str, int]:
        """Detect presence of different pattern types in text."""
        pattern_counts = {
            'email': len(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)),
            'phone': len(re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text)),
            'money': len(re.findall(r'\$[\d,]+', text)),
            'date': len(re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', text)),
            'time': len(re.findall(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', text)),
            'url': len(re.findall(r'https?://[^\s]+', text)),
            'version': len(re.findall(r'\bv?\d+\.\d+', text)),
            'regulation': len(re.findall(r'\b\d{1,2}\s*CFR\s*\d{3,4}', text, re.IGNORECASE)),
            'measurement': len(re.findall(r'\b\d+(?:\.\d+)?\s*(?:mg|g|kg|lbs?|oz|ml|l|ft|meters?|m|cm|mm)', text, re.IGNORECASE))
        }
        
        return pattern_counts
    
    def _infer_document_type(self, text_lower: str, pattern_types: Dict[str, int]) -> str:
        """Infer document type based on content analysis."""
        # Safety-focused document
        safety_indicators = ['osha', 'safety', 'hazard', 'ppe', 'emergency', 'accident']
        safety_score = sum(1 for indicator in safety_indicators if indicator in text_lower)
        
        # Technical document
        technical_indicators = ['specification', 'standard', 'procedure', 'cfr', 'regulation']
        technical_score = sum(1 for indicator in technical_indicators if indicator in text_lower)
        
        # Environmental document
        env_indicators = ['epa', 'environmental', 'pollution', 'emission', 'waste']
        env_score = sum(1 for indicator in env_indicators if indicator in text_lower)
        
        # Complex patterns present
        complex_patterns = sum(pattern_types.values())
        
        if safety_score >= 2:
            return 'safety'
        elif technical_score >= 2:
            return 'technical'
        elif env_score >= 2:
            return 'environmental'
        elif complex_patterns >= 5:
            return 'complex'
        else:
            return 'simple'
    
    def _make_routing_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make routing decision based on content analysis."""
        keyword_density = analysis['keyword_density']
        complexity_score = analysis['complexity_score']
        doc_type = analysis['document_type']
        pattern_types = analysis['pattern_types']
        
        # Calculate confidence based on clear indicators
        confidence = 0.5  # Base confidence
        
        # High keyword density suggests AC is optimal
        if keyword_density >= self.keyword_threshold:
            strategy = 'aho_corasick'
            pattern_set = self._select_ac_pattern_set(doc_type)
            confidence += 0.3
            
        # High complexity suggests FLPC is needed
        elif complexity_score >= self.complexity_threshold:
            strategy = 'flpc_rust'
            pattern_set = self._select_flpc_pattern_set(pattern_types)
            confidence += 0.3
            
        # Mixed content suggests hybrid approach
        elif keyword_density >= 0.4 and complexity_score >= 0.2:
            strategy = 'hybrid'
            pattern_set = 'mixed'
            confidence += 0.2
            
        # Simple content - prefer AC for speed
        elif analysis['word_count'] < 500 and sum(pattern_types.values()) < 3:
            strategy = 'aho_corasick'
            pattern_set = 'minimal'
            confidence += 0.4
            
        # Default to FLPC for comprehensive coverage
        else:
            strategy = 'flpc_rust'
            pattern_set = 'default'
            confidence += 0.1
        
        # Adjust confidence based on document type clarity
        if doc_type != 'simple':
            confidence += 0.1
        
        # Ensure confidence doesn't exceed 1.0
        confidence = min(confidence, 1.0)
        
        decision = {
            'strategy': strategy,
            'pattern_set': pattern_set,
            'confidence': confidence,
            'reasoning': self._generate_reasoning(analysis, strategy, confidence)
        }
        
        # Add engine-specific pattern selections for hybrid
        if strategy == 'hybrid':
            decision['ac_patterns'] = self._select_ac_pattern_set(doc_type)
            decision['flpc_patterns'] = self._select_flpc_pattern_set(pattern_types)
        
        return decision
    
    def _select_ac_pattern_set(self, doc_type: str) -> str:
        """Select appropriate Aho-Corasick pattern set based on document type."""
        if doc_type == 'safety':
            return 'osha_focused'
        elif doc_type == 'environmental':
            return 'environmental_focused'
        elif doc_type == 'simple':
            return 'minimal'
        else:
            return 'default'
    
    def _select_flpc_pattern_set(self, pattern_types: Dict[str, int]) -> str:
        """Select appropriate FLPC pattern set based on detected patterns."""
        total_patterns = sum(pattern_types.values())
        
        if total_patterns < 3:
            return 'minimal'
        elif total_patterns > 10:
            return 'complete'
        else:
            return 'default'
    
    def _generate_reasoning(self, analysis: Dict[str, Any], strategy: str, confidence: float) -> str:
        """Generate human-readable reasoning for the routing decision."""
        keyword_density = analysis['keyword_density']
        complexity_score = analysis['complexity_score']
        doc_type = analysis['document_type']
        
        reasoning_parts = []
        
        if strategy == 'aho_corasick':
            reasoning_parts.append(f"High keyword density ({keyword_density:.2f})")
            reasoning_parts.append("Simple string matching optimal")
            
        elif strategy == 'flpc_rust':
            reasoning_parts.append(f"Complex patterns detected ({complexity_score:.2f})")
            reasoning_parts.append("Regex processing required")
            
        elif strategy == 'hybrid':
            reasoning_parts.append("Mixed content detected")
            reasoning_parts.append("Both keywords and complex patterns present")
        
        reasoning_parts.append(f"Document type: {doc_type}")
        reasoning_parts.append(f"Confidence: {confidence:.2f}")
        
        return "; ".join(reasoning_parts)
    
    def _fallback_decision(self) -> Dict[str, Any]:
        """Fallback decision when routing fails."""
        return {
            'strategy': 'flpc_rust',  # Most capable engine
            'pattern_set': 'default',
            'confidence': 0.3,
            'reasoning': 'Fallback due to routing error',
            'error': True
        }
    
    def _update_metrics(self, strategy: str):
        """Update routing metrics."""
        self.metrics['routing_decisions'] += 1
        
        if strategy == 'aho_corasick':
            self.metrics['ac_selections'] += 1
        elif strategy == 'flpc_rust':
            self.metrics['flpc_selections'] += 1
        elif strategy == 'hybrid':
            self.metrics['hybrid_selections'] += 1
    
    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing performance metrics."""
        total_decisions = self.metrics['routing_decisions']
        
        if total_decisions == 0:
            return self.metrics
        
        return {
            **self.metrics,
            'ac_selection_rate': self.metrics['ac_selections'] / total_decisions,
            'flpc_selection_rate': self.metrics['flpc_selections'] / total_decisions,
            'hybrid_selection_rate': self.metrics['hybrid_selections'] / total_decisions,
            'avg_routing_time_ms': self.metrics['routing_time'] / total_decisions * 1000
        }
    
    def benchmark_routing(self, test_texts: List[str]) -> Dict[str, Any]:
        """Benchmark routing performance on multiple texts."""
        start_time = time.time()
        decisions = []
        
        for text in test_texts:
            decision = self.route(text)
            decisions.append(decision)
        
        total_time = time.time() - start_time
        
        # Analyze decision distribution
        strategies = [d['strategy'] for d in decisions]
        strategy_counts = Counter(strategies)
        
        # Calculate average confidence
        avg_confidence = sum(d['confidence'] for d in decisions) / len(decisions)
        
        return {
            'total_texts': len(test_texts),
            'total_time_seconds': total_time,
            'decisions_per_second': len(test_texts) / total_time,
            'avg_confidence': avg_confidence,
            'strategy_distribution': dict(strategy_counts),
            'routing_overhead_ms': total_time / len(test_texts) * 1000
        }


if __name__ == "__main__":
    # Simple test
    config = {
        'fusion_engine': {
            'routing': {
                'smart_routing': True,
                'keyword_threshold': 0.8,
                'complexity_threshold': 0.3
            }
        }
    }
    
    router = PatternRouter(config)
    
    test_texts = [
        "OSHA requires safety training for all workers using PPE equipment.",
        "Contact john.doe@company.com for pricing information of $2,500 on March 15, 2024.",
        "EPA regulation 40 CFR 261.1 specifies waste classification procedures.",
        "Simple document with basic safety information and training requirements."
    ]
    
    print("Pattern Router Test:")
    for i, text in enumerate(test_texts):
        decision = router.route(text)
        print(f"\nText {i+1}: {text[:50]}...")
        print(f"Strategy: {decision['strategy']}")
        print(f"Confidence: {decision['confidence']:.2f}")
        print(f"Reasoning: {decision['reasoning']}")
    
    # Benchmark
    benchmark = router.benchmark_routing(test_texts * 25)  # 100 total texts
    print(f"\nBenchmark: {benchmark['decisions_per_second']:,.0f} decisions/sec")