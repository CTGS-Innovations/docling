#!/usr/bin/env python3
"""
GOAL: Clean single-word organizations corpus by removing noise words
REASON: False positives like "we move", "e fund", "real estate" detected as orgs
PROBLEM: Need to remove common words while preserving legitimate companies
"""

import sys
import os
from pathlib import Path

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def clean_organization_corpus():
    """Clean the single-word organizations corpus file"""
    
    # Words to remove - common words that cause false positives
    words_to_remove = {
        # Common nouns
        'able', 'actions', 'addiction', 'area', 'asia', 'bar', 'basic', 'beast', 
        'bench', 'blue', 'brown', 'cage', 'cake', 'care', 'catch', 'cheap', 
        'china', 'christ', 'cia', 'city', 'clear', 'coach', 'coffee', 'cook',
        'core', 'cos', 'crossing', 'culture', 'deal', 'denim', 'dig', 'dish',
        'divine', 'dod', 'doe', 'doj', 'dollar', 'dough', 'duke', 'east',
        'easy', 'eat', 'egg', 'element', 'face', 'fish', 'folk', 'ford',
        'fork', 'friend', 'fuel', 'gap', 'garage', 'george', 'giant', 'gold',
        'ground', 'here', 'hero', 'home', 'house', 'icon', 'industry', 'lab',
        'leaf', 'length', 'level', 'liberty', 'lime', 'loaded', 'london',
        'loop', 'lounge', 'lux', 'meat', 'mint', 'moo', 'orange', 'play',
        'pod', 'pop', 'root', 'sage', 'salt', 'see', 'seen', 'shell', 'shoe',
        'six', 'slate', 'soap', 'sol', 'soma', 'south', 'spot', 'steam',
        'stock', 'street', 'sweat', 'table', 'talk', 'target', 'temple',
        'terra', 'theory', 'time', 'toast', 'trust', 'twist', 'urban',
        'verde', 'victory', 'villa', 'vista', 'volt', 'wise', 'wonder',
        'you', 'zinc', 'zoom',
        
        # Government abbreviations (too generic)
        'sec', 'fbi', 'fcc', 'fda', 'irs', 'cdc', 'epa', 'nasa', 'nsa', 'nsf', 'tsa',
        
        # Common business words
        'move', 'way', 'fund', 'real', 'estate', 'business', 'services', 'development',
        'common', 'line', 'type', 'form', 'kind', 'part', 'side', 'terms', 'use',
        
        # Articles and conjunctions that somehow got in
        'the', 'and', 'or', 'but', 'we', 'they', 'who', 'what', 'when', 'where',
        'how', 'why', 'other', 'some', 'any', 'all', 'each', 'every', 'both',
        
        # Generic industry terms
        'tech', 'technology', 'software', 'hardware', 'data', 'information',
        'systems', 'solutions', 'group', 'company', 'corporation', 'inc',
        'llc', 'ltd', 'corp',
        
        # Colors (too generic unless clearly a company)
        'red', 'green', 'yellow', 'purple', 'pink', 'black', 'white', 'gray',
        'grey',
        
        # Numbers and letters
        'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
        'ten', 'zero', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k',
        'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'
    }
    
    # Known legitimate single-word companies to preserve
    legitimate_companies = {
        'google', 'apple', 'microsoft', 'amazon', 'facebook', 'tesla', 'netflix',
        'spotify', 'adobe', 'nvidia', 'qualcomm', 'intel', 'samsung', 'sony',
        'canon', 'nike', 'adidas', 'starbucks', 'mcdonalds', 'walmart', 'costco',
        'target', 'boeing', 'airbus', 'ford', 'ferrari', 'porsche', 'bmw',
        'mercedes', 'volkswagen', 'honda', 'toyota', 'nissan', 'hyundai',
        'siemens', 'philips', 'panasonic', 'xerox', 'kodak', 'polaroid',
        'pepsi', 'cocacola', 'budweiser', 'heineken', 'marlboro', 'kraft',
        'nestle', 'unilever', 'gillette', 'colgate', 'johnson', 'pfizer',
        'merck', 'novartis', 'roche', 'bayer', 'abbott', 'medtronic',
        'mastercard', 'visa', 'paypal', 'american', 'chase', 'citibank',
        'wells', 'goldman', 'morgan', 'berkshire', 'blackrock', 'vanguard'
    }
    
    corpus_file = Path('/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data/org/single_word_organizations.txt')
    
    if not corpus_file.exists():
        print(f"❌ Corpus file not found: {corpus_file}")
        return
    
    print(f"📂 Reading corpus file: {corpus_file}")
    
    # Read current corpus
    with open(corpus_file, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    original_count = len(original_lines)
    print(f"📊 Original corpus size: {original_count:,} organizations")
    
    # Process lines
    cleaned_lines = []
    removed_words = []
    preserved_companies = []
    
    for line in original_lines:
        word = line.strip().lower()
        
        # Skip empty lines
        if not word:
            continue
            
        # Check if it's a word to remove
        if word in words_to_remove:
            # But preserve if it's a known legitimate company
            if word in legitimate_companies:
                cleaned_lines.append(line)
                preserved_companies.append(word)
                print(f"✅ Preserved legitimate company: {word}")
            else:
                removed_words.append(word)
                print(f"🗑️  Removed: {word}")
        else:
            # Keep all other words
            cleaned_lines.append(line)
    
    cleaned_count = len(cleaned_lines)
    removed_count = len(removed_words)
    
    print(f"\n📊 CLEANING RESULTS:")
    print(f"   Original: {original_count:,} organizations")
    print(f"   Cleaned:  {cleaned_count:,} organizations")
    print(f"   Removed:  {removed_count:,} words ({removed_count/original_count*100:.1f}%)")
    print(f"   Preserved: {len(preserved_companies)} legitimate companies")
    
    # Create backup
    backup_file = corpus_file.with_suffix('.txt.backup')
    corpus_file.rename(backup_file)
    print(f"💾 Created backup: {backup_file}")
    
    # Write cleaned corpus
    with open(corpus_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ Cleaned corpus written to: {corpus_file}")
    
    # Show some examples of removed words
    print(f"\n🗑️  Examples of removed words:")
    for word in sorted(removed_words)[:20]:
        print(f"   - {word}")
    if len(removed_words) > 20:
        print(f"   ... and {len(removed_words) - 20} more")
    
    print(f"\n✅ Corpus cleaning complete!")
    return cleaned_count, removed_count

if __name__ == "__main__":
    clean_organization_corpus()