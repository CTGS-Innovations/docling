#!/usr/bin/env python3
"""
CPU Utilization Diagnostic
===========================
GOAL: Identify why CPU utilization is low and cores aren't fully utilized  
REASON: User observes CPU bouncing between cores, not reaching 80% utilization
PROBLEM: Sequential processing uses 1 core, ThreadPool had 1,887ms overhead

Evidence-based analysis to optimize CPU utilization vs I/O bottlenecks.
"""

import time
import threading
import psutil
import multiprocessing
import concurrent.futures
import os
from pathlib import Path

def get_cpu_affinity():
    """Get current process CPU affinity"""
    try:
        return psutil.Process().cpu_affinity()
    except:
        return "Unknown"

def monitor_cpu_utilization(duration_seconds=10, sample_interval=0.1):
    """Monitor CPU utilization during processing"""
    print(f"🔍 Monitoring CPU utilization for {duration_seconds}s...")
    
    samples = []
    start_time = time.time()
    
    while time.time() - start_time < duration_seconds:
        # Per-core utilization
        per_cpu = psutil.cpu_percent(interval=None, percpu=True)
        overall = psutil.cpu_percent(interval=None)
        
        samples.append({
            'timestamp': time.time() - start_time,
            'overall': overall,
            'per_core': per_cpu
        })
        
        time.sleep(sample_interval)
    
    return samples

def cpu_intensive_task(task_id, work_duration=0.1):
    """Simulate CPU-intensive work (like entity extraction)"""
    start = time.perf_counter()
    
    # Get current thread/process info
    thread_name = threading.current_thread().name
    process_id = os.getpid()
    
    # Simulate computational work
    result = 0
    target_time = start + work_duration
    
    while time.perf_counter() < target_time:
        # Simulate entity extraction workload
        for i in range(1000):
            result += i * 0.001
    
    end = time.perf_counter()
    
    return {
        'task_id': task_id,
        'thread_name': thread_name,
        'process_id': process_id,
        'duration_ms': (end - start) * 1000,
        'result': result
    }

def test_sequential_processing(num_tasks=20):
    """Test sequential processing (current approach)"""
    print("🔄 Testing Sequential Processing (1 core)")
    print(f"CPU Affinity: {get_cpu_affinity()}")
    
    # Start CPU monitoring in background
    cpu_monitor = []
    monitor_thread = threading.Thread(
        target=lambda: cpu_monitor.extend(monitor_cpu_utilization(3)),
        daemon=True
    )
    monitor_thread.start()
    
    start_time = time.perf_counter()
    results = []
    
    for i in range(num_tasks):
        result = cpu_intensive_task(i, 0.1)  # 100ms per task
        results.append(result)
    
    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    
    # Wait for monitoring to complete
    monitor_thread.join(timeout=1)
    
    return {
        'approach': 'Sequential',
        'total_time_ms': total_time,
        'tasks': len(results),
        'avg_per_task_ms': total_time / len(results),
        'cpu_samples': cpu_monitor,
        'theoretical_speedup': 'N/A (single core)'
    }

def test_threadpool_processing(num_tasks=20, max_workers=2):
    """Test ThreadPool processing (parallel approach)"""
    print(f"⚡ Testing ThreadPool Processing ({max_workers} workers)")
    print(f"CPU Affinity: {get_cpu_affinity()}")
    
    # Start CPU monitoring in background  
    cpu_monitor = []
    monitor_thread = threading.Thread(
        target=lambda: cpu_monitor.extend(monitor_cpu_utilization(3)),
        daemon=True
    )
    monitor_thread.start()
    
    start_time = time.perf_counter()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(cpu_intensive_task, i, 0.1) for i in range(num_tasks)]
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    
    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    
    # Wait for monitoring to complete
    monitor_thread.join(timeout=1)
    
    return {
        'approach': f'ThreadPool-{max_workers}',
        'total_time_ms': total_time,
        'tasks': len(results),
        'avg_per_task_ms': total_time / len(results),
        'cpu_samples': cpu_monitor,
        'theoretical_speedup': f'{max_workers}x'
    }

def test_process_pool_processing(num_tasks=20, max_workers=2):
    """Test ProcessPool processing (true parallelism)"""
    print(f"🚀 Testing ProcessPool Processing ({max_workers} workers)")
    print(f"CPU Affinity: {get_cpu_affinity()}")
    
    # Start CPU monitoring in background
    cpu_monitor = []
    monitor_thread = threading.Thread(
        target=lambda: cpu_monitor.extend(monitor_cpu_utilization(3)),
        daemon=True
    )
    monitor_thread.start()
    
    start_time = time.perf_counter()
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = [executor.submit(cpu_intensive_task, i, 0.1) for i in range(num_tasks)]
        
        # Collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    
    end_time = time.perf_counter()
    total_time = (end_time - start_time) * 1000
    
    # Wait for monitoring to complete
    monitor_thread.join(timeout=1)
    
    return {
        'approach': f'ProcessPool-{max_workers}',
        'total_time_ms': total_time,
        'tasks': len(results),
        'avg_per_task_ms': total_time / len(results),
        'cpu_samples': cpu_monitor,
        'theoretical_speedup': f'{max_workers}x'
    }

def analyze_cpu_utilization(cpu_samples, approach_name):
    """Analyze CPU utilization patterns"""
    if not cpu_samples:
        return "No CPU data available"
    
    overall_utils = [sample['overall'] for sample in cpu_samples]
    per_core_utils = []
    
    if cpu_samples and 'per_core' in cpu_samples[0]:
        num_cores = len(cpu_samples[0]['per_core'])
        for core_idx in range(num_cores):
            core_utils = [sample['per_core'][core_idx] for sample in cpu_samples]
            per_core_utils.append(core_utils)
    
    analysis = {
        'approach': approach_name,
        'avg_overall_cpu': sum(overall_utils) / len(overall_utils) if overall_utils else 0,
        'max_overall_cpu': max(overall_utils) if overall_utils else 0,
        'per_core_avg': [sum(core) / len(core) for core in per_core_utils] if per_core_utils else [],
        'per_core_max': [max(core) for core in per_core_utils] if per_core_utils else [],
        'cpu_efficiency': 'HIGH' if (sum(overall_utils) / len(overall_utils) if overall_utils else 0) > 70 else 'LOW'
    }
    
    return analysis

def main():
    """Main CPU utilization diagnostic"""
    print("🖥️  CPU UTILIZATION DIAGNOSTIC")
    print("=" * 60)
    print(f"🔧 Available cores: {multiprocessing.cpu_count()}")
    print(f"🎯 Target CPU utilization: 80%+")
    print(f"🔍 Testing with 20 tasks (simulating document processing)")
    print()
    
    # Test different approaches
    test_approaches = [
        ('Sequential', test_sequential_processing),
        ('ThreadPool-2', lambda: test_threadpool_processing(20, 2)),
        ('ProcessPool-2', lambda: test_process_pool_processing(20, 2))
    ]
    
    results = []
    
    for name, test_func in test_approaches:
        print(f"🧪 Running {name} test...")
        try:
            result = test_func()
            results.append(result)
            
            print(f"   ⏱️  Total time: {result['total_time_ms']:.1f}ms")
            print(f"   📊 Per task: {result['avg_per_task_ms']:.1f}ms")
            print(f"   🚀 Rate: {1000/result['avg_per_task_ms']:.1f} tasks/sec")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()
        time.sleep(1)  # Brief pause between tests
    
    # Analyze results
    print("📊 PERFORMANCE COMPARISON")
    print("-" * 60)
    
    baseline_time = None
    for result in results:
        if result['approach'] == 'Sequential':
            baseline_time = result['total_time_ms']
            break
    
    for result in results:
        total_time = result['total_time_ms']
        approach = result['approach']
        
        if baseline_time and approach != 'Sequential':
            speedup = baseline_time / total_time
            improvement = ((baseline_time - total_time) / baseline_time) * 100
            print(f"{approach:15}: {total_time:6.1f}ms ({speedup:.1f}x speedup, {improvement:+5.1f}%)")
        else:
            print(f"{approach:15}: {total_time:6.1f}ms (baseline)")
    
    print()
    
    # CPU utilization analysis
    print("🖥️  CPU UTILIZATION ANALYSIS")
    print("-" * 60)
    
    for result in results:
        cpu_analysis = analyze_cpu_utilization(result['cpu_samples'], result['approach'])
        if isinstance(cpu_analysis, dict):
            print(f"{cpu_analysis['approach']:15}:")
            print(f"   Overall CPU: {cpu_analysis['avg_overall_cpu']:5.1f}% avg, {cpu_analysis['max_overall_cpu']:5.1f}% peak")
            
            if cpu_analysis['per_core_avg']:
                for i, (avg, max_val) in enumerate(zip(cpu_analysis['per_core_avg'], cpu_analysis['per_core_max'])):
                    print(f"   Core {i}:      {avg:5.1f}% avg, {max_val:5.1f}% peak")
            
            print(f"   Efficiency:  {cpu_analysis['cpu_efficiency']}")
            print()
    
    # Recommendations
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)
    
    if results:
        best_result = min(results, key=lambda x: x['total_time_ms'])
        best_approach = best_result['approach']
        
        if baseline_time:
            speedup = baseline_time / best_result['total_time_ms']
            print(f"🏆 OPTIMAL APPROACH: {best_approach}")
            print(f"   Performance gain: {speedup:.1f}x faster than sequential")
            print(f"   Time for 675 files: {(best_result['avg_per_task_ms'] * 675) / 1000:.2f}s")
            
            # CPU utilization recommendation
            best_cpu = analyze_cpu_utilization(best_result['cpu_samples'], best_approach)
            if isinstance(best_cpu, dict):
                if best_cpu['cpu_efficiency'] == 'HIGH':
                    print(f"   ✅ CPU utilization: OPTIMAL ({best_cpu['avg_overall_cpu']:.1f}%)")
                else:
                    print(f"   ⚠️  CPU utilization: LOW ({best_cpu['avg_overall_cpu']:.1f}%) - further optimization needed")
        
        print()
        print("📋 NEXT STEPS:")
        print("1. Implement the optimal approach in your pipeline")
        print("2. Monitor CPU utilization during real document processing")  
        print("3. If CPU < 80%, investigate pipeline bottlenecks")
        print("4. Only then consider I/O optimizations")

if __name__ == "__main__":
    main()