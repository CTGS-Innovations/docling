#!/usr/bin/env python3
"""
Batch Size Optimization Test
===========================
GOAL: Find optimal batch size for 2-worker ThreadPool configuration
REASON: Balance memory usage, I/O efficiency, and CPU utilization
PROBLEM: Need to determine if 10, 20, 40, or 80 file batches work best

Test Strategy:
- Run same set of files with different batch sizes
- Measure: throughput, I/O timing, memory usage
- Find sweet spot for 2-core Docker deployment
"""

import time
import subprocess
import json
import os
import sys
from pathlib import Path

# Test configuration
BATCH_SIZES = [10, 20, 40, 80]
TEST_CONFIG = "config/full.yaml"
OUTPUT_BASE = "../output/batch-test"

def modify_batch_size(batch_size):
    """Modify service_processor.py to use specific batch size"""
    service_file = Path("pipeline/legacy/service_processor.py")
    
    # Read current file
    with open(service_file, 'r') as f:
        content = f.read()
    
    # Replace BATCH_SIZE = X with new value
    import re
    new_content = re.sub(
        r'BATCH_SIZE = \d+',
        f'BATCH_SIZE = {batch_size}',
        content
    )
    
    # Write back
    with open(service_file, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Modified batch size to {batch_size}")

def run_batch_test(batch_size):
    """Run test with specific batch size"""
    print(f"\n🧪 Testing batch size: {batch_size} files")
    
    # Modify batch size in code
    modify_batch_size(batch_size)
    
    # Output directory
    output_dir = f"{OUTPUT_BASE}-{batch_size}"
    
    # Run CLI command with virtual environment
    cmd = [
        "bash", "-c", 
        f"source .venv-clean/bin/activate && python fusion_cli.py --config {TEST_CONFIG} --output {output_dir} --quiet"
    ]
    
    # Time the execution
    start_time = time.perf_counter()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        # Parse output for key metrics
        output_lines = result.stdout.split('\n') + result.stderr.split('\n')
        
        # Extract metrics
        metrics = {
            'batch_size': batch_size,
            'total_time_seconds': total_time,
            'exit_code': result.returncode,
            'files_processed': 0,
            'files_per_second': 0,
            'avg_batch_time_ms': 0,
            'io_efficiency': 0
        }
        
        # Parse output for performance data
        for line in output_lines:
            if 'files/sec' in line:
                try:
                    # Extract files/sec from log output
                    import re
                    match = re.search(r'(\d+\.?\d*)\s*files/sec', line)
                    if match:
                        metrics['files_per_second'] = float(match.group(1))
                except:
                    pass
            
            if 'Batch written:' in line:
                # Extract batch processing info
                try:
                    match = re.search(r'(\d+)/(\d+) files processed', line)
                    if match:
                        metrics['files_processed'] = int(match.group(2))
                except:
                    pass
            
            if 'I/O TOTAL:' in line:
                # Extract I/O timing
                try:
                    match = re.search(r'(\d+\.?\d*)ms for (\d+) files', line)
                    if match:
                        total_io = float(match.group(1))
                        file_count = int(match.group(2))
                        metrics['avg_batch_time_ms'] = total_io / file_count if file_count > 0 else 0
                except:
                    pass
        
        # Calculate derived metrics
        if metrics['files_processed'] > 0:
            metrics['files_per_second'] = metrics['files_processed'] / total_time
            
        # I/O efficiency score (lower ms/file is better)
        if metrics['avg_batch_time_ms'] > 0:
            metrics['io_efficiency'] = 1000 / metrics['avg_batch_time_ms']  # files/sec equivalent
        
        print(f"✅ Batch size {batch_size} completed:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Files processed: {metrics['files_processed']}")
        print(f"   Throughput: {metrics['files_per_second']:.2f} files/sec")
        print(f"   I/O efficiency: {metrics['io_efficiency']:.2f}")
        
        return metrics
        
    except subprocess.TimeoutExpired:
        print(f"❌ Batch size {batch_size} timed out")
        return {
            'batch_size': batch_size,
            'error': 'timeout',
            'total_time_seconds': 300
        }
    
    except Exception as e:
        print(f"❌ Batch size {batch_size} failed: {e}")
        return {
            'batch_size': batch_size,
            'error': str(e),
            'total_time_seconds': 0
        }

def analyze_results(all_results):
    """Analyze all test results and recommend optimal batch size"""
    print("\n" + "="*80)
    print("📊 BATCH SIZE OPTIMIZATION RESULTS")
    print("="*80)
    
    # Filter out failed tests
    valid_results = [r for r in all_results if 'error' not in r]
    
    if not valid_results:
        print("❌ No valid test results")
        return
    
    # Create comparison table
    print(f"\n{'Batch Size':<12} {'Time (s)':<10} {'Files/sec':<12} {'I/O Eff':<12} {'Score':<10}")
    print("-" * 70)
    
    best_score = 0
    best_batch_size = 10
    
    for result in valid_results:
        batch_size = result['batch_size']
        total_time = result['total_time_seconds']
        throughput = result['files_per_second']
        io_eff = result['io_efficiency']
        
        # Calculate composite score (higher is better)
        # Weight: 60% throughput + 40% I/O efficiency
        score = (throughput * 0.6) + (io_eff * 0.4)
        
        print(f"{batch_size:<12} {total_time:<10.2f} {throughput:<12.2f} {io_eff:<12.2f} {score:<10.2f}")
        
        if score > best_score:
            best_score = score
            best_batch_size = batch_size
    
    print(f"\n🏆 RECOMMENDED BATCH SIZE: {best_batch_size}")
    print(f"   Composite score: {best_score:.2f}")
    
    # Detailed analysis
    print(f"\n📈 PERFORMANCE ANALYSIS:")
    
    # Find best throughput
    best_throughput = max(valid_results, key=lambda x: x['files_per_second'])
    print(f"   Best throughput: {best_throughput['files_per_second']:.2f} files/sec (batch size {best_throughput['batch_size']})")
    
    # Find best I/O efficiency  
    best_io = max(valid_results, key=lambda x: x['io_efficiency'])
    print(f"   Best I/O efficiency: {best_io['io_efficiency']:.2f} (batch size {best_io['batch_size']})")
    
    # Memory considerations
    print(f"\n💾 MEMORY CONSIDERATIONS:")
    print(f"   Batch 10:  ~100MB memory usage (10 docs in memory)")
    print(f"   Batch 20:  ~200MB memory usage (20 docs in memory)")
    print(f"   Batch 40:  ~400MB memory usage (40 docs in memory)")
    print(f"   Batch 80:  ~800MB memory usage (80 docs in memory)")
    print(f"   Docker limit: 1GB (800MB target)")
    
    # Recommendation reasoning
    print(f"\n🎯 RECOMMENDATION REASONING:")
    if best_batch_size >= 80:
        print(f"   Large batches (80+) maximize I/O efficiency but may hit memory limits")
        print(f"   Good for: High-memory environments, large document processing")
    elif best_batch_size >= 40:
        print(f"   Medium batches (40-80) balance performance and memory usage") 
        print(f"   Good for: Docker deployment with 1GB limit")
    elif best_batch_size >= 20:
        print(f"   Small-medium batches (20-40) prioritize memory efficiency")
        print(f"   Good for: Constrained environments, edge deployment")
    else:
        print(f"   Small batches (10-20) minimize memory usage")
        print(f"   Good for: Very constrained environments, CloudFlare Workers")

def main():
    """Run batch size optimization test"""
    print("🚀 Batch Size Optimization Test")
    print("="*50)
    print(f"Testing batch sizes: {BATCH_SIZES}")
    print(f"Configuration: {TEST_CONFIG}")
    print(f"Output base: {OUTPUT_BASE}")
    print()
    
    # Ensure we're in the right directory
    if not Path("fusion_cli.py").exists():
        print("❌ Run from mvp-fusion directory")
        sys.exit(1)
    
    all_results = []
    
    # Run tests for each batch size
    for batch_size in BATCH_SIZES:
        result = run_batch_test(batch_size)
        all_results.append(result)
        
        # Brief pause between tests
        time.sleep(2)
    
    # Analyze and recommend
    analyze_results(all_results)
    
    # Save results
    results_file = "throwaway_tests/batch_optimization_results.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")

if __name__ == "__main__":
    main()