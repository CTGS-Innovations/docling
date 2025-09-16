#!/usr/bin/env python3
"""
Test pure sequential processing to match MVP-Hyper's likely approach
"""

import time
from pathlib import Path

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def extract_pdf_sequential(pdf_path):
    """Pure sequential extraction - no threading overhead"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": f"PDF has {page_count} pages (limit: 100)", "pages": 0}
        
        # Sequential extraction - no threading
        text_parts = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text()  # Simple method
                text_parts.append(text or "")
            except:
                text_parts.append(f"[Page {i+1} failed]")
        
        doc.close()
        return {"file": str(pdf_path), "success": True, "pages": page_count}
        
    except Exception as e:
        return {"file": str(pdf_path), "success": False, "error": str(e), "pages": 0}

def test_pure_sequential():
    """Test pure sequential processing"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"🚀 PURE SEQUENTIAL TEST")
    print(f"📁 Testing {len(pdfs)} OSHA PDF files")
    print("🔄 Processing files one by one (no threading)")
    
    start_time = time.perf_counter()
    
    results = []
    for i, pdf in enumerate(pdfs):
        result = extract_pdf_sequential(pdf)
        results.append(result)
        
        # Progress indicator
        if (i + 1) % 20 == 0:
            elapsed = time.perf_counter() - start_time
            rate = (i + 1) / elapsed
            print(f"  Processed {i+1}/{len(pdfs)} files ({rate:.1f} files/sec)")
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.get("success")]
    skipped = [r for r in results if not r.get("success") and "limit: 100" in r.get("error", "")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    
    print(f"\n✅ SEQUENTIAL RESULTS:")
    print(f"   Files processed: {len(successful)}")
    print(f"   Files skipped: {len(skipped)}")
    print(f"   Total pages: {total_pages}")
    print(f"   Time: {total_time:.2f}s")
    print(f"   📊 Current: {pages_per_sec:.1f} pages/sec")
    
    # Compare to MVP-Hyper and threaded version
    mvp_hyper_avg = 710
    threaded_result = 558
    
    print(f"\n🎯 PERFORMANCE COMPARISON:")
    print(f"   MVP-Hyper: {mvp_hyper_avg} pages/sec")
    print(f"   Our threaded: {threaded_result} pages/sec")
    print(f"   Our sequential: {pages_per_sec:.1f} pages/sec")
    
    if abs(pages_per_sec - mvp_hyper_avg) < abs(threaded_result - mvp_hyper_avg):
        print(f"   ✅ Sequential is CLOSER to MVP-Hyper!")
        gap = mvp_hyper_avg - pages_per_sec
        print(f"   Remaining gap: {gap:.1f} pages/sec")
    else:
        print(f"   ⚠️  Threading was better")

if __name__ == "__main__":
    test_pure_sequential()