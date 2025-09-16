#!/usr/bin/env python3
"""
PDF Performance Diagnostic - Section by Section Analysis
======================================================

Systematic analysis to find the 4x performance gap in PDF processing:
- Your MVP-Hyper: 0.011s avg per PDF (612.9 pages/sec)  
- Our Ultra-Fast-Fusion: 0.046s avg per PDF (263.5 pages/sec)

We'll test each section individually to isolate the bottleneck.
"""

import time
import sys
from pathlib import Path
from typing import List

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "../mvp-hyper/core"))

try:
    import fitz
    print("✅ PyMuPDF available")
except ImportError:
    print("❌ PyMuPDF not available")
    sys.exit(1)

def get_sample_pdfs(count=10) -> List[Path]:
    """Get sample PDF files for testing."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    pdf_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            files = list(test_dir.glob("*.pdf"))
            pdf_files.extend(files)
            if len(pdf_files) >= count:
                break
    
    return sorted(pdf_files[:count])

def diagnostic_section_1_imports():
    """Section 1: Import and initialization overhead."""
    print("\n" + "="*60)
    print("🔍 SECTION 1: IMPORTS AND INITIALIZATION")
    print("="*60)
    
    # Test 1A: Basic imports timing
    print("\n1A. Import timing test:")
    
    start = time.perf_counter()
    import fitz
    import_time = time.perf_counter() - start
    print(f"   PyMuPDF import: {import_time*1000:.3f}ms")
    
    start = time.perf_counter()
    from ultra_fast_fusion import UltraFastFusion
    our_import_time = time.perf_counter() - start
    print(f"   Our UltraFastFusion import: {our_import_time*1000:.3f}ms")
    
    # Test 1B: Class initialization timing
    print("\n1B. Class initialization timing:")
    
    start = time.perf_counter()
    fusion = UltraFastFusion({})
    our_init_time = time.perf_counter() - start
    print(f"   Our UltraFastFusion init: {our_init_time*1000:.3f}ms")
    
    return {
        'import_time': import_time * 1000,
        'our_import_time': our_import_time * 1000,
        'our_init_time': our_init_time * 1000
    }

def diagnostic_section_2_file_operations():
    """Section 2: File operations and Path handling."""
    from ultra_fast_fusion import UltraFastFusion
    print("\n" + "="*60)
    print("🔍 SECTION 2: FILE OPERATIONS")
    print("="*60)
    
    sample_pdfs = get_sample_pdfs(5)
    if not sample_pdfs:
        print("❌ No PDF files found")
        return {}
    
    sample_file = sample_pdfs[0]
    print(f"Testing with: {sample_file.name}")
    
    # Test 2A: Path operations timing
    print("\n2A. Path operations timing:")
    
    times = []
    for _ in range(100):
        start = time.perf_counter()
        file_path = Path(sample_file)
        file_ext = file_path.suffix.lower()
        file_size = file_path.stat().st_size
        file_mtime = file_path.stat().st_mtime
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)
    
    avg_path_time = sum(times) / len(times)
    print(f"   Path operations avg: {avg_path_time:.4f}ms")
    
    # Test 2B: Cache key generation timing
    print("\n2B. Cache key generation timing:")
    
    fusion = UltraFastFusion({})
    times = []
    for _ in range(100):
        start = time.perf_counter()
        cache_key = fusion._get_cache_key(sample_file)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)
    
    avg_cache_time = sum(times) / len(times)
    print(f"   Cache key generation avg: {avg_cache_time:.4f}ms")
    
    return {
        'avg_path_time': avg_path_time,
        'avg_cache_time': avg_cache_time
    }

def diagnostic_section_3_pdf_opening():
    """Section 3: PDF file opening and basic operations."""
    print("\n" + "="*60)
    print("🔍 SECTION 3: PDF OPENING AND BASIC OPS")
    print("="*60)
    
    sample_pdfs = get_sample_pdfs(10)
    if not sample_pdfs:
        print("❌ No PDF files found")
        return {}
    
    # Test 3A: Pure fitz.open timing
    print("\n3A. Pure fitz.open() timing:")
    
    open_times = []
    page_count_times = []
    close_times = []
    
    for pdf_file in sample_pdfs:
        # Test pure open
        start = time.perf_counter()
        doc = fitz.open(str(pdf_file))
        open_time = time.perf_counter() - start
        open_times.append(open_time * 1000)
        
        # Test page count
        start = time.perf_counter()
        page_count = len(doc)
        page_count_time = time.perf_counter() - start
        page_count_times.append(page_count_time * 1000)
        
        # Test close
        start = time.perf_counter()
        doc.close()
        close_time = time.perf_counter() - start
        close_times.append(close_time * 1000)
        
        print(f"   {pdf_file.name}: open={open_time*1000:.3f}ms, pages={page_count}, count={page_count_time*1000:.4f}ms, close={close_time*1000:.4f}ms")
    
    print(f"\n3A Summary:")
    print(f"   Avg open time: {sum(open_times)/len(open_times):.3f}ms")
    print(f"   Avg page count time: {sum(page_count_times)/len(page_count_times):.4f}ms") 
    print(f"   Avg close time: {sum(close_times)/len(close_times):.4f}ms")
    
    return {
        'avg_open_time': sum(open_times)/len(open_times),
        'avg_page_count_time': sum(page_count_times)/len(page_count_times),
        'avg_close_time': sum(close_times)/len(close_times)
    }

def diagnostic_section_4_text_extraction():
    """Section 4: Core text extraction methods."""
    print("\n" + "="*60)
    print("🔍 SECTION 4: TEXT EXTRACTION METHODS")
    print("="*60)
    
    sample_pdfs = get_sample_pdfs(5)
    if not sample_pdfs:
        print("❌ No PDF files found")
        return {}
    
    print("\n4A. Text extraction method comparison:")
    
    methods_results = {
        'method_1_simple': [],
        'method_2_flags': [],
        'method_3_mvp_pattern': []
    }
    
    for pdf_file in sample_pdfs:
        doc = fitz.open(str(pdf_file))
        page_count = len(doc)
        
        print(f"\n   Testing {pdf_file.name} ({page_count} pages):")
        
        # Method 1: Simple get_text()
        start = time.perf_counter()
        texts = []
        for page in doc:
            text = page.get_text()
            texts.append(text or "")
        content1 = '\n'.join(texts)
        method1_time = time.perf_counter() - start
        method1_speed = page_count / method1_time if method1_time > 0 else 0
        methods_results['method_1_simple'].append(method1_speed)
        print(f"     Method 1 (simple): {method1_time*1000:.2f}ms, {method1_speed:.1f} p/s")
        
        # Method 2: get_text with flags
        start = time.perf_counter()
        texts = []
        for page in doc:
            text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            texts.append(text or "")
        content2 = '\n'.join(texts)
        method2_time = time.perf_counter() - start
        method2_speed = page_count / method2_time if method2_time > 0 else 0
        methods_results['method_2_flags'].append(method2_speed)
        print(f"     Method 2 (flags): {method2_time*1000:.2f}ms, {method2_speed:.1f} p/s")
        
        # Method 3: MVP-Hyper pattern (direct indexing)
        start = time.perf_counter()
        texts = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                texts.append(text or "")
            except Exception as e:
                texts.append(f"[Page {i+1} failed: {str(e)[:50]}]")
        content3 = '\n'.join(texts)
        method3_time = time.perf_counter() - start
        method3_speed = page_count / method3_time if method3_time > 0 else 0
        methods_results['method_3_mvp_pattern'].append(method3_speed)
        print(f"     Method 3 (MVP): {method3_time*1000:.2f}ms, {method3_speed:.1f} p/s")
        
        doc.close()
    
    # Summary
    print(f"\n4A Summary (average across {len(sample_pdfs)} files):")
    for method, speeds in methods_results.items():
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        print(f"   {method}: {avg_speed:.1f} pages/sec")
    
    return methods_results

def diagnostic_section_5_full_pipeline():
    """Section 5: Full pipeline timing breakdown."""
    from ultra_fast_fusion import UltraFastFusion
    print("\n" + "="*60)
    print("🔍 SECTION 5: FULL PIPELINE BREAKDOWN")
    print("="*60)
    
    sample_pdfs = get_sample_pdfs(10)
    if not sample_pdfs:
        print("❌ No PDF files found")
        return {}
    
    fusion = UltraFastFusion({})
    
    print("\n5A. Our full pipeline timing breakdown:")
    
    total_times = {
        'cache_check': [],
        'file_open': [],
        'page_count': [],
        'text_extraction': [],
        'content_join': [],
        'file_close': [],
        'result_creation': [],
        'cache_store': []
    }
    
    for pdf_file in sample_pdfs:
        print(f"\n   Analyzing {pdf_file.name}:")
        
        overall_start = time.perf_counter()
        
        # Cache check
        start = time.perf_counter()
        cache_key = fusion._get_cache_key(pdf_file)
        cached = cache_key in fusion.cache
        cache_check_time = time.perf_counter() - start
        total_times['cache_check'].append(cache_check_time * 1000)
        
        # File open
        start = time.perf_counter()
        doc = fitz.open(str(pdf_file))
        file_open_time = time.perf_counter() - start
        total_times['file_open'].append(file_open_time * 1000)
        
        # Page count
        start = time.perf_counter()
        page_count = len(doc)
        page_count_time = time.perf_counter() - start
        total_times['page_count'].append(page_count_time * 1000)
        
        # Text extraction
        start = time.perf_counter()
        texts = []
        for i in range(page_count):
            try:
                page = doc[i]
                text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                texts.append(text or "")
            except Exception as e:
                texts.append(f"[Page {i+1} failed: {str(e)[:50]}]")
        text_extraction_time = time.perf_counter() - start
        total_times['text_extraction'].append(text_extraction_time * 1000)
        
        # Content join
        start = time.perf_counter()
        content = '\n'.join(texts)
        content_join_time = time.perf_counter() - start
        total_times['content_join'].append(content_join_time * 1000)
        
        # File close
        start = time.perf_counter()
        doc.close()
        file_close_time = time.perf_counter() - start
        total_times['file_close'].append(file_close_time * 1000)
        
        # Result creation
        start = time.perf_counter()
        extraction_time = time.perf_counter() - overall_start
        pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
        from ultra_fast_fusion import UltraFastResult
        result = UltraFastResult(
            file_path=str(pdf_file),
            success=True,
            text=content,
            page_count=page_count,
            extraction_time_ms=extraction_time * 1000,
            pages_per_second=pages_per_second,
            file_size_bytes=pdf_file.stat().st_size
        )
        result_creation_time = time.perf_counter() - start
        total_times['result_creation'].append(result_creation_time * 1000)
        
        # Cache store
        start = time.perf_counter()
        fusion.cache[cache_key] = {
            'text': result.text,
            'pages': result.page_count,
            'metadata': {"filename": pdf_file.name, "format": "PDF"}
        }
        cache_store_time = time.perf_counter() - start
        total_times['cache_store'].append(cache_store_time * 1000)
        
        overall_time = time.perf_counter() - overall_start
        overall_speed = page_count / overall_time if overall_time > 0 else 0
        
        print(f"     Cache check: {cache_check_time*1000:.3f}ms")
        print(f"     File open: {file_open_time*1000:.3f}ms")
        print(f"     Page count: {page_count_time*1000:.4f}ms")
        print(f"     Text extraction: {text_extraction_time*1000:.2f}ms")
        print(f"     Content join: {content_join_time*1000:.3f}ms")
        print(f"     File close: {file_close_time*1000:.4f}ms")
        print(f"     Result creation: {result_creation_time*1000:.3f}ms")
        print(f"     Cache store: {cache_store_time*1000:.3f}ms")
        print(f"     TOTAL: {overall_time*1000:.2f}ms ({overall_speed:.1f} p/s)")
    
    print(f"\n5A Summary (averages across {len(sample_pdfs)} files):")
    for component, times in total_times.items():
        avg_time = sum(times) / len(times) if times else 0
        print(f"   {component}: {avg_time:.3f}ms")
    
    total_avg = sum(sum(times) for times in total_times.values()) / len(sample_pdfs)
    print(f"   TOTAL AVERAGE: {total_avg:.2f}ms")
    
    return total_times

def main():
    """Run complete diagnostic analysis."""
    print("🚀 PDF PERFORMANCE DIAGNOSTIC")
    print("🎯 Goal: Find why our PDFs take 0.046s vs MVP-Hyper's 0.011s (4x slower)")
    print()
    
    # Run all diagnostic sections
    section1 = diagnostic_section_1_imports()
    section2 = diagnostic_section_2_file_operations() 
    section3 = diagnostic_section_3_pdf_opening()
    section4 = diagnostic_section_4_text_extraction()
    section5 = diagnostic_section_5_full_pipeline()
    
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    print("Target: Reduce per-file time from 46ms to 11ms (4x improvement needed)")
    print()
    
    if section5:
        total_times = section5
        total_avg = sum(sum(times) for times in total_times.values()) / len(list(total_times.values())[0])
        print(f"Current average time per PDF: {total_avg:.1f}ms")
        print(f"Target time per PDF: 11ms")
        print(f"Improvement needed: {total_avg/11:.1f}x")
        print()
        print("Biggest time consumers:")
        
        avg_times = {}
        for component, times in total_times.items():
            avg_times[component] = sum(times) / len(times) if times else 0
        
        sorted_components = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)
        for component, avg_time in sorted_components:
            percentage = (avg_time / total_avg) * 100 if total_avg > 0 else 0
            print(f"   {component}: {avg_time:.2f}ms ({percentage:.1f}%)")

if __name__ == "__main__":
    main()