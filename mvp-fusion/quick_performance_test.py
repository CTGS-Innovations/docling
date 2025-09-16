#!/usr/bin/env python3
"""
Quick performance test for UltraFastFusion - Small subset for rapid iteration.
"""

import time
import sys
from pathlib import Path
from typing import Dict, List
import statistics

# Add ultra_fast_fusion to path
sys.path.insert(0, str(Path(__file__).parent))

from ultra_fast_fusion import UltraFastFusion

def get_test_files(limit: int = 20) -> List[Path]:
    """Get limited set of PDF files for quick testing."""
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

def quick_performance_test() -> Dict:
    """Run quick performance test with small file set."""
    print("⚡ QUICK PERFORMANCE TEST - UltraFastFusion")
    print("=" * 50)
    
    # Get small test set
    test_files = get_test_files(20)
    if not test_files:
        print("❌ No PDF files found")
        return {}
    
    print(f"📁 Testing with {len(test_files)} PDF files")
    
    # Optimal config for performance
    config = {
        'performance': {
            'max_workers': 8,
            'memory_pool_mb': 512,
            'cache_size': 100,  # Smaller cache for testing
        }
    }
    
    print("\n🔧 INITIALIZATION")
    init_start = time.perf_counter()
    fusion = UltraFastFusion(config)
    init_time = time.perf_counter() - init_start
    print(f"✅ Init: {init_time:.3f}s")
    
    # Single accurate run
    print("\n⚡ PROCESSING")
    start_time = time.perf_counter()
    
    processed_files = 0
    successful_extractions = 0
    total_pages = 0
    
    for file_path in test_files:
        try:
            result = fusion.extract_document(file_path)
            processed_files += 1
            
            if result.success and result.text:
                successful_extractions += 1
                total_pages += result.page_count
                print(f"✅ {file_path.name}: {result.page_count} pages, {result.pages_per_second:.1f} p/s")
            else:
                print(f"❌ {file_path.name}: {result.error or 'Unknown error'}")
                
        except Exception as e:
            print(f"⚠️  {file_path.name}: {e}")
    
    end_time = time.perf_counter()
    processing_time = end_time - start_time
    
    # Calculate metrics
    files_per_sec = processed_files / processing_time
    pages_per_sec = total_pages / processing_time
    success_rate = (successful_extractions / processed_files) * 100 if processed_files > 0 else 0
    
    print(f"\n📊 RESULTS")
    print(f"   Files: {successful_extractions}/{processed_files} ({success_rate:.1f}%)")
    print(f"   Pages: {total_pages}")
    print(f"   Time: {processing_time:.2f}s")
    print(f"   Speed: {files_per_sec:.1f} files/sec, {pages_per_sec:.1f} pages/sec")
    
    # Compare to baseline
    baseline_pages_per_sec = 700
    if pages_per_sec >= baseline_pages_per_sec:
        improvement = pages_per_sec / baseline_pages_per_sec
        print(f"🎉 SUCCESS: {improvement:.1f}x baseline performance!")
    else:
        ratio = pages_per_sec / baseline_pages_per_sec
        print(f"⚠️  BELOW BASELINE: {ratio:.1f}x baseline performance")
    
    return {
        'files_per_sec': files_per_sec,
        'pages_per_sec': pages_per_sec,
        'success_rate': success_rate,
        'processing_time': processing_time
    }

if __name__ == "__main__":
    try:
        results = quick_performance_test()
        if results:
            print(f"\n🎯 QUICK TEST: {results['pages_per_sec']:.1f} pages/sec")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)