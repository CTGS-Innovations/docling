#!/usr/bin/env python3
"""
Simplified Bottleneck Test
==========================

GOAL: Quickly identify the main bottleneck without full pipeline dependencies
REASON: Need to isolate slowdown source with minimal setup
PROBLEM: Full pipeline test requires many dependencies

This simplified test focuses on:
1. I/O operations (file reading/writing)
2. Queue overhead
3. Thread/process switching
4. Memory allocation patterns
"""

import time
import threading
import queue
import json
import yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp
from typing import List, Dict, Any
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class SimplifiedBottleneckTest:
    """Simplified test to identify major bottlenecks"""
    
    def __init__(self, config_path: str = "config/full.yaml"):
        """Initialize test"""
        self.config_path = Path(config_path)
        
        # Load config
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            print(f"⚠️  Config not found, using defaults")
            self.config = {
                'deployment': {'profiles': {'local': {'max_workers': 2, 'queue_size': 100}}},
                'inputs': {'directories': ['/home/corey/projects/docling/cli/data_osha']}
            }
        
        self.max_workers = self.config.get('deployment', {}).get('profiles', {}).get('local', {}).get('max_workers', 2)
        self.queue_size = self.config.get('deployment', {}).get('profiles', {}).get('local', {}).get('queue_size', 100)
        
        print(f"🔬 Simplified Bottleneck Test")
        print(f"⚙️  Workers: {self.max_workers}, Queue size: {self.queue_size}")
        print("-" * 60)
    
    def test_1_file_discovery(self) -> float:
        """Test 1: File discovery speed"""
        print("\n📁 Test 1: File Discovery")
        
        start = time.perf_counter()
        
        files = []
        test_dir = Path("/home/corey/projects/docling/cli/data_osha")
        if test_dir.exists():
            # Test various file patterns
            patterns = ["*.pdf", "*.txt", "*.md", "*.doc", "*.docx"]
            for pattern in patterns:
                files.extend(test_dir.glob(f"**/{pattern}"))
        
        duration = (time.perf_counter() - start) * 1000
        print(f"   Found {len(files)} files in {duration:.2f}ms")
        print(f"   Speed: {len(files)/(duration/1000):.0f} files/sec")
        
        return duration
    
    def test_2_file_io(self, num_files: int = 100) -> Dict[str, float]:
        """Test 2: File I/O performance"""
        print(f"\n💾 Test 2: File I/O ({num_files} files)")
        
        results = {}
        test_dir = Path("/home/corey/projects/docling/cli/data_osha")
        
        # Find test files
        files = list(test_dir.glob("**/*.*"))[:num_files]
        if not files:
            print("   ⚠️  No files found for I/O test")
            return {}
        
        # Test sequential read
        start = time.perf_counter()
        total_bytes = 0
        for f in files:
            try:
                with open(f, 'rb') as file:
                    data = file.read()
                    total_bytes += len(data)
            except:
                pass
        
        seq_read_time = (time.perf_counter() - start) * 1000
        results['sequential_read_ms'] = seq_read_time
        mb_read = total_bytes / (1024 * 1024)
        print(f"   Sequential read: {seq_read_time:.2f}ms ({mb_read:.1f}MB)")
        print(f"   Speed: {mb_read/(seq_read_time/1000):.1f} MB/sec")
        
        # Test parallel read with threads
        start = time.perf_counter()
        
        def read_file(path):
            try:
                with open(path, 'rb') as f:
                    return len(f.read())
            except:
                return 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            sizes = list(executor.map(read_file, files))
        
        parallel_read_time = (time.perf_counter() - start) * 1000
        results['parallel_read_ms'] = parallel_read_time
        print(f"   Parallel read: {parallel_read_time:.2f}ms")
        print(f"   Speedup: {seq_read_time/parallel_read_time:.2f}x")
        
        # Test write performance
        test_data = b"x" * 10000  # 10KB test data
        output_dir = Path("../output/io_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        start = time.perf_counter()
        for i in range(100):
            output_file = output_dir / f"test_{i}.txt"
            with open(output_file, 'wb') as f:
                f.write(test_data)
        
        write_time = (time.perf_counter() - start) * 1000
        results['write_100_files_ms'] = write_time
        print(f"   Write 100 files: {write_time:.2f}ms")
        print(f"   Speed: {100/(write_time/1000):.0f} files/sec")
        
        # Cleanup
        for i in range(100):
            (output_dir / f"test_{i}.txt").unlink(missing_ok=True)
        
        return results
    
    def test_3_queue_overhead(self) -> Dict[str, float]:
        """Test 3: Queue and threading overhead"""
        print(f"\n🔄 Test 3: Queue & Threading Overhead")
        print(f"   Config: max_workers={self.max_workers}, queue_size={self.queue_size}")
        
        results = {}
        
        # Test queue creation
        start = time.perf_counter()
        q = queue.Queue(maxsize=self.queue_size)
        queue_create_time = (time.perf_counter() - start) * 1000
        results['queue_creation_ms'] = queue_create_time
        print(f"   ✅ Queue creation: {queue_create_time:.4f}ms")
        
        # Test queue operations with smaller number first
        num_items = 100  # Reduced from 1000 to avoid hanging
        
        # Single thread baseline with timeout protection
        print(f"   Testing single thread operations...")
        start = time.perf_counter()
        try:
            test_queue = queue.Queue(maxsize=self.queue_size)
            for i in range(num_items):
                test_queue.put(i, timeout=1.0)  # Add timeout
            
            retrieved = 0
            while retrieved < num_items:
                try:
                    test_queue.get(timeout=0.1)
                    retrieved += 1
                except queue.Empty:
                    print(f"   ⚠️  Queue empty after {retrieved}/{num_items} items")
                    break
            
            single_thread_time = (time.perf_counter() - start) * 1000
            results['single_thread_ms'] = single_thread_time
            print(f"   ✅ Single thread {num_items} ops: {single_thread_time:.2f}ms")
            
        except Exception as e:
            print(f"   ❌ Single thread test failed: {e}")
            results['single_thread_ms'] = -1
            return results
        
        # Multi-thread with queue - simplified version
        print(f"   Testing multi-thread operations with {self.max_workers} workers...")
        
        work_queue = queue.Queue(maxsize=min(self.queue_size, 50))  # Limit queue size
        result_queue = queue.Queue()
        stop_flag = threading.Event()
        
        def producer(n):
            """Producer with timeout and error handling"""
            produced = 0
            for i in range(n):
                try:
                    work_queue.put(i, timeout=1.0)
                    produced += 1
                except queue.Full:
                    print(f"   ⚠️  Work queue full at item {i}")
                    break
                except Exception as e:
                    print(f"   ❌ Producer error: {e}")
                    break
            print(f"   Producer finished: {produced}/{n} items")
            # Signal completion
            for _ in range(self.max_workers):
                try:
                    work_queue.put(None, timeout=1.0)  # Poison pill
                except:
                    pass
        
        def consumer(worker_id):
            """Consumer with timeout and poison pill"""
            consumed = 0
            while not stop_flag.is_set():
                try:
                    item = work_queue.get(timeout=2.0)
                    if item is None:  # Poison pill
                        break
                    result_queue.put(item * 2)
                    consumed += 1
                    work_queue.task_done()
                except queue.Empty:
                    print(f"   Worker {worker_id} timeout - stopping")
                    break
                except Exception as e:
                    print(f"   Worker {worker_id} error: {e}")
                    break
            print(f"   Worker {worker_id} finished: {consumed} items")
        
        start = time.perf_counter()
        
        try:
            # Start threads
            prod_thread = threading.Thread(target=producer, args=(num_items,))
            cons_threads = [threading.Thread(target=consumer, args=(i,)) 
                          for i in range(self.max_workers)]
            
            prod_thread.start()
            for t in cons_threads:
                t.start()
            
            # Wait with timeout
            prod_thread.join(timeout=5.0)
            if prod_thread.is_alive():
                print("   ⚠️  Producer thread timeout!")
                stop_flag.set()
            
            for t in cons_threads:
                t.join(timeout=2.0)
                if t.is_alive():
                    print(f"   ⚠️  Consumer thread timeout!")
                    stop_flag.set()
            
            multi_thread_time = (time.perf_counter() - start) * 1000
            results['multi_thread_ms'] = multi_thread_time
            print(f"   ✅ Multi-thread {num_items} ops: {multi_thread_time:.2f}ms")
            print(f"   📊 Results in queue: {result_queue.qsize()}")
            
            if single_thread_time > 0:
                overhead = multi_thread_time - single_thread_time
                speedup = single_thread_time / multi_thread_time if multi_thread_time > 0 else 0
                print(f"   📈 Overhead: {overhead:.2f}ms")
                print(f"   📈 Speedup: {speedup:.2f}x")
                results['overhead_ms'] = overhead
                results['speedup'] = speedup
            
        except Exception as e:
            print(f"   ❌ Multi-thread test failed: {e}")
            results['multi_thread_ms'] = -1
        
        return results
    
    def test_4_process_vs_thread(self) -> Dict[str, float]:
        """Test 4: Process vs Thread performance"""
        print(f"\n🔀 Test 4: Process vs Thread Performance")
        
        results = {}
        
        # Define a CPU-bound task
        def cpu_task(n):
            total = 0
            for i in range(n):
                total += i * i
            return total
        
        # Test sequential
        start = time.perf_counter()
        for _ in range(10):
            cpu_task(100000)
        
        sequential_time = (time.perf_counter() - start) * 1000
        results['sequential_ms'] = sequential_time
        print(f"   Sequential: {sequential_time:.2f}ms")
        
        # Test with threads
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(cpu_task, 100000) for _ in range(10)]
            results_thread = [f.result() for f in futures]
        
        thread_time = (time.perf_counter() - start) * 1000
        results['thread_pool_ms'] = thread_time
        print(f"   ThreadPool: {thread_time:.2f}ms")
        
        # Test with processes
        start = time.perf_counter()
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(cpu_task, 100000) for _ in range(10)]
            results_process = [f.result() for f in futures]
        
        process_time = (time.perf_counter() - start) * 1000
        results['process_pool_ms'] = process_time
        print(f"   ProcessPool: {process_time:.2f}ms")
        
        print(f"   Thread speedup: {sequential_time/thread_time:.2f}x")
        print(f"   Process speedup: {sequential_time/process_time:.2f}x")
        
        return results
    
    def test_5_memory_allocation(self) -> Dict[str, float]:
        """Test 5: Memory allocation patterns"""
        print(f"\n🧠 Test 5: Memory Allocation Patterns")
        
        results = {}
        
        # Test small allocations
        start = time.perf_counter()
        small_objects = []
        for i in range(10000):
            small_objects.append({"id": i, "data": "x" * 100})
        
        small_alloc_time = (time.perf_counter() - start) * 1000
        results['small_allocations_ms'] = small_alloc_time
        print(f"   10K small objects: {small_alloc_time:.2f}ms")
        
        # Test large allocations
        start = time.perf_counter()
        large_objects = []
        for i in range(100):
            large_objects.append("x" * 1000000)  # 1MB strings
        
        large_alloc_time = (time.perf_counter() - start) * 1000
        results['large_allocations_ms'] = large_alloc_time
        print(f"   100 large objects (1MB each): {large_alloc_time:.2f}ms")
        
        # Test dictionary operations
        start = time.perf_counter()
        test_dict = {}
        for i in range(10000):
            test_dict[f"key_{i}"] = {"value": i, "data": "x" * 100}
        
        dict_time = (time.perf_counter() - start) * 1000
        results['dict_operations_ms'] = dict_time
        print(f"   10K dict operations: {dict_time:.2f}ms")
        
        # Test list operations
        start = time.perf_counter()
        test_list = []
        for i in range(10000):
            test_list.append(i)
            if i % 100 == 0:
                test_list.sort()  # Periodic sorting
        
        list_time = (time.perf_counter() - start) * 1000
        results['list_operations_ms'] = list_time
        print(f"   10K list operations with sorting: {list_time:.2f}ms")
        
        return results
    
    def test_6_json_serialization(self) -> Dict[str, float]:
        """Test 6: JSON serialization performance"""
        print(f"\n📝 Test 6: JSON Serialization")
        
        results = {}
        
        # Create test data
        test_data = {
            "documents": [
                {
                    "id": i,
                    "content": "x" * 1000,
                    "metadata": {
                        "entities": ["entity1", "entity2", "entity3"],
                        "classification": "document",
                        "score": 0.95
                    }
                }
                for i in range(100)
            ]
        }
        
        # Test serialization
        start = time.perf_counter()
        json_str = json.dumps(test_data)
        serialize_time = (time.perf_counter() - start) * 1000
        results['serialize_ms'] = serialize_time
        print(f"   Serialization: {serialize_time:.2f}ms")
        print(f"   Data size: {len(json_str) / 1024:.1f}KB")
        
        # Test deserialization
        start = time.perf_counter()
        loaded_data = json.loads(json_str)
        deserialize_time = (time.perf_counter() - start) * 1000
        results['deserialize_ms'] = deserialize_time
        print(f"   Deserialization: {deserialize_time:.2f}ms")
        
        # Test file write
        output_file = Path("../output/test.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        start = time.perf_counter()
        with open(output_file, 'w') as f:
            json.dump(test_data, f)
        
        file_write_time = (time.perf_counter() - start) * 1000
        results['file_write_ms'] = file_write_time
        print(f"   File write: {file_write_time:.2f}ms")
        
        # Cleanup
        output_file.unlink(missing_ok=True)
        
        return results
    
    def generate_report(self, all_results: Dict[str, Any]):
        """Generate analysis report"""
        print("\n" + "=" * 80)
        print("📊 BOTTLENECK ANALYSIS SUMMARY")
        print("=" * 80)
        
        # Identify potential bottlenecks
        bottlenecks = []
        
        # Check I/O bottleneck
        if 'test_2' in all_results:
            io_results = all_results['test_2']
            if io_results.get('sequential_read_ms', 0) > 1000:
                bottlenecks.append("🔴 I/O: Sequential file reading is slow (>1s for 100 files)")
            if io_results.get('parallel_read_ms', 0) > io_results.get('sequential_read_ms', 0) * 0.7:
                bottlenecks.append("🟡 I/O: Parallel reading not providing expected speedup")
        
        # Check queue overhead
        if 'test_3' in all_results:
            queue_results = all_results['test_3']
            overhead = queue_results.get('multi_thread_ms', 0) - queue_results.get('single_thread_ms', 0)
            if overhead > 100:
                bottlenecks.append(f"🔴 Queue: High threading overhead ({overhead:.0f}ms)")
        
        # Check CPU bottleneck
        if 'test_4' in all_results:
            cpu_results = all_results['test_4']
            thread_time = cpu_results.get('thread_pool_ms', 0)
            process_time = cpu_results.get('process_pool_ms', 0)
            if thread_time > cpu_results.get('sequential_ms', 0) * 0.8:
                bottlenecks.append("🔴 CPU: GIL blocking - threads not improving CPU-bound tasks")
                bottlenecks.append("💡 Consider using ProcessPoolExecutor for CPU-intensive operations")
        
        # Check memory patterns
        if 'test_5' in all_results:
            mem_results = all_results['test_5']
            if mem_results.get('small_allocations_ms', 0) > 100:
                bottlenecks.append("🟡 Memory: Slow small object allocations")
            if mem_results.get('dict_operations_ms', 0) > 200:
                bottlenecks.append("🟡 Memory: Slow dictionary operations")
        
        # Check JSON performance
        if 'test_6' in all_results:
            json_results = all_results['test_6']
            if json_results.get('serialize_ms', 0) > 50:
                bottlenecks.append("🟡 JSON: Slow serialization (consider orjson)")
        
        # Print bottlenecks
        if bottlenecks:
            print("\n🚨 Identified Bottlenecks:")
            for b in bottlenecks:
                print(f"   {b}")
        else:
            print("\n✅ No major bottlenecks detected")
        
        # Performance recommendations
        print("\n💡 Recommendations:")
        print("   1. If I/O bound: Consider async I/O or memory-mapped files")
        print("   2. If CPU bound: Use ProcessPoolExecutor instead of ThreadPoolExecutor")
        print("   3. If queue overhead: Reduce queue operations or use shared memory")
        print("   4. If memory bound: Stream processing instead of loading all data")
        print("   5. For JSON: Use orjson or ujson for faster serialization")
        
        # Save detailed results
        report_path = Path("../output/bottleneck_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path}")
        print("=" * 80)
    
    def run_all_tests(self):
        """Run all bottleneck tests"""
        print("\n🚀 Running Bottleneck Analysis")
        print("=" * 80)
        
        all_results = {}
        
        # Run each test
        all_results['test_1'] = self.test_1_file_discovery()
        all_results['test_2'] = self.test_2_file_io()
        all_results['test_3'] = self.test_3_queue_overhead()
        all_results['test_4'] = self.test_4_process_vs_thread()
        all_results['test_5'] = self.test_5_memory_allocation()
        all_results['test_6'] = self.test_6_json_serialization()
        
        # Generate report
        self.generate_report(all_results)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Simplified Bottleneck Test")
    parser.add_argument('--config', default='config/full.yaml', help='Config file path')
    parser.add_argument('--test', type=int, help='Run specific test number (1-6)')
    
    args = parser.parse_args()
    
    # Create and run test
    tester = SimplifiedBottleneckTest(args.config)
    
    if args.test:
        # Run specific test
        test_method = f"test_{args.test}_*"
        methods = [m for m in dir(tester) if m.startswith(f"test_{args.test}_")]
        if methods:
            method = getattr(tester, methods[0])
            result = method()
            print(f"\nTest result: {result}")
        else:
            print(f"⚠️  Unknown test number: {args.test}")
            print("Available tests: 1-6")
    else:
        # Run all tests
        tester.run_all_tests()


if __name__ == "__main__":
    main()