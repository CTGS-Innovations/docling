#!/usr/bin/env python3
"""
Step-by-Step Comparison: Ultra-Fast-Fusion vs MVP-Hyper
======================================================

Direct comparison of every single step to find hidden overhead:
- Telemetry/logging
- Extra metric gathering  
- Additional processing steps
- Memory allocations
- Any other hidden overhead
"""

import time
import sys
from pathlib import Path
import logging
from typing import List

# Add paths
sys.path.insert(0, str(Path(__file__).parent))

try:
    import fitz
    print("✅ PyMuPDF available")
except ImportError:
    print("❌ PyMuPDF not available")
    sys.exit(1)

def get_sample_pdf() -> Path:
    """Get one sample PDF for testing."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    for test_dir in test_dirs:
        if test_dir.exists():
            pdfs = list(test_dir.glob("*.pdf"))
            if pdfs:
                return pdfs[0]
    
    raise FileNotFoundError("No PDF files found")

def test_mvp_hyper_steps():
    """Test MVP-Hyper's exact steps with timing."""
    print("\n" + "="*60)
    print("🎯 MVP-HYPER EXACT STEPS")
    print("="*60)
    
    sample_pdf = get_sample_pdf()
    print(f"Testing: {sample_pdf.name}")
    
    overall_start = time.perf_counter()
    
    # Step 1: MVP-Hyper file path handling
    print("\nStep 1: File path handling")
    step_start = time.perf_counter()
    file_path = Path(sample_pdf)
    file_ext = file_path.suffix.lower()
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 2: Cache key generation (MVP-Hyper style)
    print("\nStep 2: Cache key generation")
    step_start = time.perf_counter()
    import hashlib
    h = hashlib.blake2b()
    key_string = f"{file_path.absolute()}_{file_path.stat().st_mtime}"
    h.update(key_string.encode())
    cache_key = h.hexdigest()
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 3: Cache check (empty cache)
    print("\nStep 3: Cache check")
    step_start = time.perf_counter()
    cache = {}
    cached_result = cache.get(cache_key)
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 4: PDF opening
    print("\nStep 4: PDF opening")
    step_start = time.perf_counter()
    doc = fitz.open(str(file_path))
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 5: Page count
    print("\nStep 5: Page count")
    step_start = time.perf_counter()
    page_count = len(doc)
    step_time = time.perf_counter() - step_start
    print(f"   Pages: {page_count}, Time: {step_time*1000:.4f}ms")
    
    # Step 6: Text extraction (MVP-Hyper _extract_sequential_safe)
    print("\nStep 6: Text extraction (MVP-Hyper pattern)")
    step_start = time.perf_counter()
    texts = []
    for i in range(page_count):
        try:
            page = doc[i]
            text = page.get_text("text", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            texts.append(text or "")
        except Exception as e:
            texts.append(f"[Page {i+1} extraction failed: {str(e)[:50]}]")
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 7: Text joining
    print("\nStep 7: Text joining")
    step_start = time.perf_counter()
    content = '\n'.join(texts)
    step_time = time.perf_counter() - step_start
    print(f"   Content length: {len(content)}, Time: {step_time*1000:.4f}ms")
    
    # Step 8: Metadata creation (MVP-Hyper minimal)
    print("\nStep 8: Metadata creation")
    step_start = time.perf_counter()
    metadata = {
        "filename": file_path.name,
        "format": "PDF",
        "pages": page_count,
        "size_bytes": file_path.stat().st_size
    }
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 9: File closing
    print("\nStep 9: File closing")
    step_start = time.perf_counter()
    doc.close()
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 10: Result creation (MVP-Hyper style)
    print("\nStep 10: Result creation")
    step_start = time.perf_counter()
    extraction_time = time.perf_counter() - overall_start
    pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
    
    # MVP-Hyper result structure (simplified)
    result = {
        'file_path': str(file_path),
        'success': True,
        'text': content,
        'page_count': page_count,
        'extraction_time': extraction_time,
        'pages_per_second': pages_per_second,
        'metadata': metadata
    }
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 11: Cache storage
    print("\nStep 11: Cache storage")
    step_start = time.perf_counter()
    cache[cache_key] = {
        'text': content,
        'pages': page_count,
        'metadata': metadata
    }
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    total_time = time.perf_counter() - overall_start
    print(f"\n🎯 MVP-HYPER TOTAL: {total_time*1000:.2f}ms ({pages_per_second:.1f} p/s)")
    
    return total_time, pages_per_second

def test_our_fusion_steps():
    """Test our Ultra-Fast-Fusion's exact steps with timing."""
    print("\n" + "="*60)
    print("🚀 OUR ULTRA-FAST-FUSION STEPS")
    print("="*60)
    
    from ultra_fast_fusion import UltraFastFusion
    
    sample_pdf = get_sample_pdf()
    print(f"Testing: {sample_pdf.name}")
    
    overall_start = time.perf_counter()
    
    # Step 0: Fusion initialization (this might be hidden overhead!)
    print("\nStep 0: Fusion initialization")
    step_start = time.perf_counter()
    fusion = UltraFastFusion({})
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 1: extract_document call overhead
    print("\nStep 1: extract_document() call setup")
    step_start = time.perf_counter()
    file_path = Path(sample_pdf)
    start_time = time.perf_counter()  # This is what our method does
    file_ext = file_path.suffix.lower()
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 2: Cache key generation (our method)
    print("\nStep 2: Our cache key generation")
    step_start = time.perf_counter()
    cache_key = fusion._get_cache_key(file_path)
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 3: Cache check (our method)
    print("\nStep 3: Our cache check")
    step_start = time.perf_counter()
    cached = cache_key in fusion.cache
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 4: Route to _extract_pdf
    print("\nStep 4: Route to _extract_pdf")
    step_start = time.perf_counter()
    # This is just the if statement routing
    will_extract_pdf = (file_ext == '.pdf')
    step_time = time.perf_counter() - step_start
    print(f"   Will extract PDF: {will_extract_pdf}, Time: {step_time*1000:.4f}ms")
    
    # Step 5: _extract_pdf method call overhead
    print("\nStep 5: _extract_pdf method call setup")
    step_start = time.perf_counter()
    # Check HAS_PYMUPDF (this is in our method)
    has_pymupdf = True  # We know it's available
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 6: PDF opening (our method)
    print("\nStep 6: Our PDF opening")
    step_start = time.perf_counter()
    doc = fitz.open(str(file_path))
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 7: Page count (our method)
    print("\nStep 7: Our page count")
    step_start = time.perf_counter()
    page_count = len(doc)
    step_time = time.perf_counter() - step_start
    print(f"   Pages: {page_count}, Time: {step_time*1000:.4f}ms")
    
    # Step 8: Text extraction (our method - should be identical)
    print("\nStep 8: Our text extraction")
    step_start = time.perf_counter()
    text = fusion._extract_sequential_safe(doc, page_count)
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 9: File closing (our method)
    print("\nStep 9: Our file closing")
    step_start = time.perf_counter()
    doc.close()
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 10: Result creation (our UltraFastResult)
    print("\nStep 10: Our result creation")
    step_start = time.perf_counter()
    extraction_time = time.perf_counter() - overall_start
    pages_per_second = page_count / extraction_time if extraction_time > 0 else 0
    
    from ultra_fast_fusion import UltraFastResult
    result = UltraFastResult(
        file_path=str(file_path),
        success=True,
        text=text,
        page_count=page_count,
        extraction_time_ms=extraction_time * 1000,
        pages_per_second=pages_per_second,
        file_size_bytes=file_path.stat().st_size
    )
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    # Step 11: Cache storage (our method)
    print("\nStep 11: Our cache storage")
    step_start = time.perf_counter()
    fusion.cache[cache_key] = {
        'text': result.text,
        'pages': result.page_count,
        'metadata': {"filename": file_path.name, "format": "PDF"}
    }
    step_time = time.perf_counter() - step_start
    print(f"   Time: {step_time*1000:.4f}ms")
    
    total_time = time.perf_counter() - overall_start
    print(f"\n🚀 OUR FUSION TOTAL: {total_time*1000:.2f}ms ({pages_per_second:.1f} p/s)")
    
    return total_time, pages_per_second

def test_comprehensive_vs_individual():
    """Test the difference between comprehensive test approach and individual calls."""
    print("\n" + "="*60)
    print("🔍 COMPREHENSIVE TEST vs INDIVIDUAL CALLS")
    print("="*60)
    
    from ultra_fast_fusion import UltraFastFusion
    
    # Get 10 sample PDFs
    test_dirs = [Path("../cli/data"), Path("../cli/data_complex"), Path("../cli/data_osha")]
    pdf_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            pdf_files.extend(list(test_dir.glob("*.pdf"))[:10])
        if len(pdf_files) >= 10:
            break
    pdf_files = pdf_files[:10]
    
    print(f"Testing with {len(pdf_files)} PDFs")
    
    # Test 1: Individual calls (like diagnostic)
    print("\n🔬 Test 1: Individual calls (diagnostic style)")
    fusion = UltraFastFusion({})
    
    individual_times = []
    individual_start = time.perf_counter()
    
    for pdf_file in pdf_files:
        file_start = time.perf_counter()
        result = fusion.extract_document(pdf_file)
        file_time = time.perf_counter() - file_start
        individual_times.append(file_time * 1000)
        print(f"   {pdf_file.name}: {file_time*1000:.2f}ms")
    
    individual_total = time.perf_counter() - individual_start
    individual_avg = sum(individual_times) / len(individual_times)
    
    print(f"   Individual avg: {individual_avg:.2f}ms")
    print(f"   Total time: {individual_total*1000:.2f}ms")
    
    # Test 2: Comprehensive test style (with progress tracking, stats, etc.)
    print("\n📊 Test 2: Comprehensive test style")
    
    # Create fresh fusion instance
    fusion2 = UltraFastFusion({})
    
    comprehensive_start = time.perf_counter()
    
    # Simulate comprehensive test overhead
    results = []
    successful_extractions = 0
    total_pages = 0
    individual_speeds = []
    
    for i, pdf_file in enumerate(pdf_files):
        try:
            file_start = time.perf_counter()
            result = fusion2.extract_document(pdf_file)
            file_time = time.perf_counter() - file_start
            
            results.append(result)
            
            if result.success and result.text:
                successful_extractions += 1
                total_pages += result.page_count
                individual_speeds.append(result.pages_per_second)
                
            # Simulate progress tracking overhead
            if (i + 1) % 5 == 0:
                import statistics
                if individual_speeds:
                    avg_speed_so_far = statistics.mean(individual_speeds)
                    # This print might cause overhead!
                    pass  # print(f"  Processed {i+1} files, avg speed: {avg_speed_so_far:.1f} p/s")
                
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {e}")
    
    comprehensive_total = time.perf_counter() - comprehensive_start
    comprehensive_avg = (comprehensive_total * 1000) / len(pdf_files)
    
    print(f"   Comprehensive avg: {comprehensive_avg:.2f}ms per file")
    print(f"   Total time: {comprehensive_total*1000:.2f}ms")
    
    # Compare
    print(f"\n📊 COMPARISON:")
    print(f"   Individual calls avg: {individual_avg:.2f}ms per file")
    print(f"   Comprehensive test avg: {comprehensive_avg:.2f}ms per file") 
    print(f"   Difference: {comprehensive_avg - individual_avg:.2f}ms ({(comprehensive_avg/individual_avg):.2f}x)")
    
    if comprehensive_avg > individual_avg:
        overhead = comprehensive_avg - individual_avg
        print(f"   🚨 FOUND OVERHEAD: {overhead:.2f}ms per file in comprehensive approach!")
    
    return individual_avg, comprehensive_avg

def main():
    """Run complete step-by-step comparison."""
    print("🔍 STEP-BY-STEP PERFORMANCE COMPARISON")
    print("🎯 Goal: Find hidden overhead causing 4x slowdown")
    print()
    
    # Test MVP-Hyper steps
    mvp_time, mvp_speed = test_mvp_hyper_steps()
    
    # Test our fusion steps
    our_time, our_speed = test_our_fusion_steps()
    
    # Test comprehensive vs individual
    individual_avg, comprehensive_avg = test_comprehensive_vs_individual()
    
    print("\n" + "="*60)
    print("📊 FINAL COMPARISON")
    print("="*60)
    
    print(f"MVP-Hyper pattern: {mvp_time*1000:.2f}ms ({mvp_speed:.1f} p/s)")
    print(f"Our Fusion pattern: {our_time*1000:.2f}ms ({our_speed:.1f} p/s)")
    
    if our_time > mvp_time:
        overhead = (our_time - mvp_time) * 1000
        factor = our_time / mvp_time
        print(f"🚨 Our method is {overhead:.2f}ms slower ({factor:.2f}x)")
    else:
        print(f"✅ Our method is faster!")
    
    print(f"\nDiagnostic individual calls: {individual_avg:.2f}ms per file")
    print(f"Comprehensive test calls: {comprehensive_avg:.2f}ms per file")
    
    if comprehensive_avg > individual_avg:
        test_overhead = comprehensive_avg - individual_avg
        print(f"🚨 Test methodology overhead: {test_overhead:.2f}ms per file")
        print(f"   This could explain the 46ms vs 8ms discrepancy!")

if __name__ == "__main__":
    main()