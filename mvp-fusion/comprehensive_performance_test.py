#!/usr/bin/env python3
"""
Comprehensive performance test across all available files.
"""

import time
import sys
from pathlib import Path
from typing import List
import statistics

# Add ultra_fast_fusion to path
sys.path.insert(0, str(Path(__file__).parent))

from ultra_fast_fusion import UltraFastFusion

def get_all_test_files() -> List[Path]:
    """Get ALL files from test directories (not just PDFs) to match MVP-Hyper."""
    test_dirs = [
        Path("../cli/data"),
        Path("../cli/data_complex"), 
        Path("../cli/data_osha")
    ]
    
    all_files = []
    for test_dir in test_dirs:
        if test_dir.exists():
            # Get ALL files recursively like MVP-Hyper does
            for file_path in test_dir.rglob("*"):
                if file_path.is_file():
                    all_files.append(file_path)
    
    return sorted(all_files)

def comprehensive_test():
    """Run comprehensive test on all available files."""
    
    # Get all files
    all_files = get_all_test_files()
    if not all_files:
        print("❌ No files found")
        return
    
    print(f"🚀 COMPREHENSIVE PERFORMANCE TEST")
    print(f"📁 Found {len(all_files)} files (ALL file types)")
    
    # Optimal config for performance
    config = {
        'performance': {
            'max_workers': 8,
            'memory_pool_mb': 512,
            'cache_size': 100,
        }
    }
    
    # Initialize once
    print("\n🔧 INITIALIZATION")
    init_start = time.perf_counter()
    fusion = UltraFastFusion(config)
    init_time = time.perf_counter() - init_start
    print(f"✅ Init: {init_time:.3f}s")
    
    # Process all files
    print(f"\n⚡ PROCESSING {len(all_files)} FILES")
    start_time = time.perf_counter()
    
    results = []
    total_pages = 0
    successful_extractions = 0
    individual_speeds = []
    
    for i, file_path in enumerate(all_files):
        try:
            file_start = time.perf_counter()
            result = fusion.extract_document(file_path)
            file_time = time.perf_counter() - file_start
            
            results.append(result)
            
            if result.success and result.text:
                successful_extractions += 1
                total_pages += result.page_count
                individual_speeds.append(result.pages_per_second)
                
                # Show progress every 50 files
                if (i + 1) % 50 == 0:
                    avg_speed_so_far = statistics.mean(individual_speeds) if individual_speeds else 0
                    print(f"  📊 Processed {i+1}/{len(all_files)} files, avg speed so far: {avg_speed_so_far:.1f} p/s")
            else:
                print(f"❌ {file_path.name}: {result.error or 'Unknown error'}")
                
        except Exception as e:
            print(f"⚠️  Error processing {file_path.name}: {e}")
    
    end_time = time.perf_counter()
    total_processing_time = end_time - start_time
    
    # Calculate comprehensive metrics
    files_per_sec = len(results) / total_processing_time
    pages_per_sec = total_pages / total_processing_time
    success_rate = (successful_extractions / len(results)) * 100 if results else 0
    
    # Detailed file type analysis
    file_type_stats = {}
    for i, result in enumerate(results):
        if result.success:
            file_path = Path(result.file_path)
            ext = file_path.suffix.lower()
            
            if ext not in file_type_stats:
                file_type_stats[ext] = {
                    'files': 0,
                    'total_time': 0,
                    'total_pages': 0
                }
            
            file_type_stats[ext]['files'] += 1
            file_type_stats[ext]['total_time'] += result.extraction_time_ms / 1000  # Convert to seconds
            file_type_stats[ext]['total_pages'] += result.page_count
    
    print(f"\n" + "=" * 70)
    print(f"📈 COMPREHENSIVE RESULTS")
    print(f"=" * 70)
    
    print(f"📁 Files processed: {len(results)}")
    print(f"✅ Successful extractions: {successful_extractions} ({success_rate:.1f}%)")
    print(f"📄 Total pages: {total_pages}")
    print(f"⏱️  Processing time: {total_processing_time:.2f}s")
    print()
    
    print(f"🚀 PERFORMANCE METRICS:")
    print(f"   Files per second: {files_per_sec:.1f}")
    print(f"   Pages per second: {pages_per_sec:.1f}")
    print()
    
    if individual_speeds:
        avg_individual = statistics.mean(individual_speeds)
        median_individual = statistics.median(individual_speeds)
        max_individual = max(individual_speeds)
        min_individual = min(individual_speeds)
        
        print(f"📊 INDIVIDUAL FILE SPEEDS:")
        print(f"   Average: {avg_individual:.1f} pages/sec")
        print(f"   Median:  {median_individual:.1f} pages/sec") 
        print(f"   Max:     {max_individual:.1f} pages/sec")
        print(f"   Min:     {min_individual:.1f} pages/sec")
        print()
    
    # Compare to baseline
    baseline_pages_per_sec = 700
    improvement_factor = pages_per_sec / baseline_pages_per_sec
    
    print(f"🎯 BASELINE COMPARISON:")
    print(f"   Target: {baseline_pages_per_sec} pages/sec (MVP-Hyper)")
    print(f"   Actual: {pages_per_sec:.1f} pages/sec")
    print(f"   Factor: {improvement_factor:.2f}x baseline")
    print()
    
    if pages_per_sec >= baseline_pages_per_sec:
        print(f"🎉 SUCCESS: Exceeded baseline performance!")
    else:
        gap = baseline_pages_per_sec - pages_per_sec
        print(f"⚠️  GAP: Need {gap:.1f} more pages/sec to reach baseline")
        
        # Analysis
        print(f"\n🔍 PERFORMANCE ANALYSIS:")
        if individual_speeds:
            fast_files = [s for s in individual_speeds if s >= baseline_pages_per_sec]
            slow_files = [s for s in individual_speeds if s < baseline_pages_per_sec]
            
            print(f"   Fast files (>= {baseline_pages_per_sec} p/s): {len(fast_files)}/{len(individual_speeds)} ({len(fast_files)/len(individual_speeds)*100:.1f}%)")
            print(f"   Slow files (< {baseline_pages_per_sec} p/s): {len(slow_files)}/{len(individual_speeds)} ({len(slow_files)/len(individual_speeds)*100:.1f}%)")
            
            if slow_files:
                print(f"   Avg slow file speed: {statistics.mean(slow_files):.1f} p/s")
    
    # Performance by file type (MVP-Hyper format)
    print(f"\n📊 PERFORMANCE BY FILE TYPE:")
    print(f"  Top time consumers:")
    
    # Sort by total time descending
    sorted_file_types = sorted(file_type_stats.items(), 
                               key=lambda x: x[1]['total_time'], 
                               reverse=True)
    
    for ext, stats in sorted_file_types:
        files_count = stats['files']
        total_time = stats['total_time']
        total_pages = stats['total_pages']
        avg_time = total_time / files_count if files_count > 0 else 0
        pages_per_sec = total_pages / total_time if total_time > 0 else 0
        
        print(f"    {ext}: {files_count} files, {total_time:.2f}s total, {avg_time:.3f}s avg, {pages_per_sec:.1f} pages/sec")
    
    # Find fastest and slowest
    if sorted_file_types:
        fastest = min(sorted_file_types, key=lambda x: x[1]['total_time'] / x[1]['files'] if x[1]['files'] > 0 else float('inf'))
        slowest = max(sorted_file_types, key=lambda x: x[1]['total_time'] / x[1]['files'] if x[1]['files'] > 0 else 0)
        
        fastest_avg = fastest[1]['total_time'] / fastest[1]['files'] if fastest[1]['files'] > 0 else 0
        slowest_avg = slowest[1]['total_time'] / slowest[1]['files'] if slowest[1]['files'] > 0 else 0
        
        print(f"\n  🚀 Fastest: {fastest[0]} ({fastest_avg:.3f}s avg)")
        print(f"  🐌 Slowest: {slowest[0]} ({slowest_avg:.3f}s avg)")
    
    print(f"\n📊 Current: {pages_per_sec:.1f} pages/sec (Target: 1000)")
    
    return {
        'files_per_sec': files_per_sec,
        'pages_per_sec': pages_per_sec,
        'success_rate': success_rate,
        'total_files': len(results),
        'total_pages': total_pages,
        'file_type_stats': file_type_stats
    }

if __name__ == "__main__":
    try:
        results = comprehensive_test()
        if results:
            print(f"\n🎯 FINAL RESULT: {results['pages_per_sec']:.1f} pages/sec on {results['total_files']} files")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)