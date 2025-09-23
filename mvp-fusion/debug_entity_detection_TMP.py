#!/usr/bin/env python3
"""
GOAL: Debug why major states/countries aren't being detected
REASON: California, Texas, Florida, Germany, Japan, Canada missing from entity extraction
PROBLEM: Need to test if Aho-Corasick automaton has the patterns and why they're not matching
"""

import sys
import os
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader
from pathlib import Path

def debug_entity_detection():
    """Test entity detection for missing states/countries"""
    
    print("🔍 DEBUGGING ENTITY DETECTION")
    print("=" * 40)
    
    # Load Core-8 corpus
    loader = Core8CorpusLoader(verbose=True)
    core8_automatons = loader.automatons
    
    print(f"📊 Loaded automatons:")
    for entity_type, automaton in core8_automatons.items():
        if hasattr(automaton, '__len__'):
            print(f"   {entity_type}: {len(automaton)} patterns")
    
    # Test specific missing entities
    test_entities = [
        "California", "Texas", "Florida", 
        "Germany", "Japan", "Canada",
        "Chicago", "Houston", "Phoenix", "Dallas"
    ]
    
    test_text = "Operations in California, Texas, and Florida. International presence in Germany, Japan, and Canada. Major cities include Chicago, Houston, Phoenix, and Dallas."
    
    print(f"\n📝 Test text: {test_text}")
    print(f"\n🔍 Testing entity detection:")
    
    # Test GPE detection
    if 'GPE' in core8_automatons:
        gpe_automaton = core8_automatons['GPE']
        print(f"\n🌍 GPE Detection:")
        found_gpe = []
        
        for end_pos, (entity_type, canonical) in gpe_automaton.iter(test_text.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = test_text[start_pos:end_pos + 1]
            found_gpe.append(original_text)
            print(f"   Found: '{original_text}' (canonical: '{canonical}')")
        
        print(f"   Total GPE found: {len(found_gpe)}")
        
        # Check what we missed
        missed_gpe = []
        for entity in ["California", "Texas", "Florida", "Germany", "Japan", "Canada"]:
            if entity not in [f.title() for f in found_gpe]:
                missed_gpe.append(entity)
        
        if missed_gpe:
            print(f"   ❌ MISSED GPE: {', '.join(missed_gpe)}")
    
    # Test LOC detection  
    if 'LOC' in core8_automatons:
        loc_automaton = core8_automatons['LOC']
        print(f"\n📍 LOC Detection:")
        found_loc = []
        
        for end_pos, (entity_type, canonical) in loc_automaton.iter(test_text.lower()):
            start_pos = end_pos - len(canonical) + 1
            original_text = test_text[start_pos:end_pos + 1]
            found_loc.append(original_text)
            print(f"   Found: '{original_text}' (canonical: '{canonical}')")
        
        print(f"   Total LOC found: {len(found_loc)}")
        
        # Check what we missed
        missed_loc = []
        for entity in ["Chicago", "Houston", "Phoenix", "Dallas"]:
            if entity not in [f.title() for f in found_loc]:
                missed_loc.append(entity)
        
        if missed_loc:
            print(f"   ❌ MISSED LOC: {', '.join(missed_loc)}")
    
    # Test case sensitivity
    print(f"\n🔤 Testing case sensitivity:")
    test_cases = ["california", "California", "CALIFORNIA"]
    
    if 'GPE' in core8_automatons:
        gpe_automaton = core8_automatons['GPE']
        for test_case in test_cases:
            matches = list(gpe_automaton.iter(test_case))
            print(f"   '{test_case}': {len(matches)} matches")
            for end_pos, (entity_type, canonical) in matches:
                print(f"     -> '{canonical}'")

if __name__ == "__main__":
    debug_entity_detection()