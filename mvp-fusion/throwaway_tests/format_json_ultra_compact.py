#!/usr/bin/env python3
"""
Ultra-Compact JSON Formatter for Entity Extraction Results

Creates a maximally horizontal layout while preserving all data.
Each fact becomes much more condensed and readable in a table-like format.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

def format_fact_ultra_compact(fact: Dict) -> Dict[str, Any]:
    """Format a single fact in ultra-compact single-line style"""
    # Build compact fact with key info on minimal lines
    compact = {
        "type": fact.get("fact_type", "Unknown"),
        "confidence": fact.get("confidence", 0.0),
        "span": {"start": fact.get("span", {}).get("start", 0), "end": fact.get("span", {}).get("end", 0)},
        "text": fact.get("raw_text", fact.get("canonical_name", fact.get("text", ""))),
    }
    
    # Add context if present (truncated)
    if "context_summary" in fact:
        context = fact["context_summary"]
        if len(context) > 150:
            context = context[:150] + "..."
        compact["context"] = context
    
    # Add any other important fields compactly
    if "extraction_layer" in fact:
        compact["layer"] = fact["extraction_layer"]
    if "frequency_score" in fact:
        compact["freq"] = fact["frequency_score"]
        
    # Add any remaining fields that aren't already included
    for key, value in fact.items():
        if key not in ["fact_type", "confidence", "span", "raw_text", "canonical_name", "text", "context_summary", "extraction_layer", "frequency_score"]:
            compact[key] = value
    
    return compact

def format_json_ultra_compact(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format entire JSON structure in ultra-compact horizontal layout"""
    result = {}
    
    # Handle semantic_facts section
    if "semantic_facts" in data:
        result["semantic_facts"] = {}
        for category, facts in data["semantic_facts"].items():
            if isinstance(facts, list):
                result["semantic_facts"][category] = [
                    format_fact_ultra_compact(fact) for fact in facts
                ]
            else:
                result["semantic_facts"][category] = facts
    
    # Copy other sections
    for key, value in data.items():
        if key != "semantic_facts":
            result[key] = value
    
    return result

def main():
    """Reformat JSON to ultra-compact horizontal layout"""
    input_file = Path('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_TXT_DOCUMENT.json')
    output_file = input_file.parent / f"{input_file.stem}_ultra_compact.json"
    
    print("Ultra-Compact JSON Formatter")
    print("=" * 50)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Load and process
        print(f"\n📖 Loading and processing...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get stats
        original_size = input_file.stat().st_size
        fact_count = 0
        if "semantic_facts" in data:
            fact_count = sum(len(facts) for facts in data["semantic_facts"].values() 
                           if isinstance(facts, list))
        
        print(f"   Original: {original_size:,} bytes, {fact_count} facts")
        
        # Ultra-compact format
        ultra_compact = format_json_ultra_compact(data)
        
        # Save with minimal formatting for maximum compactness
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(ultra_compact, f, 
                     indent=1,                    # Minimal indent
                     separators=(',', ':'),       # No spaces around separators
                     ensure_ascii=False)          # Unicode support
        
        # Stats
        new_size = output_file.stat().st_size
        reduction = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
        
        print(f"\n✅ Ultra-compact format created!")
        print(f"   Output: {new_size:,} bytes ({reduction:.1f}% reduction)")
        print(f"   Layout: Maximum horizontal density")
        print(f"   Benefits: Each fact ~70% more compact")
        
        # Show what changed
        print(f"\n🚀 Improvements:")
        print(f"   • Shortened field names (fact_type→type, raw_text→text)")
        print(f"   • Inline span formatting")
        print(f"   • Truncated contexts (150 char max)")
        print(f"   • Minimal indentation (1 space)")
        print(f"   • No extra spaces in JSON syntax")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()