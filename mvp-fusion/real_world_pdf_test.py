#!/usr/bin/env python3
"""
REAL-WORLD PDF Test: Process ALL pages of OSHA PDFs to get accurate performance data
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

def extract_all_pages_pdf(pdf_path):
    """Extract ALL pages from PDF - real-world test"""
    try:
        print(f"Thread {threading.current_thread().name}: Processing {pdf_path.name}")
        
        # Open PDF
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count == 0:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": "No pages", "pages": 0}
        
        # Extract ALL pages (real-world processing)
        all_text = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                all_text.append(text or "")
            except Exception as e:
                all_text.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
        
        full_text = '\n'.join(all_text)
        doc.close()
        
        return {
            "file": str(pdf_path),
            "success": True,
            "pages": page_count,
            "text_len": len(full_text),
            "full_text": full_text
        }
        
    except Exception as e:
        return {"file": str(pdf_path), "success": False, "error": str(e), "pages": 0}

def find_osha_pdfs(limit=100):
    """Find OSHA PDF files for real-world testing"""
    osha_dir = Path("../cli/data_osha")
    
    if not osha_dir.exists():
        print(f"❌ OSHA directory not found: {osha_dir}")
        return []
    
    pdfs = []
    for pdf in osha_dir.glob("*.pdf"):
        pdfs.append(pdf)
        if len(pdfs) >= limit:
            break
    
    return sorted(pdfs)

def real_world_performance_test():
    """Test real-world PDF processing performance on ALL pages"""
    
    # Get OSHA PDFs
    pdfs = find_osha_pdfs(100)
    if not pdfs:
        print("❌ No OSHA PDFs found")
        return
    
    print(f"🚀 REAL-WORLD PDF TEST (ALL PAGES)")
    print(f"📁 Found {len(pdfs)} OSHA PDF files")
    
    # Analyze first 10 files to understand scope
    print(f"\n📋 SAMPLE FILE ANALYSIS:")
    sample_total_pages = 0
    for i, pdf in enumerate(pdfs[:10]):
        try:
            doc = fitz.open(str(pdf))
            pages = len(doc)
            size = pdf.stat().st_size
            doc.close()
            print(f"  {i+1}. {pdf.name}: {pages} pages, {size:,} bytes")
            sample_total_pages += pages
        except Exception as e:
            print(f"  {i+1}. {pdf.name}: ERROR - {e}")
    
    print(f"\n📊 EXPECTED WORKLOAD:")
    print(f"First 10 files: {sample_total_pages} pages")
    estimated_total = (sample_total_pages * len(pdfs)) // 10
    print(f"Estimated total for {len(pdfs)} files: ~{estimated_total} pages")
    
    # Run the actual test with threading
    print(f"\n⚡ PROCESSING ALL PAGES WITH THREADING")
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for pdf in pdfs:
            future = executor.submit(extract_all_pages_pdf, pdf)
            futures.append(future)
        
        results = []
        for future in futures:
            results.append(future.result())
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    # Calculate real metrics
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    total_text_chars = sum(r.get("text_len", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time
    files_per_sec = len(successful) / total_time
    chars_per_sec = total_text_chars / total_time
    
    print(f"\n" + "=" * 70)
    print(f"📈 REAL-WORLD RESULTS (ALL PAGES)")
    print(f"=" * 70)
    
    print(f"📁 Files processed: {len(successful)}/{len(results)}")
    print(f"📄 Total pages: {total_pages}")
    print(f"📝 Total text chars: {total_text_chars:,}")
    print(f"⏱️  Processing time: {total_time:.2f}s")
    print()
    
    print(f"🚀 PERFORMANCE METRICS:")
    print(f"   Files per second: {files_per_sec:.1f}")
    print(f"   Pages per second: {pages_per_sec:.1f}")
    print(f"   Characters per second: {chars_per_sec:,.0f}")
    print()
    
    # Compare to previous misleading test
    print(f"🔍 COMPARISON:")
    print(f"   Previous (first page only): ~3386 pages/sec")
    print(f"   Real-world (all pages): {pages_per_sec:.1f} pages/sec")
    
    if pages_per_sec < 3386:
        reduction_factor = 3386 / pages_per_sec
        print(f"   Reality check: {reduction_factor:.1f}x slower than misleading test")
    
    print(f"\n🎯 MVP-HYPER COMPARISON:")
    mvp_hyper_baseline = 707  # pages/sec from evidence
    if pages_per_sec >= mvp_hyper_baseline:
        print(f"   ✅ EXCEEDS MVP-Hyper baseline: {pages_per_sec:.1f} vs {mvp_hyper_baseline}")
    else:
        gap = mvp_hyper_baseline - pages_per_sec
        print(f"   ❌ Below MVP-Hyper baseline by {gap:.1f} pages/sec")
    
    return {
        'files_per_sec': files_per_sec,
        'pages_per_sec': pages_per_sec,
        'chars_per_sec': chars_per_sec,
        'total_files': len(successful),
        'total_pages': total_pages
    }

if __name__ == "__main__":
    try:
        results = real_world_performance_test()
        if results:
            print(f"\n🎯 FINAL REAL-WORLD RESULT: {results['pages_per_sec']:.1f} pages/sec on {results['total_pages']} pages")
    except Exception as e:
        print(f"❌ Test failed: {e}")