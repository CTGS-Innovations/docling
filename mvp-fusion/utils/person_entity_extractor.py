#!/usr/bin/env python3
"""
Conservative Person Entity Extractor
====================================
High-accuracy person entity extraction with strict validation rules.
Prioritizes precision over recall to minimize false positives.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from pathlib import Path
import json
from dataclasses import dataclass
from enum import Enum

class ConfidenceLevel(Enum):
    """Confidence levels for person entity extraction"""
    VERY_HIGH = 0.9   # Has title + full name + action verb
    HIGH = 0.8        # Has full name + strong context
    MEDIUM = 0.7      # Minimum threshold for acceptance
    LOW = 0.5         # Below threshold, rejected
    VERY_LOW = 0.3    # Ambiguous, definitely rejected

@dataclass
class PersonCandidate:
    """Represents a potential person entity"""
    tokens: List[str]
    text: str
    context: str  # Surrounding text (±50 chars)
    position: int  # Position in document
    confidence: float = 0.0
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []

class PersonEntityExtractor:
    """Conservative person entity extractor with high accuracy requirements"""
    
    def __init__(self, 
                 first_names_path: Optional[Path] = None,
                 last_names_path: Optional[Path] = None,
                 organizations_path: Optional[Path] = None,
                 min_confidence: float = 0.7):
        """
        Initialize the person entity extractor.
        
        Args:
            first_names_path: Path to first names corpus
            last_names_path: Path to last names corpus  
            organizations_path: Path to organizations corpus
            min_confidence: Minimum confidence threshold (default 0.7)
        """
        self.min_confidence = min_confidence
        
        # Load name corpora
        self.first_names = self._load_corpus(first_names_path) if first_names_path else set()
        self.last_names = self._load_corpus(last_names_path) if last_names_path else set()
        self.organizations = self._load_corpus(organizations_path) if organizations_path else set()
        
        # Initialize blacklists and patterns
        self._init_blacklists()
        self._init_patterns()
        
    def _load_corpus(self, path: Path) -> Set[str]:
        """Load a corpus file into a set"""
        if not path.exists():
            print(f"Warning: Corpus file not found: {path}")
            return set()
            
        with open(path, 'r', encoding='utf-8') as f:
            # Handle different corpus formats (JSON, text list, etc.)
            content = f.read()
            try:
                # Try JSON first
                data = json.loads(content)
                if isinstance(data, list):
                    return {str(item).lower() for item in data}
                elif isinstance(data, dict):
                    # Might have a 'names' or 'entities' key
                    for key in ['names', 'entities', 'items']:
                        if key in data:
                            return {str(item).lower() for item in data[key]}
            except json.JSONDecodeError:
                # Fall back to line-by-line text
                return {line.strip().lower() for line in content.splitlines() if line.strip()}
        
        return set()
    
    def _init_blacklists(self):
        """Initialize blacklists for ambiguous names"""
        
        # Company founder names that are often companies themselves
        self.COMPANY_FOUNDER_NAMES = {
            'ford', 'disney', 'dell', 'walton', 'mars', 'johnson',
            'kellogg', 'hilton', 'marriott', 'ferrari', 'porsche',
            'boeing', 'siemens', 'philips', 'bosch', 'krupp',
            'carnegie', 'morgan', 'goldman', 'sachs', 'wells',
            'fargo', 'stanley', 'lynch', 'schwab', 'buffett',
            'hewlett', 'packard', 'procter', 'gamble', 'colgate',
            'palmolive', 'kraft', 'heinz', 'nestle', 'unilever'
        }
        
        # Common words that are also names
        self.COMMON_WORD_NAMES = {
            'mark', 'bill', 'page', 'stone', 'rock', 'rose',
            'lily', 'ivy', 'hope', 'faith', 'grace', 'may',
            'june', 'august', 'lane', 'brook', 'river', 'sky',
            'star', 'moon', 'sun', 'rain', 'snow', 'storm',
            'field', 'forest', 'hill', 'valley', 'meadow'
        }
        
        # Tech companies often mistaken for people
        self.TECH_COMPANIES = {
            'apple', 'google', 'microsoft', 'amazon', 'tesla',
            'meta', 'facebook', 'twitter', 'netflix', 'uber',
            'airbnb', 'spotify', 'slack', 'zoom', 'adobe'
        }
        
    def _init_patterns(self):
        """Initialize regex patterns for person detection"""
        
        # Strong person indicators (high confidence)
        self.STRONG_PERSON_PATTERNS = [
            # Titles and honorifics
            r"(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Sir|Lady|Lord)\s+{NAME}",
            r"(President|CEO|CTO|CFO|COO|Chairman|Director)\s+{NAME}",
            
            # Biographical indicators
            r"{NAME}\s+(was born|died|passed away|graduated)",
            r"{NAME}\s+\((\d{{4}}-\d{{4}}|\d{{4}}-present|born \d{{4}})\)",
            
            # Clear person actions (past tense often more reliable)
            r"{NAME}\s+(said|stated|announced|founded|invented)",
            r"{NAME}\s+(wrote|published|discovered|created|developed)",
            
            # Roles with names
            r"{NAME},\s+(founder|co-founder|author|scientist|researcher)",
            r"{NAME},\s+\d+,",  # Name, age, ...
        ]
        
        # Medium confidence patterns
        self.MEDIUM_PERSON_PATTERNS = [
            r"by\s+{NAME}",
            r"with\s+{NAME}",
            r"{NAME}'s\s+(work|research|company|team|book)",
            r"(interviewed|met|contacted)\s+{NAME}",
        ]
        
        # Organization patterns (negative indicators)
        self.ORG_PATTERNS = [
            r"{NAME}\s+(Inc\.|LLC|Ltd\.|Corp|Corporation|Company|Group)",
            r"{NAME}\s+(Technologies|Systems|Software|Solutions|Services)",
            r"at\s+{NAME}(?!\s+(said|announced))",  # "at Google" vs "at Google, John said"
            r"from\s+{NAME}(?!\s+(said|announced))",
            r"{NAME}\s+(announced|released|launched)\s+(its|their)",
        ]
        
    def extract_persons(self, text: str, document_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Extract person entities from text with conservative validation.
        
        Args:
            text: Input text to process
            document_metadata: Optional metadata about the document
            
        Returns:
            List of validated person entities with confidence scores
        """
        candidates = self._identify_candidates(text)
        validated_persons = []
        
        for candidate in candidates:
            # Step 1: Apply blacklist filtering
            if self._is_blacklisted(candidate):
                continue
                
            # Step 2: Check if it's likely an organization
            if self._is_likely_organization(candidate):
                continue
                
            # Step 3: Apply simple validation rules
            evidence_score = self._calculate_evidence_score(candidate, text)
            
            # Step 4: Apply threshold (evidence score IS the final confidence)
            if evidence_score >= self.min_confidence and evidence_score > 0.0:
                validated_persons.append({
                    'text': candidate.text,
                    'type': 'PERSON',
                    'confidence': evidence_score,  # Use evidence score directly
                    'position': candidate.position,
                    'context': candidate.context,
                    'evidence': candidate.evidence
                })
                
        return validated_persons
    
    def _identify_candidates(self, text: str) -> List[PersonCandidate]:
        """Identify potential person name candidates in text"""
        candidates = []
        
        # Simple tokenization (you might want to use spaCy or NLTK for better results)
        # Look for capitalized word sequences
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b'
        
        for match in re.finditer(pattern, text):
            name = match.group()
            tokens = name.split()
            
            # Skip single letters or very short names
            if len(name) < 3:
                continue
                
            # Get context (±50 characters)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            candidate = PersonCandidate(
                tokens=tokens,
                text=name,
                context=context,
                position=match.start()
            )
            
            candidates.append(candidate)
            
        return candidates
    
    def _is_blacklisted(self, candidate: PersonCandidate) -> bool:
        """Check if candidate is in blacklist"""
        text_lower = candidate.text.lower()
        tokens_lower = [t.lower() for t in candidate.tokens]
        
        # Check company founder names
        if any(name in tokens_lower for name in self.COMPANY_FOUNDER_NAMES):
            # Only accept with very strong evidence (title)
            if not re.search(r"(Mr\.|Ms\.|Dr\.)\s+" + re.escape(candidate.text), 
                           candidate.context):
                candidate.evidence.append('blacklisted_founder_name')
                return True
                
        # Check tech companies
        if text_lower in self.TECH_COMPANIES:
            candidate.evidence.append('tech_company_name')
            return True
            
        # Check single common word names
        if len(candidate.tokens) == 1 and tokens_lower[0] in self.COMMON_WORD_NAMES:
            # Need very strong context for these
            if not self._has_strong_person_context(candidate):
                candidate.evidence.append('ambiguous_common_word')
                return True
                
        return False
    
    def _is_likely_organization(self, candidate: PersonCandidate) -> bool:
        """Check if candidate is likely an organization"""
        
        # Check against organization corpus
        if candidate.text.lower() in self.organizations:
            candidate.evidence.append('in_org_corpus')
            return True
            
        # Check organization patterns
        for pattern in self.ORG_PATTERNS:
            pattern_filled = pattern.replace("{NAME}", re.escape(candidate.text))
            if re.search(pattern_filled, candidate.context, re.IGNORECASE):
                candidate.evidence.append('matches_org_pattern')
                return True
                
        return False
    
    def _calculate_evidence_score(self, candidate: PersonCandidate, full_text: str) -> float:
        """Calculate evidence score using simple, clear rules"""
        
        # Parse name components
        tokens = candidate.tokens
        if not tokens:
            return 0.0
            
        first_token = tokens[0].lower()
        last_token = tokens[-1].lower() if len(tokens) > 1 else ""
        
        # Check for title in context (before the name)
        title_pattern = r"(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.|Professor|CEO|President|Director|Founder)\s+" + re.escape(candidate.text)
        has_title = bool(re.search(title_pattern, candidate.context, re.IGNORECASE))
        
        # Also check for role-based titles after the name
        role_pattern = re.escape(candidate.text) + r",?\s+(CEO|President|Director|Founder)"
        has_role_title = bool(re.search(role_pattern, candidate.context, re.IGNORECASE))
        
        has_title = has_title or has_role_title
        
        # Check against name corpora
        has_first = first_token in self.first_names
        has_last = last_token in self.last_names if last_token else False
        
        # Apply YOUR EXACT LOGIC:
        
        # IDEAL: Title + First Name + Last Name = High Confidence
        if has_title and has_first and has_last:
            candidate.evidence.extend(['title', 'first_name', 'last_name'])
            return 0.9
            
        # VERY GOOD: First Name + Last Name (both in corpus) = High Confidence
        if has_first and has_last and len(tokens) >= 2:
            candidate.evidence.extend(['first_name', 'last_name'])
            return 0.85
            
        # GOOD: Title + Last Name = Medium-High Confidence  
        if has_title and has_last:
            candidate.evidence.extend(['title', 'last_name'])
            return 0.8
            
        # MAYBE: Single First Name (if in corpus) = Lower Confidence
        if len(tokens) == 1 and has_first:
            candidate.evidence.append('single_first_name')
            return 0.6
            
        # REJECT: Everything else
        candidate.evidence.append('failed_name_validation')
        return 0.0
    
    def _calculate_pattern_score(self, candidate: PersonCandidate) -> float:
        """Calculate pattern matching score"""
        
        # Check strong patterns (high confidence)
        for pattern in self.STRONG_PERSON_PATTERNS:
            pattern_filled = pattern.replace("{NAME}", re.escape(candidate.text))
            if re.search(pattern_filled, candidate.context):
                candidate.evidence.append(f'strong_pattern: {pattern[:30]}')
                return 0.9
                
        # Check medium patterns
        for pattern in self.MEDIUM_PERSON_PATTERNS:
            pattern_filled = pattern.replace("{NAME}", re.escape(candidate.text))
            if re.search(pattern_filled, candidate.context):
                candidate.evidence.append(f'medium_pattern: {pattern[:30]}')
                return 0.6
                
        return 0.3  # No pattern match
    
    def _has_strong_person_context(self, candidate: PersonCandidate) -> bool:
        """Check for strong person context indicators"""
        strong_indicators = [
            r"(said|announced|stated)",
            r"(was born|died|graduated)",
            r"(Mr\.|Ms\.|Dr\.|Prof\.)",
            r"(CEO|founder|president)",
        ]
        
        for indicator in strong_indicators:
            if re.search(indicator, candidate.context):
                return True
        return False
    
    def _calculate_final_confidence(self, candidate: PersonCandidate, 
                                   evidence_score: float, 
                                   pattern_score: float) -> float:
        """Calculate final confidence score"""
        
        # Weighted combination
        base_confidence = (evidence_score * 0.6 + pattern_score * 0.4)
        
        # Boost for full names
        if len(candidate.tokens) >= 2:
            base_confidence *= 1.1
            
        # Penalty for single names
        if len(candidate.tokens) == 1:
            base_confidence *= 0.7
            
        # Penalty for ambiguous names
        if any(word in candidate.evidence for word in ['blacklisted', 'ambiguous']):
            base_confidence *= 0.5
            
        # Cap at 1.0
        return min(base_confidence, 1.0)
    
    def evaluate_accuracy(self, test_cases: List[Tuple[str, bool]]) -> Dict:
        """
        Evaluate accuracy on test cases.
        
        Args:
            test_cases: List of (text, expected_has_person) tuples
            
        Returns:
            Dictionary with accuracy metrics
        """
        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0
        
        for text, expected_has_person in test_cases:
            persons = self.extract_persons(text)
            found_person = len(persons) > 0
            
            if found_person and expected_has_person:
                true_positives += 1
            elif not found_person and not expected_has_person:
                true_negatives += 1
            elif found_person and not expected_has_person:
                false_positives += 1
                print(f"FALSE POSITIVE: {text}")
                print(f"  Found: {persons}")
            elif not found_person and expected_has_person:
                false_negatives += 1
                print(f"FALSE NEGATIVE: {text}")
                
        total = len(test_cases)
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': true_positives,
            'true_negatives': true_negatives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }


# Test suite
def run_tests():
    """Run test suite for person entity extraction"""
    
    # Initialize extractor (without corpus files for testing)
    extractor = PersonEntityExtractor(min_confidence=0.7)
    
    # Add some sample names for testing
    extractor.first_names = {'john', 'jane', 'michael', 'sarah', 'tim', 'walt', 'henry'}
    extractor.last_names = {'smith', 'doe', 'dell', 'cook', 'disney', 'ford', 'gates'}
    extractor.organizations = {'apple', 'google', 'microsoft', 'dell', 'ford motor company'}
    
    # Test cases (text, should_have_person)
    test_cases = [
        # Should REJECT (False)
        ("Ford announced new vehicles", False),
        ("Dell computers on sale", False),
        ("Disney+ streaming service", False),
        ("visited Apple headquarters", False),
        ("working at Goldman Sachs", False),
        ("Mark reached new heights", False),
        ("Rose in the garden", False),
        ("Microsoft released Windows 11", False),
        ("Tesla's stock price increased", False),
        
        # Should ACCEPT (True)
        ("Dr. Ford announced findings", True),
        ("Michael Dell, founder of Dell Technologies", True),
        ("Walt Disney founded the company", True),
        ("Tim Cook, CEO of Apple, said", True),
        ("Mr. Goldman testified yesterday", True),
        ("John Smith announced the merger", True),
        ("Sarah Doe, president of the company, stated", True),
        ("Professor Jane Smith published a paper", True),
        ("Henry Ford was born in 1863", True),
    ]
    
    print("="*60)
    print("PERSON ENTITY EXTRACTION TEST SUITE")
    print("="*60)
    
    # Run individual tests
    print("\nIndividual Test Results:")
    print("-"*40)
    
    for text, expected in test_cases:
        persons = extractor.extract_persons(text)
        found_person = len(persons) > 0
        status = "✓" if found_person == expected else "✗"
        
        print(f"{status} '{text}'")
        if found_person:
            for person in persons:
                print(f"   Found: {person['text']} (confidence: {person['confidence']:.2f})")
                print(f"   Evidence: {', '.join(person['evidence'])}")
        print()
    
    # Calculate metrics
    print("\n" + "="*60)
    print("ACCURACY METRICS")
    print("="*60)
    
    metrics = extractor.evaluate_accuracy(test_cases)
    
    print(f"Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall:    {metrics['recall']:.2%}")
    print(f"F1 Score:  {metrics['f1_score']:.2%}")
    print()
    print(f"True Positives:  {metrics['true_positives']}")
    print(f"True Negatives:  {metrics['true_negatives']}")
    print(f"False Positives: {metrics['false_positives']}")
    print(f"False Negatives: {metrics['false_negatives']}")


if __name__ == "__main__":
    run_tests()