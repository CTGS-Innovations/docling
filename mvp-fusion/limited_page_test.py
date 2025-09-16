#!/usr/bin/env python3
"""
Test MVP-Fusion with 100-page limit to match MVP-Hyper performance
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

def extract_pdf_with_100_page_limit(pdf_path):
    """Extract PDF with 100-page limit like MVP-Hyper"""
    try:
        print(f"Thread {threading.current_thread().name}: Processing {pdf_path.name}")
        
        # Open PDF
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count == 0:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": "No pages", "pages": 0}
        
        # MVP-Hyper logic: Skip if over 100 pages
        if page_count > 100:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": f"PDF has {page_count} pages (limit: 100)", "pages": 0}
        
        # Extract all pages (up to 100)
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
    """Find OSHA PDF files for testing"""
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

def test_with_100_page_limit():
    """Test with MVP-Hyper's 100-page limit"""
    
    # Get OSHA PDFs
    pdfs = find_osha_pdfs(100)
    if not pdfs:
        print("❌ No OSHA PDFs found")
        return
    
    print(f"🚀 MVP-FUSION WITH 100-PAGE LIMIT TEST")
    print(f"📁 Found {len(pdfs)} OSHA PDF files")
    
    # Analyze files to show what gets skipped vs processed
    print(f"\n📋 FILE ANALYSIS (100-page limit):")
    processed_files = 0
    skipped_files = 0
    expected_pages = 0
    
    for i, pdf in enumerate(pdfs[:20]):  # Show first 20
        try:
            doc = fitz.open(str(pdf))
            pages = len(doc)
            size = pdf.stat().st_size
            doc.close()
            
            if pages > 100:
                print(f"  {i+1}. {pdf.name}: {pages} pages - SKIP (over limit)")
                skipped_files += 1
            else:
                print(f"  {i+1}. {pdf.name}: {pages} pages - PROCESS")
                processed_files += 1
                expected_pages += pages
                
        except Exception as e:
            print(f"  {i+1}. {pdf.name}: ERROR - {e}")
    
    print(f"\n📊 EXPECTED WORKLOAD (first 20 files):")
    print(f"Files to process: {processed_files}")
    print(f"Files to skip: {skipped_files}")
    print(f"Expected pages: {expected_pages}")
    
    # Run the actual test with threading
    print(f"\n⚡ PROCESSING WITH 100-PAGE LIMIT + THREADING")
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for pdf in pdfs:
            future = executor.submit(extract_pdf_with_100_page_limit, pdf)
            futures.append(future)
        
        results = []
        for future in futures:
            results.append(future.result())
    
    end_time = time.perf_counter()
    total_time = end_time - start_time
    
    # Calculate metrics
    successful = [r for r in results if r.get("success")]
    skipped = [r for r in results if not r.get("success") and "limit: 100" in r.get("error", "")]
    errors = [r for r in results if not r.get("success") and "limit: 100" not in r.get("error", "")]
    
    total_pages = sum(r.get("pages", 0) for r in successful)
    total_text_chars = sum(r.get("text_len", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    files_per_sec = len(successful) / total_time if total_time > 0 else 0
    
    print(f"\n" + "=" * 70)
    print(f"📈 MVP-FUSION WITH 100-PAGE LIMIT RESULTS")
    print(f"=" * 70)
    
    print(f"📁 Files processed: {len(successful)}")
    print(f"🚫 Files skipped (>100 pages): {len(skipped)}")
    print(f"❌ Files with errors: {len(errors)}")
    print(f"📄 Total pages processed: {total_pages}")
    print(f"📝 Total text chars: {total_text_chars:,}")
    print(f"⏱️  Processing time: {total_time:.2f}s")
    print()
    
    print(f"🚀 PERFORMANCE METRICS:")
    print(f"   Files per second: {files_per_sec:.1f}")
    print(f"   Pages per second: {pages_per_sec:.1f}")
    print()
    
    # Compare to MVP-Hyper and previous tests
    print(f"🎯 PERFORMANCE COMPARISON:")
    print(f"   MVP-Hyper (100-page limit): 707.1 pages/sec")
    print(f"   MVP-Fusion (100-page limit): {pages_per_sec:.1f} pages/sec")
    print(f"   Our previous (all pages): 249.9 pages/sec")
    print()
    
    if pages_per_sec >= 707:
        print(f"✅ MATCHES MVP-Hyper performance!")
        improvement = ((pages_per_sec - 707) / 707) * 100
        print(f"   Improvement: +{improvement:.1f}%")
    else:
        gap = 707 - pages_per_sec
        print(f"⚠️  Gap to MVP-Hyper: {gap:.1f} pages/sec")
        print(f"   Achievement: {(pages_per_sec/707)*100:.1f}% of MVP-Hyper")
    
    # Show skipped files breakdown
    if skipped:
        print(f"\n🚫 SKIPPED FILES ANALYSIS:")
        skip_examples = skipped[:5]  # Show first 5 examples
        for skip in skip_examples:
            filename = Path(skip["file"]).name
            print(f"   {filename}: {skip['error']}")
        if len(skipped) > 5:
            print(f"   ... and {len(skipped) - 5} more files skipped")
    
    return {
        'files_per_sec': files_per_sec,
        'pages_per_sec': pages_per_sec,
        'total_files': len(successful),
        'total_pages': total_pages,
        'skipped_files': len(skipped)
    }

if __name__ == "__main__":
    try:
        results = test_with_100_page_limit()
        if results:
            print(f"\n🎯 FINAL RESULT: {results['pages_per_sec']:.1f} pages/sec (100-page limit)")
            print(f"📄 Processed: {results['total_pages']} pages from {results['total_files']} files")
            print(f"🚫 Skipped: {results['skipped_files']} large files")
    except Exception as e:
        print(f"❌ Test failed: {e}")