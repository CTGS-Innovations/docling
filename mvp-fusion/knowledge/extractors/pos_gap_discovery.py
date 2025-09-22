#!/usr/bin/env python3
"""
Gap-Filling POS Discovery Engine for MVP-Fusion
==============================================

Smart entity discovery using POS patterns only on sentences with no AC/FLPC hits.
Optimized for performance with configurable on/off controls.

Key Features:
- Only processes sentences with zero entity spans (gap-filling)
- POS pattern discovery for unknown organizations, people, locations
- Auto-learning: discoveries feed back to AC corpus
- Configurable and encapsulated for A/B testing
"""

import time
import re
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import logging

# Conditional spaCy import for lightweight POS tagging
try:
    import spacy
    from spacy import Language
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

logger = logging.getLogger(__name__)


@dataclass
class POSDiscovery:
    """Represents a POS-discovered entity."""
    text: str
    entity_type: str
    start: int
    end: int
    sentence_id: int
    confidence: float
    pos_pattern: str
    metadata: Dict[str, Any] = None


@dataclass
class GapAnalysis:
    """Analysis of document coverage gaps."""
    total_sentences: int
    sentences_with_entities: int
    empty_sentences: int
    coverage_percent: float
    gap_sentences: List[int]


class POSGapDiscovery:
    """
    Gap-filling POS discovery engine.
    
    Processes only sentences with no AC/FLPC entity hits to discover
    unknown organizations, people, and locations using POS patterns.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize POS gap discovery engine."""
        self.config = config or {}
        
        # Feature control - can be disabled entirely
        # Check both root level and pipeline level for config
        pos_config = self.config.get('pos_gap_discovery', {})
        if not pos_config and 'pipeline' in self.config:
            pos_config = self.config['pipeline'].get('pos_gap_discovery', {})
        
        self.enabled = pos_config.get('enabled', False)
        self.discovery_config = pos_config
        
        # Performance settings
        self.max_sentence_length = self.discovery_config.get('max_sentence_length', 200)
        self.min_confidence_threshold = self.discovery_config.get('min_confidence_threshold', 0.7)
        self.max_discoveries_per_sentence = self.discovery_config.get('max_discoveries_per_sentence', 3)
        
        # Discovery targets
        self.discover_organizations = self.discovery_config.get('discover_organizations', True)
        self.discover_people = self.discovery_config.get('discover_people', True)
        self.discover_locations = self.discovery_config.get('discover_locations', False)  # Conservative default
        
        # Learning pipeline
        self.auto_learn_enabled = self.discovery_config.get('auto_learn_enabled', True)
        self.learning_confidence_threshold = self.discovery_config.get('learning_confidence_threshold', 0.8)
        
        # Performance tracking
        self.stats = {
            'total_calls': 0,
            'total_processing_time_ms': 0.0,
            'sentences_processed': 0,
            'discoveries_made': 0,
            'entities_learned': 0
        }
        
        # Initialize spaCy if available and enabled
        self.nlp = None
        if self.enabled and HAS_SPACY:
            self._initialize_spacy()
        
        # POS patterns for entity discovery
        self._initialize_pos_patterns()
    
    def _initialize_spacy(self):
        """Initialize lightweight spaCy model for POS tagging only."""
        try:
            # Load minimal spaCy model with only tokenizer, tagger, and sentencizer
            self.nlp = spacy.load(
                "en_core_web_sm", 
                disable=["parser", "ner", "lemmatizer", "attribute_ruler"]
            )
            # Add sentencizer for sentence boundary detection
            self.nlp.add_pipe('sentencizer')
            logger.info("✅ POS Gap Discovery: spaCy initialized (tokenizer + tagger + sentencizer)")
        except Exception as e:
            logger.warning(f"⚠️ POS Gap Discovery: Failed to load spaCy: {e}")
            self.enabled = False
    
    def _initialize_pos_patterns(self):
        """Initialize POS patterns for entity discovery."""
        
        # Organization patterns (highest priority for unknown companies)
        self.organization_patterns = [
            {
                'name': 'corporate_suffix',
                'pattern': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)[,\s]+(Inc|LLC|Corp|Corporation|Ltd|Company|Technologies|Systems|Solutions|Enterprises|Group)\.?',
                'confidence_base': 0.9,
                'pos_validation': []  # Skip POS validation for now - rely on pattern strength
            },
            {
                'name': 'government_agency',
                'pattern': r'(Department|Ministry|Office|Bureau|Agency|Commission|Administration)\s+of\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                'confidence_base': 0.85,
                'pos_validation': []  # Skip POS validation for now
            },
            {
                'name': 'educational_institution',
                'pattern': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(University|Institute|College|School|Academy)',
                'confidence_base': 0.8,
                'pos_validation': []
            },
            {
                'name': 'business_partnership',
                'pattern': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+&\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(LLP|Partnership|Associates)',
                'confidence_base': 0.85,
                'pos_validation': []
            }
        ]
        
        # Person patterns (for unknown people not in corpus)
        self.person_patterns = [
            {
                'name': 'title_person',
                'pattern': r'(Dr|Prof|Mr|Mrs|Ms|Miss|CEO|CTO|CFO|President|Director|Manager)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)',
                'confidence_base': 0.8,
                'pos_validation': ['NOUN', 'PROPN']  # Title + proper noun
            },
            {
                'name': 'person_role',
                'pattern': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)[,\s]+(CEO|CTO|CFO|President|Director|Manager|Engineer|Analyst|Specialist)',
                'confidence_base': 0.75,
                'pos_validation': ['PROPN', 'NOUN']
            }
        ]
        
        # Location patterns (conservative - only clear geographic indicators)
        self.location_patterns = [
            {
                'name': 'geographic_feature',
                'pattern': r'([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(Mountain|River|Lake|Valley|Desert|Forest|Park|Beach)',
                'confidence_base': 0.8,
                'pos_validation': ['PROPN', 'NOUN']
            }
        ]
    
    def is_enabled(self) -> bool:
        """Check if POS gap discovery is enabled and functional."""
        return self.enabled and self.nlp is not None
    
    def analyze_coverage_gaps(self, document_text: str, existing_entities: List[Dict]) -> GapAnalysis:
        """
        Analyze document to identify sentences with no entity coverage.
        
        Args:
            document_text: Full document text
            existing_entities: List of entities found by AC/FLPC with spans
            
        Returns:
            GapAnalysis with coverage statistics and gap identification
        """
        if not self.is_enabled():
            return GapAnalysis(0, 0, 0, 0.0, [])
        
        # Split into sentences using spaCy
        doc = self.nlp(document_text)
        sentences = list(doc.sents)
        
        # Track which sentences have entities
        sentences_with_entities = set()
        
        for entity in existing_entities:
            span = entity.get('span', {})
            start = span.get('start', -1)
            end = span.get('end', -1)
            
            if start >= 0 and end >= 0:
                # Find which sentence contains this entity
                for i, sent in enumerate(sentences):
                    if sent.start_char <= start < sent.end_char:
                        sentences_with_entities.add(i)
                        break
        
        # Identify gap sentences
        total_sentences = len(sentences)
        sentences_with_entities_count = len(sentences_with_entities)
        empty_sentences = total_sentences - sentences_with_entities_count
        coverage_percent = (sentences_with_entities_count / total_sentences * 100) if total_sentences > 0 else 0
        
        gap_sentences = [i for i in range(total_sentences) if i not in sentences_with_entities]
        
        return GapAnalysis(
            total_sentences=total_sentences,
            sentences_with_entities=sentences_with_entities_count,
            empty_sentences=empty_sentences,
            coverage_percent=coverage_percent,
            gap_sentences=gap_sentences
        )
    
    def discover_entities_in_gaps(self, document_text: str, existing_entities: List[Dict]) -> List[POSDiscovery]:
        """
        Main discovery function: find entities in sentences with no existing coverage.
        
        Args:
            document_text: Full document text
            existing_entities: Entities already found by AC/FLPC
            
        Returns:
            List of newly discovered entities
        """
        if not self.is_enabled():
            return []
        
        start_time = time.perf_counter()
        self.stats['total_calls'] += 1
        
        try:
            # Analyze coverage gaps
            gap_analysis = self.analyze_coverage_gaps(document_text, existing_entities)
            
            if gap_analysis.empty_sentences == 0:
                logger.debug("🔍 POS Gap Discovery: No gaps found, skipping")
                return []
            
            logger.debug(f"🔍 POS Gap Discovery: {gap_analysis.empty_sentences}/{gap_analysis.total_sentences} sentences need processing ({gap_analysis.coverage_percent:.1f}% coverage)")
            
            # Process only gap sentences
            doc = self.nlp(document_text)
            sentences = list(doc.sents)
            discoveries = []
            
            for sentence_id in gap_analysis.gap_sentences:
                sentence = sentences[sentence_id]
                
                # Skip very long sentences for performance
                if len(sentence.text) > self.max_sentence_length:
                    continue
                
                # Discover entities in this sentence
                sentence_discoveries = self._discover_in_sentence(sentence, sentence_id)
                discoveries.extend(sentence_discoveries)
                
                # Limit discoveries per sentence
                if len(sentence_discoveries) >= self.max_discoveries_per_sentence:
                    break
            
            # Update stats
            processing_time = (time.perf_counter() - start_time) * 1000
            self.stats['total_processing_time_ms'] += processing_time
            self.stats['sentences_processed'] += len(gap_analysis.gap_sentences)
            self.stats['discoveries_made'] += len(discoveries)
            
            logger.debug(f"🟢 POS Gap Discovery: Found {len(discoveries)} new entities in {processing_time:.1f}ms")
            
            return discoveries
            
        except Exception as e:
            logger.warning(f"⚠️ POS Gap Discovery failed: {e}")
            return []
    
    def _discover_in_sentence(self, sentence, sentence_id: int) -> List[POSDiscovery]:
        """Discover entities within a single sentence using POS patterns."""
        discoveries = []
        sentence_text = sentence.text
        
        # Get POS tags for the sentence
        pos_tags = [token.pos_ for token in sentence]
        
        # Try organization patterns
        if self.discover_organizations:
            for pattern_config in self.organization_patterns:
                pattern_discoveries = self._apply_pos_pattern(
                    sentence_text, sentence, sentence_id, pattern_config, 'ORG', pos_tags
                )
                discoveries.extend(pattern_discoveries)
        
        # Try person patterns  
        if self.discover_people:
            for pattern_config in self.person_patterns:
                pattern_discoveries = self._apply_pos_pattern(
                    sentence_text, sentence, sentence_id, pattern_config, 'PERSON', pos_tags
                )
                discoveries.extend(pattern_discoveries)
        
        # Try location patterns
        if self.discover_locations:
            for pattern_config in self.location_patterns:
                pattern_discoveries = self._apply_pos_pattern(
                    sentence_text, sentence, sentence_id, pattern_config, 'LOCATION', pos_tags
                )
                discoveries.extend(pattern_discoveries)
        
        return discoveries
    
    def _apply_pos_pattern(self, sentence_text: str, sentence, sentence_id: int, 
                          pattern_config: Dict, entity_type: str, pos_tags: List[str]) -> List[POSDiscovery]:
        """Apply a specific POS pattern to discover entities."""
        discoveries = []
        
        try:
            pattern = pattern_config['pattern']
            matches = re.finditer(pattern, sentence_text)
            
            for match in matches:
                # Extract entity text
                entity_text = match.group(0).strip()
                start_pos = sentence.start_char + match.start()
                end_pos = sentence.start_char + match.end()
                
                # Validate using POS tags
                if self._validate_pos_pattern(match, sentence, pattern_config.get('pos_validation', [])):
                    # Calculate confidence
                    confidence = self._calculate_confidence(entity_text, pattern_config, pos_tags)
                    
                    if confidence >= self.min_confidence_threshold:
                        discovery = POSDiscovery(
                            text=entity_text,
                            entity_type=entity_type,
                            start=start_pos,
                            end=end_pos,
                            sentence_id=sentence_id,
                            confidence=confidence,
                            pos_pattern=pattern_config['name'],
                            metadata={
                                'pattern_type': pattern_config['name'],
                                'sentence_text': sentence_text,
                                'pos_validation': pattern_config.get('pos_validation', [])
                            }
                        )
                        discoveries.append(discovery)
        
        except Exception as e:
            logger.debug(f"Pattern application failed: {e}")
        
        return discoveries
    
    def _validate_pos_pattern(self, match, sentence, expected_pos: List[str]) -> bool:
        """Validate that the matched text has expected POS tags."""
        if not expected_pos:
            return True
        
        try:
            # Get tokens that overlap with the match
            match_tokens = []
            for token in sentence:
                token_start = token.idx
                token_end = token.idx + len(token.text)
                match_start = match.start()
                match_end = match.end()
                
                # Check if token overlaps with match
                if not (token_end <= match_start or token_start >= match_end):
                    match_tokens.append(token)
            
            # Check if POS pattern matches
            if len(match_tokens) >= len(expected_pos):
                for i, expected in enumerate(expected_pos):
                    if i < len(match_tokens):
                        if match_tokens[i].pos_ != expected:
                            return False
                return True
            
        except Exception:
            pass
        
        return False
    
    def _calculate_confidence(self, entity_text: str, pattern_config: Dict, pos_tags: List[str]) -> float:
        """Calculate confidence score for discovered entity."""
        base_confidence = pattern_config.get('confidence_base', 0.7)
        
        # Adjust based on text characteristics
        confidence = base_confidence
        
        # Boost for proper capitalization
        if entity_text.istitle():
            confidence += 0.05
        
        # Boost for multiple words (more specific)
        word_count = len(entity_text.split())
        if word_count > 1:
            confidence += 0.05 * (word_count - 1)
        
        # Reduce for very short entities
        if len(entity_text) < 4:
            confidence -= 0.1
        
        # Reduce for all caps (might be acronym without context)
        if entity_text.isupper() and len(entity_text) < 6:
            confidence -= 0.05
        
        return min(1.0, max(0.1, confidence))
    
    def get_learning_candidates(self, discoveries: List[POSDiscovery]) -> List[POSDiscovery]:
        """Get high-confidence discoveries suitable for AC corpus learning."""
        if not self.auto_learn_enabled:
            return []
        
        learning_candidates = []
        for discovery in discoveries:
            if discovery.confidence >= self.learning_confidence_threshold:
                learning_candidates.append(discovery)
        
        return learning_candidates
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance and usage statistics."""
        stats = self.stats.copy()
        
        # Calculate derived metrics
        if stats['total_calls'] > 0:
            stats['avg_processing_time_ms'] = stats['total_processing_time_ms'] / stats['total_calls']
            stats['avg_sentences_per_call'] = stats['sentences_processed'] / stats['total_calls']
            stats['avg_discoveries_per_call'] = stats['discoveries_made'] / stats['total_calls']
        else:
            stats['avg_processing_time_ms'] = 0
            stats['avg_sentences_per_call'] = 0
            stats['avg_discoveries_per_call'] = 0
        
        # Configuration info
        stats['enabled'] = self.enabled
        stats['spacy_available'] = HAS_SPACY
        stats['config'] = self.discovery_config
        
        return stats
    
    def reset_statistics(self):
        """Reset performance statistics."""
        self.stats = {
            'total_calls': 0,
            'total_processing_time_ms': 0.0,
            'sentences_processed': 0,
            'discoveries_made': 0,
            'entities_learned': 0
        }


# Factory function for easy integration
def create_pos_gap_discovery(config: Dict[str, Any] = None) -> POSGapDiscovery:
    """Create and return a POS gap discovery instance."""
    return POSGapDiscovery(config)


# Test function
def test_pos_gap_discovery():
    """Test the POS gap discovery system."""
    print("🚀 Testing POS Gap Discovery System")
    print("=" * 50)
    
    # Test configuration
    test_config = {
        'pos_gap_discovery': {
            'enabled': True,
            'discover_organizations': True,
            'discover_people': True,
            'discover_locations': False,
            'min_confidence_threshold': 0.7,
            'auto_learn_enabled': True
        }
    }
    
    # Initialize discovery engine
    discovery = POSGapDiscovery(test_config)
    
    if not discovery.is_enabled():
        print("❌ POS Gap Discovery not available (spaCy not installed)")
        return
    
    # Test document with known and unknown entities
    test_doc = """
    OSHA issued new safety guidelines last month. The guidelines were developed by Department of Emerging Technologies.
    CyberSecure Solutions, Inc. reported no workplace incidents. Their CEO, Sarah Martinez, praised the new protocols.
    InnovaTech LLC implemented AI safety monitoring systems. The Microsoft Corporation also announced improvements.
    """
    
    # Simulate existing AC/FLPC entities (some sentences covered, some not)
    existing_entities = [
        {'text': 'OSHA', 'type': 'ORG', 'span': {'start': 0, 'end': 4}},
        {'text': 'Microsoft Corporation', 'type': 'ORG', 'span': {'start': 280, 'end': 301}}
    ]
    
    print(f"📄 Test document: {len(test_doc)} characters")
    print(f"🎯 Existing entities: {len(existing_entities)}")
    
    # Analyze gaps
    gap_analysis = discovery.analyze_coverage_gaps(test_doc, existing_entities)
    print(f"\n📊 Coverage Analysis:")
    print(f"   Total sentences: {gap_analysis.total_sentences}")
    print(f"   Sentences with entities: {gap_analysis.sentences_with_entities}")
    print(f"   Empty sentences: {gap_analysis.empty_sentences}")
    print(f"   Coverage: {gap_analysis.coverage_percent:.1f}%")
    
    # Discover entities in gaps
    discoveries = discovery.discover_entities_in_gaps(test_doc, existing_entities)
    
    print(f"\n🔍 POS Discoveries: {len(discoveries)}")
    for i, disc in enumerate(discoveries, 1):
        print(f"   {i}. {disc.entity_type}: '{disc.text}' (confidence: {disc.confidence:.2f}, pattern: {disc.pos_pattern})")
    
    # Learning candidates
    learning_candidates = discovery.get_learning_candidates(discoveries)
    print(f"\n🧠 Learning candidates: {len(learning_candidates)}")
    for candidate in learning_candidates:
        print(f"   - {candidate.text} ({candidate.confidence:.2f})")
    
    # Statistics
    stats = discovery.get_statistics()
    print(f"\n📈 Performance Statistics:")
    print(f"   Processing time: {stats['avg_processing_time_ms']:.1f}ms")
    print(f"   Sentences processed: {stats['sentences_processed']}")
    print(f"   Discoveries made: {stats['discoveries_made']}")
    
    print("\n✅ POS Gap Discovery test complete!")


if __name__ == "__main__":
    test_pos_gap_discovery()