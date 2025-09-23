#!/usr/bin/env python3
"""
Pipeline Performance Comparison - Real vs Optimized
===================================================

GOAL: Compare your actual pipeline performance with optimized sidecar
REASON: Show real-world impact of optimized document processing  
PROBLEM: Demonstrate speedup using your actual test files

This compares your 2892ms result with optimized processing.
"""

import sys
import time
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_optimized_pipeline():
    """Run the same files through optimized processing."""
    print("🚀 Running Optimized Pipeline on Your Test Files")
    print("=" * 60)
    
    # Use same directory as your pipeline
    data_dir = Path("/home/corey/projects/docling/cli/data_complex")
    
    if not data_dir.exists():
        print(f"❌ Directory not found: {data_dir}")
        return
    
    # Find all files (same as your pipeline)
    files = []
    for pattern in ['*.pdf', '*.txt', '*.md']:
        files.extend(data_dir.rglob(pattern))  # Recursive search
    
    print(f"📁 Found {len(files)} files (matching your pipeline):")
    total_size = 0
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        total_size += size_mb
        print(f"   • {f.name} ({size_mb:.1f} MB)")
    
    print(f"📊 Total size: {total_size:.1f} MB")
    
    # Import optimized processor
    sys.path.insert(0, str(Path(__file__).parent.parent / 'pipeline'))
    from optimized_doc_processor import OptimizedDocProcessor
    
    # Run optimized processing
    config = {'optimization_level': 'maximum'}
    processor = OptimizedDocProcessor(config)
    
    start_time = time.perf_counter()
    result = processor.process(files, {'output_dir': '/tmp'})
    total_time = (time.perf_counter() - start_time) * 1000
    
    print(f"\n🎯 OPTIMIZED PIPELINE RESULTS:")
    print(f"=" * 60)
    
    if result.success:
        print(f"✅ **SUCCESS**: Processing completed")
        print(f"⏱️  **TIMING**: {result.timing_ms:.2f}ms")
        print(f"📊 **FILES**: {result.data['processed_files']} processed")
        print(f"📈 **SIZE**: {result.data['total_size_bytes'] / (1024*1024):.1f} MB")
        
        # Compare with your actual pipeline results
        your_time_ms = 2892.83  # From your output
        speedup = your_time_ms / result.timing_ms if result.timing_ms > 0 else 0
        time_saved = your_time_ms - result.timing_ms
        
        print(f"\n📊 COMPARISON WITH YOUR ACTUAL PIPELINE:")
        print(f"   🐌 **YOUR CURRENT**: {your_time_ms:.2f}ms")  
        print(f"   🚀 **OPTIMIZED**: {result.timing_ms:.2f}ms")
        print(f"   ⚡ **SPEEDUP**: {speedup:.1f}x faster")
        print(f"   💾 **TIME SAVED**: -{time_saved:.2f}ms ({time_saved/1000:.2f} seconds)")
        
        # Performance per file
        if len(files) > 0:
            your_per_file = your_time_ms / len(files)
            optimized_per_file = result.timing_ms / len(files)
            print(f"\n📋 PER-FILE PERFORMANCE:")
            print(f"   • Your current: {your_per_file:.2f}ms per file")
            print(f"   • Optimized: {optimized_per_file:.2f}ms per file")
            print(f"   • Improvement: {your_per_file/optimized_per_file:.1f}x faster per file")
        
        # Show what this means for larger batches
        if len(files) > 0:
            print(f"\n🔮 SCALING IMPACT:")
            files_10 = 10
            files_100 = 100  
            files_1000 = 1000
            
            current_10 = (your_time_ms / len(files)) * files_10 / 1000
            optimized_10 = (result.timing_ms / len(files)) * files_10 / 1000
            
            current_100 = (your_time_ms / len(files)) * files_100 / 1000  
            optimized_100 = (result.timing_ms / len(files)) * files_100 / 1000
            
            current_1000 = (your_time_ms / len(files)) * files_1000 / 1000
            optimized_1000 = (result.timing_ms / len(files)) * files_1000 / 1000
            
            if optimized_10 > 0:
                print(f"   • 10 files: {current_10:.1f}s → {optimized_10:.1f}s ({current_10/optimized_10:.0f}x faster)")
                print(f"   • 100 files: {current_100:.1f}s → {optimized_100:.1f}s ({current_100/optimized_100:.0f}x faster)")
                print(f"   • 1000 files: {current_1000:.0f}s → {optimized_1000:.1f}s ({current_1000/optimized_1000:.0f}x faster)")
            else:
                print(f"   • Optimized processing is near-instantaneous for all file counts")
        
    else:
        print(f"❌ **FAILED**: {result.error}")

if __name__ == "__main__":
    run_optimized_pipeline()