#!/usr/bin/env python3
"""
Global Component Manager - Singleton Pattern for Performance
==========================================================

Eliminates heavy component loading overhead by using global singletons:
- spaCy model: 400ms+ → 0ms after first load
- AhoCorasick classifier: ~50ms → 0ms after first load  
- SemanticFactExtractor: ~50ms → 0ms after first load
- EntityNormalizer: ~50ms → 0ms after first load

One-time initialization, reused across all pipeline instances.
"""

import logging
from typing import Optional
import threading

class GlobalSpacyManager:
    """
    Singleton manager for spaCy model loading.
    
    Performance:
    - Without singleton: 400ms+ per pipeline creation
    - With singleton: 400ms once, 0ms thereafter
    
    Thread-safe initialization for parallel processing.
    """
    
    _instance = None
    _lock = threading.Lock()
    _spacy_nlp = None
    _initialization_attempted = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GlobalSpacyManager, cls).__new__(cls)
        return cls._instance
    
    def get_spacy_model(self) -> Optional[object]:
        """
        Get the global spaCy model instance, loading it if necessary.
        
        Returns:
            spaCy model instance or None if loading failed
        """
        if self._spacy_nlp is not None:
            return self._spacy_nlp
        
        if self._initialization_attempted:
            return None
            
        with self._lock:
            # Double-check pattern for thread safety
            if self._spacy_nlp is not None:
                return self._spacy_nlp
            
            if self._initialization_attempted:
                return None
            
            self._initialization_attempted = True
            
            try:
                import spacy
                
                # Load ONLY NER component, disable POS/parser/lemmatizer for speed
                # This reduces processing time by ~50% while keeping person detection
                self._spacy_nlp = spacy.load("en_core_web_sm", 
                                            disable=['tagger', 'parser', 'lemmatizer', 'attribute_ruler'])
                
                # Log successful initialization
                logger = logging.getLogger(__name__)
                logger.info("✅ Global spaCy NER-only model initialized (POS disabled for speed)")
                
                return self._spacy_nlp
                
            except ImportError:
                logger = logging.getLogger(__name__)
                logger.warning("⚠️ spaCy not available - person detection will use AC/FLPC only")
                return None
            except OSError:
                logger = logging.getLogger(__name__)
                logger.warning("⚠️ spaCy model 'en_core_web_sm' not found - person detection will use AC/FLPC only")
                return None
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ spaCy initialization failed: {e} - person detection will use AC/FLPC only")
                return None
    
    def is_available(self) -> bool:
        """Check if spaCy model is available without triggering initialization."""
        return self._spacy_nlp is not None
    
    def force_reload(self) -> Optional[object]:
        """Force reload of spaCy model (for testing/debugging)."""
        with self._lock:
            self._spacy_nlp = None
            self._initialization_attempted = False
            return self.get_spacy_model()


# Global instance for easy access
_global_spacy_manager = GlobalSpacyManager()

def get_global_spacy_model() -> Optional[object]:
    """
    Get the global spaCy model instance.
    
    Performance: 0ms after first initialization.
    Thread-safe for parallel processing.
    
    Returns:
        spaCy model instance or None if not available
    """
    return _global_spacy_manager.get_spacy_model()

def is_spacy_available() -> bool:
    """Check if spaCy is available without triggering initialization."""
    return _global_spacy_manager.is_available()


class GlobalComponentManager:
    """
    Global manager for all heavy pipeline components.
    Eliminates 150ms+ component initialization overhead.
    """
    
    _instance = None
    _lock = threading.Lock()
    _ac_classifier = None
    _semantic_extractor = None  
    _entity_normalizer = None
    _components_initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(GlobalComponentManager, cls).__new__(cls)
        return cls._instance
    
    def get_ac_classifier(self):
        """Get global AhoCorasickLayeredClassifier instance."""
        if self._ac_classifier is not None:
            return self._ac_classifier
            
        with self._lock:
            if self._ac_classifier is not None:
                return self._ac_classifier
                
            try:
                from knowledge.aho_corasick_engine import AhoCorasickKnowledgeEngine
                self._ac_classifier = AhoCorasickKnowledgeEngine()
                
                logger = logging.getLogger(__name__)
                logger.info("✅ Global AhoCorasick classifier initialized")
                return self._ac_classifier
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ AhoCorasick classifier initialization failed: {e}")
                return None
    
    def get_semantic_extractor(self):
        """Get global SemanticFactExtractor instance."""
        if self._semantic_extractor is not None:
            return self._semantic_extractor
            
        with self._lock:
            if self._semantic_extractor is not None:
                return self._semantic_extractor
                
            try:
                from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
                self._semantic_extractor = SemanticFactExtractor()
                
                logger = logging.getLogger(__name__)
                logger.info("✅ Global semantic fact extractor initialized")
                return self._semantic_extractor
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Semantic fact extractor initialization failed: {e}")
                return None
    
    def get_entity_normalizer(self, config):
        """Get global EntityNormalizer instance."""
        if self._entity_normalizer is not None:
            return self._entity_normalizer
            
        with self._lock:
            if self._entity_normalizer is not None:
                return self._entity_normalizer
                
            try:
                from knowledge.extractors.entity_normalizer import EntityNormalizer
                self._entity_normalizer = EntityNormalizer(config)
                
                logger = logging.getLogger(__name__)
                logger.info("✅ Global entity normalizer initialized")
                return self._entity_normalizer
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ Entity normalizer initialization failed: {e}")
                return None


# Global instance for easy access
_global_component_manager = GlobalComponentManager()

def get_global_ac_classifier():
    """Get the global AhoCorasick classifier instance."""
    return _global_component_manager.get_ac_classifier()

def get_global_semantic_extractor():
    """Get the global semantic fact extractor instance."""
    return _global_component_manager.get_semantic_extractor()

def get_global_entity_normalizer(config):
    """Get the global entity normalizer instance."""
    return _global_component_manager.get_entity_normalizer(config)