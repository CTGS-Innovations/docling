#!/usr/bin/env python3
"""
Test with various Python optimization flags and environment variables
"""

import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Set optimization environment variables
os.environ['PYTHONOPTIMIZE'] = '2'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def extract_optimized(pdf_path):
    """Optimized extraction with minimal overhead"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Minimal processing - just count pages, don't extract text
        # This tests pure PyMuPDF overhead
        doc.close()
        return {"success": True, "pages": page_count}
        
    except Exception:
        return {"success": False, "pages": 0}

def test_minimal_overhead():
    """Test with absolute minimal processing"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"🚀 MINIMAL OVERHEAD TEST")
    print(f"📁 Testing {len(pdfs)} files")
    print("⚡ Only opening/closing PDFs, no text extraction")
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(extract_optimized, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    
    print(f"✅ MINIMAL OVERHEAD RESULTS:")
    print(f"   Files: {len(successful)}/{len(results)}")
    print(f"   Pages: {total_pages}")
    print(f"   Time: {total_time:.2f}s")
    print(f"   📊 Current: {pages_per_sec:.1f} pages/sec")
    print(f"   🎯 This is our theoretical maximum")
    
    return pages_per_sec

def extract_text_optimized(pdf_path):
    """Extract text with optimizations"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0}
        
        # Optimized text extraction
        for i in range(page_count):
            page = doc[i]
            # Use fastest extraction method
            _ = page.get_text()  # Don't store text, just extract
        
        doc.close()
        return {"success": True, "pages": page_count}
        
    except Exception:
        return {"success": False, "pages": 0}

def test_optimized_extraction():
    """Test with optimized text extraction"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"\n🚀 OPTIMIZED EXTRACTION TEST")
    print(f"📁 Testing {len(pdfs)} files")
    print("⚡ Extract text but don't store it")
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(extract_text_optimized, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    
    print(f"✅ OPTIMIZED EXTRACTION RESULTS:")
    print(f"   Files: {len(successful)}/{len(results)}")
    print(f"   Pages: {total_pages}")
    print(f"   Time: {total_time:.2f}s")
    print(f"   📊 Current: {pages_per_sec:.1f} pages/sec")
    
    return pages_per_sec

if __name__ == "__main__":
    print("🔧 OPTIMIZATION FLAGS ENABLED:")
    print(f"   PYTHONOPTIMIZE=2")
    print(f"   Threading limited to 1 for all numeric libraries")
    
    minimal_speed = test_minimal_overhead()
    extraction_speed = test_optimized_extraction()
    
    print(f"\n📊 OPTIMIZATION ANALYSIS:")
    print(f"   Minimal overhead: {minimal_speed:.1f} pages/sec")
    print(f"   With text extraction: {extraction_speed:.1f} pages/sec")
    print(f"   Text extraction overhead: {minimal_speed - extraction_speed:.1f} pages/sec")
    print(f"   MVP-Hyper target: 710 pages/sec")
    
    if minimal_speed >= 710:
        print(f"   ✅ We can theoretically reach MVP-Hyper speed!")
        print(f"   🎯 Need to optimize text extraction by {710 - extraction_speed:.1f} pages/sec")
    else:
        print(f"   ❌ Environment limitation: {710 - minimal_speed:.1f} pages/sec below theoretical max")