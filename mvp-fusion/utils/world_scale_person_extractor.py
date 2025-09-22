#!/usr/bin/env python3
"""
World-Scale Person Entity Extractor
===================================

High-performance person entity extraction using pure Aho-Corasick + FLPC strategy.
NO Python regex fallbacks - designed for world-scale performance.

Performance Target: 10,000+ pages/sec
Strategy: Single-pass Aho-Corasick automaton + FLPC pattern validation
"""

import time
import ahocorasick
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import sys

# Import FLPC for high-performance pattern matching
sys.path.append(str(Path(__file__).parent.parent))
from knowledge.extractors.fast_regex import FastRegexEngine

@dataclass
class PersonMatch:
    """Optimized person match with metadata"""
    text: str
    start: int
    end: int
    confidence: float
    evidence: List[str]
    context: str

class WorldScalePersonExtractor:
    """
    World-scale person entity extractor using pure Aho-Corasick + FLPC strategy.
    Zero Python regex usage - optimized for 10,000+ pages/sec performance.
    """
    
    def __init__(self, 
                 first_names_path: Optional[Path] = None,
                 last_names_path: Optional[Path] = None,
                 organizations_path: Optional[Path] = None,
                 min_confidence: float = 0.7):
        """
        Initialize world-scale person extractor.
        
        Args:
            first_names_path: Path to first names corpus
            last_names_path: Path to last names corpus  
            organizations_path: Path to organizations corpus
            min_confidence: Minimum confidence threshold
        """
        self.min_confidence = min_confidence
        
        # Load name corpora into sets for O(1) lookup
        self.first_names = self._load_corpus_fast(first_names_path) if first_names_path else set()
        self.last_names = self._load_corpus_fast(last_names_path) if last_names_path else set()
        self.organizations = self._load_corpus_fast(organizations_path) if organizations_path else set()
        
        # Initialize FLPC engine for pattern matching (NO Python regex)
        self.flpc_engine = FastRegexEngine()
        
        # Build blacklists as sets for O(1) lookup
        self._init_blacklists()
        
        # Build FLPC patterns for context validation
        self._init_flpc_patterns()
        
        # Build automatons AFTER loading corpus data
        self.name_automaton = None
        self.org_automaton = None
        self._build_automatons()
        
        # Initialization complete (reported in Core-8 summary)
    
    def _load_corpus_fast(self, path: Path) -> Set[str]:
        """Fast corpus loading optimized for large files"""
        if not path.exists():
            print(f"Warning: Corpus file not found: {path}")
            return set()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                # Single read + set comprehension for maximum speed
                return {line.strip().lower() for line in f if line.strip()}
        except Exception as e:
            print(f"Error loading corpus {path}: {e}")
            return set()
    
    def _init_blacklists(self):
        """Initialize blacklists as sets for O(1) lookup performance"""
        
        # Company founder names (fast set lookup)
        self.company_founder_names = {
            'ford', 'disney', 'dell', 'walton', 'mars', 'johnson',
            'kellogg', 'hilton', 'marriott', 'ferrari', 'porsche',
            'boeing', 'siemens', 'philips', 'bosch', 'krupp',
            'carnegie', 'morgan', 'goldman', 'sachs', 'wells',
            'fargo', 'stanley', 'lynch', 'schwab', 'buffett',
            'hewlett', 'packard', 'procter', 'gamble', 'colgate',
            'palmolive', 'kraft', 'heinz', 'nestle', 'unilever'
        }
        
        # Common word names
        self.common_word_names = {
            'mark', 'bill', 'page', 'stone', 'rock', 'rose',
            'lily', 'ivy', 'hope', 'faith', 'grace', 'may',
            'june', 'august', 'lane', 'brook', 'river', 'sky',
            'star', 'moon', 'sun', 'rain', 'snow', 'storm',
            'field', 'forest', 'hill', 'valley', 'meadow'
        }
        
        # Tech companies
        self.tech_companies = {
            'apple', 'google', 'microsoft', 'amazon', 'tesla',
            'meta', 'facebook', 'twitter', 'netflix', 'uber',
            'airbnb', 'spotify', 'slack', 'zoom', 'adobe'
        }
        
        # Job titles
        self.job_titles = {
            'chief', 'executive', 'officer', 'director', 'president',
            'manager', 'supervisor', 'coordinator', 'administrator',
            'secretary', 'treasurer', 'chairman', 'chairwoman',
            'vice', 'assistant', 'deputy', 'senior', 'junior',
            'lead', 'head', 'principal', 'captain', 'major',
            'general', 'colonel', 'lieutenant', 'sergeant'
        }
        
        # Geographic patterns (common patterns as keywords for AC)
        self.geographic_keywords = {
            'new york', 'new jersey', 'new mexico', 'new hampshire',
            'south carolina', 'south dakota', 'north carolina', 'north dakota',
            'west virginia', 'los angeles', 'san francisco', 'new orleans', 'las vegas',
            'street', 'avenue', 'road', 'boulevard', 'drive'
        }
        
        # Publication keywords
        self.publication_keywords = {
            'federal register', 'wall street journal', 'new york times',
            'washington post', 'journal', 'magazine', 'review',
            'register', 'bulletin', 'newsletter', 'times', 'post',
            'herald', 'tribune', 'gazette'
        }
    
    def _init_flpc_patterns(self):
        """Initialize FLPC patterns for context validation (NO Python regex)"""
        
        # High-confidence person context patterns
        self.person_context_patterns = {
            'title_prefix': r'(?i)(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Professor|CEO|President|Director|Founder|Chairman|Manager)\s+',
            'biographical': r'(?i)(was born|died|passed away|graduated|founded|invented|discovered|created)',
            'person_actions': r'(?i)(said|stated|announced|wrote|published|testified)',
            'role_suffix': r'(?i),\s*(CEO|President|Director|Founder|Chairman|Manager|Engineer|Scientist)',
            'suffix_pattern': r'(?i)\b(Jr\.?|Sr\.?|III|IV|V|II|PhD|MD|Esq\.?)$'
        }
        
        # Organization context patterns (negative indicators)
        # Note: FLPC doesn't support lookahead/lookbehind, using simpler patterns
        self.org_context_patterns = {
            'company_suffix': r'(?i)(Inc\.|LLC|Ltd\.|Corp|Corporation|Company|Group|Technologies|Systems|Software|Solutions|Services)',
            'company_action': r'(?i)(announced|released|launched|reported)\s+(its|their)',
            # Simplified patterns without lookahead - will filter in post-processing
            'at_company': r'(?i)at\s+[A-Z]\w+',  # "at" followed by capitalized word
            'from_company': r'(?i)from\s+[A-Z]\w+'  # "from" followed by capitalized word  
        }
    
    def _build_automatons(self):
        """Build Aho-Corasick automatons for single-pass name detection"""
        
        # Quietly build automatons (already reported in Core-8 initialization)
        
        # Build name automaton (first + last names)
        self.name_automaton = ahocorasick.Automaton()
        
        # Add all last names first
        added_count = 0
        for name in self.last_names:
            if name:  # Skip empty names
                self.name_automaton.add_word(name, ('last', name))
                added_count += 1
        
        # Add all first names second (priority over last names for overlaps)
        for name in self.first_names:
            if name:  # Skip empty names
                self.name_automaton.add_word(name, ('first', name))
                added_count += 1
        
        # Build the automaton silently
        self.name_automaton.make_automaton()
        
        # Build organization automaton for negative filtering
        self.org_automaton = ahocorasick.Automaton()
        
        org_count = 0
        for org in self.organizations:
            if org:  # Skip empty orgs
                self.org_automaton.add_word(org.lower(), ('org', org))
                org_count += 1
        
        if org_count > 0:
            self.org_automaton.make_automaton()
            pass  # Organization automaton ready
        else:
            pass  # No organizations loaded
        
        # Initialization complete (details shown in Core-8 summary)
        self.first_name_count = len(self.first_names)
        self.last_name_count = len(self.last_names)
    
    def extract_persons(self, text: str, document_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Extract person entities using world-scale Aho-Corasick + FLPC strategy.
        NO Python regex fallbacks - pure high-performance processing.
        
        Args:
            text: Input text to process
            document_metadata: Optional document metadata
            
        Returns:
            List of validated person entities with confidence scores
        """
        start_time = time.perf_counter()
        
        # Check if automaton is properly built
        if not self.name_automaton:
            raise Exception("Name automaton not built - call _build_automatons() first")
        
        # Step 1: Single-pass Aho-Corasick scan to find ALL name candidates
        name_matches = self._find_name_candidates_ac(text)
        
        # Step 2: Build potential person candidates from name sequences
        person_candidates = self._build_person_candidates(text, name_matches)
        
        # Step 3: Fast validation using FLPC context patterns
        validated_persons = self._validate_with_flpc(text, person_candidates)
        
        # Step 4: Final confidence scoring and filtering
        final_persons = self._apply_confidence_threshold(validated_persons)
        
        processing_time = (time.perf_counter() - start_time) * 1000
        
        # Convert to service processor format
        results = []
        for person in final_persons:
            results.append({
                'text': person.text,
                'type': 'PERSON',
                'confidence': person.confidence,
                'position': person.start,
                'context': person.context,
                'evidence': person.evidence,
                'span': {'start': person.start, 'end': person.end}
            })
        
        return results
    
    def _find_name_candidates_ac(self, text: str) -> List[Dict]:
        """Single-pass Aho-Corasick scan to find ALL name components"""
        text_lower = text.lower()
        name_matches = []
        
        # Single pass through text using Aho-Corasick
        for end_index, (name_type, name) in self.name_automaton.iter(text_lower):
            start_index = end_index - len(name) + 1
            
            # Word boundary check (fast character-based)
            if self._is_word_boundary_fast(text, start_index, len(name)):
                name_matches.append({
                    'text': text[start_index:end_index + 1],
                    'type': name_type,  # 'first' or 'last'
                    'start': start_index,
                    'end': end_index + 1,
                    'canonical': name
                })
        
        # Sort by position for sequence building
        return sorted(name_matches, key=lambda x: x['start'])
    
    def _is_word_boundary_fast(self, text: str, start: int, length: int) -> bool:
        """Fast word boundary check without regex"""
        end = start + length
        
        # Check character before
        if start > 0:
            prev_char = text[start - 1]
            if prev_char.isalnum() or prev_char == "'":
                return False
        
        # Check character after
        if end < len(text):
            next_char = text[end]
            if next_char.isalnum() or next_char == "'":
                return False
        
        return True
    
    def _build_person_candidates(self, text: str, name_matches: List[Dict]) -> List[PersonMatch]:
        """Build person candidates from name sequences"""
        candidates = []
        i = 0
        
        while i < len(name_matches):
            current_match = name_matches[i]
            
            # Try to build multi-word name sequences
            sequence = [current_match]
            j = i + 1
            
            # Look for adjacent name components (within reasonable distance)
            while j < len(name_matches):
                next_match = name_matches[j]
                gap = next_match['start'] - sequence[-1]['end']
                
                # Allow small gaps (spaces, middle initials, etc.)
                if gap <= 20 and gap >= 0:
                    # Check if gap contains only whitespace or single letters
                    gap_text = text[sequence[-1]['end']:next_match['start']]
                    if self._is_valid_name_gap(gap_text):
                        sequence.append(next_match)
                        j += 1
                    else:
                        break
                else:
                    break
            
            # Create person candidate from sequence
            if self._is_valid_person_sequence(sequence):
                candidate = self._create_person_candidate(text, sequence)
                if candidate:
                    candidates.append(candidate)
            
            # Move to next potential sequence
            i = max(i + 1, j)
        
        return candidates
    
    def _is_valid_name_gap(self, gap_text: str) -> bool:
        """Check if gap between names is valid (no regex)"""
        gap_clean = gap_text.strip()
        
        # Empty gap or just whitespace
        if not gap_clean:
            return True
        
        # Single letter (middle initial)
        if len(gap_clean) == 1 and gap_clean.isalpha():
            return True
        
        # Single letter with period (middle initial)
        if len(gap_clean) == 2 and gap_clean[0].isalpha() and gap_clean[1] == '.':
            return True
        
        # Common conjunctions
        if gap_clean.lower() in ['and', 'von', 'van', 'de', 'la', 'le', 'del', 'du']:
            return True
        
        return False
    
    def _is_valid_person_sequence(self, sequence: List[Dict]) -> bool:
        """Validate name sequence using position-aware corpus logic"""
        
        # Need at least one name component
        if not sequence:
            return False
        
        # Single name: accept if it's a first name
        if len(sequence) == 1:
            return sequence[0]['type'] == 'first'
        
        # Multiple names: Use position-based logic
        # First position should typically be first name, last position should be last name
        if len(sequence) >= 2:
            first_word = sequence[0]['canonical']
            last_word = sequence[-1]['canonical']
            
            # Check if first word can be a first name and last word can be a last name
            is_first_valid = first_word in self.first_names
            is_last_valid = last_word in self.last_names
            
            # Override the types based on position if both are valid
            if is_first_valid and is_last_valid:
                sequence[0]['type'] = 'first'  # Force first position to be first name
                sequence[-1]['type'] = 'last'  # Force last position to be last name
                return True
            elif is_first_valid:  # Only first position is valid first name
                return True
            elif is_last_valid:   # Only last position is valid last name  
                return True
        
        return False
    
    def _create_person_candidate(self, text: str, sequence: List[Dict]) -> Optional[PersonMatch]:
        """Create person candidate from name sequence"""
        
        if not sequence:
            return None
        
        # Calculate full span
        start_pos = sequence[0]['start']
        end_pos = sequence[-1]['end']
        candidate_text = text[start_pos:end_pos]
        
        # Get context (±50 characters)
        context_start = max(0, start_pos - 50)
        context_end = min(len(text), end_pos + 50)
        context = text[context_start:context_end]
        
        # Initial evidence
        evidence = []
        if len(sequence) == 1:
            evidence.append('single_first_name')
        else:
            evidence.append('full_name')
            evidence.append(f'{len(sequence)}_components')
        
        return PersonMatch(
            text=candidate_text,
            start=start_pos,
            end=end_pos,
            confidence=0.0,  # Will be calculated later
            evidence=evidence,
            context=context
        )
    
    def _validate_with_flpc(self, text: str, candidates: List[PersonMatch]) -> List[PersonMatch]:
        """Validate candidates using FLPC pattern matching (NO Python regex)"""
        validated = []
        
        for candidate in candidates:
            # Fast blacklist filtering
            if self._is_blacklisted_fast(candidate):
                continue
            
            # Check for organization indicators using FLPC
            if self._is_organization_flpc(candidate):
                continue
            
            # Calculate confidence using FLPC context patterns
            confidence = self._calculate_confidence_flpc(candidate)
            candidate.confidence = confidence
            
            if confidence > 0.0:  # Will apply threshold later
                validated.append(candidate)
        
        return validated
    
    def _is_blacklisted_fast(self, candidate: PersonMatch) -> bool:
        """Fast blacklist check using set lookups (O(1))"""
        text_lower = candidate.text.lower()
        tokens = text_lower.split()
        
        # Single token blacklists
        if len(tokens) == 1:
            token = tokens[0]
            if (token in self.company_founder_names or 
                token in self.tech_companies or 
                token in self.common_word_names):
                candidate.evidence.append('blacklisted_single_token')
                return True
        
        # Full text blacklists
        if (text_lower in self.company_founder_names or 
            text_lower in self.tech_companies):
            candidate.evidence.append('blacklisted_full_text')
            return True
        
        # Geographic/publication keywords
        for keyword in self.geographic_keywords:
            if keyword in text_lower:
                candidate.evidence.append('geographic_keyword')
                return True
        
        for keyword in self.publication_keywords:
            if keyword in text_lower:
                candidate.evidence.append('publication_keyword')
                return True
        
        return False
    
    def _is_organization_flpc(self, candidate: PersonMatch) -> bool:
        """Check if candidate is organization using FLPC patterns"""
        
        # Check organization automaton (only if built)
        if self.org_automaton and len(self.organizations) > 0:
            text_lower = candidate.text.lower()
            for end_index, (org_type, org_name) in self.org_automaton.iter(text_lower):
                if org_name in text_lower:
                    candidate.evidence.append('in_org_corpus')
                    return True
        
        # Check organization context using FLPC
        for pattern_name, pattern in self.org_context_patterns.items():
            try:
                matches = self.flpc_engine.findall(pattern, candidate.context)
                if matches:
                    candidate.evidence.append(f'org_context_{pattern_name}')
                    return True
            except Exception:
                # If FLPC fails, skip this pattern (no Python regex fallback)
                continue
        
        return False
    
    def _calculate_confidence_flpc(self, candidate: PersonMatch) -> float:
        """Calculate confidence using FLPC pattern matching"""
        base_score = 0.5  # Base score for valid name sequence
        bonus_score = 0.0
        
        # Title prefix bonus using FLPC
        try:
            title_matches = self.flpc_engine.findall(
                self.person_context_patterns['title_prefix'], 
                candidate.context
            )
            if title_matches:
                bonus_score += 0.3
                candidate.evidence.append('title_prefix')
        except Exception:
            pass
        
        # Person action bonus using FLPC
        try:
            action_matches = self.flpc_engine.findall(
                self.person_context_patterns['person_actions'],
                candidate.context
            )
            if action_matches:
                bonus_score += 0.2
                candidate.evidence.append('person_actions')
        except Exception:
            pass
        
        # Biographical context bonus using FLPC
        try:
            bio_matches = self.flpc_engine.findall(
                self.person_context_patterns['biographical'],
                candidate.context
            )
            if bio_matches:
                bonus_score += 0.3
                candidate.evidence.append('biographical')
        except Exception:
            pass
        
        # Role suffix bonus using FLPC
        try:
            role_matches = self.flpc_engine.findall(
                self.person_context_patterns['role_suffix'],
                candidate.context
            )
            if role_matches:
                bonus_score += 0.2
                candidate.evidence.append('role_suffix')
        except Exception:
            pass
        
        # Name suffix bonus using FLPC
        try:
            suffix_matches = self.flpc_engine.findall(
                self.person_context_patterns['suffix_pattern'],
                candidate.text
            )
            if suffix_matches:
                bonus_score += 0.1
                candidate.evidence.append('name_suffix')
        except Exception:
            pass
        
        # Full name bonus
        if len(candidate.text.split()) >= 2:
            bonus_score += 0.2
            candidate.evidence.append('full_name_bonus')
        
        return min(base_score + bonus_score, 1.0)
    
    def _apply_confidence_threshold(self, candidates: List[PersonMatch]) -> List[PersonMatch]:
        """Apply confidence threshold and return final results"""
        return [c for c in candidates if c.confidence >= self.min_confidence]
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'engine': 'World-Scale AC + FLPC',
            'strategy': 'Pure Aho-Corasick + FLPC (No Python regex)',
            'first_names_count': len(self.first_names),
            'last_names_count': len(self.last_names),
            'organizations_count': len(self.organizations),
            'target_performance': '10,000+ pages/sec'
        }


def test_world_scale_extractor():
    """Test the world-scale person extractor"""
    
    # Create sample corpus data for testing
    sample_first_names = {'john', 'jane', 'michael', 'sarah', 'tim', 'walt', 'henry', 'mary', 'david', 'lisa'}
    sample_last_names = {'smith', 'doe', 'dell', 'cook', 'disney', 'ford', 'gates', 'johnson', 'brown', 'wilson'}
    sample_orgs = {'apple', 'google', 'microsoft', 'dell', 'ford motor company'}
    
    # Initialize extractor
    extractor = WorldScalePersonExtractor(min_confidence=0.7)
    extractor.first_names = sample_first_names
    extractor.last_names = sample_last_names
    extractor.organizations = sample_orgs
    extractor._build_automatons()  # Rebuild with test data
    
    test_texts = [
        "Dr. John Smith announced the new research findings.",
        "Tim Cook, CEO of Apple, said the company will expand.",
        "Ford announced new vehicles this year.",  # Should reject - company
        "Jane Doe and Michael Brown attended the meeting.",
        "Apple released a new product yesterday.",  # Should reject - company
        "Professor Sarah Wilson published her research.",
        "The meeting with Henry Ford Jr. was productive.",
        "Microsoft Corporation announced quarterly results."  # Should reject - company
    ]
    
    print("🧪 Testing World-Scale Person Extractor")
    print("=" * 50)
    
    total_start = time.perf_counter()
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: {text}")
        
        start = time.perf_counter()
        persons = extractor.extract_persons(text)
        timing = (time.perf_counter() - start) * 1000
        
        print(f"  Time: {timing:.2f}ms")
        print(f"  Found: {len(persons)} persons")
        
        for person in persons:
            print(f"    - {person['text']} (confidence: {person['confidence']:.2f})")
            print(f"      Evidence: {', '.join(person['evidence'])}")
    
    total_time = (time.perf_counter() - total_start) * 1000
    print(f"\n🚀 Total processing time: {total_time:.2f}ms")
    print(f"📊 Average per text: {total_time/len(test_texts):.2f}ms")
    
    # Performance stats
    stats = extractor.get_performance_stats()
    print(f"\n📈 Performance Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    test_world_scale_extractor()