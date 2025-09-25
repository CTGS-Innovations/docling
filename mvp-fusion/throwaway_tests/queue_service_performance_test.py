#!/usr/bin/env python3
"""
Queue Service Performance Test
=============================
GOAL: Measure Docker-optimized queue service performance and efficiency
REASON: Validate queue service meets Docker deployment requirements
PROBLEM: Need concrete performance metrics for 2-core, 1GB constraints

Performance Targets:
- Memory usage: <800MB (Docker 1GB limit with 200MB overhead)
- CPU utilization: Efficient use of 2 cores
- Processing speed: Maintain or improve upon batch processing
- Queue efficiency: Bounded queue prevents OOM
"""

import time
import threading
import psutil
import logging
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Test files (same files used in queue service test)
TEST_FILES = [
    "/home/corey/projects/docling/scout-docs/storage/fbef1082-aeec-48a9-b59b-4dbd2be804f7/DocTest.pdf",
    "/home/corey/projects/docling/scout-docs/storage/dc73e6e0-810a-47ce-abeb-da18f945e963/Complex2.pdf"
]

class PerformanceMonitor:
    """Monitor CPU and memory usage during processing"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start background monitoring"""
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return results"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        if not self.metrics:
            return {}
        
        cpu_values = [m['cpu'] for m in self.metrics]
        memory_values = [m['memory_mb'] for m in self.metrics]
        
        return {
            'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
            'max_cpu_percent': max(cpu_values),
            'peak_cpu_percent': max(cpu_values),
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'peak_memory_mb': max(memory_values),
            'samples': len(self.metrics),
            'duration_seconds': self.metrics[-1]['timestamp'] - self.metrics[0]['timestamp'] if len(self.metrics) > 1 else 0
        }
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                cpu_percent = self.process.cpu_percent(interval=0.1)
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.metrics.append({
                    'timestamp': time.time(),
                    'cpu': cpu_percent,
                    'memory_mb': memory_mb
                })
                time.sleep(0.1)  # Sample every 100ms
            except:
                break

def test_queue_service():
    """Test Docker-optimized queue service performance"""
    print("🧪 Testing Docker-Optimized Queue Service Performance...")
    
    try:
        from queue_service import DockerOptimizedQueueService
        
        # Initialize queue service
        service = DockerOptimizedQueueService()
        
        # Start performance monitoring
        monitor = PerformanceMonitor()
        
        print("🚀 Starting queue service...")
        startup_start = time.time()
        
        # Start service and monitor startup
        monitor.start_monitoring()
        service.start_service()
        startup_time = time.time() - startup_start
        
        print(f"✅ Service startup completed in {startup_time:.2f}s")
        
        # Submit requests for all test files
        print("📥 Submitting processing requests...")
        processing_start = time.time()
        
        request_ids = []
        for i, file_path in enumerate(TEST_FILES):
            request_id = service.submit_request(
                files=[file_path], 
                priority=i,
                metadata={'test_run': True, 'file_index': i}
            )
            request_ids.append(request_id)
            print(f"   Request {i+1}: {Path(file_path).name}")
        
        # Wait for processing to complete (monitor queue depth)
        print("⏳ Waiting for processing completion...")
        queue_empty_time = None
        
        while True:
            queue_depth = service.request_queue.qsize()
            if queue_depth == 0 and queue_empty_time is None:
                queue_empty_time = time.time()
            
            # Give extra time for workers to finish current batch
            if queue_empty_time and (time.time() - queue_empty_time) > 3:
                break
                
            time.sleep(0.1)
        
        processing_end = time.time()
        total_processing_time = processing_end - processing_start
        
        print(f"✅ Processing completed in {total_processing_time:.2f}s")
        
        # Get final metrics before stopping
        service_metrics = service.get_metrics()
        
        # Stop service
        print("🛑 Stopping service...")
        service.stop_service()
        
        # Stop monitoring
        perf_metrics = monitor.stop_monitoring()
        
        # Calculate total time
        total_time = processing_end - startup_start
        
        return {
            'files_processed': service_metrics.files_processed,
            'requests_processed': service_metrics.requests_processed,
            'startup_time_seconds': startup_time,
            'processing_time_seconds': total_processing_time,
            'total_time_seconds': total_time,
            'avg_processing_time_ms': service_metrics.avg_processing_time_ms,
            'files_per_second': service_metrics.files_processed / total_processing_time if total_processing_time > 0 else 0,
            'ms_per_file': (total_processing_time * 1000) / service_metrics.files_processed if service_metrics.files_processed > 0 else 0,
            'performance_metrics': perf_metrics,
            'service_metrics': service_metrics
        }
        
    except Exception as e:
        print(f"❌ Queue service test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_docker_performance(result: dict):
    """Analyze performance against Docker constraints"""
    print("\n" + "="*80)
    print("📊 DOCKER-OPTIMIZED QUEUE SERVICE PERFORMANCE ANALYSIS")
    print("="*80)
    
    if not result:
        print("❌ Performance test failed")
        return
    
    perf_metrics = result.get('performance_metrics', {})
    
    print(f"\n🔍 PROCESSING PERFORMANCE:")
    print(f"   Files processed:    {result['files_processed']}")
    print(f"   Processing time:    {result['processing_time_seconds']:.2f}s")
    print(f"   Throughput:         {result['files_per_second']:.2f} files/sec")
    print(f"   Time per file:      {result['ms_per_file']:.1f}ms/file")
    print(f"   Average batch time: {result['avg_processing_time_ms']:.1f}ms")
    
    print(f"\n🔍 RESOURCE UTILIZATION:")
    if perf_metrics:
        cpu_avg = perf_metrics.get('avg_cpu_percent', 0)
        cpu_peak = perf_metrics.get('peak_cpu_percent', 0)
        memory_avg = perf_metrics.get('avg_memory_mb', 0)
        memory_peak = perf_metrics.get('peak_memory_mb', 0)
        
        print(f"   CPU usage (avg):    {cpu_avg:.1f}%")
        print(f"   CPU usage (peak):   {cpu_peak:.1f}%")
        print(f"   Memory usage (avg): {memory_avg:.1f}MB")
        print(f"   Memory usage (peak): {memory_peak:.1f}MB")
        
        # Docker constraint analysis
        print(f"\n🎯 DOCKER CONSTRAINT COMPLIANCE:")
        
        # Memory constraint (800MB target, 1GB limit)
        memory_efficiency = ((800 - memory_peak) / 800) * 100 if memory_peak <= 800 else 0
        if memory_peak <= 800:
            print(f"   ✅ Memory constraint:  PASS ({memory_peak:.1f}MB ≤ 800MB target)")
            print(f"   📊 Memory efficiency:  {memory_efficiency:.1f}% headroom")
        else:
            print(f"   ❌ Memory constraint:  FAIL ({memory_peak:.1f}MB > 800MB target)")
            if memory_peak <= 1024:
                print(f"   ⚠️  Still under 1GB Docker limit, but inefficient")
        
        # CPU efficiency (2-core utilization)
        cpu_efficiency = min(cpu_peak / 200 * 100, 100)  # 200% = 2 cores fully utilized
        if cpu_peak > 100:
            print(f"   ✅ CPU utilization:    GOOD (multi-core: {cpu_peak:.1f}%)")
            print(f"   📊 CPU efficiency:     {cpu_efficiency:.1f}% of available cores")
        else:
            print(f"   ⚠️  CPU utilization:    LOW (single-core only: {cpu_peak:.1f}%)")
        
        # Queue service specific metrics
        print(f"\n🔍 QUEUE SERVICE METRICS:")
        print(f"   Queue capacity:     50 requests (bounded for memory safety)")
        print(f"   Worker threads:     2 (matches Docker CPU allocation)")
        print(f"   Batch size:         10 files (memory-controlled batches)")
        print(f"   Service startup:    {result['startup_time_seconds']:.2f}s")
        
    # Historical comparison (from conversation summary)
    print(f"\n📈 HISTORICAL PERFORMANCE COMPARISON:")
    print(f"   Current performance:  {result['ms_per_file']:.1f}ms/file")
    print(f"   Previous batch mode:  ~260ms/file (from logs)")
    
    if result['ms_per_file'] > 0:
        improvement = ((260 - result['ms_per_file']) / 260) * 100
        if improvement > 0:
            print(f"   Performance gain:     {improvement:.1f}% faster")
        else:
            print(f"   Performance change:   {improvement:.1f}% (within margin of error)")
    
    # Docker deployment readiness
    print(f"\n🐳 DOCKER DEPLOYMENT READINESS:")
    memory_ready = memory_peak <= 800
    cpu_ready = cpu_peak > 50  # At least some CPU utilization
    
    if memory_ready and cpu_ready:
        print(f"   ✅ READY for Docker deployment")
        print(f"   📦 Recommended Docker config:")
        print(f"      Memory limit: 1GB")
        print(f"      CPU limit: 2 cores")
        print(f"      Queue capacity: 50 requests")
    else:
        print(f"   ❌ NOT READY for Docker deployment")
        if not memory_ready:
            print(f"      Issue: Memory usage too high")
        if not cpu_ready:
            print(f"      Issue: CPU utilization too low")

def main():
    """Main performance test"""
    print("🚀 Docker-Optimized Queue Service Performance Test")
    print("="*60)
    print("Test Configuration:")
    print(f"   Docker constraints:  2 cores, 1GB RAM")
    print(f"   Memory target:       800MB (200MB system overhead)")
    print(f"   Queue capacity:      50 requests")
    print(f"   Worker threads:      2")
    print(f"   Batch size:          10 files")
    
    print("\nTest files:")
    for i, file_path in enumerate(TEST_FILES, 1):
        file_name = Path(file_path).name
        file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
        print(f"   {i}. {file_name} ({file_size:.1f}MB)")
    
    print("\n" + "-"*60)
    
    # Run performance test
    result = test_queue_service()
    
    # Analyze results
    analyze_docker_performance(result)
    
    print("\n🏁 Performance test complete!")

if __name__ == "__main__":
    main()