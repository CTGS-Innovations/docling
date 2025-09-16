#!/usr/bin/env python3
"""
Aho-Corasick Automaton Engine
============================

High-speed keyword matching engine using Aho-Corasick algorithm.
Optimized for simple string matching at 50M+ chars/sec.

Perfect for:
- Organization names (OSHA, EPA, FDA)
- Safety keywords (hazard, risk, safety)
- Domain terminology (compliance, regulation)
- Technical terms that don't require regex
"""

import time
import logging
from typing import Dict, List, Any, Set, Optional
import yaml
from pathlib import Path

try:
    import ahocorasick
    AC_AVAILABLE = True
except ImportError:
    AC_AVAILABLE = False


class AhoCorasickEngine:
    """
    High-performance Aho-Corasick automaton for keyword matching.
    
    Performance Target: 50M+ chars/sec
    Use Case: Simple string matching without regex complexity
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Aho-Corasick engine."""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        if not AC_AVAILABLE:
            raise ImportError("Aho-Corasick not available. Install with: pip install pyahocorasick")
        
        # Performance metrics
        self.metrics = {
            'chars_processed': 0,
            'processing_time': 0.0,
            'keywords_matched': 0,
            'automaton_hits': 0
        }
        
        # Automatons for different pattern sets
        self.automatons = {}
        self.keyword_sets = {}
        
        # Initialize automatons
        self._load_patterns()
        self._build_automatons()
        
    def _load_patterns(self):
        """Load keyword patterns from configuration."""
        # Try to load from pattern sets file
        config_dir = Path(__file__).parent.parent / "config"
        pattern_file = config_dir / "pattern_sets.yaml"
        
        if pattern_file.exists():
            with open(pattern_file, 'r') as f:
                patterns_config = yaml.safe_load(f)
                self.keyword_sets = patterns_config.get('aho_corasick_patterns', {})
        
        # Fallback to default patterns if file not found
        if not self.keyword_sets:
            self.keyword_sets = self._get_default_patterns()
        
        self.logger.info(f"Loaded {len(self.keyword_sets)} keyword pattern sets")
    
    def _get_default_patterns(self) -> Dict[str, List[str]]:
        """Get default keyword patterns for high-performance matching."""
        return {
            'safety_keywords': [
                'safety', 'hazard', 'risk', 'danger', 'warning', 'caution',
                'emergency', 'accident', 'incident', 'injury', 'fatality',
                'compliance', 'regulation', 'standard', 'requirement',
                'mandatory', 'prohibited', 'restricted', 'approved', 'certified'
            ],
            'organizations': [
                'OSHA', 'EPA', 'NIOSH', 'FDA', 'NFPA', 'ANSI', 'ISO',
                'DOT', 'FAA', 'CDC', 'MSHA', 'CPSC'
            ],
            'workplace_safety': [
                'PPE', 'personal protective equipment', 'hard hat',
                'safety glasses', 'respirator', 'harness', 'lockout',
                'tagout', 'LOTO', 'confined space', 'fall protection',
                'scaffolding', 'ladder safety', 'excavation', 'trenching'
            ],
            'environmental': [
                'pollution', 'contamination', 'emission', 'discharge',
                'waste', 'recycling', 'environmental impact', 'air quality',
                'water quality', 'soil contamination', 'groundwater',
                'hazardous material', 'toxic', 'carcinogen'
            ]
        }
    
    def _build_automatons(self):
        """Build Aho-Corasick automatons for each pattern set."""
        for set_name, keywords in self.keyword_sets.items():
            automaton = ahocorasick.Automaton()
            
            # Add keywords to automaton (case-insensitive)
            for i, keyword in enumerate(keywords):
                # Add both original case and lowercase
                automaton.add_word(keyword.lower(), (set_name, keyword, i))
                if keyword.lower() != keyword:
                    automaton.add_word(keyword, (set_name, keyword, i))
            
            # Make automaton
            automaton.make_automaton()
            self.automatons[set_name] = automaton
            
            self.logger.info(f"Built automaton for '{set_name}' with {len(keywords)} keywords")
    
    def extract_entities(self, text: str, pattern_set: str = "default") -> Dict[str, Any]:
        """
        Extract entities using Aho-Corasick pattern matching.
        
        Args:
            text: Input text to process
            pattern_set: Which pattern set to use ('default', 'minimal', 'complete')
            
        Returns:
            Dictionary with extracted entities and metadata
        """
        start_time = time.time()
        text_lower = text.lower()  # Case-insensitive matching
        
        results = {
            'entities': {},
            'metadata': {
                'engine': 'aho_corasick',
                'pattern_set': pattern_set,
                'chars_processed': len(text)
            }
        }
        
        try:
            # Determine which automatons to use
            automatons_to_use = self._select_automatons(pattern_set)
            
            # Process with each relevant automaton
            total_matches = 0
            for automaton_name in automatons_to_use:
                if automaton_name in self.automatons:
                    matches = self._scan_with_automaton(
                        text_lower, self.automatons[automaton_name], automaton_name
                    )
                    
                    # Merge results
                    for entity_type, entities in matches.items():
                        if entity_type not in results['entities']:
                            results['entities'][entity_type] = []
                        results['entities'][entity_type].extend(entities)
                        total_matches += len(entities)
            
            # Remove duplicates while preserving order
            for entity_type in results['entities']:
                results['entities'][entity_type] = list(dict.fromkeys(
                    results['entities'][entity_type]
                ))
            
            # Performance metadata
            processing_time = time.time() - start_time
            results['metadata'].update({
                'processing_time_ms': processing_time * 1000,
                'chars_per_sec': len(text) / processing_time if processing_time > 0 else 0,
                'matches_found': total_matches,
                'automatons_used': automatons_to_use
            })
            
            # Update metrics
            self._update_metrics(len(text), processing_time, total_matches)
            
        except Exception as e:
            self.logger.error(f"Error in Aho-Corasick processing: {e}")
            results['error'] = str(e)
            results['metadata']['processing_time_ms'] = (time.time() - start_time) * 1000
        
        return results
    
    def _select_automatons(self, pattern_set: str) -> List[str]:
        """Select which automatons to use based on pattern set."""
        if pattern_set == "minimal":
            return ['safety_keywords', 'organizations']
        elif pattern_set == "complete":
            return list(self.automatons.keys())
        elif pattern_set == "osha_focused":
            return ['safety_keywords', 'workplace_safety']
        elif pattern_set == "environmental_focused":
            return ['environmental', 'organizations']
        else:  # default
            return ['safety_keywords', 'organizations', 'workplace_safety']
    
    def _scan_with_automaton(self, text: str, automaton, automaton_name: str) -> Dict[str, List[str]]:
        """Scan text with a specific automaton."""
        matches = {}
        
        for end_index, (set_name, original_keyword, keyword_index) in automaton.iter(text):
            # Extract the actual matched text from the original text
            start_index = end_index - len(original_keyword) + 1
            matched_text = text[start_index:end_index + 1]
            
            # Group by entity type (use set_name as entity type)
            entity_type = set_name.upper()
            if entity_type not in matches:
                matches[entity_type] = []
            
            matches[entity_type].append(original_keyword)
        
        return matches
    
    def _update_metrics(self, chars_processed: int, processing_time: float, matches_found: int):
        """Update performance metrics."""
        self.metrics['chars_processed'] += chars_processed
        self.metrics['processing_time'] += processing_time
        self.metrics['keywords_matched'] += matches_found
        self.metrics['automaton_hits'] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if self.metrics['chars_processed'] == 0:
            return self.metrics
        
        total_time = self.metrics['processing_time']
        chars_per_sec = self.metrics['chars_processed'] / total_time if total_time > 0 else 0
        
        return {
            **self.metrics,
            'chars_per_second': chars_per_sec,
            'avg_matches_per_scan': (
                self.metrics['keywords_matched'] / self.metrics['automaton_hits']
                if self.metrics['automaton_hits'] > 0 else 0
            )
        }
    
    def benchmark(self, test_text: str, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark the Aho-Corasick engine performance."""
        self.logger.info(f"Starting benchmark with {iterations} iterations")
        
        start_time = time.time()
        total_matches = 0
        total_chars = 0
        
        for i in range(iterations):
            result = self.extract_entities(test_text, "default")
            entities = result.get('entities', {})
            matches = sum(len(v) for v in entities.values())
            total_matches += matches
            total_chars += len(test_text)
        
        total_time = time.time() - start_time
        
        benchmark_results = {
            'iterations': iterations,
            'total_time_seconds': total_time,
            'total_chars_processed': total_chars,
            'total_matches_found': total_matches,
            'chars_per_second': total_chars / total_time,
            'iterations_per_second': iterations / total_time,
            'matches_per_iteration': total_matches / iterations,
            'avg_time_per_iteration_ms': (total_time / iterations) * 1000
        }
        
        self.logger.info(f"Benchmark complete: {benchmark_results['chars_per_second']:,.0f} chars/sec")
        return benchmark_results
    
    def get_available_pattern_sets(self) -> List[str]:
        """Get list of available pattern sets."""
        return list(self.automatons.keys())
    
    def get_keyword_count(self, pattern_set: str = None) -> int:
        """Get total number of keywords in a pattern set or all sets."""
        if pattern_set and pattern_set in self.keyword_sets:
            return len(self.keyword_sets[pattern_set])
        return sum(len(keywords) for keywords in self.keyword_sets.values())


if __name__ == "__main__":
    # Simple test
    config = {}
    engine = AhoCorasickEngine(config)
    
    test_text = """
    OSHA requires safety training for all workers. The EPA monitors environmental 
    compliance while NIOSH provides health guidance. Workers must wear PPE including 
    hard hats and safety glasses. Lockout/tagout procedures are mandatory for 
    equipment maintenance. Hazardous materials require special handling.
    """
    
    print("Aho-Corasick Engine Test:")
    results = engine.extract_entities(test_text)
    print(f"Entities found: {results.get('entities', {})}")
    print(f"Metadata: {results.get('metadata', {})}")
    
    # Quick benchmark
    benchmark = engine.benchmark(test_text, 100)
    print(f"Benchmark: {benchmark['chars_per_second']:,.0f} chars/sec")