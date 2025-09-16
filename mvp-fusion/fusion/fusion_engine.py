#!/usr/bin/env python3
"""
Fusion Engine - Core High-Performance Text Processing
====================================================

Main coordinator that combines multiple engines for maximum speed:
- Aho-Corasick automaton for simple keyword matching
- FLPC Rust regex for complex pattern matching  
- Smart routing based on content analysis
- Vectorized parallel processing

Target Performance: 10,000+ pages/sec
"""

import time
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import yaml

try:
    import ahocorasick
    AC_AVAILABLE = True
except ImportError:
    AC_AVAILABLE = False
    logging.warning("Aho-Corasick not available. Install with: pip install pyahocorasick")

try:
    import flpc
    FLPC_AVAILABLE = True
except ImportError:
    FLPC_AVAILABLE = False
    logging.warning("FLPC not available. Install with: pip install flpc")

try:
    from .ac_automaton import AhoCorasickEngine
    from .flpc_engine import FLPCEngine
    from .pattern_router import PatternRouter
    from .batch_processor import BatchProcessor
except ImportError:
    # Fallback for command line execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from ac_automaton import AhoCorasickEngine
    from flpc_engine import FLPCEngine
    from pattern_router import PatternRouter
    from batch_processor import BatchProcessor


class FusionEngine:
    """
    High-performance fusion engine combining multiple text processing engines.
    
    Performance Targets:
    - Aho-Corasick: 50M+ chars/sec for keywords
    - FLPC Rust: 69M chars/sec for complex patterns
    - Combined: 10,000+ pages/sec processing
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the fusion engine with configuration."""
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Performance metrics
        self.metrics = {
            'documents_processed': 0,
            'total_processing_time': 0.0,
            'entities_extracted': 0,
            'engine_usage': {'ac': 0, 'flpc': 0, 'hybrid': 0}
        }
        
        # Initialize engines
        self.ac_engine = None
        self.flpc_engine = None
        self.pattern_router = None
        self.batch_processor = None
        
        self._initialize_engines()
        
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load configuration from file or use defaults."""
        # If config_path is already a dict, return it
        if isinstance(config_path, dict):
            return config_path
            
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default high-performance configuration
        return {
            'fusion_engine': {
                'engines': {
                    'aho_corasick': {
                        'enabled': True,
                        'priority': 1,
                        'target_chars_per_sec': 50000000
                    },
                    'flpc_rust': {
                        'enabled': True,
                        'priority': 2,
                        'target_chars_per_sec': 69000000
                    }
                },
                'routing': {
                    'smart_routing': True,
                    'keyword_threshold': 0.8,
                    'complexity_threshold': 0.3,
                    'early_termination': True,
                    'confidence_threshold': 0.95
                }
            },
            'performance': {
                'batch_size': 32,
                'max_workers': 16,
                'enable_vectorization': True,
                'enable_parallel_processing': True
            }
        }
    
    def _initialize_engines(self):
        """Initialize all processing engines."""
        config = self.config.get('fusion_engine', {})
        engines_config = config.get('engines', {})
        
        # Initialize Aho-Corasick engine
        if engines_config.get('aho_corasick', {}).get('enabled', True) and AC_AVAILABLE:
            try:
                self.ac_engine = AhoCorasickEngine(self.config)
                self.logger.info("Aho-Corasick engine initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Aho-Corasick engine: {e}")
        
        # Initialize FLPC engine
        if engines_config.get('flpc_rust', {}).get('enabled', True) and FLPC_AVAILABLE:
            try:
                self.flpc_engine = FLPCEngine(self.config)
                self.logger.info("FLPC Rust engine initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize FLPC engine: {e}")
        
        # Initialize pattern router
        try:
            self.pattern_router = PatternRouter(self.config)
            self.logger.info("Pattern router initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize pattern router: {e}")
        
        # Initialize batch processor
        try:
            self.batch_processor = BatchProcessor(self.config)
            self.logger.info("Batch processor initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize batch processor: {e}")
    
    def process_text(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Process text using the optimal engine combination.
        
        Args:
            text: Input text to process
            filename: Optional filename for context
            
        Returns:
            Dictionary containing extracted entities and metadata
        """
        start_time = time.time()
        
        try:
            # Route patterns based on content analysis
            routing_decision = self._route_patterns(text)
            
            # Process with selected engine(s)
            if routing_decision['strategy'] == 'aho_corasick':
                results = self._process_with_ac(text, routing_decision)
                self.metrics['engine_usage']['ac'] += 1
                
            elif routing_decision['strategy'] == 'flpc_rust':
                results = self._process_with_flpc(text, routing_decision)
                self.metrics['engine_usage']['flpc'] += 1
                
            elif routing_decision['strategy'] == 'hybrid':
                results = self._process_hybrid(text, routing_decision)
                self.metrics['engine_usage']['hybrid'] += 1
                
            else:
                # Fallback to available engine
                results = self._process_fallback(text)
            
            # Add processing metadata
            processing_time = time.time() - start_time
            results['processing_metadata'] = {
                'processing_time_ms': processing_time * 1000,
                'chars_processed': len(text),
                'chars_per_sec': len(text) / processing_time if processing_time > 0 else 0,
                'engine_used': routing_decision['strategy'],
                'filename': filename
            }
            
            # Update metrics
            self._update_metrics(results, processing_time)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing text from {filename}: {e}")
            return {
                'entities': {},
                'error': str(e),
                'processing_metadata': {
                    'processing_time_ms': (time.time() - start_time) * 1000,
                    'chars_processed': len(text),
                    'engine_used': 'error',
                    'filename': filename
                }
            }
    
    def _route_patterns(self, text: str) -> Dict[str, Any]:
        """Determine optimal processing strategy for the text."""
        if not self.pattern_router:
            # Default routing if router not available
            return {
                'strategy': 'flpc_rust' if self.flpc_engine else 'aho_corasick',
                'patterns': 'default',
                'confidence': 0.5
            }
        
        return self.pattern_router.route(text)
    
    def _process_with_ac(self, text: str, routing_decision: Dict) -> Dict[str, Any]:
        """Process text using Aho-Corasick engine."""
        if not self.ac_engine:
            return {'entities': {}, 'error': 'Aho-Corasick engine not available'}
        
        return self.ac_engine.extract_entities(text, routing_decision.get('patterns', 'default'))
    
    def _process_with_flpc(self, text: str, routing_decision: Dict) -> Dict[str, Any]:
        """Process text using FLPC Rust engine."""
        if not self.flpc_engine:
            return {'entities': {}, 'error': 'FLPC engine not available'}
        
        return self.flpc_engine.extract_entities(text, routing_decision.get('patterns', 'default'))
    
    def _process_hybrid(self, text: str, routing_decision: Dict) -> Dict[str, Any]:
        """Process text using both engines in parallel."""
        results = {'entities': {}}
        
        # Process keywords with AC (if available)
        if self.ac_engine:
            ac_results = self.ac_engine.extract_entities(
                text, routing_decision.get('ac_patterns', 'keywords')
            )
            results['entities'].update(ac_results.get('entities', {}))
        
        # Process complex patterns with FLPC (if available)
        if self.flpc_engine:
            flpc_results = self.flpc_engine.extract_entities(
                text, routing_decision.get('flpc_patterns', 'regex')
            )
            results['entities'].update(flpc_results.get('entities', {}))
        
        return results
    
    def _process_fallback(self, text: str) -> Dict[str, Any]:
        """Fallback processing when routing fails."""
        # Try FLPC first (more capable)
        if self.flpc_engine:
            return self.flpc_engine.extract_entities(text, 'default')
        
        # Fall back to AC
        if self.ac_engine:
            return self.ac_engine.extract_entities(text, 'default')
        
        # No engines available
        return {
            'entities': {},
            'error': 'No processing engines available'
        }
    
    def _update_metrics(self, results: Dict, processing_time: float):
        """Update performance metrics."""
        self.metrics['documents_processed'] += 1
        self.metrics['total_processing_time'] += processing_time
        
        entities = results.get('entities', {})
        entity_count = sum(len(v) if isinstance(v, list) else 1 for v in entities.values())
        self.metrics['entities_extracted'] += entity_count
    
    def process_batch(self, texts: List[str], filenames: List[str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple texts in a batch for improved performance.
        
        Args:
            texts: List of text strings to process
            filenames: Optional list of filenames
            
        Returns:
            List of result dictionaries
        """
        if not self.batch_processor:
            # Process individually if batch processor not available
            if filenames:
                return [self.process_text(text, filename) 
                       for text, filename in zip(texts, filenames)]
            else:
                return [self.process_text(text) for text in texts]
        
        return self.batch_processor.process_batch(texts, filenames)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        if self.metrics['documents_processed'] == 0:
            return self.metrics
        
        avg_time = self.metrics['total_processing_time'] / self.metrics['documents_processed']
        pages_per_sec = 1.0 / avg_time if avg_time > 0 else 0
        
        return {
            **self.metrics,
            'average_processing_time': avg_time,
            'pages_per_second': pages_per_sec,
            'entities_per_document': self.metrics['entities_extracted'] / self.metrics['documents_processed']
        }
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get status of all engines."""
        return {
            'aho_corasick': {
                'available': AC_AVAILABLE,
                'initialized': self.ac_engine is not None,
                'status': 'ready' if self.ac_engine else 'unavailable'
            },
            'flpc_rust': {
                'available': FLPC_AVAILABLE,
                'initialized': self.flpc_engine is not None,
                'status': 'ready' if self.flpc_engine else 'unavailable'
            },
            'pattern_router': {
                'initialized': self.pattern_router is not None,
                'status': 'ready' if self.pattern_router else 'unavailable'
            },
            'batch_processor': {
                'initialized': self.batch_processor is not None,
                'status': 'ready' if self.batch_processor else 'unavailable'
            }
        }


if __name__ == "__main__":
    # Simple test
    engine = FusionEngine()
    
    test_text = """
    OSHA regulation 29 CFR 1926.95 requires hard hats in construction.
    Contact safety@company.com for $500 training on PPE.
    Meeting scheduled for 2:30 PM on March 15, 2024.
    """
    
    results = engine.process_text(test_text, "test.txt")
    print("Fusion Engine Test Results:")
    print(f"Entities found: {results.get('entities', {})}")
    print(f"Processing metadata: {results.get('processing_metadata', {})}")
    print(f"Performance metrics: {engine.get_performance_metrics()}")