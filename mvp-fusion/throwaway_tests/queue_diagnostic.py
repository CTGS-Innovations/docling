#!/usr/bin/env python3
"""
Queue Diagnostic Test
=====================

GOAL: Identify the exact queue bottleneck causing the pipeline slowdown
REASON: Queue operations are hanging/slow in the main pipeline
PROBLEM: Need to isolate whether it's queue size, worker count, or blocking operations

This focused test examines:
1. Different queue sizes
2. Different worker counts
3. Blocking vs non-blocking operations
4. Queue.Queue vs multiprocessing.Queue
5. Memory pressure from queue operations
"""

import time
import queue
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class QueueDiagnostic:
    """Diagnose queue performance issues"""
    
    def __init__(self):
        """Initialize diagnostic"""
        print("🔬 Queue Performance Diagnostic")
        print("=" * 60)
        self.results = []
    
    def test_queue_sizes(self) -> Dict[str, float]:
        """Test different queue sizes impact"""
        print("\n📏 Testing Queue Sizes Impact")
        print("-" * 40)
        
        results = {}
        test_sizes = [10, 50, 100, 500, 1000, None]  # None = unlimited
        num_items = 100
        
        for size in test_sizes:
            size_label = str(size) if size else "unlimited"
            
            try:
                # Create queue with specific size
                q = queue.Queue(maxsize=size) if size else queue.Queue()
                
                # Test put/get operations
                start = time.perf_counter()
                
                # Put items
                for i in range(num_items):
                    if size and i >= size:
                        # Queue is full, need to get before putting more
                        q.get()
                    q.put(i)
                
                # Get all items
                retrieved = []
                while not q.empty():
                    retrieved.append(q.get())
                
                duration = (time.perf_counter() - start) * 1000
                results[f"size_{size_label}"] = duration
                
                print(f"   Queue size={size_label}: {duration:.2f}ms for {num_items} items")
                
            except Exception as e:
                print(f"   ❌ Failed with size={size_label}: {e}")
                results[f"size_{size_label}"] = -1
        
        # Find optimal size
        best_size = min(results, key=results.get)
        print(f"\n   ✅ Best queue size: {best_size} ({results[best_size]:.2f}ms)")
        
        return results
    
    def test_worker_counts(self) -> Dict[str, float]:
        """Test different worker counts impact"""
        print("\n👷 Testing Worker Count Impact")
        print("-" * 40)
        
        results = {}
        worker_counts = [1, 2, 4, 8, 16]
        num_items = 100
        queue_size = 50
        
        for workers in worker_counts:
            work_queue = queue.Queue(maxsize=queue_size)
            result_queue = queue.Queue()
            items_processed = threading.Event()
            
            def producer():
                for i in range(num_items):
                    work_queue.put(i)
                # Send poison pills
                for _ in range(workers):
                    work_queue.put(None)
            
            def consumer():
                count = 0
                while True:
                    item = work_queue.get()
                    if item is None:
                        break
                    result_queue.put(item * 2)
                    count += 1
                    work_queue.task_done()
                return count
            
            start = time.perf_counter()
            
            # Start producer
            prod_thread = threading.Thread(target=producer)
            prod_thread.start()
            
            # Start consumers
            cons_threads = []
            for _ in range(workers):
                t = threading.Thread(target=consumer)
                t.start()
                cons_threads.append(t)
            
            # Wait for completion
            prod_thread.join()
            for t in cons_threads:
                t.join()
            
            duration = (time.perf_counter() - start) * 1000
            results[f"workers_{workers}"] = duration
            
            print(f"   Workers={workers}: {duration:.2f}ms")
            print(f"      Items processed: {result_queue.qsize()}")
        
        # Find optimal worker count
        best_workers = min(results, key=results.get)
        print(f"\n   ✅ Best worker count: {best_workers} ({results[best_workers]:.2f}ms)")
        
        return results
    
    def test_blocking_vs_nonblocking(self) -> Dict[str, float]:
        """Test blocking vs non-blocking queue operations"""
        print("\n🚦 Testing Blocking vs Non-Blocking Operations")
        print("-" * 40)
        
        results = {}
        num_items = 100
        
        # Test 1: Blocking put/get
        print("   Testing blocking operations...")
        q = queue.Queue(maxsize=50)
        
        start = time.perf_counter()
        for i in range(num_items):
            q.put(i, block=True)  # Will block if full
        
        for i in range(num_items):
            q.get(block=True)  # Will block if empty
        
        blocking_time = (time.perf_counter() - start) * 1000
        results['blocking'] = blocking_time
        print(f"   Blocking: {blocking_time:.2f}ms")
        
        # Test 2: Non-blocking with exception handling
        print("   Testing non-blocking operations...")
        q = queue.Queue(maxsize=50)
        
        start = time.perf_counter()
        
        # Non-blocking put
        items_put = 0
        for i in range(num_items):
            try:
                q.put(i, block=False)
                items_put += 1
            except queue.Full:
                # Queue is full, get one item and retry
                q.get()
                q.put(i, block=False)
                items_put += 1
        
        # Non-blocking get
        items_got = 0
        while items_got < items_put:
            try:
                q.get(block=False)
                items_got += 1
            except queue.Empty:
                time.sleep(0.001)  # Brief wait
        
        nonblocking_time = (time.perf_counter() - start) * 1000
        results['nonblocking'] = nonblocking_time
        print(f"   Non-blocking: {nonblocking_time:.2f}ms")
        
        # Test 3: Timeout-based operations
        print("   Testing timeout operations...")
        q = queue.Queue(maxsize=50)
        
        start = time.perf_counter()
        
        for i in range(num_items):
            while True:
                try:
                    q.put(i, timeout=0.01)
                    break
                except queue.Full:
                    q.get()  # Make room
        
        for i in range(num_items):
            q.get(timeout=0.01)
        
        timeout_time = (time.perf_counter() - start) * 1000
        results['timeout'] = timeout_time
        print(f"   Timeout-based: {timeout_time:.2f}ms")
        
        # Comparison
        print(f"\n   📊 Performance comparison:")
        fastest = min(results, key=results.get)
        print(f"   ✅ Fastest: {fastest} ({results[fastest]:.2f}ms)")
        
        return results
    
    def test_queue_types(self) -> Dict[str, float]:
        """Test different queue implementations"""
        print("\n🔧 Testing Different Queue Types")
        print("-" * 40)
        
        results = {}
        num_items = 100
        
        # Test 1: Standard queue.Queue
        print("   Testing queue.Queue...")
        q = queue.Queue()
        
        start = time.perf_counter()
        for i in range(num_items):
            q.put(i)
        for i in range(num_items):
            q.get()
        
        std_queue_time = (time.perf_counter() - start) * 1000
        results['queue.Queue'] = std_queue_time
        print(f"   queue.Queue: {std_queue_time:.2f}ms")
        
        # Test 2: queue.SimpleQueue (Python 3.7+)
        if hasattr(queue, 'SimpleQueue'):
            print("   Testing queue.SimpleQueue...")
            q = queue.SimpleQueue()
            
            start = time.perf_counter()
            for i in range(num_items):
                q.put(i)
            for i in range(num_items):
                q.get()
            
            simple_queue_time = (time.perf_counter() - start) * 1000
            results['queue.SimpleQueue'] = simple_queue_time
            print(f"   queue.SimpleQueue: {simple_queue_time:.2f}ms")
        
        # Test 3: queue.LifoQueue
        print("   Testing queue.LifoQueue...")
        q = queue.LifoQueue()
        
        start = time.perf_counter()
        for i in range(num_items):
            q.put(i)
        for i in range(num_items):
            q.get()
        
        lifo_queue_time = (time.perf_counter() - start) * 1000
        results['queue.LifoQueue'] = lifo_queue_time
        print(f"   queue.LifoQueue: {lifo_queue_time:.2f}ms")
        
        # Test 4: List as queue (baseline)
        print("   Testing list (baseline)...")
        q = []
        
        start = time.perf_counter()
        for i in range(num_items):
            q.append(i)
        for i in range(num_items):
            if q:
                q.pop(0)
        
        list_time = (time.perf_counter() - start) * 1000
        results['list'] = list_time
        print(f"   List: {list_time:.2f}ms")
        
        # Test 5: multiprocessing.Queue (if needed for processes)
        print("   Testing multiprocessing.Queue...")
        q = mp.Queue()
        
        start = time.perf_counter()
        for i in range(num_items):
            q.put(i)
        for i in range(num_items):
            q.get()
        
        mp_queue_time = (time.perf_counter() - start) * 1000
        results['multiprocessing.Queue'] = mp_queue_time
        print(f"   multiprocessing.Queue: {mp_queue_time:.2f}ms")
        
        # Find fastest
        fastest = min(results, key=results.get)
        print(f"\n   ✅ Fastest queue type: {fastest} ({results[fastest]:.2f}ms)")
        
        return results
    
    def test_real_workload(self) -> Dict[str, float]:
        """Test with realistic document processing workload"""
        print("\n📄 Testing Realistic Document Workload")
        print("-" * 40)
        
        results = {}
        
        # Simulate document processing
        class Document:
            def __init__(self, doc_id, size):
                self.id = doc_id
                self.size = size
                self.content = "x" * size
                self.metadata = {}
        
        # Create test documents
        num_docs = 50
        docs = [Document(i, 10000) for i in range(num_docs)]  # 10KB docs
        
        # Test 1: Current approach (queue-based)
        print("   Testing queue-based approach...")
        work_queue = queue.Queue(maxsize=10)
        result_queue = queue.Queue()
        
        def process_doc(doc):
            # Simulate processing
            doc.metadata['processed'] = True
            doc.metadata['word_count'] = len(doc.content.split())
            return doc
        
        def producer():
            for doc in docs:
                work_queue.put(doc)
            for _ in range(2):  # 2 workers
                work_queue.put(None)
        
        def consumer():
            while True:
                doc = work_queue.get()
                if doc is None:
                    break
                processed = process_doc(doc)
                result_queue.put(processed)
        
        start = time.perf_counter()
        
        prod = threading.Thread(target=producer)
        cons = [threading.Thread(target=consumer) for _ in range(2)]
        
        prod.start()
        for c in cons:
            c.start()
        
        prod.join()
        for c in cons:
            c.join()
        
        queue_approach_time = (time.perf_counter() - start) * 1000
        results['queue_approach'] = queue_approach_time
        print(f"   Queue approach: {queue_approach_time:.2f}ms")
        print(f"   Docs processed: {result_queue.qsize()}")
        
        # Test 2: Direct approach (no queues)
        print("   Testing direct approach...")
        
        start = time.perf_counter()
        
        processed_docs = []
        for doc in docs:
            processed = process_doc(doc)
            processed_docs.append(processed)
        
        direct_approach_time = (time.perf_counter() - start) * 1000
        results['direct_approach'] = direct_approach_time
        print(f"   Direct approach: {direct_approach_time:.2f}ms")
        print(f"   Docs processed: {len(processed_docs)}")
        
        # Test 3: ThreadPoolExecutor approach
        print("   Testing ThreadPoolExecutor...")
        
        start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            processed_docs = list(executor.map(process_doc, docs))
        
        executor_approach_time = (time.perf_counter() - start) * 1000
        results['executor_approach'] = executor_approach_time
        print(f"   ThreadPoolExecutor: {executor_approach_time:.2f}ms")
        print(f"   Docs processed: {len(processed_docs)}")
        
        # Comparison
        print(f"\n   📊 Approach comparison:")
        fastest = min(results, key=results.get)
        slowest = max(results, key=results.get)
        print(f"   ✅ Fastest: {fastest} ({results[fastest]:.2f}ms)")
        print(f"   ❌ Slowest: {slowest} ({results[slowest]:.2f}ms)")
        print(f"   🔄 Overhead: {results[slowest] - results[fastest]:.2f}ms")
        
        return results
    
    def generate_report(self):
        """Generate diagnostic report"""
        print("\n" + "=" * 60)
        print("📊 QUEUE DIAGNOSTIC SUMMARY")
        print("=" * 60)
        
        print("\n🔴 KEY FINDINGS:")
        print("-" * 40)
        
        # Analyze results
        if hasattr(self, 'size_results'):
            print("\n📏 Queue Size Impact:")
            if self.size_results.get('size_unlimited', 0) < self.size_results.get('size_100', 0):
                print("   ⚠️  Unlimited queue is faster - fixed size causing blocking")
            else:
                print("   ✅ Fixed size queue is fine")
        
        if hasattr(self, 'worker_results'):
            print("\n👷 Worker Count Impact:")
            best = min(self.worker_results, key=self.worker_results.get)
            print(f"   Optimal workers: {best}")
            if 'workers_1' in self.worker_results and 'workers_2' in self.worker_results:
                speedup = self.worker_results['workers_1'] / self.worker_results['workers_2']
                if speedup < 1.5:
                    print("   ⚠️  Poor parallelization - likely GIL or synchronization issue")
        
        if hasattr(self, 'blocking_results'):
            print("\n🚦 Blocking Operations:")
            if self.blocking_results.get('blocking', 0) > self.blocking_results.get('nonblocking', 0) * 1.5:
                print("   ⚠️  Blocking operations causing significant slowdown")
        
        if hasattr(self, 'type_results'):
            print("\n🔧 Queue Type Performance:")
            fastest = min(self.type_results, key=self.type_results.get)
            print(f"   Recommended: {fastest}")
            if fastest == 'list':
                print("   ⚠️  Basic list outperforms queues - overhead issue")
        
        if hasattr(self, 'workload_results'):
            print("\n📄 Realistic Workload:")
            if self.workload_results.get('queue_approach', 0) > self.workload_results.get('direct_approach', 0) * 1.2:
                overhead = self.workload_results['queue_approach'] - self.workload_results['direct_approach']
                print(f"   ⚠️  Queue adds {overhead:.0f}ms overhead vs direct processing")
                print("   💡 Consider removing queues for sequential stages")
            
            if self.workload_results.get('executor_approach', 0) < self.workload_results.get('queue_approach', 0):
                print("   ✅ ThreadPoolExecutor is faster than manual queue management")
                print("   💡 Switch to ThreadPoolExecutor for parallelization")
        
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 40)
        print("1. If queue overhead > 20%, consider direct processing")
        print("2. If workers > 2 don't help, you have GIL blocking")
        print("3. If fixed size causes blocking, use unlimited queue")
        print("4. If ThreadPoolExecutor is faster, switch to it")
        print("5. For CPU-bound work, use ProcessPoolExecutor")
        
        print("=" * 60)
    
    def run_all_tests(self):
        """Run complete diagnostic"""
        print("\n🚀 Starting Queue Diagnostic")
        print("This will identify the exact queue bottleneck")
        print("=" * 60)
        
        # Run tests
        self.size_results = self.test_queue_sizes()
        self.worker_results = self.test_worker_counts()
        self.blocking_results = self.test_blocking_vs_nonblocking()
        self.type_results = self.test_queue_types()
        self.workload_results = self.test_real_workload()
        
        # Generate report
        self.generate_report()


def main():
    """Main entry point"""
    diagnostic = QueueDiagnostic()
    diagnostic.run_all_tests()


if __name__ == "__main__":
    main()