#!/usr/bin/env python3
"""
Performance comparison test: PyMuPDF4LLM vs Our Complex Bounding Box Approach
Test how long it takes to extract markdown from a PDF using both methods.
"""

import time
import fitz  # Standard PyMuPDF
from pathlib import Path
import sys
import json

def test_standard_pymupdf(file_path: Path):
    """Test standard PyMuPDF text extraction to markdown."""
    print("🔄 Testing Standard PyMuPDF...")
    start_time = time.time()
    
    try:
        # Open document
        doc = fitz.open(str(file_path))
        
        # Extract text from all pages
        all_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text("text", sort=True)  # Use sort=True like our enhanced method
            all_text.append(f"# Page {page_num + 1}\n\n{page_text}\n\n")
        
        # Combine into markdown-like format
        markdown_content = "".join(all_text)
        
        doc.close()
        extraction_time = time.time() - start_time
        
        return {
            "success": True,
            "method": "Standard PyMuPDF",
            "time": extraction_time,
            "content": markdown_content,
            "pages": len(all_text),
            "characters": len(markdown_content),
            "words": len(markdown_content.split())
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "Standard PyMuPDF", 
            "error": str(e),
            "time": time.time() - start_time
        }

def test_pymupdf4llm(file_path: Path):
    """Test PyMuPDF4LLM optimized extraction."""
    print("🚀 Testing PyMuPDF4LLM...")
    start_time = time.time()
    
    try:
        # Check if pymupdf4llm is available
        try:
            import pymupdf4llm
        except ImportError:
            print("⚠️  PyMuPDF4LLM not installed. Installing...")
            import subprocess
            import sys
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pymupdf4llm'])
            import pymupdf4llm
        
        # Extract using PyMuPDF4LLM
        markdown_content = pymupdf4llm.to_markdown(str(file_path))
        
        extraction_time = time.time() - start_time
        
        return {
            "success": True,
            "method": "PyMuPDF4LLM",
            "time": extraction_time,
            "content": markdown_content,
            "characters": len(markdown_content),
            "words": len(markdown_content.split()),
            "lines": len(markdown_content.split('\n'))
        }
        
    except Exception as e:
        return {
            "success": False,
            "method": "PyMuPDF4LLM",
            "error": str(e),
            "time": time.time() - start_time
        }

def test_our_complex_approach(file_path: Path):
    """Test our complex bounding box + detection approach (simulated timing)."""
    print("🔧 Testing Our Complex Approach...")
    start_time = time.time()
    
    try:
        # Import our processor
        from bounding_box_match_method import TwoPhaseProcessor
        
        # Run our complex processing
        processor = TwoPhaseProcessor(log_to_file=False)  # Disable logging for clean timing
        result = processor.process_document(file_path)
        
        processing_time = time.time() - start_time
        
        if result.get("success"):
            # Simulate markdown generation from detected regions
            # (In reality, this would go through VLM processing)
            full_text = result.get("full_text", "")
            special_regions = result.get("special_regions", [])
            
            return {
                "success": True,
                "method": "Our Complex Approach",
                "time": processing_time,
                "text_extraction_time": result["performance"]["text_extraction_time"],
                "detection_time": result["performance"]["detection_time"],
                "total_time": result["performance"]["total_time"],
                "pages": result["performance"]["pages_processed"],
                "special_regions_found": len(special_regions),
                "characters": len(full_text),
                "words": len(full_text.split()) if full_text else 0,
                "note": "This includes full text extraction + region detection + VLM processing time would be additional"
            }
        else:
            return {
                "success": False,
                "method": "Our Complex Approach",
                "error": result.get("error", "Unknown error"),
                "time": processing_time
            }
        
    except Exception as e:
        return {
            "success": False,
            "method": "Our Complex Approach",
            "error": str(e),
            "time": time.time() - start_time
        }

def compare_methods(file_path: Path):
    """Compare all three methods and show results."""
    print(f"📊 PERFORMANCE COMPARISON TEST")
    print("=" * 60)
    print(f"📄 File: {file_path.name}")
    print(f"📐 Size: {file_path.stat().st_size / 1024:.1f} KB")
    print()
    
    # Run all tests
    results = []
    
    # Test 1: Standard PyMuPDF
    result1 = test_standard_pymupdf(file_path)
    results.append(result1)
    if result1["success"]:
        print(f"   ✅ {result1['time']:.3f}s - {result1['pages']} pages, {result1['words']:,} words")
    else:
        print(f"   ❌ Failed: {result1['error']}")
    
    # Test 2: PyMuPDF4LLM
    result2 = test_pymupdf4llm(file_path)
    results.append(result2)
    if result2["success"]:
        print(f"   ✅ {result2['time']:.3f}s - {result2['words']:,} words")
    else:
        print(f"   ❌ Failed: {result2['error']}")
    
    # Test 3: Our Complex Approach  
    result3 = test_our_complex_approach(file_path)
    results.append(result3)
    if result3["success"]:
        print(f"   ✅ {result3['time']:.3f}s - {result3['pages']} pages, {result3['special_regions_found']} special regions")
        print(f"     └─ Text extraction: {result3['text_extraction_time']:.3f}s, Detection: {result3['detection_time']:.3f}s")
    else:
        print(f"   ❌ Failed: {result3['error']}")
    
    # Analysis
    print(f"\n📈 PERFORMANCE ANALYSIS")
    print("=" * 40)
    
    successful_results = [r for r in results if r["success"]]
    if len(successful_results) >= 2:
        times = [r["time"] for r in successful_results]
        fastest_time = min(times)
        fastest_method = next(r["method"] for r in successful_results if r["time"] == fastest_time)
        
        print(f"🏆 Fastest: {fastest_method} ({fastest_time:.3f}s)")
        
        for result in successful_results:
            if result["time"] != fastest_time:
                speedup = result["time"] / fastest_time
                print(f"⚡ {fastest_method} is {speedup:.1f}x faster than {result['method']}")
    
    # Save detailed results
    output_dir = Path('/home/corey/projects/docling/cli/output/latest')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    comparison_file = output_dir / f"{file_path.stem}_method_comparison.json"
    with open(comparison_file, 'w') as f:
        json.dump({
            "file": str(file_path),
            "file_size_kb": file_path.stat().st_size / 1024,
            "test_timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "results": results
        }, f, indent=2)
    
    # Save markdown outputs for comparison
    for i, result in enumerate(results):
        if result["success"] and "content" in result:
            method_name = result["method"].lower().replace(" ", "_")
            markdown_file = output_dir / f"{file_path.stem}_{method_name}_output.md"
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(f"# {result['method']} Output\n")
                f.write(f"Extraction time: {result['time']:.3f}s\n\n")
                f.write(result["content"])
    
    print(f"\n💾 Results saved to: {comparison_file.name}")
    print(f"📝 Markdown outputs saved for manual comparison")
    
    return results

def main():
    """Main comparison test."""
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # Default to Complex1.pdf
        file_path = Path('/home/corey/projects/docling/cli/data/complex_pdfs/Complex1.pdf')
        print("💡 Usage: python test_pymupdf4llm_comparison.py <path_to_pdf>")
        print(f"   Using default file: {file_path.name}")
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        print(f"💡 Usage: python test_pymupdf4llm_comparison.py <path_to_pdf>")
        return
    
    results = compare_methods(file_path)
    
    # Summary
    print(f"\n🎯 SUMMARY")
    print("=" * 30)
    pymupdf4llm_result = next((r for r in results if r["method"] == "PyMuPDF4LLM" and r["success"]), None)
    complex_result = next((r for r in results if r["method"] == "Our Complex Approach" and r["success"]), None)
    
    if pymupdf4llm_result and complex_result:
        print(f"PyMuPDF4LLM: {pymupdf4llm_result['time']:.3f}s (optimized for LLM)")
        print(f"Our approach: {complex_result['time']:.3f}s (includes detection)")
        
        if pymupdf4llm_result['time'] < complex_result['time']:
            speedup = complex_result['time'] / pymupdf4llm_result['time'] 
            print(f"🚀 PyMuPDF4LLM is {speedup:.1f}x faster!")
            print(f"💡 Consider using PyMuPDF4LLM for simple text extraction")
            print(f"🔧 Our approach adds value for complex formula/table detection")
        else:
            print(f"🤔 Unexpected: Our approach was faster")
    
    print(f"\n✨ Next steps: Compare the markdown quality manually!")

if __name__ == "__main__":
    main()