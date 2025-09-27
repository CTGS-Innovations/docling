#!/usr/bin/env python3
"""
GOAL: Clean multi-word organizations corpus by removing generic terms and phrases
REASON: False positives like "real estate", "privacy policy", "we move" being detected
PROBLEM: Need to remove generic terms while preserving legitimate multi-word companies
"""

import sys
import os
from pathlib import Path

def clean_multiword_org_corpus():
    """Clean the multi-word organizations corpus file"""
    
    # Generic terms/phrases to remove - these are not specific organizations
    terms_to_remove = {
        # Generic industry terms
        'real estate',
        'privacy policy', 
        'terms of use',
        
        # Common phrases that aren't organizations
        'the way',
        'we move',
        'on the way',
        'all the way',
        
        # Generic legal/business terms
        'environmental defense fund',  # Too generic without qualifier
        'national health insurance fund',  # Too generic
        'world wildlife fund',  # Too generic without qualifier
        'world wide fund for nature',  # Too generic
        
        # Other generic terms that might cause false positives
        'real estate connection',
        'real estate direct', 
        'real estate inspections',
        'chicken on the way',  # Random phrase
        'on top of the world real estate of pinellas',  # Too wordy/generic
    }
    
    corpus_file = Path('/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data/org/multi_word_organizations.txt')
    
    if not corpus_file.exists():
        print(f"❌ Corpus file not found: {corpus_file}")
        return
    
    print(f"📂 Reading multi-word organizations corpus: {corpus_file}")
    
    # Read current corpus
    with open(corpus_file, 'r', encoding='utf-8') as f:
        original_lines = f.readlines()
    
    original_count = len(original_lines)
    print(f"📊 Original corpus size: {original_count:,} organizations")
    
    # Process lines
    cleaned_lines = []
    removed_terms = []
    
    for line in original_lines:
        org_name = line.strip().lower()
        
        # Skip empty lines
        if not org_name:
            continue
            
        # Check if it's a term to remove
        if org_name in terms_to_remove:
            removed_terms.append(org_name)
            print(f"🗑️  Removed: {org_name}")
        else:
            # Keep all other organizations
            cleaned_lines.append(line)
    
    cleaned_count = len(cleaned_lines)
    removed_count = len(removed_terms)
    
    print(f"\n📊 CLEANING RESULTS:")
    print(f"   Original: {original_count:,} organizations")
    print(f"   Cleaned:  {cleaned_count:,} organizations")
    print(f"   Removed:  {removed_count:,} terms ({removed_count/original_count*100:.1f}%)")
    
    # Create backup
    backup_file = corpus_file.with_suffix('.txt.backup')
    if not backup_file.exists():  # Don't overwrite existing backup
        with open(corpus_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        print(f"💾 Created backup: {backup_file}")
    
    # Write cleaned corpus
    with open(corpus_file, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)
    
    print(f"✅ Cleaned corpus written to: {corpus_file}")
    
    # Show removed terms
    print(f"\n🗑️  Removed generic terms:")
    for term in sorted(removed_terms):
        print(f"   - {term}")
    
    print(f"\n✅ Multi-word corpus cleaning complete!")
    return cleaned_count, removed_count

if __name__ == "__main__":
    clean_multiword_org_corpus()