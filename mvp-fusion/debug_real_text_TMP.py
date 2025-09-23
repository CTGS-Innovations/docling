#!/usr/bin/env python3
"""
GOAL: Debug detection on the exact text from the source document
REASON: Dallas, Houston, Phoenix, Chicago not detected in real processing
PROBLEM: Need to test exact source text vs processed text
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.core8_corpus_loader import Core8CorpusLoader

def debug_real_text():
    """Test detection on exact source text"""
    
    print("🔍 DEBUGGING REAL DOCUMENT TEXT")
    print("=" * 45)
    
    # Load corpus
    loader = Core8CorpusLoader(verbose=False)
    gpe_automaton = loader.automatons['GPE']
    
    # Exact text from source document
    source_text = "Operations expanded to: **New York City**, **Los Angeles**, **Chicago**, **Houston**, **Phoenix**, **Philadelphia**, **San Antonio**, **San Diego**, **Dallas**, and **San Jose**."
    
    print(f"📝 Source text: {source_text}")
    print(f"📝 Lowercase text: {source_text.lower()}")
    print(f"\n🔍 GPE detection on source text:")
    
    detected_cities = []
    missing_cities = []
    target_cities = ['Chicago', 'Houston', 'Phoenix', 'Dallas']
    
    for end_pos, (entity_type, canonical) in gpe_automaton.iter(source_text.lower()):
        start_pos = end_pos - len(canonical) + 1
        original_text = source_text[start_pos:end_pos + 1]
        detected_cities.append(original_text)
        print(f"   Detected: '{original_text}' (canonical: '{canonical}')")
    
    print(f"\n📊 Target city detection:")
    for city in target_cities:
        found = any(city.lower() in d.lower() for d in detected_cities)
        status = "✅" if found else "❌"
        print(f"   {status} {city}")
        if not found:
            missing_cities.append(city)
    
    # Test individual cities
    print(f"\n🔤 Individual city tests:")
    for city in target_cities:
        matches = list(gpe_automaton.iter(city.lower()))
        print(f"   '{city}': {len(matches)} matches")
        for end_pos, (entity_type, canonical) in matches:
            print(f"     -> '{canonical}'")
    
    # Check if cities are in the automaton at all
    print(f"\n🗂️  Direct automaton check:")
    for city in target_cities:
        try:
            # Check if city is in the automaton
            found = gpe_automaton.exists(city.lower())
            print(f"   '{city.lower()}' exists in automaton: {found}")
        except:
            # Alternative check - try to find it
            matches = list(gpe_automaton.iter(city.lower()))
            print(f"   '{city.lower()}' matches: {len(matches)}")

if __name__ == "__main__":
    debug_real_text()