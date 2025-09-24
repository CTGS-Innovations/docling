#!/usr/bin/env python3
"""
Test improved extraction patterns on temp_test_doc.md
"""

from pathlib import Path
import sys
sys.path.append('..')
from knowledge.extractors.standalone_intelligent_extractor import StandaloneIntelligentExtractor
from utils.high_performance_json import save_semantic_facts_fast

def test_improved_extraction():
    """Test the improved extractor on our document"""
    
    # Load document
    with open('../temp_test_doc.md', 'r') as f:
        text = f.read()
    
    print("📊 TESTING IMPROVED EXTRACTION PATTERNS")
    print("=" * 50)
    
    # Extract with improved patterns
    extractor = StandaloneIntelligentExtractor()
    results = extractor.extract_semantic_facts(text)
    
    # Save results
    output_path = Path('/home/corey/projects/docling/output/fusion/ENTITY_EXTRACTION_TXT_DOCUMENT_final.json')
    save_semantic_facts_fast(results, str(output_path))
    
    print(f'🟢 **SUCCESS**: Extracted {results["semantic_summary"]["total_facts"]} facts')
    print(f'📁 **OUTPUT**: {output_path}')
    
    # Show summary
    print(f'\n📊 SUMMARY:')
    print(f'Total facts: {results["semantic_summary"]["total_facts"]}')
    print(f'Categories: {results["semantic_summary"]["fact_types"]}')
    print(f'Extraction time: {results["intelligent_extraction"]["extraction_time_ms"]:.1f}ms')
    
    return results

if __name__ == "__main__":
    test_improved_extraction()