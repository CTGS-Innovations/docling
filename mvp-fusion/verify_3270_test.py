#!/usr/bin/env python3
"""
Verify what the 3270 pages/sec test actually did
"""

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def simple_pdf_extract_no_cache(pdf_path):
    """The exact function that was tested"""
    try:
        print(f"Thread {threading.current_thread().name}: Processing {pdf_path.name}")
        
        # Minimal PDF processing
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count == 0:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": "No pages"}
        
        # Extract just first page to minimize memory usage
        page = doc[0]
        text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        doc.close()
        
        return {
            "file": str(pdf_path),
            "success": True,
            "pages": page_count,
            "text_len": len(text or "")
        }
        
    except Exception as e:
        return {"file": str(pdf_path), "success": False, "error": str(e)}

def find_pdfs(limit=100):
    """Find PDF files - focus on OSHA repository for wide range"""
    test_dirs = [
        Path("../cli/data_osha"),  # OSHA PDFs first - wide variety
        Path("../cli/data"),
        Path("../cli/data_complex")
    ]
    
    pdfs = []
    for test_dir in test_dirs:
        if test_dir.exists():
            for pdf in test_dir.rglob("*.pdf"):
                pdfs.append(pdf)
                if len(pdfs) >= limit:
                    break
    return pdfs[:limit]

def analyze_test_validity():
    """Analyze if the 3270 pages/sec test was valid"""
    
    pdfs = find_pdfs(100)
    print(f"🔍 ANALYZING TEST VALIDITY")
    print(f"Found {len(pdfs)} PDFs")
    
    # Check for duplicate files
    unique_names = set(pdf.name for pdf in pdfs)
    print(f"Unique filenames: {len(unique_names)}")
    
    if len(unique_names) < len(pdfs):
        print("⚠️  WARNING: Duplicate filenames detected!")
        
    # Check file sizes and page counts
    print(f"\n📋 FIRST 10 FILES ANALYSIS:")
    total_pages = 0
    for i, pdf in enumerate(pdfs[:10]):
        try:
            doc = fitz.open(str(pdf))
            pages = len(doc)
            size = pdf.stat().st_size
            doc.close()
            print(f"  {i+1}. {pdf.name}: {pages} pages, {size:,} bytes")
            total_pages += pages
        except Exception as e:
            print(f"  {i+1}. {pdf.name}: ERROR - {e}")
    
    print(f"\n📊 PROJECTED PERFORMANCE:")
    print(f"First 10 files: {total_pages} pages")
    print(f"If all 100 files similar: ~{total_pages * 10} pages")
    print(f"If processed in 0.55s: ~{(total_pages * 10) / 0.55:.1f} pages/sec")
    
    # Actually run the test to verify
    print(f"\n🧵 RUNNING ACTUAL TEST:")
    start = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for pdf in pdfs:
            future = executor.submit(simple_pdf_extract_no_cache, pdf)
            futures.append(future)
        
        results = []
        for future in futures:
            results.append(future.result())
    
    elapsed = time.perf_counter() - start
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    
    print(f"✅ ACTUAL RESULTS:")
    print(f"   Files: {len(successful)}/{len(results)}")
    print(f"   Total pages: {total_pages}")
    print(f"   Time: {elapsed:.2f}s")
    print(f"   Speed: {total_pages/elapsed:.1f} pages/sec")
    
    return total_pages, elapsed

if __name__ == "__main__":
    analyze_test_validity()