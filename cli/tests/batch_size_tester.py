#!/usr/bin/env python3
"""
Batch Size Tester
Tests different batch sizes to find the optimal size that doesn't cause chunk failures
"""

import subprocess
import time
from pathlib import Path
import json
import random

def test_batch_size(files, batch_size):
    """Test processing a specific batch size"""
    
    output_dir = Path(f"/tmp/batch_test_{batch_size}")
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Take a random sample of files for testing
    test_files = random.sample(files, min(batch_size, len(files)))
    
    cmd = [
        'docling',
        '--to', 'md',
        '--output', str(output_dir),
        '--device', 'cuda',
        '--num-threads', '4',
        '--page-batch-size', str(batch_size),
        '--pipeline', 'standard',
        '--pdf-backend', 'dlparse_v4'
    ]
    
    # Add files to command
    cmd.extend([str(f) for f in test_files])
    
    print(f"Testing batch size {batch_size} with {len(test_files)} files...")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
        duration = time.time() - start_time
        
        success = result.returncode == 0
        
        # Clean up
        if output_dir.exists():
            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
        
        return {
            'batch_size': batch_size,
            'files_tested': len(test_files),
            'success': success,
            'duration': duration,
            'throughput': len(test_files) / duration if success and duration > 0 else 0,
            'error_snippet': result.stderr[:300] if result.stderr else None
        }
        
    except subprocess.TimeoutExpired:
        return {
            'batch_size': batch_size,
            'files_tested': len(test_files),
            'success': False,
            'duration': 300,
            'throughput': 0,
            'error_snippet': 'Batch processing timeout after 5 minutes'
        }
    except Exception as e:
        return {
            'batch_size': batch_size,
            'files_tested': len(test_files),
            'success': False,
            'duration': 0,
            'throughput': 0,
            'error_snippet': str(e)
        }

def main():
    """Test different batch sizes to find optimal configuration"""
    
    data_dir = Path('/home/corey/projects/docling/cli/data')
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return
    
    # Get sample files (mix of different types)
    all_files = []
    for ext in ['.pdf', '.docx', '.csv', '.md', '.html']:
        files = list(data_dir.glob(f"**/*{ext}"))[:10]  # Max 10 of each type
        all_files.extend(files)
    
    if len(all_files) < 5:
        print("❌ Need at least 5 files for batch testing")
        return
    
    print(f"🧪 Testing batch processing with {len(all_files)} sample files")
    
    # Test different batch sizes
    batch_sizes = [1, 2, 3, 5, 10, 15, 20, 25, 30]  # Start small and increase
    results = []
    
    for batch_size in batch_sizes:
        if batch_size > len(all_files):
            continue
            
        result = test_batch_size(all_files, batch_size)
        results.append(result)
        
        if result['success']:
            print(f"   ✅ Batch size {batch_size}: {result['throughput']:.1f} files/sec")
        else:
            print(f"   ❌ Batch size {batch_size}: FAILED")
            break  # Stop at first failure
    
    # Analysis
    successful_results = [r for r in results if r['success']]
    
    print(f"\n📊 BATCH SIZE ANALYSIS:")
    print("=" * 50)
    
    if successful_results:
        # Find optimal batch size (best throughput)
        optimal = max(successful_results, key=lambda x: x['throughput'])
        
        print(f"✅ Working batch sizes: {[r['batch_size'] for r in successful_results]}")
        print(f"🏆 Optimal batch size: {optimal['batch_size']} ({optimal['throughput']:.1f} files/sec)")
        
        # Show performance breakdown
        print(f"\nPerformance by batch size:")
        for result in successful_results:
            print(f"   Batch {result['batch_size']:2d}: {result['throughput']:5.1f} files/sec ({result['duration']:4.1f}s)")
    
    else:
        print("❌ No batch sizes worked - try individual file processing only")
        print("💡 Set batch_size = 1 in benchmark script")
    
    # First failure analysis
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        first_failure = failed_results[0]
        print(f"\n⚠️  First failure at batch size: {first_failure['batch_size']}")
        print(f"Error: {first_failure['error_snippet'][:100]}...")
    
    # Recommendations
    print(f"\n🎯 RECOMMENDATIONS:")
    if successful_results:
        safe_batch_size = max([r['batch_size'] for r in successful_results])
        print(f"   Use batch size: {safe_batch_size} (largest working size)")
        print(f"   Or optimal size: {optimal['batch_size']} (best throughput)")
        print(f"\n💻 UPDATE BENCHMARK:")
        print(f"   config['page_batch_size'] = {safe_batch_size}")
    else:
        print("   Use individual processing: config['page_batch_size'] = 1")
        print("   Consider investigating file-specific issues")
    
    # Save results
    results_file = Path('/home/corey/projects/docling/cli/tests/batch_size_analysis.json')
    with open(results_file, 'w') as f:
        json.dump({
            'optimal_batch_size': optimal['batch_size'] if successful_results else 1,
            'max_working_batch_size': max([r['batch_size'] for r in successful_results]) if successful_results else 1,
            'all_results': results
        }, f, indent=2)
    
    print(f"\n💾 Analysis saved: {results_file}")

if __name__ == "__main__":
    main()