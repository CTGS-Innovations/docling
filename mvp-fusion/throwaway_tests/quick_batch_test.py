#!/usr/bin/env python3
"""
Quick Batch Size Test
====================
GOAL: Test different batch sizes with small file set for faster results
REASON: Original test takes too long with full config initialization
PROBLEM: Need to find optimal batch size without waiting for full 675-file processing

Test small set of files with different batch sizes.
"""

import time
import subprocess
import sys
import re
from pathlib import Path

# Small test set - just a few files
BATCH_SIZES = [5, 10, 20]
TEST_FILES_DIR = "~/projects/docling/scout-docs/storage"
OUTPUT_BASE = "../output/quick-batch-test"

def modify_batch_size(batch_size):
    """Modify service_processor.py to use specific batch size"""
    service_file = Path("pipeline/legacy/service_processor.py")
    
    # Read current file
    with open(service_file, 'r') as f:
        content = f.read()
    
    # Replace BATCH_SIZE = X with new value
    new_content = re.sub(
        r'BATCH_SIZE = \d+',
        f'BATCH_SIZE = {batch_size}',
        content
    )
    
    # Write back
    with open(service_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Modified batch size to {batch_size}")

def run_quick_test(batch_size):
    """Run quick test with specific batch size"""
    print(f"\n🧪 Testing batch size: {batch_size} files")
    
    # Modify batch size in code
    modify_batch_size(batch_size)
    
    # Output directory
    output_dir = f"{OUTPUT_BASE}-{batch_size}"
    
    # Run with small directory
    cmd = [
        "bash", "-c", 
        f"source .venv-clean/bin/activate && python fusion_cli.py --directory {TEST_FILES_DIR} --output {output_dir}"
    ]
    
    # Time the execution
    start_time = time.perf_counter()
    
    try:
        print(f"🔄 Running: directory {TEST_FILES_DIR} with batch size {batch_size}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Parse results
        output_lines = result.stdout.split('\n') + result.stderr.split('\n')
        
        files_processed = 0
        batches_written = 0
        avg_batch_time = 0
        
        for line in output_lines:
            if 'Batch written:' in line:
                batches_written += 1
                # Extract progress numbers
                match = re.search(r'(\d+)/(\d+) files processed', line)
                if match:
                    files_processed = int(match.group(1))
            
            if 'I/O TOTAL:' in line:
                # Extract I/O timing per file
                match = re.search(r'(\d+\.?\d*)ms.*?(\d+) files.*?\((\d+\.?\d*)ms/file\)', line)
                if match:
                    avg_batch_time = float(match.group(3))
        
        # Calculate metrics
        throughput = files_processed / total_time if total_time > 0 else 0
        
        print(f"✅ Batch size {batch_size} results:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Files processed: {files_processed}")
        print(f"   Batches written: {batches_written}")
        print(f"   Throughput: {throughput:.2f} files/sec")
        print(f"   Avg time/file: {avg_batch_time:.1f}ms")
        
        return {
            'batch_size': batch_size,
            'total_time': total_time,
            'files_processed': files_processed,
            'batches_written': batches_written,
            'throughput': throughput,
            'avg_batch_time': avg_batch_time,
            'exit_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print(f"❌ Batch size {batch_size} timed out")
        return {'batch_size': batch_size, 'error': 'timeout'}
    
    except Exception as e:
        print(f"❌ Batch size {batch_size} failed: {e}")
        return {'batch_size': batch_size, 'error': str(e)}

def main():
    """Run quick batch size test"""
    print("🚀 Quick Batch Size Test")
    print("="*40)
    print(f"Testing batch sizes: {BATCH_SIZES}")
    print(f"Test directory: {TEST_FILES_DIR}")
    print()
    
    # Ensure we're in the right directory
    if not Path("fusion_cli.py").exists():
        print("❌ Run from mvp-fusion directory")
        sys.exit(1)
    
    results = []
    
    # Run tests for each batch size
    for batch_size in BATCH_SIZES:
        result = run_quick_test(batch_size)
        results.append(result)
        time.sleep(1)  # Brief pause
    
    # Quick analysis
    print(f"\n📊 QUICK BATCH SIZE COMPARISON")
    print("="*50)
    
    valid_results = [r for r in results if 'error' not in r and r.get('files_processed', 0) > 0]
    
    if valid_results:
        print(f"{'Size':<6} {'Time':<8} {'Files':<6} {'Batches':<8} {'Rate':<10} {'ms/file':<10}")
        print("-" * 60)
        
        best_throughput = 0
        best_batch_size = BATCH_SIZES[0]
        
        for result in valid_results:
            batch_size = result['batch_size']
            total_time = result['total_time']
            files = result['files_processed']
            batches = result['batches_written']
            rate = result['throughput']
            ms_per_file = result['avg_batch_time']
            
            print(f"{batch_size:<6} {total_time:<8.1f} {files:<6} {batches:<8} {rate:<10.2f} {ms_per_file:<10.1f}")
            
            if rate > best_throughput:
                best_throughput = rate
                best_batch_size = batch_size
        
        print(f"\n🏆 BEST BATCH SIZE: {best_batch_size}")
        print(f"   Throughput: {best_throughput:.2f} files/sec")
        
        # Memory analysis
        print(f"\n💾 MEMORY IMPACT:")
        for batch_size in BATCH_SIZES:
            memory_mb = batch_size * 10  # Rough estimate: 10MB per file in memory
            print(f"   Batch {batch_size:2d}: ~{memory_mb:3d}MB memory usage")
        
    else:
        print("❌ No valid results")
    
    print(f"\n💾 Results: {len(results)} tests completed")

if __name__ == "__main__":
    main()