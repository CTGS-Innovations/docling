#!/usr/bin/env python3
"""
Analyze file size distribution to understand performance bottleneck.
DELETE THIS FILE AFTER TESTING.
"""

from pathlib import Path
import os

def analyze_file_sizes():
    """Analyze the distribution of file sizes in output directory."""
    
    output_dir = Path(__file__).parent.parent / 'output'
    
    print("📊 FILE SIZE DISTRIBUTION ANALYSIS")
    print("=" * 50)
    
    # Get all markdown files with sizes
    files_data = []
    total_size = 0
    
    for md_file in output_dir.glob("*.md"):
        size_bytes = md_file.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        files_data.append((md_file.name, size_mb, size_bytes))
        total_size += size_bytes
    
    # Sort by size
    files_data.sort(key=lambda x: x[1], reverse=True)
    
    print(f"📁 Total files: {len(files_data)}")
    print(f"💾 Total size: {total_size / (1024*1024):.1f} MB")
    print(f"📊 Average size: {(total_size / len(files_data)) / (1024*1024):.2f} MB")
    
    # Show size buckets
    buckets = {
        "> 5MB": [],
        "1-5MB": [],
        "100KB-1MB": [],
        "< 100KB": []
    }
    
    for name, size_mb, size_bytes in files_data:
        if size_mb > 5:
            buckets["> 5MB"].append((name, size_mb))
        elif size_mb > 1:
            buckets["1-5MB"].append((name, size_mb))
        elif size_bytes > 100*1024:
            buckets["100KB-1MB"].append((name, size_mb))
        else:
            buckets["< 100KB"].append((name, size_mb))
    
    print("\n📈 SIZE DISTRIBUTION:")
    for bucket, files in buckets.items():
        print(f"{bucket}: {len(files)} files")
        if bucket == "> 5MB" and files:
            print("   Large files:")
            for name, size in files[:10]:  # Show top 10
                print(f"      {name} ({size:.1f}MB)")
    
    # Calculate performance impact
    large_files = buckets["> 5MB"]
    if large_files:
        total_large_size = sum(size for _, size in large_files)
        print(f"\n⚠️  PERFORMANCE IMPACT:")
        print(f"   Large files (>5MB): {len(large_files)} files, {total_large_size:.1f}MB")
        print(f"   % of total files: {len(large_files)/len(files_data)*100:.1f}%")
        print(f"   % of total data: {total_large_size/(total_size/(1024*1024))*100:.1f}%")
        
        # Estimate time impact (based on our 5.5s for 11MB test)
        # Rough estimate: 0.5 seconds per MB for large files
        estimated_large_file_time = total_large_size * 0.5
        estimated_small_file_time = (len(files_data) - len(large_files)) * 0.01  # 10ms per small file
        
        print(f"\n⏱️  TIME ESTIMATES:")
        print(f"   Large files processing time: ~{estimated_large_file_time:.0f}s")
        print(f"   Small files processing time: ~{estimated_small_file_time:.1f}s")
        print(f"   Total estimated time: ~{estimated_large_file_time + estimated_small_file_time:.0f}s")
        
        pages_per_sec = len(files_data) / (estimated_large_file_time + estimated_small_file_time)
        print(f"   Estimated performance: {pages_per_sec:.0f} files/sec")

if __name__ == "__main__":
    analyze_file_sizes()