#!/usr/bin/env python3
"""
GOAL: Test if markdown bold formatting (**text**) is breaking entity detection
REASON: Entities like **California** might not be detected due to ** formatting
PROBLEM: Aho-Corasick may not match text with markdown formatting
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def test_markdown_formatting():
    """Test detection with and without markdown formatting"""
    
    print("🔍 TESTING MARKDOWN FORMATTING IMPACT")
    print("=" * 50)
    
    # Load corpus
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    # Test cases
    test_cases = [
        ("Plain text", "California, Texas, Florida, Germany, Japan, Canada"),
        ("With bold", "**California**, **Texas**, **Florida**, **Germany**, **Japan**, **Canada**"),
        ("Mixed", "California, **Texas**, Florida, **Germany**, Japan, **Canada**"),
        ("Real source", "International presence in: **California**, **Texas**, **Florida**, **United States**, **Canada**, **United Kingdom**, **Germany**, **Japan**, **Australia**, and **Brazil**.")
    ]
    
    target_entities = ['California', 'Texas', 'Florida', 'Germany', 'Japan', 'Canada', 'United States', 'United Kingdom', 'Australia', 'Brazil']
    
    for test_name, test_text in test_cases:
        print(f"\n📝 {test_name}:")
        print(f"   Text: {test_text}")
        print(f"   Detection:")
        
        detected = []
        for end_pos, (entity_type, canonical) in gpe_automaton.iter(test_text.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = test_text[start_pos:end_pos + 1]
            # Only show meaningful entities (not fragments like 'ed', 'ic')
            if len(canonical) > 2:
                detected.append(original_text)
                print(f"     ✅ Found: '{original_text}' (canonical: '{canonical}')")
        
        # Check what we missed
        missed = []
        for entity in target_entities:
            found = any(entity.lower() in d.lower() for d in detected)
            if not found:
                missed.append(entity)
        
        if missed:
            print(f"     ❌ MISSED: {', '.join(missed)}")
        else:
            print(f"     🎯 ALL FOUND!")
    
    # Specific test for markdown interference
    print(f"\n🔬 SPECIFIC MARKDOWN INTERFERENCE TEST:")
    markdown_pairs = [
        ("california", "**california**"),
        ("texas", "**texas**"),
        ("florida", "**florida**"),
        ("germany", "**germany**")
    ]
    
    for plain, bold in markdown_pairs:
        plain_matches = list(gpe_automaton.iter(plain))
        bold_matches = list(gpe_automaton.iter(bold))
        
        print(f"   '{plain}': {len(plain_matches)} matches")
        print(f"   '{bold}': {len(bold_matches)} matches")
        
        if len(plain_matches) > len(bold_matches):
            print(f"     🚨 MARKDOWN BREAKS DETECTION for {plain}")

if __name__ == "__main__":
    test_markdown_formatting()