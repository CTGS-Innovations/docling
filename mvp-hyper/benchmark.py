#!/usr/bin/env python3
"""
Ultra-Performance Benchmark
===========================
Test harness to verify 1000+ pages/second target
"""

import time
import psutil
import statistics
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
import multiprocessing as mp

from mvp_hyper_core import UltraFastExtractor, HyperBatchProcessor


class UltraBenchmark:
    """Benchmark suite for ultra-high-performance testing."""
    
    def __init__(self, test_dir: Path = None):
        self.test_dir = test_dir or Path('/home/corey/projects/docling/cli/data')
        self.results = []
        
    def run_speed_test(self, num_files: int = 10) -> Dict:
        """Run speed test on sample files."""
        
        print("🚀 ULTRA-PERFORMANCE BENCHMARK")
        print("=" * 60)
        print(f"Target: 1,000+ pages/second")
        print(f"CPUs: {mp.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        print("=" * 60)
        
        # Find test PDFs
        pdf_files = list(self.test_dir.glob("**/*.pdf"))[:num_files]
        
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return {}
        
        print(f"\n📁 Testing with {len(pdf_files)} files")
        
        # Test different configurations
        configs = [
            ("Single Worker", 1),
            ("Half CPUs", mp.cpu_count() // 2),
            ("All CPUs", mp.cpu_count()),
            ("Oversubscribed", mp.cpu_count() * 2)
        ]
        
        best_config = None
        best_speed = 0
        
        for config_name, num_workers in configs:
            print(f"\n📊 Testing: {config_name} ({num_workers} workers)")
            print("-" * 40)
            
            extractor = UltraFastExtractor(num_workers=num_workers)
            
            # Warm-up run
            if len(pdf_files) > 0:
                _ = extractor.extract_pdf_ultrafast(pdf_files[0])
            
            # Timed run
            start_time = time.perf_counter()
            results = []
            total_pages = 0
            
            for pdf_file in pdf_files:
                result = extractor.extract_pdf_ultrafast(pdf_file)
                results.append(result)
                if result.success:
                    total_pages += result.page_count
            
            total_time = time.perf_counter() - start_time
            
            # Calculate metrics
            pages_per_second = total_pages / total_time if total_time > 0 else 0
            files_per_second = len(pdf_files) / total_time if total_time > 0 else 0
            
            # Individual file speeds
            file_speeds = [r.pages_per_second for r in results if r.success]
            
            config_result = {
                "config": config_name,
                "workers": num_workers,
                "files_processed": len(pdf_files),
                "total_pages": total_pages,
                "total_time": total_time,
                "pages_per_second": pages_per_second,
                "files_per_second": files_per_second,
                "avg_file_speed": statistics.mean(file_speeds) if file_speeds else 0,
                "median_file_speed": statistics.median(file_speeds) if file_speeds else 0,
                "max_file_speed": max(file_speeds) if file_speeds else 0,
                "min_file_speed": min(file_speeds) if file_speeds else 0
            }
            
            self.results.append(config_result)
            
            # Print results
            print(f"  Total pages: {total_pages}")
            print(f"  Total time: {total_time:.2f}s")
            print(f"  Pages/second: {pages_per_second:.1f}")
            print(f"  Files/second: {files_per_second:.1f}")
            
            if pages_per_second >= 1000:
                print(f"  ✅ TARGET ACHIEVED!")
            elif pages_per_second >= 500:
                print(f"  🔶 Good performance (50% of target)")
            elif pages_per_second >= 100:
                print(f"  ⚡ Acceptable (10% of target)")
            else:
                print(f"  ⚠️  Below expectations")
            
            if pages_per_second > best_speed:
                best_speed = pages_per_second
                best_config = config_name
            
            extractor.shutdown()
        
        # Batch processing test
        print("\n🎯 BATCH PROCESSING TEST")
        print("-" * 40)
        
        processor = HyperBatchProcessor(num_extractors=4)
        stats = processor.process_directory(self.test_dir.parent, "*.pdf")
        
        print(f"  Batch pages/second: {stats['pages_per_second']:.1f}")
        print(f"  Batch files/second: {stats['files_per_second']:.1f}")
        
        processor.shutdown()
        
        # Summary
        print("\n" + "="*60)
        print("📈 BENCHMARK SUMMARY")
        print("="*60)
        print(f"Best configuration: {best_config}")
        print(f"Best speed: {best_speed:.1f} pages/second")
        
        if best_speed >= 1000:
            print("\n🎉 SUCCESS: 1000+ pages/second achieved!")
        else:
            shortfall = 1000 - best_speed
            print(f"\n📊 Current: {best_speed:.1f} pages/sec")
            print(f"   Target: 1000 pages/sec")
            print(f"   Gap: {shortfall:.1f} pages/sec")
            print(f"   Achievement: {(best_speed/1000)*100:.1f}%")
        
        # Save detailed results
        self._save_results()
        
        return {
            "best_config": best_config,
            "best_speed": best_speed,
            "target_achieved": best_speed >= 1000,
            "all_results": self.results
        }
    
    def run_stress_test(self, duration_seconds: int = 60):
        """Run sustained stress test."""
        
        print(f"\n⚡ STRESS TEST ({duration_seconds} seconds)")
        print("=" * 60)
        
        pdf_files = list(self.test_dir.glob("**/*.pdf"))
        if not pdf_files:
            print("No files for stress test")
            return
        
        extractor = UltraFastExtractor(num_workers=mp.cpu_count())
        
        start_time = time.perf_counter()
        end_time = start_time + duration_seconds
        
        total_pages = 0
        total_files = 0
        speeds = []
        
        print("Running... (Press Ctrl+C to stop)")
        
        try:
            while time.perf_counter() < end_time:
                for pdf_file in pdf_files:
                    if time.perf_counter() >= end_time:
                        break
                    
                    result = extractor.extract_pdf_ultrafast(pdf_file)
                    if result.success:
                        total_pages += result.page_count
                        total_files += 1
                        speeds.append(result.pages_per_second)
                    
                    # Print progress every 10 files
                    if total_files % 10 == 0:
                        elapsed = time.perf_counter() - start_time
                        current_speed = total_pages / elapsed
                        print(f"  [{total_files} files, {total_pages} pages] "
                              f"Speed: {current_speed:.1f} pages/sec")
        
        except KeyboardInterrupt:
            print("\nStopped by user")
        
        finally:
            extractor.shutdown()
        
        total_time = time.perf_counter() - start_time
        avg_speed = total_pages / total_time if total_time > 0 else 0
        
        print("\n" + "-"*40)
        print(f"Stress Test Results:")
        print(f"  Duration: {total_time:.1f}s")
        print(f"  Files processed: {total_files}")
        print(f"  Pages processed: {total_pages}")
        print(f"  Average speed: {avg_speed:.1f} pages/sec")
        print(f"  Peak speed: {max(speeds):.1f} pages/sec" if speeds else "N/A")
        print(f"  Sustained 1000+ pages/sec: {'Yes ✅' if avg_speed >= 1000 else 'No ❌'}")
    
    def _save_results(self):
        """Save benchmark results to file."""
        
        output_file = Path(f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(output_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "cpus": mp.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3)
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_file}")


def main():
    """Run benchmark suite."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultra-performance benchmark")
    parser.add_argument("--test-dir", type=Path, 
                       default=Path('/home/corey/projects/docling/cli/data'),
                       help="Directory with test PDFs")
    parser.add_argument("--num-files", type=int, default=10,
                       help="Number of files to test")
    parser.add_argument("--stress", action="store_true",
                       help="Run stress test")
    parser.add_argument("--duration", type=int, default=60,
                       help="Stress test duration in seconds")
    
    args = parser.parse_args()
    
    benchmark = UltraBenchmark(args.test_dir)
    
    # Run speed test
    results = benchmark.run_speed_test(args.num_files)
    
    # Run stress test if requested
    if args.stress:
        benchmark.run_stress_test(args.duration)
    
    # Performance recommendations
    if results.get("best_speed", 0) < 1000:
        print("\n💡 PERFORMANCE RECOMMENDATIONS:")
        print("-" * 40)
        print("1. Ensure PyMuPDF is compiled with optimizations")
        print("2. Use NVMe SSD for test files")
        print("3. Disable CPU frequency scaling")
        print("4. Increase system file descriptor limits")
        print("5. Use tmpfs/ramdisk for ultra-fast I/O")
        print("6. Consider GPU-accelerated PDF libraries")
        print("7. Profile with 'perf' to find bottlenecks")


if __name__ == "__main__":
    main()