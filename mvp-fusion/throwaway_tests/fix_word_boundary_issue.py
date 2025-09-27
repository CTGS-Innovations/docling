#!/usr/bin/env python3
"""
GOAL: Fix word boundary issue in Aho-Corasick entity extraction
REASON: "e fund" being extracted from "the funding" due to substring matching
PROBLEM: Need to add word boundary validation after AC matches to ensure whole words only
"""

import sys
import os
import re
from pathlib import Path

# Add mvp-fusion to path for imports
sys.path.insert(0, '/home/corey/projects/docling/mvp-fusion')

def fix_word_boundary_issue():
    """Add word boundary validation to entity extraction methods"""
    
    service_processor_file = Path('/home/corey/projects/docling/mvp-fusion/pipeline/legacy/service_processor.py')
    
    print("🔧 FIXING WORD BOUNDARY ISSUE IN ENTITY EXTRACTION")
    print("=" * 55)
    
    # Read the current file
    with open(service_processor_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The problematic code section to replace
    old_extraction_code = '''                # Extract entities from this sentence
                for end_pos, (ent_type, canonical) in automaton.iter(sentence_text.lower()):
                    start_pos = end_pos - len(canonical) + 1
                    original_text = sentence_text[start_pos:end_pos + 1]'''
    
    # The fixed code with word boundary validation
    new_extraction_code = '''                # Extract entities from this sentence with word boundary validation
                for end_pos, (ent_type, canonical) in automaton.iter(sentence_text.lower()):
                    start_pos = end_pos - len(canonical) + 1
                    original_text = sentence_text[start_pos:end_pos + 1]
                    
                    # WORD BOUNDARY VALIDATION: Ensure we're matching whole words, not substrings
                    # Check that the match is bounded by non-alphanumeric characters or string boundaries
                    is_valid_word_boundary = True
                    
                    # Check character before the match (if exists)
                    if start_pos > 0:
                        char_before = sentence_text[start_pos - 1]
                        if char_before.isalnum():  # If previous character is alphanumeric, it's not a word boundary
                            is_valid_word_boundary = False
                    
                    # Check character after the match (if exists)  
                    if end_pos + 1 < len(sentence_text):
                        char_after = sentence_text[end_pos + 1]
                        if char_after.isalnum():  # If next character is alphanumeric, it's not a word boundary
                            is_valid_word_boundary = False
                    
                    # Skip this match if it's not a valid word boundary
                    if not is_valid_word_boundary:
                        continue'''
    
    if old_extraction_code in content:
        # Apply the fix
        new_content = content.replace(old_extraction_code, new_extraction_code)
        
        # Create backup
        backup_file = service_processor_file.with_suffix('.py.backup_wordboundary')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Created backup: {backup_file}")
        
        # Write the fixed content
        with open(service_processor_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Applied word boundary fix to: {service_processor_file}")
        print(f"🎯 This should prevent 'e fund' from matching in 'the funding'")
        print(f"🎯 This should prevent 'the pan' from matching within words")
        print(f"🎯 Only whole words will be matched as entities")
        
        return True
    else:
        print(f"❌ Could not find the target code section to fix")
        print(f"⚠️  The code structure may have changed")
        return False

if __name__ == "__main__":
    success = fix_word_boundary_issue()
    if success:
        print(f"\n🟢 WORD BOUNDARY FIX APPLIED SUCCESSFULLY!")
        print(f"💡 Next: Test the fix with problematic phrases")
    else:
        print(f"\n🔴 WORD BOUNDARY FIX FAILED")
        print(f"💡 Manual intervention may be needed")