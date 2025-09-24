#!/usr/bin/env python3
"""
Single-Word Organization Validation Algorithm
============================================

GOAL: Create performance regex patterns to validate single-word organizations
APPROACH: Expand valid matches rather than just filter bad ones
TARGET: 70%+ accuracy with high performance

Algorithm Logic:
1. Short words (<4 chars) need stronger evidence
2. Capitalization context matters
3. Numeric/alphanumeric patterns indicate organizations
4. Corporate context clues help validation
"""

import re
from typing import Dict, List, Tuple

class SingleWordOrgValidator:
    """High-performance single-word organization validator using regex patterns."""
    
    def __init__(self):
        self.validation_patterns = self._compile_validation_patterns()
        self.common_words_blacklist = self._load_common_words()
    
    def _compile_validation_patterns(self) -> Dict[str, re.Pattern]:
        """Compile high-performance regex patterns for organization validation."""
        
        patterns = {
            # Pattern 1: Numeric-prefixed organizations (3M, 1stBank, 7Eleven)
            'numeric_prefix': re.compile(r'\b\d+[A-Za-z][A-Za-z0-9]*\b'),
            
            # Pattern 2: CamelCase organizations (PayPal, iPhone, eBay)
            'camel_case': re.compile(r'\b[a-z][A-Z][A-Za-z0-9]*\b|\b[A-Z][a-z]+[A-Z][A-Za-z0-9]*\b'),
            
            # Pattern 3: All-caps acronyms (IBM, NASA, FBI) - 2+ chars
            'acronym': re.compile(r'\b[A-Z]{2,6}\b'),
            
            # Pattern 4: Mixed alphanumeric (B2B, H&R, AT&T-style)
            'mixed_alphanum': re.compile(r'\b[A-Za-z]+\d+[A-Za-z]*\b|\b[A-Za-z]*\d+[A-Za-z]+\b'),
            
            # Pattern 5: Corporate suffixes nearby (within 10 chars)
            'corporate_suffix_context': re.compile(r'\b[A-Za-z]+\s*(?:Inc|LLC|Ltd|Corp|Co|SA|GmbH|PLC|AG)\b', re.IGNORECASE),
            
            # Pattern 6: Capitalized in title/sentence context
            'title_case_context': re.compile(r'(?:^|[.!?]\s+|:\s*)[A-Z][a-z]+'),
            
            # Pattern 7: Brand/domain indicators (@, .com, www)
            'brand_indicators': re.compile(r'\b[A-Za-z]+(?:\.com|\.org|\.net)\b|\b@[A-Za-z]+\b|\bwww\.[A-Za-z]+\b'),
        }
        
        return patterns
    
    def _load_common_words(self) -> set:
        """Load blacklist of common English words that should never be organizations."""
        return {
            # Ultra-common words (definite blacklist)
            'here', 'there', 'where', 'when', 'what', 'how', 'why', 'who',
            'this', 'that', 'these', 'those', 'they', 'them', 'their',
            'with', 'from', 'into', 'onto', 'upon', 'over', 'under',
            'very', 'much', 'more', 'most', 'some', 'many', 'few',
            'good', 'best', 'bad', 'new', 'old', 'big', 'small',
            'first', 'last', 'next', 'each', 'every', 'all', 'any',
            'make', 'take', 'give', 'get', 'put', 'see', 'know',
            'think', 'feel', 'look', 'seem', 'come', 'go', 'want',
            
            # Short ambiguous words
            'as', 'at', 'be', 'by', 'do', 'go', 'he', 'if', 'in', 'is', 'it',
            'me', 'my', 'no', 'of', 'on', 'or', 'so', 'to', 'up', 'we',
            
            # Common business words that aren't organizations themselves
            'inc', 'llc', 'ltd', 'corp', 'co', 'company', 'business',
            'service', 'services', 'group', 'team', 'office', 'center'
        }
    
    def validate_single_word_org(self, word: str, context: str = "", position: int = 0) -> Tuple[bool, str, float]:
        """
        Validate if a single word could be a legitimate organization.
        
        Args:
            word: The word to validate
            context: Surrounding text context (±50 chars)
            position: Position of word in context
            
        Returns:
            (is_valid, reason, confidence_score)
        """
        word_lower = word.lower()
        word_len = len(word)
        
        # Immediate blacklist check
        if word_lower in self.common_words_blacklist:
            return False, "common_word_blacklist", 0.0
        
        # Short word validation (< 4 characters)
        if word_len < 4:
            return self._validate_short_word(word, context, position)
        
        # Medium word validation (4-6 characters)
        elif word_len <= 6:
            return self._validate_medium_word(word, context, position)
        
        # Longer words (7+ characters) - more likely to be organizations
        else:
            return self._validate_long_word(word, context, position)
    
    def _validate_short_word(self, word: str, context: str, position: int) -> Tuple[bool, str, float]:
        """Validate short words (<4 chars) with strict criteria."""
        
        # Pattern 1: Numeric prefix (3M, 7Up)
        if self.validation_patterns['numeric_prefix'].match(word):
            return True, "numeric_prefix_pattern", 0.9
        
        # Pattern 2: All caps acronym (IBM, FBI)
        if self.validation_patterns['acronym'].match(word):
            return True, "acronym_pattern", 0.85
        
        # Pattern 3: Mixed alphanumeric (B2B, H&R)
        if self.validation_patterns['mixed_alphanum'].match(word):
            return True, "mixed_alphanum_pattern", 0.8
        
        # Pattern 4: Corporate context nearby
        context_window = context[max(0, position-20):position+len(word)+20]
        if self.validation_patterns['corporate_suffix_context'].search(context_window):
            return True, "corporate_context", 0.75
        
        # Pattern 5: Must be capitalized if standalone
        if word.isupper() or (word[0].isupper() and len(word) >= 2):
            # Check if it's in a title context
            if self.validation_patterns['title_case_context'].search(context[max(0, position-10):position+len(word)+10]):
                return True, "title_case_capitalized", 0.7
        
        # Short words without strong evidence are rejected
        return False, "insufficient_evidence_short_word", 0.2
    
    def _validate_medium_word(self, word: str, context: str, position: int) -> Tuple[bool, str, float]:
        """Validate medium words (4-6 chars) with moderate criteria."""
        
        # All short word patterns apply
        is_valid, reason, confidence = self._validate_short_word(word, context, position)
        if is_valid:
            return is_valid, reason, confidence
        
        # Pattern 6: CamelCase (eBay, PayPal)
        if self.validation_patterns['camel_case'].match(word):
            return True, "camel_case_pattern", 0.8
        
        # Pattern 7: Brand indicators
        context_window = context[max(0, position-15):position+len(word)+15]
        if self.validation_patterns['brand_indicators'].search(context_window):
            return True, "brand_indicator_context", 0.75
        
        # Pattern 8: Capitalized in business context
        if word[0].isupper() and any(biz_word in context.lower() for biz_word in 
                                     ['company', 'corporation', 'business', 'firm', 'agency']):
            return True, "business_context_capitalized", 0.7
        
        # Medium words need less evidence than short words
        if word[0].isupper():
            return True, "capitalized_medium_word", 0.6
        
        return False, "insufficient_evidence_medium_word", 0.3
    
    def _validate_long_word(self, word: str, context: str, position: int) -> Tuple[bool, str, float]:
        """Validate long words (7+ chars) with lenient criteria."""
        
        # Most patterns from shorter words apply
        is_valid, reason, confidence = self._validate_medium_word(word, context, position)
        if is_valid:
            return is_valid, reason, min(confidence + 0.1, 0.95)  # Boost confidence slightly
        
        # Pattern 9: Long capitalized words are likely organizations
        if word[0].isupper():
            return True, "capitalized_long_word", 0.75
        
        # Pattern 10: Even lowercase long words might be brands (google, amazon)
        if word.islower() and len(word) >= 8:
            return True, "long_lowercase_brand", 0.6
        
        return False, "insufficient_evidence_long_word", 0.4

def test_validation_algorithm():
    """Test the validation algorithm with sample cases."""
    validator = SingleWordOrgValidator()
    
    # Test cases: (word, context, expected_result)
    test_cases = [
        ("here", "We are here today", False),
        ("HERE", "HERE Inc is a company", True),  # Corporate context
        ("3M", "3M company makes products", True),  # Numeric prefix
        ("IBM", "IBM announced today", True),  # Acronym
        ("PayPal", "PayPal payments", True),  # CamelCase
        ("Google", "Google search engine", True),  # Capitalized long word
        ("apple", "eat an apple", False),  # Common word
        ("Apple", "Apple Inc makes computers", True),  # Corporate context
        ("B2B", "B2B solutions", True),  # Mixed alphanumeric
        ("the", "the company", False),  # Blacklisted
        ("as", "as we know", False),  # Blacklisted short
        ("AT", "AT the meeting", False),  # Short without evidence
        ("ATT", "ATT wireless service", True),  # 3-char acronym
    ]
    
    print("🧪 TESTING SINGLE-WORD ORGANIZATION VALIDATION")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for word, context, expected in test_cases:
        is_valid, reason, confidence = validator.validate_single_word_org(word, context, 10)
        is_correct = is_valid == expected
        correct += is_correct
        
        status = "✅" if is_correct else "❌"
        print(f"{status} {word:10} | {is_valid:5} | {confidence:.2f} | {reason:25} | '{context[:30]}'")
    
    accuracy = (correct / total) * 100
    print("=" * 60)
    print(f"🎯 ACCURACY: {accuracy:.1f}% ({correct}/{total})")
    print(f"🚀 TARGET: 70%+ ({'PASSED' if accuracy >= 70 else 'NEEDS IMPROVEMENT'})")

if __name__ == "__main__":
    test_validation_algorithm()