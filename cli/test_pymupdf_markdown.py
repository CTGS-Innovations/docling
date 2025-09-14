#!/usr/bin/env python3
"""
Test PyMuPDF's direct markdown conversion capabilities.
Let's see how it handles formulas, tables, and complex content.
"""

import fitz  # PyMuPDF
import time
from pathlib import Path

def test_pymupdf_markdown_conversion(file_path: Path):
    """Test PyMuPDF's built-in markdown conversion."""
    print(f"🧪 TESTING PYMUPDF DIRECT MARKDOWN CONVERSION")
    print("=" * 60)
    print(f"📄 File: {file_path.name}")
    print()
    
    try:
        # Open document
        start_time = time.time()
        doc = fitz.open(str(file_path))
        open_time = time.time() - start_time
        
        print(f"📖 Opened document: {len(doc)} pages ({open_time:.3f}s)")
        
        # Test markdown conversion
        conversion_start = time.time()
        
        # Convert each page to markdown
        all_markdown = []
        page_results = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            display_page_num = page_num + 1
            
            page_start = time.time()
            
            # Try to get markdown - check if PyMuPDF supports this
            try:
                # Check if there's a direct markdown method
                if hasattr(page, 'get_text'):
                    # Test different text extraction methods that might produce markdown-like output
                    methods_to_test = [
                        ("text", lambda: page.get_text("text")),
                        ("blocks", lambda: page.get_text("blocks")),
                        ("dict", lambda: page.get_text("dict")),
                        ("html", lambda: page.get_text("html")),
                    ]
                    
                    for method_name, extract_func in methods_to_test:
                        if display_page_num <= 3:  # Only test first 3 pages for speed
                            method_start = time.time()
                            result = extract_func()
                            method_time = time.time() - method_start
                            
                            # Save results for analysis
                            output_dir = Path('/home/corey/projects/docling/cli/output/latest')
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Use appropriate file extension based on method
                            if method_name == "html":
                                result_file = output_dir / f"page_{display_page_num}_pymupdf_{method_name}.html"
                            elif method_name == "dict":
                                result_file = output_dir / f"page_{display_page_num}_pymupdf_{method_name}.json"
                            elif method_name in ["text", "blocks"]:
                                result_file = output_dir / f"page_{display_page_num}_pymupdf_{method_name}.txt"
                            else:
                                result_file = output_dir / f"page_{display_page_num}_pymupdf_{method_name}.txt"
                            with open(result_file, 'w', encoding='utf-8') as f:
                                if method_name == "dict":
                                    # Save as proper JSON
                                    import json
                                    json.dump({
                                        "page": display_page_num,
                                        "method": method_name,
                                        "extraction_time": method_time,
                                        "data": result
                                    }, f, indent=2, ensure_ascii=False)
                                elif method_name == "html":
                                    # Save as proper HTML with metadata comment
                                    f.write(f"<!-- PAGE {display_page_num} - METHOD: {method_name.upper()} -->\n")
                                    f.write(f"<!-- Extraction time: {method_time:.3f}s -->\n")
                                    f.write(f"<!-- Length: {len(result) if isinstance(result, str) else 'N/A'} characters -->\n\n")
                                    f.write(result if isinstance(result, str) else str(result))
                                elif isinstance(result, str):
                                    f.write(f"=== PAGE {display_page_num} - METHOD: {method_name.upper()} ===\n")
                                    f.write(f"Extraction time: {method_time:.3f}s\n")
                                    f.write(f"Length: {len(result)} characters\n")
                                    f.write("=" * 50 + "\n\n")
                                    f.write(result)
                                elif isinstance(result, list):
                                    f.write(f"=== PAGE {display_page_num} - METHOD: {method_name.upper()} ===\n")
                                    f.write(f"Extraction time: {method_time:.3f}s\n")
                                    f.write(f"Items: {len(result)}\n")
                                    f.write("=" * 50 + "\n\n")
                                    for i, item in enumerate(result):
                                        f.write(f"[{i}] {item}\n\n")
                                else:
                                    f.write(f"=== PAGE {display_page_num} - METHOD: {method_name.upper()} ===\n")
                                    f.write(f"Extraction time: {method_time:.3f}s\n")
                                    f.write("=" * 50 + "\n\n")
                                    f.write(str(result))
                            
                            print(f"   Page {display_page_num} - {method_name}: {method_time:.3f}s")
                
                # Get simple text for markdown-like formatting attempt
                page_text = page.get_text("text")
                all_markdown.append(f"# Page {display_page_num}\n\n{page_text}\n\n")
                
                page_time = time.time() - page_start
                page_results.append({
                    "page": display_page_num,
                    "time": page_time,
                    "char_count": len(page_text),
                    "has_formulas": any(symbol in page_text for symbol in ['∑', '∫', '∏', '√', '±', '∞', '≈', '≤', '≥'])
                })
                
                if display_page_num <= 5:  # Show progress for first few pages
                    print(f"   Page {display_page_num}: {page_time:.3f}s, {len(page_text)} chars")
            
            except Exception as e:
                print(f"   ❌ Page {display_page_num} failed: {e}")
                page_results.append({
                    "page": display_page_num,
                    "error": str(e)
                })
        
        conversion_time = time.time() - conversion_start
        doc.close()
        
        # Save combined markdown
        output_dir = Path('/home/corey/projects/docling/cli/output/latest')
        markdown_file = output_dir / f"{file_path.stem}_pymupdf_markdown.md"
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(f"# PyMuPDF Markdown Conversion: {file_path.name}\n\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Conversion time: {conversion_time:.3f}s\n\n")
            f.write("---\n\n")
            f.write("".join(all_markdown))
        
        # Analysis
        print(f"\n📊 CONVERSION ANALYSIS")
        print("=" * 40)
        print(f"Total time: {conversion_time:.3f}s")
        print(f"Pages processed: {len(page_results)}")
        print(f"Average per page: {conversion_time / len(page_results):.3f}s")
        
        formula_pages = [p for p in page_results if p.get("has_formulas", False)]
        print(f"Pages with formulas: {len(formula_pages)}")
        
        print(f"\n💾 Output saved:")
        print(f"   📝 Markdown: {markdown_file.name}")
        print(f"   📁 Individual extractions:")
        print(f"      📄 Text: page_*_pymupdf_text.txt")
        print(f"      📋 Blocks: page_*_pymupdf_blocks.txt") 
        print(f"      🌐 HTML: page_*_pymupdf_html.html")
        print(f"      📊 JSON: page_*_pymupdf_dict.json")
        
        # Quick formula analysis on page 3
        if len(page_results) >= 3:
            page_3_result = page_results[2]  # 0-based index
            if "has_formulas" in page_3_result and page_3_result["has_formulas"]:
                print(f"   🧮 Page 3 contains mathematical symbols")
            else:
                print(f"   ⚠️  Page 3 - no mathematical symbols detected in plain text")
        
        return {
            "success": True,
            "conversion_time": conversion_time,
            "pages_processed": len(page_results),
            "markdown_file": str(markdown_file),
            "pages_with_formulas": len(formula_pages)
        }
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

def main():
    """Test PyMuPDF markdown conversion on any PDF file."""
    import sys
    
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default to Complex1.pdf if no argument provided
        file_path = Path('/home/corey/projects/docling/cli/data/complex_pdfs/Complex1.pdf')
        print("💡 Usage: python test_pymupdf_markdown.py <path_to_pdf_file>")
        print(f"   Using default file: {file_path.name}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print(f"💡 Usage: python test_pymupdf_markdown.py <path_to_pdf_file>")
        return
    
    result = test_pymupdf_markdown_conversion(file_path)
    
    if result.get("success"):
        print(f"\n✅ SUCCESS! PyMuPDF markdown conversion completed.")
        print(f"📈 Performance: {result['pages_processed']} pages in {result['conversion_time']:.3f}s")
        
        if result.get("pages_with_formulas", 0) > 0:
            print(f"🧮 Formula detection: {result['pages_with_formulas']} pages contain mathematical symbols")
        else:
            print(f"⚠️  Formula concern: No mathematical symbols detected in plain text extraction")
            print(f"   This suggests formulas might not be properly preserved in markdown")
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
    
    print(f"\n💡 Next steps:")
    print(f"   1. Check the generated markdown file for formula quality")
    print(f"   2. Compare with our bounding box approach")
    print(f"   3. Examine individual extraction methods for best results")

if __name__ == "__main__":
    main()