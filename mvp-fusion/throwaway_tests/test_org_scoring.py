#!/usr/bin/env python3
"""
Test the confidence scoring cascade for organization detection
"""

def calculate_org_confidence(text, context=""):
    """Simulate the scoring logic from _validate_organization_entity"""
    
    confidence_score = 0.0
    word_count = len(text.split())
    word_length = len(text.strip())
    
    # BASE SCORES
    if word_count > 1:
        confidence_score = 0.9
    elif text[0].isupper() if text else False:
        confidence_score = 0.3
    else:
        confidence_score = 0.1
    
    # SHORT WORD PENALTY
    if word_count == 1 and word_length <= 4:
        confidence_score *= 0.5
    
    # EVIDENCE MODIFIERS (simplified for testing)
    text_lower = text.lower()
    
    # Check for numbers
    if any(c.isdigit() for c in text):
        confidence_score += 0.4
    
    # Check for legal suffixes
    legal_suffixes = ['inc', 'llc', 'ltd', 'corp', 'co', 'gmbh', 'plc']
    for suffix in legal_suffixes:
        if suffix in text_lower:
            confidence_score += 0.5
            break
    
    # Check for all caps (3+ letters)
    if word_count == 1 and len(text) >= 3 and text.isupper():
        confidence_score += 0.2
    
    # COMMON WORDS CHECK
    common_words = {'here', 'there', 'place', 'spa', 'front', 'back', 'made', 'built'}
    if text_lower in common_words:
        # Need very strong evidence (0.8 threshold)
        return confidence_score, confidence_score >= 0.8
    
    # THRESHOLDS
    if word_count > 1:
        threshold = 0.5
    elif word_length <= 4:
        threshold = 0.6
    else:
        threshold = 0.5
    
    return confidence_score, confidence_score >= threshold


# TEST CASES
test_cases = [
    # Format: (text, expected_accept, description)
    
    # Multi-word organizations (should all pass)
    ("Apple Inc", True, "Multi-word with suffix"),
    ("Goldman Sachs", True, "Multi-word company name"),
    ("3M Company", True, "Multi-word with number"),
    
    # Single words with numbers (should pass)
    ("3M", True, "Number prefix"),
    ("SPA2000", True, "Letters with numbers"),
    ("G4S", True, "Embedded number"),
    ("33", False, "Just a number (no context)"),
    
    # Short words without evidence (should fail)
    ("spa", False, "Common word, lowercase"),
    ("here", False, "Common word, lowercase"),
    ("Spa", False, "Common word, capitalized only"),
    ("Here", False, "Common word, capitalized only"),
    
    # Short words with evidence (should pass)
    ("SPA", True, "All caps, 3 letters"),
    ("IBM", True, "All caps acronym"),
    ("NASA", True, "All caps, 4 letters"),
    
    # Legal suffixes
    ("SpaCo", True, "With Co suffix"),
    ("HereInc", True, "Common word + Inc suffix"),
    
    # Edge cases
    ("A", False, "Single letter"),
    ("AB", False, "Two letters, no evidence"),
    ("ABC", True, "Three letters, all caps"),
    ("abc", False, "Three letters, lowercase"),
]

print("=" * 70)
print("ORGANIZATION CONFIDENCE SCORING TEST")
print("=" * 70)

passed = 0
failed = 0

for text, expected, description in test_cases:
    score, accepted = calculate_org_confidence(text)
    status = "✓" if accepted == expected else "✗"
    
    if accepted == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{status} {text:15} Score: {score:.2f} Accept: {accepted:5} Expected: {expected:5} | {description}")

print("=" * 70)
print(f"Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print(f"Success rate: {(passed/len(test_cases))*100:.1f}%")

# Additional scoring breakdown examples
print("\n" + "=" * 70)
print("DETAILED SCORING EXAMPLES")
print("=" * 70)

examples = ["spa", "Spa", "SPA", "SPA2000", "Spa Inc", "here", "Here", "33here"]
for ex in examples:
    score, accepted = calculate_org_confidence(ex)
    print(f"'{ex}': Score={score:.2f}, Accept={accepted}")