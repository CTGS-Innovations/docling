#!/usr/bin/env python3
"""
Test in clean environment with full 100 files
"""

import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    import fitz
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    print("❌ No PyMuPDF")
    exit(1)

def extract_pdf_clean(pdf_path):
    """Clean extraction matching MVP-Hyper logic"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        # MVP-Hyper 100-page limit
        if page_count > 100:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": f"PDF has {page_count} pages (limit: 100)", "pages": 0}
        
        # Extract all pages
        text_parts = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text()  # Simple method
                text_parts.append(text or "")
            except:
                text_parts.append(f"[Page {i+1} failed]")
        
        full_text = '\n'.join(text_parts)
        doc.close()
        
        return {
            "file": str(pdf_path),
            "success": True,
            "pages": page_count,
            "text_len": len(full_text)
        }
        
    except Exception as e:
        return {"file": str(pdf_path), "success": False, "error": str(e), "pages": 0}

def test_full_performance():
    """Test full performance in clean environment"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:100]
    
    print(f"🚀 CLEAN ENVIRONMENT TEST")
    print(f"📁 Testing {len(pdfs)} OSHA PDF files")
    
    # Test different worker counts
    for workers in [1, 16]:
        print(f"\n⚡ TESTING WITH {workers} WORKERS")
        
        start_time = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(extract_pdf_clean, pdf) for pdf in pdfs]
            results = [future.result() for future in futures]
        
        total_time = time.perf_counter() - start_time
        successful = [r for r in results if r.get("success")]
        skipped = [r for r in results if not r.get("success") and "limit: 100" in r.get("error", "")]
        total_pages = sum(r.get("pages", 0) for r in successful)
        
        pages_per_sec = total_pages / total_time if total_time > 0 else 0
        
        print(f"✅ {workers} Workers Results:")
        print(f"   Files processed: {len(successful)}")
        print(f"   Files skipped: {len(skipped)}")
        print(f"   Total pages: {total_pages}")
        print(f"   Time: {total_time:.2f}s")
        print(f"   📊 Current: {pages_per_sec:.1f} pages/sec")
        
        # Compare to MVP-Hyper
        mvp_hyper_avg = 710
        if abs(pages_per_sec - mvp_hyper_avg) < 50:
            print(f"   🎯 MATCHES MVP-Hyper baseline!")
        else:
            gap = mvp_hyper_avg - pages_per_sec
            print(f"   Gap: {gap:+.1f} pages/sec vs MVP-Hyper")

if __name__ == "__main__":
    test_full_performance()