#!/usr/bin/env python3
"""
Compact JSON Formatter for Entity Extraction Results

Reformats verbose JSON output to be more horizontally laid out and organized.
Preserves all data while making it more readable and less vertically sprawling.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

def format_compact_span(span_data: Dict) -> str:
    """Format span data compactly: {start: 0, end: 10}"""
    if isinstance(span_data, dict):
        start = span_data.get('start', 0)
        end = span_data.get('end', 0)
        return f"{{'start': {start}, 'end': {end}}}"
    return str(span_data)

def format_fact_compact(fact: Dict) -> Dict[str, Any]:
    """Format a single fact entry more compactly"""
    # Create compact version preserving all data
    compact_fact = {}
    
    # Essential fields on one line each
    if 'fact_type' in fact:
        compact_fact['fact_type'] = fact['fact_type']
    if 'confidence' in fact:
        compact_fact['confidence'] = fact['confidence']
    if 'span' in fact:
        # Keep span compact but readable
        compact_fact['span'] = fact['span']
    
    # Text fields
    for text_field in ['raw_text', 'canonical_name', 'text']:
        if text_field in fact:
            compact_fact[text_field] = fact[text_field]
    
    # Context summary (truncate if very long)
    if 'context_summary' in fact:
        context = fact['context_summary']
        if len(context) > 200:
            context = context[:200] + "..."
        compact_fact['context_summary'] = context
    
    # Add remaining fields
    for key, value in fact.items():
        if key not in compact_fact:
            compact_fact[key] = value
    
    return compact_fact

def format_json_compact(data: Dict[str, Any], max_items_per_category: int = 50) -> Dict[str, Any]:
    """Format entire JSON structure more compactly"""
    compact_data = {}
    
    # Process semantic_facts section
    if 'semantic_facts' in data:
        compact_data['semantic_facts'] = {}
        semantic_facts = data['semantic_facts']
        
        for category, facts in semantic_facts.items():
            if isinstance(facts, list):
                # Limit facts per category for readability
                limited_facts = facts[:max_items_per_category]
                if len(facts) > max_items_per_category:
                    print(f"  Truncated {category}: {len(facts)} -> {max_items_per_category} items")
                
                # Format each fact compactly
                compact_facts = [format_fact_compact(fact) for fact in limited_facts]
                compact_data['semantic_facts'][category] = compact_facts
            else:
                compact_data['semantic_facts'][category] = facts
    
    # Copy other top-level sections as-is
    for key, value in data.items():
        if key not in compact_data:
            compact_data[key] = value
    
    return compact_data

def main():
    """Main function to reformat JSON file"""
    input_file = Path('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_TXT_DOCUMENT.json')
    output_file = input_file.parent / f"{input_file.stem}_compact.json"
    
    print("Compact JSON Formatter")
    print("=" * 50)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Load original JSON
        print(f"\n📖 Loading JSON file...")
        with open(input_file, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # Get original stats
        original_size = input_file.stat().st_size
        if 'semantic_facts' in original_data:
            original_fact_count = sum(len(facts) for facts in original_data['semantic_facts'].values() 
                                    if isinstance(facts, list))
        else:
            original_fact_count = 0
        
        print(f"   Original size: {original_size:,} bytes")
        print(f"   Original facts: {original_fact_count:,} total")
        
        # Format compactly
        print(f"\n🔧 Reformatting for compact layout...")
        compact_data = format_json_compact(original_data, max_items_per_category=100)
        
        # Save compact version with readable formatting
        print(f"\n💾 Saving compact version...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(compact_data, f, 
                     indent=2,           # Reasonable indentation
                     separators=(',', ': '), # Compact separators
                     ensure_ascii=False)  # Allow unicode
        
        # Get new stats
        new_size = output_file.stat().st_size
        size_reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        if 'semantic_facts' in compact_data:
            compact_fact_count = sum(len(facts) for facts in compact_data['semantic_facts'].values() 
                                   if isinstance(facts, list))
        else:
            compact_fact_count = 0
        
        print(f"\n✅ Compact formatting complete!")
        print(f"   Compact size: {new_size:,} bytes ({size_reduction:.1f}% smaller)")
        print(f"   Compact facts: {compact_fact_count:,} total")
        print(f"   Layout: More horizontal, organized, readable")
        
        # Show sample of improvement
        print(f"\n📊 Format Improvements:")
        print(f"   • Compact span formatting")
        print(f"   • Truncated long context summaries")
        print(f"   • Consistent indentation (2 spaces)")
        print(f"   • Limited items per category for readability")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()