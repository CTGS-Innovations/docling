#!/usr/bin/env python3
"""
Multi-Extractor Performance Test
Test different PyMuPDF extraction methods and alternative extractors
"""

import os
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

# Optimization flags
os.environ['PYTHONOPTIMIZE'] = '2'
os.environ['OMP_NUM_THREADS'] = '1'

try:
    import fitz
    HAS_PYMUPDF = True
    print(f"✅ PyMuPDF: {fitz.version}")
except ImportError:
    HAS_PYMUPDF = False
    print("❌ No PyMuPDF")

# Test alternative extractors
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
    print(f"✅ pdfplumber available")
except ImportError:
    HAS_PDFPLUMBER = False
    print("❌ pdfplumber not available")

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
    print(f"✅ PyPDF available")
except ImportError:
    HAS_PYPDF = False
    print("❌ PyPDF not available")

try:
    import pdfminer.high_level
    HAS_PDFMINER = True
    print(f"✅ pdfminer.six available")
except ImportError:
    HAS_PDFMINER = False
    print("❌ pdfminer.six not available")

def extract_pymupdf_method1(pdf_path):
    """PyMuPDF Method 1: Basic get_text()"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0, "method": "pymupdf_basic"}
        
        text_parts = []
        for i in range(page_count):
            page = doc[i]
            text = page.get_text()  # Basic method
            text_parts.append(text or "")
        
        doc.close()
        full_text = '\n'.join(text_parts)
        
        return {
            "success": True, 
            "pages": page_count, 
            "text_len": len(full_text),
            "method": "pymupdf_basic"
        }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pymupdf_basic", "error": str(e)}

def extract_pymupdf_method2(pdf_path):
    """PyMuPDF Method 2: get_text with blocks"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0, "method": "pymupdf_blocks"}
        
        text_parts = []
        for i in range(page_count):
            page = doc[i]
            blocks = page.get_text("blocks")  # Block-based extraction
            block_text = " ".join([block[4] for block in blocks if len(block) > 4])
            text_parts.append(block_text or "")
        
        doc.close()
        full_text = '\n'.join(text_parts)
        
        return {
            "success": True, 
            "pages": page_count, 
            "text_len": len(full_text),
            "method": "pymupdf_blocks"
        }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pymupdf_blocks", "error": str(e)}

def extract_pymupdf_method3(pdf_path):
    """PyMuPDF Method 3: get_text with dict"""
    try:
        doc = fitz.open(str(pdf_path))
        page_count = len(doc)
        
        if page_count > 100:
            doc.close()
            return {"success": False, "pages": 0, "method": "pymupdf_dict"}
        
        text_parts = []
        for i in range(page_count):
            page = doc[i]
            text_dict = page.get_text("dict")  # Dictionary-based extraction
            # Extract text from dict structure (simplified)
            page_text = ""
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            page_text += span.get("text", "")
            text_parts.append(page_text)
        
        doc.close()
        full_text = '\n'.join(text_parts)
        
        return {
            "success": True, 
            "pages": page_count, 
            "text_len": len(full_text),
            "method": "pymupdf_dict"
        }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pymupdf_dict", "error": str(e)}

def extract_pdfplumber(pdf_path):
    """pdfplumber extractor"""
    if not HAS_PDFPLUMBER:
        return {"success": False, "pages": 0, "method": "pdfplumber", "error": "Not available"}
    
    try:
        import pdfplumber
        
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            
            if page_count > 100:
                return {"success": False, "pages": 0, "method": "pdfplumber"}
            
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                text_parts.append(text or "")
            
            full_text = '\n'.join(text_parts)
            
            return {
                "success": True, 
                "pages": page_count, 
                "text_len": len(full_text),
                "method": "pdfplumber"
            }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pdfplumber", "error": str(e)}

def extract_pypdf(pdf_path):
    """PyPDF extractor"""
    if not HAS_PYPDF:
        return {"success": False, "pages": 0, "method": "pypdf", "error": "Not available"}
    
    try:
        from pypdf import PdfReader
        
        reader = PdfReader(str(pdf_path))
        page_count = len(reader.pages)
        
        if page_count > 100:
            return {"success": False, "pages": 0, "method": "pypdf"}
        
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            text_parts.append(text or "")
        
        full_text = '\n'.join(text_parts)
        
        return {
            "success": True, 
            "pages": page_count, 
            "text_len": len(full_text),
            "method": "pypdf"
        }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pypdf", "error": str(e)}

def extract_pdfminer(pdf_path):
    """pdfminer.six extractor"""
    if not HAS_PDFMINER:
        return {"success": False, "pages": 0, "method": "pdfminer", "error": "Not available"}
    
    try:
        import pdfminer.high_level
        
        # First check page count (using PyMuPDF for speed)
        if HAS_PYMUPDF:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            doc.close()
            
            if page_count > 100:
                return {"success": False, "pages": 0, "method": "pdfminer"}
        else:
            page_count = 1  # Assume reasonable if we can't check
        
        text = pdfminer.high_level.extract_text(str(pdf_path))
        
        return {
            "success": True, 
            "pages": page_count, 
            "text_len": len(text or ""),
            "method": "pdfminer"
        }
    except Exception as e:
        return {"success": False, "pages": 0, "method": "pdfminer", "error": str(e)}

def test_extraction_method(pdfs, method_func, method_name, max_workers=16):
    """Test a specific extraction method"""
    print(f"\n⚡ TESTING: {method_name}")
    print(f"🚀 Processing {len(pdfs)} files with {max_workers} workers")
    
    start_time = time.perf_counter()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(method_func, pdf) for pdf in pdfs]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.get("success")]
    total_pages = sum(r.get("pages", 0) for r in successful)
    total_chars = sum(r.get("text_len", 0) for r in successful)
    
    pages_per_sec = total_pages / total_time if total_time > 0 else 0
    chars_per_sec = total_chars / total_time if total_time > 0 else 0
    
    print(f"✅ {method_name} Results:")
    print(f"   Files: {len(successful)}/{len(results)}")
    print(f"   Pages: {total_pages}")
    print(f"   Characters: {total_chars:,}")
    print(f"   Time: {total_time:.3f}s")
    print(f"   📊 Speed: {pages_per_sec:.1f} pages/sec")
    print(f"   📝 Chars/sec: {chars_per_sec:,.0f}")
    
    # Show errors
    errors = [r for r in results if not r.get("success")]
    if errors:
        error_types = {}
        for error in errors:
            error_msg = error.get("error", "Unknown")[:50]
            error_types[error_msg] = error_types.get(error_msg, 0) + 1
        print(f"   ⚠️  Errors: {len(errors)} files")
        for error, count in error_types.items():
            print(f"      {error}: {count} files")
    
    return pages_per_sec, successful, total_time

def benchmark_all_extractors():
    """Benchmark all available extraction methods"""
    osha_dir = Path("../cli/data_osha")
    pdfs = list(osha_dir.glob("*.pdf"))[:50]  # Test on 50 files for speed
    
    print(f"🎯 MULTI-EXTRACTOR BENCHMARK")
    print(f"📁 Testing {len(pdfs)} OSHA PDF files")
    print(f"🎯 Target: Beat 700 pages/sec baseline")
    
    extractors = [
        (extract_pymupdf_method1, "PyMuPDF Basic"),
        (extract_pymupdf_method2, "PyMuPDF Blocks"), 
        (extract_pymupdf_method3, "PyMuPDF Dict"),
    ]
    
    # Add alternative extractors if available
    if HAS_PDFPLUMBER:
        extractors.append((extract_pdfplumber, "pdfplumber"))
    if HAS_PYPDF:
        extractors.append((extract_pypdf, "PyPDF"))
    if HAS_PDFMINER:
        extractors.append((extract_pdfminer, "pdfminer.six"))
    
    results = []
    
    for method_func, method_name in extractors:
        try:
            speed, successful, time_taken = test_extraction_method(
                pdfs, method_func, method_name, max_workers=32
            )
            
            results.append({
                'method': method_name,
                'speed': speed,
                'files': len(successful),
                'time': time_taken
            })
            
            if speed >= 2000:
                print(f"   🎉 EXTREME TARGET HIT!")
            elif speed >= 700:
                print(f"   ✅ BASELINE BEATEN! ({speed/700:.1f}x)")
            else:
                print(f"   📊 Below baseline ({speed/700:.1f}x of 700)")
                
        except Exception as e:
            print(f"   ❌ {method_name} failed: {e}")
            results.append({
                'method': method_name,
                'speed': 0,
                'files': 0,
                'time': 0,
                'error': str(e)
            })
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 MULTI-EXTRACTOR RESULTS SUMMARY")
    print(f"=" * 60)
    
    # Sort by speed
    successful_results = [r for r in results if r['speed'] > 0]
    successful_results.sort(key=lambda x: x['speed'], reverse=True)
    
    for i, result in enumerate(successful_results):
        rank = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1:2d}."
        method = result['method']
        speed = result['speed']
        vs_baseline = speed / 700
        
        print(f"{rank} {method:20s}: {speed:8.1f} pages/sec ({vs_baseline:.1f}x baseline)")
    
    if successful_results:
        best = successful_results[0]
        print(f"\n🏆 WINNER: {best['method']} at {best['speed']:.1f} pages/sec")
        
        if best['speed'] >= 2000:
            print("🎉 EXTREME TARGET ACHIEVED!")
        elif best['speed'] >= 700:
            print("✅ BASELINE CRUSHED!")
        else:
            print("⚙️  All methods below baseline - need more optimization")
    
    return successful_results

if __name__ == "__main__":
    print("🔥 MULTI-EXTRACTOR PERFORMANCE TEST")
    print("🎯 Finding the fastest PDF text extraction method")
    
    try:
        results = benchmark_all_extractors()
        
        if results:
            best_method = results[0]
            print(f"\n🏁 RECOMMENDATION: Use {best_method['method']}")
            print(f"🚀 Performance: {best_method['speed']:.1f} pages/sec")
            
            if best_method['speed'] >= 700:
                improvement = ((best_method['speed'] - 700) / 700) * 100
                print(f"📈 Improvement over baseline: +{improvement:.1f}%")
        else:
            print("\n❌ No extractors succeeded")
            
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()