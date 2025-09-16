#!/usr/bin/env python3
"""
Test MVP-Hyper compatible version vs our current implementation.
"""

import time
import sys
from pathlib import Path
from typing import List
import statistics

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from ultra_fast_fusion import UltraFastFusion
from mvp_hyper_compatible import MVPHyperCompatible

def get_test_files(limit: int = 20) -> List[Path]:
    """Get limited set of PDF files for testing."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    pdf_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            files = list(test_dir.glob("*.pdf"))[:limit//len(test_dirs)+1]
            pdf_files.extend(files)
            if len(pdf_files) >= limit:
                break
    
    return sorted(pdf_files[:limit])

def test_both_implementations():
    """Compare our implementation vs MVP-Hyper compatible."""
    
    test_files = get_test_files(20)
    if not test_files:
        print("❌ No PDF files found")
        return
    
    print("⚡ MVP-HYPER COMPATIBILITY TEST")
    print(f"📁 Testing with {len(test_files)} files")
    print("=" * 60)
    
    # Test 1: Our current UltraFastFusion
    print("\n🚀 TEST 1: Current UltraFastFusion")
    config = {
        'performance': {
            'max_workers': 8,
            'memory_pool_mb': 512,
            'cache_size': 100,
        }
    }
    
    init_start = time.perf_counter()
    fusion = UltraFastFusion(config)
    init_time = time.perf_counter() - init_start
    print(f"Init: {init_time:.3f}s")
    
    start_time = time.perf_counter()
    results1 = []
    for file_path in test_files:
        result = fusion.extract_document(file_path)
        results1.append(result)
    
    time1 = time.perf_counter() - start_time
    successful1 = [r for r in results1 if r.success and r.text]
    total_pages1 = sum(r.page_count for r in successful1)
    pages_per_sec1 = total_pages1 / time1 if time1 > 0 else 0
    
    print(f"Results: {len(successful1)}/{len(results1)} successful")
    print(f"Pages: {total_pages1}, Time: {time1:.3f}s")
    print(f"Performance: {pages_per_sec1:.1f} pages/sec")
    
    # Test 2: MVP-Hyper Compatible
    print("\n🎯 TEST 2: MVP-Hyper Compatible")
    
    init_start = time.perf_counter()
    mvp_fusion = MVPHyperCompatible(num_workers=8)
    init_time = time.perf_counter() - init_start
    print(f"Init: {init_time:.3f}s")
    
    start_time = time.perf_counter()
    results2 = []
    for file_path in test_files:
        result = mvp_fusion.extract_document(file_path)
        results2.append(result)
    
    time2 = time.perf_counter() - start_time
    successful2 = [r for r in results2 if r.success and r.text]
    total_pages2 = sum(r.page_count for r in successful2)
    pages_per_sec2 = total_pages2 / time2 if time2 > 0 else 0
    
    print(f"Results: {len(successful2)}/{len(results2)} successful")
    print(f"Pages: {total_pages2}, Time: {time2:.3f}s")
    print(f"Performance: {pages_per_sec2:.1f} pages/sec")
    
    # Compare
    print("\n" + "=" * 60)
    print("📊 COMPARISON")
    print("=" * 60)
    
    baseline = 700  # MVP-Hyper target
    
    print(f"Current UltraFastFusion: {pages_per_sec1:.1f} pages/sec ({pages_per_sec1/baseline:.2f}x baseline)")
    print(f"MVP-Hyper Compatible:   {pages_per_sec2:.1f} pages/sec ({pages_per_sec2/baseline:.2f}x baseline)")
    
    improvement = pages_per_sec2 / pages_per_sec1 if pages_per_sec1 > 0 else 0
    print(f"Improvement factor: {improvement:.2f}x")
    
    if pages_per_sec2 >= baseline:
        print(f"🎉 MVP-Hyper Compatible MEETS baseline!")
    else:
        gap = baseline - pages_per_sec2
        print(f"⚠️  Still {gap:.1f} pages/sec short of baseline")
    
    # Individual file comparison
    print(f"\n🔍 INDIVIDUAL FILE ANALYSIS:")
    speeds1 = [r.pages_per_second for r in results1 if r.success]
    speeds2 = [r.pages_per_second for r in results2 if r.success]
    
    if speeds1 and speeds2:
        print(f"Current - Avg: {statistics.mean(speeds1):.1f}, Max: {max(speeds1):.1f}")
        print(f"Compatible - Avg: {statistics.mean(speeds2):.1f}, Max: {max(speeds2):.1f}")

if __name__ == "__main__":
    test_both_implementations()