#!/usr/bin/env python3
"""
Test script for mathematical and table detection improvements.

This tests our enhanced PDF processing system that detects and preserves
mathematical formulas, tables, and other special content before PyMuPDF
converts them to plain text.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from fast_text_extractor import FastTextExtractor

def test_math_detection():
    """Test mathematical and table detection on Complex1.pdf"""
    
    print("🔬 TESTING MATHEMATICAL & TABLE DETECTION")
    print("=" * 60)
    
    # Initialize extractor
    extractor = FastTextExtractor()
    
    # Test file path
    test_file = Path("data/complex_pdfs/Complex1.pdf")
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        print("   Please make sure Complex1.pdf is in the data/complex_pdfs/ directory")
        return
    
    print(f"📄 Processing: {test_file.name}")
    print()
    
    # Extract with our improved detection
    result = extractor.extract(test_file)
    
    if not result.success:
        print(f"❌ Extraction failed: {result.error_message}")
        return
    
    # Analyze results
    print(f"✅ Extraction successful!")
    print(f"📊 Total placeholders found: {len(result.visual_placeholders)}")
    print()
    
    # Categorize placeholders
    placeholders_by_type = {}
    for placeholder in result.visual_placeholders:
        element_type = placeholder.get('element_type', 'unknown')
        if element_type not in placeholders_by_type:
            placeholders_by_type[element_type] = []
        placeholders_by_type[element_type].append(placeholder)
    
    # Print summary by type
    print("📋 PLACEHOLDER BREAKDOWN:")
    for element_type, placeholders in placeholders_by_type.items():
        print(f"   {element_type.upper()}: {len(placeholders)}")
    print()
    
    # Show details for each type
    for element_type, placeholders in placeholders_by_type.items():
        print(f"🔍 {element_type.upper()} DETAILS:")
        for i, placeholder in enumerate(placeholders[:5], 1):  # Show first 5 of each type
            desc = placeholder.get('description', 'No description')
            page = placeholder.get('page_number', '?')
            print(f"   {i}. Page {page}: {desc[:80]}{'...' if len(desc) > 80 else ''}")
        
        if len(placeholders) > 5:
            print(f"   ... and {len(placeholders) - 5} more")
        print()
    
    # Test placeholder integration in text
    print("🔍 PLACEHOLDER INTEGRATION TEST:")
    text_preview = result.text_content[:2000]  # First 2000 chars
    placeholder_count = text_preview.count('[visual_')
    print(f"   Found {placeholder_count} inline placeholders in first 2000 characters")
    
    # Show some examples of inline placeholders
    import re
    placeholder_matches = re.findall(r'`\[visual_\d+\]`', text_preview)
    if placeholder_matches:
        print(f"   Examples: {', '.join(placeholder_matches[:5])}")
    else:
        print("   ⚠️  No inline placeholders found in preview - may be an issue")
    print()
    
    # Save detailed results
    output_file = Path("tests/math_detection_results.txt")
    with open(output_file, 'w') as f:
        f.write("MATHEMATICAL & TABLE DETECTION TEST RESULTS\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"File: {test_file}\n")
        f.write(f"Total placeholders: {len(result.visual_placeholders)}\n\n")
        
        f.write("PLACEHOLDER BREAKDOWN:\n")
        for element_type, placeholders in placeholders_by_type.items():
            f.write(f"  {element_type}: {len(placeholders)}\n")
        f.write("\n")
        
        f.write("DETAILED PLACEHOLDERS:\n")
        for placeholder in result.visual_placeholders:
            f.write(f"- {placeholder.get('element_type', 'unknown')} (Page {placeholder.get('page_number', '?')}): {placeholder.get('description', 'No description')}\n")
        f.write("\n")
        
        f.write("TEXT PREVIEW (first 3000 chars):\n")
        f.write("-" * 40 + "\n")
        f.write(result.text_content[:3000])
        f.write("\n" + "-" * 40 + "\n")
    
    print(f"📁 Detailed results saved to: {output_file}")
    print()
    
    # Final assessment
    formula_count = len(placeholders_by_type.get('formula', []))
    table_count = len(placeholders_by_type.get('table', []))
    total_math_table = formula_count + table_count
    
    print("🎯 ASSESSMENT:")
    if total_math_table > 0:
        print(f"   ✅ SUCCESS! Detected {formula_count} formulas and {table_count} tables")
        if formula_count > 5:
            print("   📈 Good mathematical content detection")
        if table_count > 2:
            print("   📊 Good table detection")
    else:
        print("   ⚠️  No mathematical formulas or tables detected")
        print("   🔧 Detection system may need tuning")
    
    if placeholder_count > 0:
        print(f"   ✅ Placeholders properly embedded inline ({placeholder_count} found)")
    else:
        print("   ❌ Placeholders not embedded inline - integration issue")

if __name__ == "__main__":
    test_math_detection()