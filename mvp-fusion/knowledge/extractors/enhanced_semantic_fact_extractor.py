"""
Enhanced Semantic Fact Extractor with SPO Hybrid Integration

This module enhances the existing semantic fact extraction with our new SPO Hybrid
AC+FLPC architecture. It provides both backward compatibility with existing domain-specific
extraction and new structured SPO fact extraction for enhanced accuracy.

Key Enhancements:
- SPO Hybrid Architecture integration for structured fact extraction
- Zero-cost SPO assembly from pre-extracted AC+FLPC components  
- Enhanced accuracy through Subject-Predicate-Object relationships
- Domain-aware extraction with regulatory compliance focus
- Backward compatibility with existing semantic fact formats
"""

import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

# Import existing semantic fact extractor as base
try:
    from .semantic_fact_extractor import SemanticFactExtractor
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent))
    from semantic_fact_extractor import SemanticFactExtractor

# Import our SPO components
try:
    from .spo_component_cache import (
        SPOComponentCache, SPOEntity, SPOPredicate, SPOModifier, 
        PredicateCategory, ComponentType
    )
    from .spo_pattern_loader import get_spo_pattern_loader
    from .spo_assembler import SPOAssembler
except ImportError:
    from spo_component_cache import (
        SPOComponentCache, SPOEntity, SPOPredicate, SPOModifier, 
        PredicateCategory, ComponentType
    )
    from spo_pattern_loader import get_spo_pattern_loader
    from spo_assembler import SPOAssembler


class EnhancedSemanticFactExtractor(SemanticFactExtractor):
    """
    Enhanced semantic fact extractor with SPO Hybrid architecture
    
    Extends the existing extractor with structured SPO fact extraction while
    maintaining full backward compatibility with existing domain-specific patterns.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize enhanced extractor with SPO capabilities"""
        super().__init__(*args, **kwargs)
        
        # Initialize SPO components
        self.spo_pattern_loader = get_spo_pattern_loader()
        self.spo_assembler = SPOAssembler()
        self.spo_cache = None  # Will be set during processing
        
        # Enhanced logging
        self.logger.logger.info("🚀 Enhanced Semantic Fact Extractor initialized with SPO Hybrid architecture")
        
        # Load SPO patterns into memory for fast access
        self.spo_patterns_loaded = len(self.spo_pattern_loader.get_all_pattern_texts())
        self.logger.logger.info(f"📋 Loaded {self.spo_patterns_loaded} SPO patterns across 9 categories")
        
        # Performance tracking
        self.spo_performance = {
            'spo_facts_extracted': 0,
            'spo_assembly_time_ms': 0,
            'traditional_facts_extracted': 0,
            'hybrid_total_time_ms': 0
        }
    
    def extract_semantic_facts(self, text: str, cache_spo_components: bool = True) -> Dict[str, Any]:
        """
        Enhanced semantic fact extraction with SPO integration
        
        Args:
            text: Full document text with YAML frontmatter
            cache_spo_components: Whether to build SPO component cache during extraction
            
        Returns:
            Enhanced semantic facts including both traditional and SPO facts
        """
        import time
        start_time = time.time()
        
        self.logger.logger.info("🧠 Starting enhanced semantic fact extraction with SPO hybrid architecture")
        
        # Step 1: Run traditional semantic fact extraction (backward compatibility)
        traditional_facts = super().extract_semantic_facts(text)
        traditional_time = time.time()
        
        # Step 2: Extract SPO components and assemble structured facts
        if cache_spo_components:
            spo_facts = self._extract_spo_facts_from_text(text)
            spo_time = time.time()
            
            # Step 3: Merge traditional and SPO facts for enhanced output
            enhanced_facts = self._merge_traditional_and_spo_facts(traditional_facts, spo_facts)
            
        else:
            # Use existing SPO cache if available (zero-cost assembly)
            if self.spo_cache:
                spo_facts = self._assemble_spo_facts_from_cache()
                enhanced_facts = self._merge_traditional_and_spo_facts(traditional_facts, spo_facts)
            else:
                enhanced_facts = traditional_facts
        
        # Performance tracking
        total_time = (time.time() - start_time) * 1000
        self.spo_performance['traditional_facts_extracted'] = self._count_traditional_facts(traditional_facts)
        self.spo_performance['hybrid_total_time_ms'] = total_time
        
        self.logger.logger.info(f"✅ Enhanced extraction complete: {total_time:.1f}ms total")
        
        return enhanced_facts
    
    def set_spo_cache(self, cache: SPOComponentCache) -> None:
        """Set pre-built SPO component cache for zero-cost assembly"""
        self.spo_cache = cache
        self.logger.logger.debug("📦 SPO component cache set for zero-cost fact assembly")
    
    def _extract_spo_facts_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract SPO facts directly from text (when no pre-built cache available)
        
        This is a fallback method that builds SPO components on-demand.
        Ideally, components should be pre-extracted during entity extraction stage.
        """
        import time
        start_time = time.time()
        
        self.logger.logger.debug("🔧 Building SPO components from text (fallback mode)")
        
        # Parse YAML and markdown sections
        parts = text.split('---')
        if len(parts) >= 3:
            yaml_content = parts[1]
            markdown_content = '---'.join(parts[2:])
        else:
            yaml_content = ""
            markdown_content = text
        
        # Build SPO cache from text
        cache = self._build_spo_cache_from_text(markdown_content, yaml_content)
        
        # Assemble SPO facts
        spo_facts = self._assemble_spo_facts_from_cache(cache)
        
        assembly_time = (time.time() - start_time) * 1000
        self.spo_performance['spo_assembly_time_ms'] = assembly_time
        
        return spo_facts
    
    def _build_spo_cache_from_text(self, markdown_content: str, yaml_content: str) -> SPOComponentCache:
        """
        Build SPO component cache from text content
        
        This simulates the enhanced entity extraction stage for SPO component preparation.
        """
        cache = SPOComponentCache()
        
        # Extract sentence boundaries
        sentences = self._extract_sentence_boundaries(markdown_content)
        cache.set_sentence_boundaries(sentences)
        
        # Extract SPO components using pattern matching
        # Note: In production, this would be done during entity extraction stage with AC+FLPC
        
        # Extract predicates using our loaded patterns
        predicates = self._extract_predicates_from_text(markdown_content)
        for predicate in predicates:
            cache.add_predicate(predicate)
        
        # Extract subjects and objects (entities)
        # For now, use simple regex - in production this would use AC engine
        entities = self._extract_entities_from_text(markdown_content)
        for entity in entities:
            if self._is_likely_subject(entity, markdown_content):
                cache.add_subject(entity)
            if self._is_likely_object(entity, markdown_content):
                cache.add_object(entity)
        
        # Extract modifiers
        modifiers = self._extract_modifiers_from_text(markdown_content)
        for modifier in modifiers:
            cache.add_modifier(modifier)
        
        return cache
    
    def _assemble_spo_facts_from_cache(self, cache: SPOComponentCache = None) -> Dict[str, Any]:
        """Assemble SPO facts from component cache"""
        if cache is None:
            cache = self.spo_cache
        
        if not cache:
            return {'spo_facts': [], 'spo_summary': {'total_facts': 0}}
        
        # Use our SPO assembler for zero-cost fact assembly
        triplets = self.spo_assembler.assemble_spo_facts(cache)
        
        # Export in semantic analysis format
        spo_export = self.spo_assembler.export_triplets_for_semantic_analysis(triplets)
        
        self.spo_performance['spo_facts_extracted'] = len(triplets)
        
        self.logger.logger.info(f"🎯 Assembled {len(triplets)} SPO facts from cached components")
        
        return spo_export
    
    def _merge_traditional_and_spo_facts(self, traditional_facts: Dict, spo_facts: Dict) -> Dict[str, Any]:
        """
        Merge traditional domain-specific facts with new SPO facts
        
        Creates an enhanced fact set that includes both approaches for maximum coverage.
        """
        enhanced_facts = traditional_facts.copy()
        
        # Add SPO facts as a new category
        if 'spo_facts' in spo_facts and spo_facts['spo_facts']:
            enhanced_facts['spo_facts'] = spo_facts['spo_facts']
        
        # Enhance semantic summary
        if 'semantic_summary' in enhanced_facts:
            enhanced_facts['semantic_summary']['extraction_engine'] = "Enhanced FLPC + Aho-Corasick + SPO Hybrid"
            enhanced_facts['semantic_summary']['spo_hybrid'] = True
            
            # Add SPO facts to total count
            spo_count = len(spo_facts.get('spo_facts', []))
            if spo_count > 0:
                current_total = enhanced_facts['semantic_summary'].get('total_facts', 0)
                enhanced_facts['semantic_summary']['total_facts'] = current_total + spo_count
                
                # Add to fact_types breakdown
                if 'fact_types' not in enhanced_facts['semantic_summary']:
                    enhanced_facts['semantic_summary']['fact_types'] = {}
                enhanced_facts['semantic_summary']['fact_types']['spo_facts'] = spo_count
        
        # Add performance metrics
        enhanced_facts['spo_performance'] = self.spo_performance.copy()
        
        self.logger.logger.debug(f"🔀 Merged facts: {self._count_traditional_facts(traditional_facts)} traditional + {spo_count} SPO = {enhanced_facts['semantic_summary'].get('total_facts', 0)} total")
        
        return enhanced_facts
    
    def _extract_sentence_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """Extract sentence boundaries for SPO scoping"""
        sentences = []
        
        # Simple sentence boundary detection
        sentence_pattern = r'[.!?]+\s+'
        matches = list(re.finditer(sentence_pattern, text))
        
        start = 0
        for match in matches:
            end = match.end()
            if end - start > 10:  # Minimum sentence length
                sentences.append((start, end))
            start = end
        
        # Add final sentence
        if start < len(text) - 10:
            sentences.append((start, len(text)))
        
        return sentences
    
    def _extract_predicates_from_text(self, text: str) -> List[SPOPredicate]:
        """Extract predicate components using our pattern library"""
        predicates = []
        
        # Get high-frequency patterns for fast extraction
        pattern_loader = self.spo_pattern_loader
        high_freq_patterns = pattern_loader.get_high_frequency_patterns(100)
        
        for pattern in high_freq_patterns:
            # Find all occurrences of this predicate pattern
            for match in re.finditer(re.escape(pattern.text), text, re.IGNORECASE):
                predicate = SPOPredicate(
                    text=pattern.text,
                    category=pattern.category,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=pattern.confidence
                )
                predicates.append(predicate)
        
        return predicates
    
    def _extract_entities_from_text(self, text: str) -> List[SPOEntity]:
        """Extract entity components (simplified for demo)"""
        entities = []
        
        # Simple entity patterns (in production, this would use AC engine)
        entity_patterns = [
            (r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', 'PERSON'),     # Simple person names
            (r'\b[A-Z][A-Z]+\b', 'ORG'),                     # Acronyms as orgs
            (r'\b[A-Z][a-z]+ Corp\b|\b[A-Z][a-z]+ Inc\b', 'ORG'),  # Companies
        ]
        
        for pattern, entity_type in entity_patterns:
            for match in re.finditer(pattern, text):
                entity = SPOEntity(
                    text=match.group(),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.8
                )
                entities.append(entity)
        
        return entities
    
    def _extract_modifiers_from_text(self, text: str) -> List[SPOModifier]:
        """Extract modifier components"""
        modifiers = []
        
        # Temporal modifiers
        temporal_patterns = [
            r'\b(since|until|during|before|after)\s+\d{4}\b',
            r'\bin\s+\d{4}\b',
            r'\b(yesterday|today|tomorrow)\b'
        ]
        
        for pattern in temporal_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                modifier = SPOModifier(
                    text=match.group(),
                    modifier_type='temporal',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.7
                )
                modifiers.append(modifier)
        
        # Quantitative modifiers
        quant_patterns = [
            r'\b(approximately|about|roughly|nearly)\s+\d+',
            r'\b\d+%\b'
        ]
        
        for pattern in quant_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                modifier = SPOModifier(
                    text=match.group(),
                    modifier_type='quantitative',
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.7
                )
                modifiers.append(modifier)
        
        return modifiers
    
    def _is_likely_subject(self, entity: SPOEntity, text: str) -> bool:
        """Simple heuristic to determine if entity is likely a subject"""
        # Look for common subject patterns around the entity
        context_start = max(0, entity.start_pos - 50)
        context_end = min(len(text), entity.end_pos + 50)
        context = text[context_start:context_end]
        
        # Check for subject indicators
        subject_indicators = ['is', 'was', 'has', 'had', 'owns', 'controls', 'founded']
        relative_pos = entity.start_pos - context_start
        
        for indicator in subject_indicators:
            # Look for predicate after entity position
            indicator_pos = context.find(indicator, relative_pos)
            if 0 < indicator_pos < relative_pos + 100:  # Within reasonable distance
                return True
        
        return entity.entity_type in ['PERSON', 'ORG']  # Default for these types
    
    def _is_likely_object(self, entity: SPOEntity, text: str) -> bool:
        """Simple heuristic to determine if entity is likely an object"""
        # Look for common object patterns around the entity
        context_start = max(0, entity.start_pos - 50)
        context_end = min(len(text), entity.end_pos + 50)
        context = text[context_start:context_end]
        
        # Check for object indicators
        object_indicators = ['of', 'by', 'from', 'to', 'in', 'at']
        relative_pos = entity.start_pos - context_start
        
        for indicator in object_indicators:
            # Look for preposition before entity position
            indicator_pos = context.rfind(indicator, 0, relative_pos)
            if indicator_pos >= 0 and relative_pos - indicator_pos < 50:
                return True
        
        return True  # All entities can potentially be objects
    
    def _count_traditional_facts(self, facts: Dict) -> int:
        """Count traditional semantic facts"""
        count = 0
        traditional_categories = ['requirements', 'action_facts', 'regulation_citations', 'financial_impacts']
        
        for category in traditional_categories:
            if category in facts:
                count += len(facts[category])
        
        return count
    
    def get_spo_performance_stats(self) -> Dict[str, Any]:
        """Get SPO performance statistics"""
        return {
            'spo_patterns_loaded': self.spo_patterns_loaded,
            'performance_metrics': self.spo_performance.copy(),
            'assembler_stats': self.spo_assembler.get_assembly_stats() if hasattr(self.spo_assembler, 'get_assembly_stats') else {}
        }


# Factory function for easy integration
def create_enhanced_semantic_extractor(*args, **kwargs) -> EnhancedSemanticFactExtractor:
    """Create enhanced semantic fact extractor with SPO capabilities"""
    return EnhancedSemanticFactExtractor(*args, **kwargs)


# Testing function
if __name__ == "__main__":
    # Test enhanced semantic fact extractor
    print("Enhanced Semantic Fact Extractor Test")
    print("=" * 60)
    
    # Mock text for testing
    test_text = """---
domain_classification:
  top_domains: ['safety_compliance']
  top_document_types: ['osha_report']
---

Microsoft acquired LinkedIn in 2016. The company was founded by Bill Gates. 
The acquisition was completed after regulatory approval. OSHA requires safety compliance.
Workers must wear protective equipment. The fine was approximately $50,000.
"""
    
    # Create enhanced extractor
    extractor = create_enhanced_semantic_extractor()
    
    # Extract facts
    enhanced_facts = extractor.extract_semantic_facts(test_text)
    
    # Display results
    print(f"Traditional facts: {extractor._count_traditional_facts(enhanced_facts)}")
    print(f"SPO facts: {len(enhanced_facts.get('spo_facts', []))}")
    print(f"Total facts: {enhanced_facts.get('semantic_summary', {}).get('total_facts', 0)}")
    
    # Show SPO facts
    if 'spo_facts' in enhanced_facts:
        print("\nSPO Facts:")
        for i, fact in enumerate(enhanced_facts['spo_facts'][:3], 1):
            print(f"  {i}. {fact['subject']['text']} -> {fact['predicate']['text']} -> {fact['object']['text']}")
    
    # Performance stats
    perf_stats = extractor.get_spo_performance_stats()
    print(f"\nPerformance: {perf_stats['performance_metrics']['hybrid_total_time_ms']:.1f}ms total")
    print(f"SPO patterns loaded: {perf_stats['spo_patterns_loaded']}")