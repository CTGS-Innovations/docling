#!/usr/bin/env python3
"""
GOAL: Comprehensive cleaning of ALL organization corpus files
REASON: Found additional noise in organizations_2025_09_18.txt and other files
PROBLEM: Need to clean all org files systematically to eliminate false positives
"""

import sys
import os
from pathlib import Path
import re

def comprehensive_corpus_cleaning():
    """Clean all organization corpus files comprehensively"""
    
    # All noise terms to remove across all organization files
    noise_terms = {
        # Generic common words
        'able', 'actions', 'addiction', 'area', 'bar', 'basic', 'beast', 
        'bench', 'blue', 'brown', 'cage', 'cake', 'care', 'catch', 'cheap', 
        'china', 'christ', 'city', 'clear', 'coach', 'coffee', 'cook',
        'core', 'cos', 'crossing', 'culture', 'deal', 'denim', 'dig', 'dish',
        'divine', 'dollar', 'dough', 'duke', 'east', 'easy', 'eat', 'egg', 
        'element', 'face', 'fish', 'folk', 'fork', 'friend', 'fuel', 'gap', 
        'garage', 'george', 'giant', 'gold', 'ground', 'here', 'hero', 'home', 
        'house', 'icon', 'industry', 'lab', 'leaf', 'length', 'level', 'liberty', 
        'lime', 'loaded', 'london', 'loop', 'lounge', 'lux', 'meat', 'mint', 
        'moo', 'orange', 'play', 'pod', 'pop', 'root', 'sage', 'salt', 'see', 
        'seen', 'shell', 'shoe', 'six', 'slate', 'soap', 'sol', 'soma', 'south', 
        'spot', 'steam', 'stock', 'street', 'sweat', 'table', 'talk', 'temple',
        'terra', 'theory', 'time', 'toast', 'trust', 'twist', 'urban',
        'verde', 'victory', 'villa', 'vista', 'volt', 'wise', 'wonder',
        'you', 'zinc', 'zoom',
        
        # Government abbreviations (too generic)
        'sec', 'fbi', 'fcc', 'fda', 'irs', 'cdc', 'epa', 'nasa', 'nsa', 'nsf', 'tsa',
        
        # Business/common terms
        'move', 'way', 'fund', 'real', 'estate', 'business', 'services', 'development',
        'common', 'line', 'type', 'form', 'kind', 'part', 'side', 'terms', 'use',
        
        # Articles/pronouns that somehow got in
        'the', 'and', 'or', 'but', 'we', 'they', 'who', 'what', 'when', 'where',
        'how', 'why', 'other', 'some', 'any', 'all', 'each', 'every', 'both',
        
        # Multi-word generic terms
        'real estate', 'privacy policy', 'terms of use', 'the way', 'we move',
        'the pan', 'the way', 'on the way', 'all the way',
        
        # Obvious non-organizations
        'chicken on the way', 'privacy policy', 'environmental defense fund',
        'national health insurance fund', 'world wide fund for nature',
        'world wildlife fund',
    }
    
    # Known legitimate companies to preserve (case-insensitive)
    legitimate_companies = {
        'google', 'apple', 'microsoft', 'amazon', 'facebook', 'tesla', 'netflix',
        'spotify', 'adobe', 'nvidia', 'qualcomm', 'intel', 'samsung', 'sony',
        'target', 'ford', 'tiger global', 'e fund', 'gap', 'shell'
    }
    
    # Find all organization corpus files
    corpus_dir = Path('/home/corey/projects/docling/mvp-fusion/knowledge/corpus/foundation_data')
    org_files = [
        corpus_dir / 'organizations_2025_09_18.txt',
        corpus_dir / 'org' / 'single_word_organizations.txt',
        corpus_dir / 'org' / 'multi_word_organizations.txt',
        corpus_dir / 'org' / 'investors_2025_09_18.txt',
        corpus_dir / 'pos_discovered_organizations.txt'
    ]
    
    print("🧹 COMPREHENSIVE CORPUS CLEANING")
    print("=" * 50)
    
    total_removed = 0
    total_original = 0
    
    for file_path in org_files:
        if not file_path.exists():
            print(f"⚠️  Skipping {file_path.name} - file not found")
            continue
            
        print(f"\n📂 Processing: {file_path.name}")
        print("-" * 40)
        
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()
        
        original_count = len([line for line in original_lines if line.strip()])
        total_original += original_count
        
        # Process lines
        cleaned_lines = []
        removed_count = 0
        
        for line in original_lines:
            term = line.strip().lower()
            
            if not term:  # Keep empty lines
                cleaned_lines.append(line)
                continue
            
            # Check if it should be removed
            if term in noise_terms:
                # But preserve if it's a legitimate company
                if term in legitimate_companies:
                    cleaned_lines.append(line)
                    print(f"✅ Preserved: {term}")
                else:
                    removed_count += 1
                    print(f"🗑️  Removed: {term}")
            else:
                # Keep all other terms
                cleaned_lines.append(line)
        
        cleaned_count = len([line for line in cleaned_lines if line.strip()])
        total_removed += removed_count
        
        print(f"📊 {file_path.name}: {original_count} → {cleaned_count} ({removed_count} removed)")
        
        if removed_count > 0:
            # Create backup if doesn't exist
            backup_path = file_path.with_suffix('.txt.backup_comprehensive')
            if not backup_path.exists():
                with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                    dst.write(src.read())
                print(f"💾 Backup: {backup_path.name}")
            
            # Write cleaned file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)
            print(f"✅ Cleaned: {file_path.name}")
        else:
            print(f"✨ Clean: {file_path.name} (no changes needed)")
    
    print(f"\n🎯 COMPREHENSIVE CLEANING SUMMARY:")
    print(f"   Total original entries: {total_original:,}")
    print(f"   Total removed: {total_removed:,}")
    print(f"   Percentage cleaned: {total_removed/total_original*100:.2f}%")
    print(f"   Files processed: {len([f for f in org_files if f.exists()])}")
    
    print(f"\n✅ Comprehensive corpus cleaning complete!")
    print(f"💡 Next: Restart system to reload cleaned corpus")

if __name__ == "__main__":
    comprehensive_corpus_cleaning()