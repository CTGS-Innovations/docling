#!/usr/bin/env python3
"""
Minimal test: Just PyMuPDF + threading
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

def extract_simple(pdf_path):
    """Minimal extraction"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"file": str(pdf_path), "success": False, "pages": 0}
        
        text_parts = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text()
                text_parts.append(text or "")
            except:
                text_parts.append("")
        
        doc.close()
        return {"file": str(pdf_path), "success": True, "pages": page_count}
        
    except Exception as e:
        return {"file": str(pdf_path), "success": False, "error": str(e), "pages": 0}

def test_minimal():
    """Test with minimal setup"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:20]  # Just 20 files
    
    print(f"Testing {len(pdfs)} files...")
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=4) as executor:  # Just 4 workers
        futures = [executor.submit(extract_simple, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    
    print(f"✅ Results: {len(successful)}/{len(results)} files")
    print(f"   Pages: {total_pages}")
    print(f"   Time: {total_time:.2f}s")
    print(f"   Speed: {total_pages/total_time:.1f} pages/sec")

if __name__ == "__main__":
    test_minimal()