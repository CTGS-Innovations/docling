#!/usr/bin/env python3
"""
Test different PyMuPDF extraction methods to match MVP-Hyper performance
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

def extract_with_optimized_method(pdf_path):
    """Use MVP-Hyper's optimized extraction pattern"""
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
        
        # Try MVP-Hyper's primary method first
        try:
            all_text = []
            for i in range(page_count):
                try:
                    page = doc[i]
                    text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                    all_text.append(text or "")
                except Exception as e:
                    all_text.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
            
            full_text = '\n'.join(all_text)
            
        except Exception as text_error:
            # MVP-Hyper fallback: Use simpler method
            print(f"  Fallback extraction for {pdf_path.name}")
            try:
                all_text = []
                for i in range(page_count):
                    try:
                        page = doc[i]
                        text = page.get_text()  # Simplest method like MVP-Hyper
                        all_text.append(text or "")
                    except:
                        all_text.append(f"[Page {i+1} failed]")
                
                full_text = '\n'.join(all_text)
                
            except Exception:
                doc.close()
                return {"file": str(pdf_path), "success": False, "error": f"Text extraction failed: {str(text_error)}", "pages": 0}
        
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

def extract_simple_method_only(pdf_path):
    """Test using ONLY the simple get_text() method"""
    try:
        print(f"Thread {threading.current_thread().name}: Processing {pdf_path.name} (SIMPLE)")
        
        # Open PDF
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count == 0:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": "No pages", "pages": 0}
        
        # Skip if over 100 pages
        if page_count > 100:
            doc.close()
            return {"file": str(pdf_path), "success": False, "error": f"PDF has {page_count} pages (limit: 100)", "pages": 0}
        
        # Use ONLY simple method
        all_text = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text()  # Simple method - no flags
                all_text.append(text or "")
            except:
                all_text.append(f"[Page {i+1} failed]")
        
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

def run_extraction_comparison():
    """Compare different extraction methods"""
    
    # Get OSHA PDFs
    pdfs = find_osha_pdfs(100)
    if not pdfs:
        print("❌ No OSHA PDFs found")
        return
    
    print(f"🚀 EXTRACTION METHOD COMPARISON")
    print(f"📁 Testing on {len(pdfs)} OSHA PDF files")
    
    # Test 1: Optimized method (MVP-Hyper pattern)
    print(f"\n⚡ TEST 1: MVP-HYPER PATTERN (with fallback)")
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for pdf in pdfs:
            future = executor.submit(extract_with_optimized_method, pdf)
            futures.append(future)
        
        results1 = []
        for future in futures:
            results1.append(future.result())
    
    time1 = time.perf_counter() - start_time
    successful1 = [r for r in results1 if r.get("success")]
    pages1 = sum(r.get("pages", 0) for r in successful1)
    speed1 = pages1 / time1 if time1 > 0 else 0
    
    print(f"✅ Method 1 Results:")
    print(f"   Files: {len(successful1)}/{len(results1)}")
    print(f"   Pages: {pages1}")
    print(f"   Time: {time1:.2f}s")
    print(f"   Speed: {speed1:.1f} pages/sec")
    
    # Test 2: Simple method only
    print(f"\n⚡ TEST 2: SIMPLE METHOD ONLY (get_text())")
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = []
        for pdf in pdfs:
            future = executor.submit(extract_simple_method_only, pdf)
            futures.append(future)
        
        results2 = []
        for future in futures:
            results2.append(future.result())
    
    time2 = time.perf_counter() - start_time
    successful2 = [r for r in results2 if r.get("success")]
    pages2 = sum(r.get("pages", 0) for r in successful2)
    speed2 = pages2 / time2 if time2 > 0 else 0
    
    print(f"✅ Method 2 Results:")
    print(f"   Files: {len(successful2)}/{len(results2)}")
    print(f"   Pages: {pages2}")
    print(f"   Time: {time2:.2f}s")
    print(f"   Speed: {speed2:.1f} pages/sec")
    
    # Comparison
    print(f"\n" + "=" * 70)
    print(f"📊 EXTRACTION METHOD COMPARISON")
    print(f"=" * 70)
    
    print(f"🔬 Method Comparison:")
    print(f"   MVP-Hyper pattern: {speed1:.1f} pages/sec")
    print(f"   Simple method only: {speed2:.1f} pages/sec")
    print(f"   Difference: {speed2 - speed1:+.1f} pages/sec")
    
    if speed2 > speed1:
        improvement = ((speed2 - speed1) / speed1) * 100
        print(f"   Simple method is {improvement:.1f}% faster!")
    else:
        degradation = ((speed1 - speed2) / speed1) * 100
        print(f"   Simple method is {degradation:.1f}% slower")
    
    print(f"\n🎯 MVP-Hyper Comparison:")
    print(f"   MVP-Hyper baseline: 707.1 pages/sec")
    print(f"   Best method: {max(speed1, speed2):.1f} pages/sec")
    gap = 707.1 - max(speed1, speed2)
    print(f"   Remaining gap: {gap:.1f} pages/sec")
    
    return {
        'optimized_speed': speed1,
        'simple_speed': speed2,
        'best_speed': max(speed1, speed2)
    }

if __name__ == "__main__":
    try:
        results = run_extraction_comparison()
        if results:
            print(f"\n🎯 BEST RESULT: {results['best_speed']:.1f} pages/sec")
    except Exception as e:
        print(f"❌ Test failed: {e}")