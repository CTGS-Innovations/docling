#!/usr/bin/env python3
"""
GOAL: Debug why obvious names like Dr. Michael O'Brien, Xi Zhang are not being detected
REASON: Several clear person names are missing from extraction results
PROBLEM: Need to check corpus coverage and confidence thresholds
"""

import sys
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

from utils.person_entity_extractor import PersonEntityExtractor
from pathlib import Path

def debug_missing_names():
    """Debug why obvious names are missing"""
    
    print("🔍 DEBUGGING MISSING PERSON NAMES")
    print("=" * 50)
    
    # Initialize PersonEntityExtractor with same config as pipeline
    corpus_dir = Path("knowledge/corpus/foundation_data")
    person_extractor = PersonEntityExtractor(
        first_names_path=corpus_dir / "first_names_2025_09_18.txt",
        last_names_path=corpus_dir / "last_names_2025_09_18.txt", 
        organizations_path=corpus_dir / "organizations_2025_09_18.txt",
        min_confidence=0.5  # Use new lower threshold
    )
    
    # Test the specific missing names
    missing_cases = [
        "Dr. Michael O'Brien is the Chief Medical Officer.",
        "Xi Zhang is a Software Engineer.",
        "José García-López is an Environmental Consultant.", 
        "François Dubois is the International Liaison.",
        "Ahmed Al-Rashid is a Security Specialist.",
        "Dr. Li presented breakthrough research.",
        "Madonna is the celebrity spokesperson.",
        "João Silva Santos is the Brazilian Operations Manager."
    ]
    
    print(f"🔧 Testing missing names with current settings:")
    print(f"   Min confidence: 0.5")
    
    for i, test_case in enumerate(missing_cases, 1):
        print(f"\n   Test {i}: {test_case}")
        
        try:
            persons = person_extractor.extract_persons(test_case)
            if persons:
                for person in persons:
                    name = person.get('text', person.get('name', ''))
                    confidence = person.get('confidence', 0)
                    print(f"     ✅ Found: '{name}' (confidence: {confidence:.2f})")
            else:
                print(f"     ❌ No persons detected")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Test with lower confidence threshold
    print(f"\n🔧 Testing with lower confidence threshold (0.3):")
    
    person_extractor_low = PersonEntityExtractor(
        first_names_path=corpus_dir / "first_names_2025_09_18.txt",
        last_names_path=corpus_dir / "last_names_2025_09_18.txt", 
        organizations_path=corpus_dir / "organizations_2025_09_18.txt",
        min_confidence=0.3  # Lower threshold
    )
    
    for i, test_case in enumerate(missing_cases, 1):
        print(f"\n   Test {i}: {test_case}")
        
        try:
            persons = person_extractor_low.extract_persons(test_case)
            if persons:
                for person in persons:
                    name = person.get('text', person.get('name', ''))
                    confidence = person.get('confidence', 0)
                    print(f"     ✅ Found: '{name}' (confidence: {confidence:.2f})")
            else:
                print(f"     ❌ Still no persons detected")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Check corpus coverage for specific names
    print(f"\n🔧 Checking corpus coverage:")
    
    # Check if first names exist in corpus
    first_names_to_check = ['Michael', 'Xi', 'José', 'François', 'Ahmed', 'João', 'Madonna']
    
    try:
        with open(corpus_dir / "first_names_2025_09_18.txt", 'r', encoding='utf-8') as f:
            first_names_corpus = set(line.strip().lower() for line in f if line.strip())
        
        print(f"   First names corpus size: {len(first_names_corpus)}")
        
        for name in first_names_to_check:
            found = name.lower() in first_names_corpus
            status = "✅" if found else "❌"
            print(f"     {status} '{name}' in first names corpus")
            
    except FileNotFoundError:
        print(f"   ❌ First names corpus file not found")
    
    # Check last names
    last_names_to_check = ['O\'Brien', 'Zhang', 'García-López', 'Dubois', 'Al-Rashid', 'Li', 'Santos']
    
    try:
        with open(corpus_dir / "last_names_2025_09_18.txt", 'r', encoding='utf-8') as f:
            last_names_corpus = set(line.strip().lower() for line in f if line.strip())
        
        print(f"\n   Last names corpus size: {len(last_names_corpus)}")
        
        for name in last_names_to_check:
            # Check variations since corpus might have different formats
            variations = [name.lower(), name.lower().replace("'", ""), name.lower().replace("-", " ")]
            found = any(var in last_names_corpus for var in variations)
            status = "✅" if found else "❌"
            print(f"     {status} '{name}' (or variations) in last names corpus")
            
    except FileNotFoundError:
        print(f"   ❌ Last names corpus file not found")

if __name__ == "__main__":
    debug_missing_names()