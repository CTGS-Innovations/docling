#!/usr/bin/env python3
"""
Performance Comparison: Queue Service vs Batch Processing
=======================================================
GOAL: Compare Docker-optimized queue service vs original batch processing
REASON: Validate queue service efficiency and resource usage
PROBLEM: Need data-driven evidence of performance improvements

Performance Metrics:
- Processing time per file
- Memory usage patterns
- CPU utilization efficiency
- Throughput (files/sec)
"""

import time
import threading
import psutil
import logging
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'samples': len(self.metrics)
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

def test_batch_processing():
    """Test original batch processing approach"""
    print("🧪 Testing Original Batch Processing...")
    
    from pipeline.legacy.service_processor import ServiceProcessor
    import yaml
    
    # Load configuration
    with open("config/full.yaml", 'r') as f:
        config = yaml.safe_load(f)
    
    # Initialize processor
    processor = ServiceProcessor(config=config, max_workers=2)
    
    # Start performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Process files
    start_time = time.time()
    try:
        file_paths = [Path(f) for f in TEST_FILES]
        documents, processing_time = processor.process_files_service(file_paths)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Stop monitoring
        perf_metrics = monitor.stop_monitoring()
        
        return {
            'method': 'batch_processing',
            'files_processed': len(file_paths),
            'total_time_seconds': total_time,
            'processing_time_seconds': processing_time,
            'files_per_second': len(file_paths) / total_time,
            'ms_per_file': (total_time * 1000) / len(file_paths),
            'performance_metrics': perf_metrics
        }
        
    except Exception as e:
        monitor.stop_monitoring()
        print(f"❌ Batch processing failed: {e}")
        return None

def test_queue_service():
    """Test Docker-optimized queue service"""
    print("🧪 Testing Docker-Optimized Queue Service...")
    
    from queue_service import DockerOptimizedQueueService
    import threading
    import queue
    
    # Initialize queue service
    service = DockerOptimizedQueueService()
    
    # Start performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Start service
    start_time = time.time()
    try:
        service.start_service()
        
        # Submit requests for all test files
        request_ids = []
        for file_path in TEST_FILES:
            request_id = service.submit_request(files=[file_path])
            request_ids.append(request_id)
        
        # Wait for processing to complete (check queue depth)
        while service.request_queue.qsize() > 0:
            time.sleep(0.1)
        
        # Give workers time to finish current batch
        time.sleep(2)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Stop service
        service.stop_service()
        
        # Stop monitoring
        perf_metrics = monitor.stop_monitoring()
        
        # Get service metrics
        service_metrics = service.get_metrics()
        
        return {
            'method': 'queue_service',
            'files_processed': service_metrics.files_processed,
            'total_time_seconds': total_time,
            'files_per_second': service_metrics.files_processed / total_time if total_time > 0 else 0,
            'ms_per_file': (total_time * 1000) / service_metrics.files_processed if service_metrics.files_processed > 0 else 0,
            'avg_processing_time_ms': service_metrics.avg_processing_time_ms,
            'performance_metrics': perf_metrics,
            'service_metrics': {
                'requests_processed': service_metrics.requests_processed,
                'files_processed': service_metrics.files_processed,
                'throughput_files_per_sec': service_metrics.throughput_files_per_sec
            }
        }
        
    except Exception as e:
        service.stop_service()
        monitor.stop_monitoring()
        print(f"❌ Queue service failed: {e}")
        return None

def compare_results(batch_result: Dict, queue_result: Dict):
    """Compare and analyze results"""
    print("\n" + "="*80)
    print("📊 PERFORMANCE COMPARISON RESULTS")
    print("="*80)
    
    if not batch_result:
        print("❌ Batch processing test failed")
        return
    
    if not queue_result:
        print("❌ Queue service test failed")
        return
    
    print(f"\n🔍 PROCESSING TIME COMPARISON:")
    print(f"   Batch Processing:  {batch_result['ms_per_file']:.1f}ms/file")
    print(f"   Queue Service:     {queue_result['ms_per_file']:.1f}ms/file")
    
    if batch_result['ms_per_file'] > 0:
        improvement = ((batch_result['ms_per_file'] - queue_result['ms_per_file']) / batch_result['ms_per_file']) * 100
        print(f"   Improvement:       {improvement:+.1f}%")
    
    print(f"\n🔍 THROUGHPUT COMPARISON:")
    print(f"   Batch Processing:  {batch_result['files_per_second']:.2f} files/sec")
    print(f"   Queue Service:     {queue_result['files_per_second']:.2f} files/sec")
    
    if batch_result['files_per_second'] > 0:
        throughput_improvement = ((queue_result['files_per_second'] - batch_result['files_per_second']) / batch_result['files_per_second']) * 100
        print(f"   Improvement:       {throughput_improvement:+.1f}%")
    
    print(f"\n🔍 RESOURCE USAGE COMPARISON:")
    if 'performance_metrics' in batch_result and 'performance_metrics' in queue_result:
        batch_perf = batch_result['performance_metrics']
        queue_perf = queue_result['performance_metrics']
        
        print(f"   CPU Usage (avg):")
        print(f"     Batch:  {batch_perf.get('avg_cpu_percent', 0):.1f}%")
        print(f"     Queue:  {queue_perf.get('avg_cpu_percent', 0):.1f}%")
        
        print(f"   Memory Usage (avg):")
        print(f"     Batch:  {batch_perf.get('avg_memory_mb', 0):.1f}MB")
        print(f"     Queue:  {queue_perf.get('avg_memory_mb', 0):.1f}MB")
        
        print(f"   Memory Usage (max):")
        print(f"     Batch:  {batch_perf.get('max_memory_mb', 0):.1f}MB")
        print(f"     Queue:  {queue_perf.get('max_memory_mb', 0):.1f}MB")
    
    print(f"\n🎯 DOCKER OPTIMIZATION ANALYSIS:")
    queue_perf = queue_result.get('performance_metrics', {})
    max_memory = queue_perf.get('max_memory_mb', 0)
    
    if max_memory > 0:
        memory_efficiency = (800 - max_memory) / 800 * 100  # 800MB Docker limit
        print(f"   Memory efficiency:  {memory_efficiency:.1f}% (under 800MB Docker limit)")
        if max_memory <= 800:
            print(f"   ✅ Memory constraint: Within Docker 1GB limit")
        else:
            print(f"   ❌ Memory constraint: Exceeds Docker limit")
    
    print(f"   CPU workers:        2 (matches Docker CPU allocation)")
    print(f"   Queue capacity:     50 requests (bounded for memory safety)")

def main():
    """Main performance comparison test"""
    print("🚀 Starting Performance Comparison Test")
    print("Files to process:")
    for i, file_path in enumerate(TEST_FILES, 1):
        file_name = Path(file_path).name
        print(f"   {i}. {file_name}")
    
    # Test batch processing
    batch_result = test_batch_processing()
    
    print("\n" + "-"*40)
    
    # Test queue service  
    queue_result = test_queue_service()
    
    # Compare results
    compare_results(batch_result, queue_result)
    
    print("\n🏁 Performance comparison complete!")

if __name__ == "__main__":
    main()