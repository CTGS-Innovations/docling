#!/usr/bin/env python3
"""
Batch Processing Analysis - Find the Real Bottleneck
==================================================

Compare batch processing approaches to find why our batch performance 
drops to 263.5 pages/sec (46ms per file) vs individual 287+ pages/sec (6.97ms).

Your MVP-Hyper batch: 612.9 pages/sec (11ms per file)  
Our batch: 263.5 pages/sec (46ms per file)
Gap: 2.3x slower in batch mode
"""

import time
import sys
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor
import threading

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

try:
    import fitz
    print("✅ PyMuPDF available")
except ImportError:
    print("❌ PyMuPDF not available")
    sys.exit(1)

def get_batch_pdfs(count=50) -> List[Path]:
    """Get batch of PDF files for testing."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    pdf_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            pdf_files.extend(list(test_dir.glob("*.pdf")))
        if len(pdf_files) >= count:
            break
    
    return sorted(pdf_files[:count])

def test_sequential_processing():
    """Test pure sequential processing (no threading)."""
    print("\n" + "="*60)
    print("🔄 SEQUENTIAL PROCESSING TEST")
    print("="*60)
    
    from ultra_fast_fusion import UltraFastFusion
    
    pdf_files = get_batch_pdfs(50)
    print(f"Testing {len(pdf_files)} PDFs sequentially")
    
    fusion = UltraFastFusion({})
    
    start_time = time.perf_counter()
    results = []
    total_pages = 0
    
    for i, pdf_file in enumerate(pdf_files):
        result = fusion.extract_document(pdf_file)
        results.append(result)
        if result.success:
            total_pages += result.page_count
        
        # Progress every 10 files
        if (i + 1) % 10 == 0:
            elapsed = time.perf_counter() - start_time
            files_per_sec = (i + 1) / elapsed
            pages_per_sec = total_pages / elapsed
            print(f"   Progress: {i+1}/{len(pdf_files)}, {files_per_sec:.1f} files/s, {pages_per_sec:.1f} pages/s")
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.success]
    
    files_per_sec = len(successful) / total_time
    pages_per_sec = total_pages / total_time
    avg_time_per_file = (total_time * 1000) / len(pdf_files)
    
    print(f"\n📊 Sequential Results:")
    print(f"   Files: {len(successful)}/{len(pdf_files)} successful")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg per file: {avg_time_per_file:.1f}ms")
    print(f"   Files/sec: {files_per_sec:.1f}")
    print(f"   Pages/sec: {pages_per_sec:.1f}")
    
    return pages_per_sec, avg_time_per_file

def test_threaded_processing():
    """Test our current threaded processing approach."""
    print("\n" + "="*60)
    print("🧵 THREADED PROCESSING TEST")
    print("="*60)
    
    from ultra_fast_fusion import UltraFastFusion
    
    pdf_files = get_batch_pdfs(50)
    print(f"Testing {len(pdf_files)} PDFs with threading")
    
    fusion = UltraFastFusion({'performance': {'max_workers': 8}})
    
    start_time = time.perf_counter()
    
    # Use our process_batch method
    results = fusion.process_batch(pdf_files)
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r.success]
    total_pages = sum(r.page_count for r in successful)
    
    files_per_sec = len(successful) / total_time
    pages_per_sec = total_pages / total_time
    avg_time_per_file = (total_time * 1000) / len(pdf_files)
    
    print(f"\n📊 Threaded Results:")
    print(f"   Files: {len(successful)}/{len(pdf_files)} successful")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg per file: {avg_time_per_file:.1f}ms")
    print(f"   Files/sec: {files_per_sec:.1f}")
    print(f"   Pages/sec: {pages_per_sec:.1f}")
    
    return pages_per_sec, avg_time_per_file

def test_mvp_hyper_style_processing():
    """Test MVP-Hyper style batch processing."""
    print("\n" + "="*60)
    print("🎯 MVP-HYPER STYLE PROCESSING")
    print("="*60)
    
    pdf_files = get_batch_pdfs(50)
    print(f"Testing {len(pdf_files)} PDFs with MVP-Hyper approach")
    
    def extract_single_pdf_mvp_style(file_path):
        """Extract single PDF using MVP-Hyper exact approach."""
        try:
            start_time = time.perf_counter()
            
            # MVP-Hyper style extraction
            doc = fitz.open(str(file_path))
            page_count = len(doc)
            
            if page_count == 0:
                doc.close()
                return None
            
            # MVP-Hyper _extract_sequential_safe
            texts = []
            for i in range(page_count):
                try:
                    page = doc[i]
                    text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                    texts.append(text or "")
                except Exception as e:
                    texts.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
            
            content = '\n'.join(texts)
            doc.close()
            
            extraction_time = time.perf_counter() - start_time
            pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
            
            return {
                'file_path': str(file_path),
                'success': True,
                'text': content,
                'page_count': page_count,
                'extraction_time': extraction_time,
                'pages_per_second': pages_per_second
            }
            
        except Exception as e:
            return {
                'file_path': str(file_path),
                'success': False,
                'error': str(e),
                'page_count': 0,
                'extraction_time': 0,
                'pages_per_second': 0
            }
    
    start_time = time.perf_counter()
    
    # Use ThreadPoolExecutor like MVP-Hyper does
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(extract_single_pdf_mvp_style, pdf) for pdf in pdf_files]
        results = [future.result() for future in futures]
    
    total_time = time.perf_counter() - start_time
    successful = [r for r in results if r and r['success']]
    total_pages = sum(r['page_count'] for r in successful)
    
    files_per_sec = len(successful) / total_time
    pages_per_sec = total_pages / total_time
    avg_time_per_file = (total_time * 1000) / len(pdf_files)
    
    print(f"\n📊 MVP-Hyper Style Results:")
    print(f"   Files: {len(successful)}/{len(pdf_files)} successful")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg per file: {avg_time_per_file:.1f}ms")
    print(f"   Files/sec: {files_per_sec:.1f}")
    print(f"   Pages/sec: {pages_per_sec:.1f}")
    
    return pages_per_sec, avg_time_per_file

def test_minimal_overhead_processing():
    """Test with absolute minimal overhead."""
    print("\n" + "="*60)
    print("⚡ MINIMAL OVERHEAD PROCESSING")
    print("="*60)
    
    pdf_files = get_batch_pdfs(50)
    print(f"Testing {len(pdf_files)} PDFs with minimal overhead")
    
    def minimal_extract(file_path):
        """Absolute minimal extraction."""
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        
        texts = []
        for i in range(page_count):
            page = doc[i]
            text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            texts.append(text or "")
        
        content = '\n'.join(texts)
        doc.close()
        
        return {'page_count': page_count, 'text': content}
    
    start_time = time.perf_counter()
    
    # Minimal processing
    results = []
    total_pages = 0
    
    for pdf_file in pdf_files:
        try:
            result = minimal_extract(pdf_file)
            results.append(result)
            total_pages += result['page_count']
        except Exception as e:
            results.append({'page_count': 0, 'error': str(e)})
    
    total_time = time.perf_counter() - start_time
    
    files_per_sec = len(results) / total_time
    pages_per_sec = total_pages / total_time
    avg_time_per_file = (total_time * 1000) / len(pdf_files)
    
    print(f"\n📊 Minimal Overhead Results:")
    print(f"   Files: {len(results)} processed")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Avg per file: {avg_time_per_file:.1f}ms")
    print(f"   Files/sec: {files_per_sec:.1f}")
    print(f"   Pages/sec: {pages_per_sec:.1f}")
    
    return pages_per_sec, avg_time_per_file

def test_cache_overhead():
    """Test if caching is causing batch slowdown."""
    print("\n" + "="*60)
    print("💾 CACHE OVERHEAD TEST")
    print("="*60)
    
    from ultra_fast_fusion import UltraFastFusion
    
    pdf_files = get_batch_pdfs(30)
    print(f"Testing cache effects with {len(pdf_files)} PDFs")
    
    # Test 1: With cache
    print("\n🔄 Test 1: With caching enabled")
    fusion_cached = UltraFastFusion({})
    
    start_time = time.perf_counter()
    results_cached = []
    for pdf_file in pdf_files:
        result = fusion_cached.extract_document(pdf_file)
        results_cached.append(result)
    
    cached_time = time.perf_counter() - start_time
    cached_pages = sum(r.page_count for r in results_cached if r.success)
    cached_pages_per_sec = cached_pages / cached_time
    print(f"   With cache: {cached_pages_per_sec:.1f} pages/sec")
    
    # Test 2: Without cache (fresh instance each time)
    print("\n🔄 Test 2: Fresh instance per file (no cache)")
    
    start_time = time.perf_counter()
    results_no_cache = []
    for pdf_file in pdf_files:
        fresh_fusion = UltraFastFusion({})  # Fresh instance = no cache
        result = fresh_fusion.extract_document(pdf_file)
        results_no_cache.append(result)
    
    no_cache_time = time.perf_counter() - start_time
    no_cache_pages = sum(r.page_count for r in results_no_cache if r.success)
    no_cache_pages_per_sec = no_cache_pages / no_cache_time
    print(f"   Without cache: {no_cache_pages_per_sec:.1f} pages/sec")
    
    print(f"\n📊 Cache Impact:")
    if cached_pages_per_sec > no_cache_pages_per_sec:
        improvement = cached_pages_per_sec / no_cache_pages_per_sec
        print(f"   Cache helps: {improvement:.2f}x faster")
    else:
        slowdown = no_cache_pages_per_sec / cached_pages_per_sec
        print(f"   🚨 Cache hurts: {slowdown:.2f}x slower")
    
    return cached_pages_per_sec, no_cache_pages_per_sec

def main():
    """Run complete batch processing analysis."""
    print("🔍 BATCH PROCESSING ANALYSIS")
    print("🎯 Goal: Close the gap from 263.5 to 612.9 pages/sec")
    print("📊 Target: Match MVP-Hyper's 11ms per file in batch mode")
    print()
    
    # Run all batch tests
    sequential_speed, sequential_time = test_sequential_processing()
    threaded_speed, threaded_time = test_threaded_processing()
    mvp_speed, mvp_time = test_mvp_hyper_style_processing()
    minimal_speed, minimal_time = test_minimal_overhead_processing()
    cached_speed, no_cache_speed = test_cache_overhead()
    
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING COMPARISON")
    print("="*60)
    
    target_speed = 612.9  # Your MVP-Hyper baseline
    target_time = 11      # ms per file
    
    print(f"🎯 Target (MVP-Hyper batch): {target_speed:.1f} pages/sec ({target_time}ms per file)")
    print()
    print(f"📊 Our Results:")
    print(f"   Sequential: {sequential_speed:.1f} pages/sec ({sequential_time:.1f}ms per file)")
    print(f"   Threaded: {threaded_speed:.1f} pages/sec ({threaded_time:.1f}ms per file)")
    print(f"   MVP-Style: {mvp_speed:.1f} pages/sec ({mvp_time:.1f}ms per file)")
    print(f"   Minimal: {minimal_speed:.1f} pages/sec ({minimal_time:.1f}ms per file)")
    print(f"   Cached: {cached_speed:.1f} pages/sec")
    print(f"   No Cache: {no_cache_speed:.1f} pages/sec")
    print()
    
    # Find best approach
    best_speed = max(sequential_speed, threaded_speed, mvp_speed, minimal_speed)
    if best_speed >= target_speed:
        improvement = best_speed / target_speed
        print(f"🎉 SUCCESS: Best approach achieves {improvement:.2f}x target!")
    else:
        gap = target_speed / best_speed
        print(f"⚠️  GAP: Need {gap:.2f}x improvement to match target")
        print(f"   Best: {best_speed:.1f} pages/sec vs target {target_speed:.1f} pages/sec")
    
    # Identify best method
    methods = [
        ("Sequential", sequential_speed),
        ("Threaded", threaded_speed), 
        ("MVP-Style", mvp_speed),
        ("Minimal", minimal_speed)
    ]
    
    best_method = max(methods, key=lambda x: x[1])
    print(f"🏆 Best performing method: {best_method[0]} ({best_method[1]:.1f} pages/sec)")

if __name__ == "__main__":
    main()