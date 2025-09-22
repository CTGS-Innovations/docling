#!/usr/bin/env python3
"""
Tentative Corpus Auto-Learning Manager for MVP-Fusion
===================================================

Manages auto-learning discoveries with human validation workflow.
Keeps main corpus clean while providing immediate speed benefits.

Key Features:
- Separate tentative corpus files for POS discoveries
- Immediate AC automaton updates for speed benefits
- Human validation workflow before promoting to main corpus
- Audit trail and quality control
"""

import time
import threading
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningCandidate:
    """Represents a candidate for corpus learning."""
    text: str
    entity_type: str
    confidence: float
    source: str  # 'pos_gap_discovery', 'manual', etc.
    discovery_timestamp: str
    discovery_context: str = ""
    metadata: Dict[str, Any] = None


@dataclass
class ValidationStats:
    """Statistics for validation workflow."""
    total_discoveries: int
    pending_validation: int
    validated_entries: int
    rejected_entries: int
    promoted_to_main: int
    last_validation_date: Optional[str] = None


class TentativeCorpusManager:
    """
    Manages tentative corpus learning with human validation workflow.
    
    Provides immediate speed benefits through live AC updates while
    maintaining quality control through human validation.
    """
    
    def __init__(self, corpus_dir: Path = None, config: Dict[str, Any] = None):
        """Initialize tentative corpus manager."""
        if corpus_dir is None:
            corpus_dir = Path("knowledge/corpus/foundation_data")
        
        self.corpus_dir = corpus_dir
        self.config = config or {}
        
        # Tentative corpus settings
        learning_config = self.config.get('tentative_learning', {})
        self.enabled = learning_config.get('enabled', True)
        self.auto_append_enabled = learning_config.get('auto_append_enabled', True)
        self.confidence_threshold = learning_config.get('confidence_threshold', 0.8)
        self.max_discoveries_per_session = learning_config.get('max_discoveries_per_session', 100)
        
        # File paths for tentative corpus
        self.tentative_files = {
            'ORG': self.corpus_dir / "pos_discovered_organizations.txt",
            'PERSON': self.corpus_dir / "pos_discovered_people.txt", 
            'LOCATION': self.corpus_dir / "pos_discovered_locations.txt",
            'GPE': self.corpus_dir / "pos_discovered_gpes.txt"
        }
        
        # Validation tracking
        self.validation_log = self.corpus_dir / "tentative_validation.log"
        self.stats_file = self.corpus_dir / "tentative_stats.json"
        
        # Thread safety for concurrent learning
        self.learning_lock = threading.Lock()
        
        # Cache for preventing duplicates
        self.known_discoveries: Dict[str, Set[str]] = {}
        self._load_existing_discoveries()
        
        # Statistics tracking
        self.session_stats = {
            'discoveries_added': 0,
            'duplicates_skipped': 0,
            'session_start': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Tentative Corpus Manager initialized (enabled: {self.enabled})")
    
    def _load_existing_discoveries(self):
        """Load existing tentative discoveries to prevent duplicates."""
        for entity_type, file_path in self.tentative_files.items():
            self.known_discoveries[entity_type] = set()
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                self.known_discoveries[entity_type].add(line.lower())
                except Exception as e:
                    logger.warning(f"Failed to load existing discoveries from {file_path}: {e}")
    
    def add_learning_candidate(self, candidate: LearningCandidate, 
                             live_automatons: Dict[str, Any] = None) -> bool:
        """
        Add a learning candidate to tentative corpus.
        
        Args:
            candidate: The learning candidate to add
            live_automatons: Optional live AC automatons to update
            
        Returns:
            True if added, False if duplicate or rejected
        """
        if not self.enabled or not self.auto_append_enabled:
            return False
        
        # Validate candidate
        if not self._validate_candidate(candidate):
            return False
        
        # Check for duplicates
        entity_lower = candidate.text.lower()
        if entity_lower in self.known_discoveries.get(candidate.entity_type, set()):
            self.session_stats['duplicates_skipped'] += 1
            logger.debug(f"Skipping duplicate discovery: {candidate.text}")
            return False
        
        # Thread-safe addition
        with self.learning_lock:
            try:
                # Add to tentative corpus file
                self._append_to_tentative_corpus(candidate)
                
                # Update live automaton for immediate speed benefit
                if live_automatons and candidate.entity_type in live_automatons:
                    self._update_live_automaton(candidate, live_automatons[candidate.entity_type])
                
                # Update caches
                if candidate.entity_type not in self.known_discoveries:
                    self.known_discoveries[candidate.entity_type] = set()
                self.known_discoveries[candidate.entity_type].add(entity_lower)
                
                # Update statistics
                self.session_stats['discoveries_added'] += 1
                
                logger.info(f"📝 Tentative learning: Added '{candidate.text}' to {candidate.entity_type} corpus (confidence: {candidate.confidence:.2f})")
                return True
                
            except Exception as e:
                logger.error(f"Failed to add learning candidate '{candidate.text}': {e}")
                return False
    
    def _validate_candidate(self, candidate: LearningCandidate) -> bool:
        """Validate a learning candidate before adding."""
        # Confidence threshold
        if candidate.confidence < self.confidence_threshold:
            return False
        
        # Text quality checks
        if not candidate.text or len(candidate.text.strip()) < 2:
            return False
        
        # Entity type validation
        if candidate.entity_type not in self.tentative_files:
            logger.warning(f"Unknown entity type for learning: {candidate.entity_type}")
            return False
        
        # Session limits
        if self.session_stats['discoveries_added'] >= self.max_discoveries_per_session:
            logger.warning(f"Session discovery limit reached: {self.max_discoveries_per_session}")
            return False
        
        return True
    
    def _append_to_tentative_corpus(self, candidate: LearningCandidate):
        """Append candidate to appropriate tentative corpus file."""
        file_path = self.tentative_files[candidate.entity_type]
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create header if file doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Tentative {candidate.entity_type} Discoveries (Auto-Learning)\n")
                f.write(f"# Generated by POS Gap Discovery - Requires Human Validation\n")
                f.write(f"# Format: entity_text\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n")
                f.write(f"#\n")
        
        # Append discovery
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(f"{candidate.text}\n")
        
        # Log to validation log
        self._log_discovery(candidate)
    
    def _update_live_automaton(self, candidate: LearningCandidate, automaton):
        """Update live AC automaton for immediate speed benefit."""
        try:
            # IMPORTANT: Cannot add words to finalized automaton
            # Skip live updates to avoid breaking the automaton
            # New entities will be available after next corpus reload
            logger.debug(f"Skipping live automaton update for '{candidate.text}' (requires corpus reload)")
        except Exception as e:
            logger.warning(f"Failed to update live automaton: {e}")
    
    def _log_discovery(self, candidate: LearningCandidate):
        """Log discovery to validation log for audit trail."""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'entity_type': candidate.entity_type,
                'text': candidate.text,
                'confidence': candidate.confidence,
                'source': candidate.source,
                'context': candidate.discovery_context
            }
            
            with open(self.validation_log, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
                
        except Exception as e:
            logger.warning(f"Failed to log discovery: {e}")
    
    def get_pending_discoveries(self, entity_type: str = None) -> Dict[str, List[str]]:
        """Get pending discoveries for human validation."""
        pending = {}
        
        entity_types = [entity_type] if entity_type else self.tentative_files.keys()
        
        for ent_type in entity_types:
            file_path = self.tentative_files[ent_type]
            discoveries = []
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                discoveries.append(line)
                except Exception as e:
                    logger.error(f"Failed to read {file_path}: {e}")
            
            if discoveries:
                pending[ent_type] = discoveries
        
        return pending
    
    def validate_discoveries(self, entity_type: str, validated_entities: List[str], 
                           rejected_entities: List[str] = None) -> bool:
        """
        Human validation of discoveries.
        
        Args:
            entity_type: Type of entities being validated
            validated_entities: List of entities confirmed as valid
            rejected_entities: List of entities rejected
            
        Returns:
            True if validation successful
        """
        try:
            file_path = self.tentative_files[entity_type]
            if not file_path.exists():
                return False
            
            # Read current discoveries
            current_discoveries = []
            with open(file_path, 'r', encoding='utf-8') as f:
                current_discoveries = [line.strip() for line in f 
                                     if line.strip() and not line.startswith('#')]
            
            # Create validated corpus file
            validated_file = self.corpus_dir / f"validated_{entity_type.lower()}s_{datetime.now().strftime('%Y_%m_%d')}.txt"
            with open(validated_file, 'w', encoding='utf-8') as f:
                f.write(f"# Validated {entity_type} Entities\n")
                f.write(f"# Validated on: {datetime.now().isoformat()}\n")
                f.write(f"# Ready for promotion to main corpus\n")
                f.write(f"#\n")
                for entity in validated_entities:
                    f.write(f"{entity}\n")
            
            # Remove validated/rejected from tentative corpus
            remaining_discoveries = [d for d in current_discoveries 
                                   if d not in validated_entities and 
                                      d not in (rejected_entities or [])]
            
            # Rewrite tentative corpus with remaining discoveries
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Tentative {entity_type} Discoveries (Auto-Learning)\n")
                f.write(f"# Updated: {datetime.now().isoformat()}\n")
                f.write(f"#\n")
                for entity in remaining_discoveries:
                    f.write(f"{entity}\n")
            
            # Log validation
            validation_entry = {
                'timestamp': datetime.now().isoformat(),
                'entity_type': entity_type,
                'validated_count': len(validated_entities),
                'rejected_count': len(rejected_entities or []),
                'validated_file': str(validated_file)
            }
            
            with open(self.validation_log, 'a', encoding='utf-8') as f:
                f.write(f"VALIDATION: {validation_entry}\n")
            
            logger.info(f"✅ Validation complete: {len(validated_entities)} validated, {len(rejected_entities or [])} rejected")
            return True
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return False
    
    def get_validation_stats(self) -> ValidationStats:
        """Get statistics for validation dashboard."""
        pending = self.get_pending_discoveries()
        total_pending = sum(len(entities) for entities in pending.values())
        
        return ValidationStats(
            total_discoveries=self.session_stats['discoveries_added'],
            pending_validation=total_pending,
            validated_entries=0,  # Would be calculated from validation log
            rejected_entries=0,   # Would be calculated from validation log
            promoted_to_main=0,   # Would be calculated from promotion log
            last_validation_date=None  # Would be read from validation log
        )
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        stats = self.session_stats.copy()
        stats['session_duration_minutes'] = (
            datetime.now() - datetime.fromisoformat(stats['session_start'])
        ).total_seconds() / 60
        return stats
    
    def is_enabled(self) -> bool:
        """Check if tentative learning is enabled."""
        return self.enabled and self.auto_append_enabled


# Utility functions for integration
def create_learning_candidate_from_pos_discovery(pos_discovery, context: str = "") -> LearningCandidate:
    """Convert POS discovery to learning candidate."""
    return LearningCandidate(
        text=pos_discovery.text,
        entity_type=pos_discovery.entity_type,
        confidence=pos_discovery.confidence,
        source='pos_gap_discovery',
        discovery_timestamp=datetime.now().isoformat(),
        discovery_context=context,
        metadata={
            'pos_pattern': pos_discovery.pos_pattern,
            'sentence_id': pos_discovery.sentence_id
        }
    )


# Test function
def test_tentative_corpus_manager():
    """Test the tentative corpus manager."""
    print("🚀 Testing Tentative Corpus Manager")
    print("=" * 50)
    
    # Initialize manager
    manager = TentativeCorpusManager()
    
    print(f"✅ Manager initialized (enabled: {manager.is_enabled()})")
    print(f"📊 Session stats: {manager.get_session_stats()}")
    
    # Test learning candidate
    candidate = LearningCandidate(
        text="Tesla, Inc.",
        entity_type="ORG",
        confidence=0.95,
        source="pos_gap_discovery",
        discovery_timestamp=datetime.now().isoformat(),
        discovery_context="Found in safety document"
    )
    
    # Add candidate
    success = manager.add_learning_candidate(candidate)
    print(f"📝 Added learning candidate: {success}")
    
    # Check pending discoveries
    pending = manager.get_pending_discoveries()
    print(f"🔍 Pending discoveries: {pending}")
    
    # Get stats
    stats = manager.get_validation_stats()
    print(f"📈 Validation stats: Total={stats.total_discoveries}, Pending={stats.pending_validation}")
    
    print("\n✅ Tentative corpus manager test complete!")


if __name__ == "__main__":
    test_tentative_corpus_manager()