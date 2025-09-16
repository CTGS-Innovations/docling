#!/usr/bin/env python3
"""
Performance test for UltraFastFusion against MVP-Hyper baseline.
Target: Beat MVP-Hyper's 700+ pages/sec baseline, achieve 1000+ pages/sec.
"""

import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import statistics

# Add ultra_fast_fusion to path
sys.path.insert(0, str(Path(__file__).parent))

from ultra_fast_fusion import UltraFastFusion

def get_test_files() -> List[Path]:
    """Get all PDF files from test directories."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    pdf_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            pdf_files.extend(list(test_dir.glob("*.pdf")))
    
    return sorted(pdf_files)

def run_performance_test() -> Dict:
    """Run comprehensive performance test."""
    print("🚀 ULTRA FAST FUSION PERFORMANCE TEST")
    print("=" * 60)
    
    # Get test files
    test_files = get_test_files()
    if not test_files:
        print("❌ No PDF files found in test directories")
        return {}
    
    print(f"📁 Found {len(test_files)} PDF files to process")
    
    # Initialize UltraFastFusion with optimal config
    config = {
        'performance': {
            'max_workers': 8,  # Optimal for most systems
            'memory_pool_mb': 512,  # Generous memory pool
            'cache_size': 1000,  # Large cache
        },
        'processing': {
            'enable_flpc': True,  # Use Rust engine if available
            'batch_size': 32  # Optimal batch size
        }
    }
    
    print("\n🔧 INITIALIZATION PHASE (Setup-once architecture)")
    init_start = time.perf_counter()
    
    fusion = UltraFastFusion(config)
    
    init_time = time.perf_counter() - init_start
    print(f"✅ Initialization completed in {init_time:.3f}s")
    
    # Performance test with multiple runs for statistical accuracy
    print("\n⚡ PROCESSING PHASE (Ultra-light per-file processing)")
    print("-" * 40)
    
    run_times = []
    file_counts = []
    
    # Run 1 iteration with fresh fusion instance each time for accurate measurement
    for run_num in range(1, 4):
        # Create fresh instance to avoid cache effects
        fusion = UltraFastFusion(config)
        print(f"\n🏃 Run {run_num}/3")
        
        start_time = time.perf_counter()
        processed_files = 0
        successful_extractions = 0
        
        # Process files in batches
        batch_size = config['processing']['batch_size']
        for i in range(0, len(test_files), batch_size):
            batch = test_files[i:i + batch_size]
            
            for file_path in batch:
                try:
                    result = fusion.extract_document(file_path)
                    processed_files += 1
                    
                    if result.success and result.text:
                        successful_extractions += 1
                        
                except Exception as e:
                    print(f"⚠️  Error processing {file_path.name}: {e}")
        
        end_time = time.perf_counter()
        run_time = end_time - start_time
        run_times.append(run_time)
        file_counts.append(processed_files)
        
        files_per_sec = processed_files / run_time
        success_rate = (successful_extractions / processed_files) * 100 if processed_files > 0 else 0
        
        print(f"   📊 Processed: {processed_files} files")
        print(f"   ✅ Successful: {successful_extractions} ({success_rate:.1f}%)")
        print(f"   ⏱️  Time: {run_time:.2f}s")
        print(f"   🚀 Speed: {files_per_sec:.1f} files/sec")
    
    # Calculate statistics
    avg_time = statistics.mean(run_times)
    avg_files = statistics.mean(file_counts)
    avg_speed = avg_files / avg_time
    
    print("\n" + "=" * 60)
    print("📈 PERFORMANCE RESULTS")
    print("=" * 60)
    
    print(f"🎯 Target Performance: 700+ files/sec (MVP-Hyper baseline)")
    print(f"🚀 Goal Performance: 1000+ files/sec")
    print()
    print(f"📊 Average Results (3 runs):")
    print(f"   Files processed: {avg_files:.0f}")
    print(f"   Processing time: {avg_time:.2f}s")
    print(f"   Performance: {avg_speed:.1f} files/sec")
    print()
    
    # Performance analysis
    baseline_speed = 700  # MVP-Hyper baseline
    improvement_factor = avg_speed / baseline_speed
    
    if avg_speed >= 1000:
        print(f"🎉 EXCELLENT: {improvement_factor:.1f}x faster than baseline!")
        print(f"✅ Achieved target goal of 1000+ files/sec")
    elif avg_speed >= baseline_speed:
        print(f"✅ GOOD: {improvement_factor:.1f}x faster than baseline")
        print(f"🎯 Met MVP-Hyper baseline performance")
    else:
        print(f"⚠️  NEEDS WORK: {improvement_factor:.1f}x of baseline performance")
        print(f"❌ Did not meet MVP-Hyper baseline")
    
    # Architecture benefits
    setup_overhead_per_file = init_time / len(test_files)
    print(f"\n🏗️  ARCHITECTURE BENEFITS:")
    print(f"   Setup-once overhead: {setup_overhead_per_file*1000:.2f}ms per file")
    print(f"   vs Per-file setup: ~50-100ms per file (old pipeline)")
    
    return {
        'avg_speed': avg_speed,
        'improvement_factor': improvement_factor,
        'init_time': init_time,
        'avg_processing_time': avg_time,
        'files_processed': avg_files
    }

if __name__ == "__main__":
    try:
        results = run_performance_test()
        
        if results:
            print(f"\n🎯 SUMMARY: {results['avg_speed']:.1f} files/sec")
            print(f"   ({results['improvement_factor']:.1f}x MVP-Hyper baseline)")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)