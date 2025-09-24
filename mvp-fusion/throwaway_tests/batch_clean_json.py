#!/usr/bin/env python3
"""
Batch JSON Cleaner for Knowledge Extraction Files
=================================================
Clean all JSON files in the output directory to remove newlines and tagged elements.
"""

import sys
sys.path.append('..')

from utils.text_cleaner import TextCleaner
from pathlib import Path
import json

def batch_clean_json_files():
    """Clean all JSON files in the fusion output directory"""
    
    output_dir = Path('/home/corey/projects/docling/output/fusion')
    cleaner = TextCleaner()
    
    if not output_dir.exists():
        print(f"🔴 Output directory not found: {output_dir}")
        return
    
    # Find all JSON files
    json_files = list(output_dir.glob("*.json"))
    
    print(f"🧹 BATCH CLEANING JSON FILES")
    print(f"=" * 40)
    print(f"📁 Directory: {output_dir}")
    print(f"📄 Found {len(json_files)} JSON files")
    
    if not json_files:
        print("🔴 No JSON files found to clean")
        return
    
    cleaned_count = 0
    
    for json_file in json_files:
        # Skip already cleaned files
        if '_cleaned' in json_file.name:
            continue
            
        print(f"\n🧹 Cleaning: {json_file.name}")
        
        try:
            # Load original
            with open(json_file, 'r', encoding='utf-8') as f:
                original_data = json.load(f)
            
            # Clean the data
            cleaned_data = cleaner.clean_semantic_facts(original_data)
            
            # Create cleaned filename
            cleaned_path = json_file.parent / f"{json_file.stem}_cleaned.json"
            
            # Save cleaned version
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            # Show before/after stats
            original_facts = original_data.get('semantic_summary', {}).get('total_facts', 0)
            cleaned_facts = cleaned_data.get('semantic_summary', {}).get('total_facts', 0)
            
            print(f"  ✅ Facts: {original_facts} → {cleaned_facts}")
            print(f"  📁 Saved: {cleaned_path.name}")
            
            cleaned_count += 1
            
        except Exception as e:
            print(f"  🔴 Error: {e}")
    
    print(f"\n🟢 BATCH CLEANING COMPLETE")
    print(f"Successfully cleaned {cleaned_count}/{len(json_files)} files")
    
    # Show sample of improvements
    if cleaned_count > 0:
        print(f"\n🎯 SAMPLE IMPROVEMENTS:")
        sample_file = [f for f in output_dir.glob("*_cleaned.json")][0]
        
        with open(sample_file, 'r') as f:
            sample_data = json.load(f)
        
        # Find a fact with context to show
        for category, facts in sample_data.get('semantic_facts', {}).items():
            if facts and isinstance(facts, list):
                fact = facts[0]
                context = fact.get('extra', {}).get('context', fact.get('context', ''))
                obj = fact.get('extra', {}).get('object', fact.get('object', ''))
                
                if context and len(context) > 50:
                    print(f"  Clean context: \"{context[:80]}...\"")
                    break
                elif obj and len(obj) > 20:
                    print(f"  Clean object: \"{obj[:60]}...\"")
                    break

if __name__ == "__main__":
    batch_clean_json_files()