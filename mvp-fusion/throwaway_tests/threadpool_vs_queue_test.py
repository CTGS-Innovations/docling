#!/usr/bin/env python3
"""
ThreadPoolExecutor vs Queue Performance Test
============================================

GOAL: Compare current ServiceProcessor queue system with ThreadPoolExecutor
REASON: Queue system is blocking/slow, need to verify ThreadPoolExecutor is faster
PROBLEM: Need concrete performance comparison before refactoring ServiceProcessor

This test compares:
1. Current ServiceProcessor approach (queue-based)
2. ThreadPoolExecutor approach (proposed replacement)
3. Direct processing (baseline)
"""

import time
import yaml
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import threading
import queue

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import actual ServiceProcessor
try:
    from pipeline.legacy.service_processor import ServiceProcessor
    SERVICE_PROCESSOR_AVAILABLE = True
except ImportError:
    SERVICE_PROCESSOR_AVAILABLE = False
    print("⚠️ ServiceProcessor not available, will use mock")


class ThreadPoolVsQueueTest:
    """Compare ThreadPoolExecutor vs current queue approach"""
    
    def __init__(self, config_path: str = "config/full.yaml"):
        """Initialize test"""
        self.config_path = Path(config_path)
        
        # Load config
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            # Default config
            self.config = {
                'deployment': {'profiles': {'local': {'max_workers': 2, 'queue_size': 100}}},
                'inputs': {'directories': ['/home/corey/projects/docling/cli/data_osha']}
            }
        
        self.max_workers = self.config.get('deployment', {}).get('profiles', {}).get('local', {}).get('max_workers', 2)
        self.queue_size = self.config.get('deployment', {}).get('profiles', {}).get('local', {}).get('queue_size', 100)
        
        print(f"🔬 ThreadPoolExecutor vs Queue Performance Test")
        print(f"⚙️  Config: {self.max_workers} workers, queue size {self.queue_size}")
        print("-" * 60)
        
        # Find test files
        self.test_files = self._find_test_files()
        print(f"📁 Found {len(self.test_files)} test files")
    
    def _find_test_files(self) -> List[Path]:
        """Find test files for processing"""
        files = []
        
        # Look for OSHA files first
        osha_dir = Path("/home/corey/projects/docling/cli/data_osha")
        if osha_dir.exists():
            files.extend(list(osha_dir.glob("**/*.pdf"))[:20])  # Limit to 20 for quick test
            files.extend(list(osha_dir.glob("**/*.txt"))[:10])  # Add some text files
        
        # If no OSHA files, look elsewhere
        if not files:
            for directory in self.config.get('inputs', {}).get('directories', []):
                dir_path = Path(directory)
                if dir_path.exists():
                    files.extend(list(dir_path.glob("**/*.*"))[:20])
                    break
        
        return files[:20]  # Limit to 20 files for quick test
    
    def _mock_process_document(self, file_path: Path) -> Dict[str, Any]:
        """Mock document processing that simulates real work"""
        start_time = time.perf_counter()
        
        try:
            # Simulate file reading (I/O bound)
            file_size = file_path.stat().st_size if file_path.exists() else 1000
            time.sleep(0.001)  # Simulate I/O delay
            
            # Simulate processing (CPU bound)
            content_length = min(file_size, 10000)  # Simulate content processing
            word_count = content_length // 5  # Estimate words
            
            # Simulate entity extraction (CPU intensive)
            entities = {
                'person': ['John Doe'] if word_count > 100 else [],
                'organization': ['OSHA'] if 'osha' in file_path.name.lower() else [],
                'date': ['2024-01-01'] if word_count > 500 else []
            }
            
            # Simulate some CPU work
            result = 0
            for i in range(min(1000, word_count)):
                result += i
            
            processing_time = (time.perf_counter() - start_time) * 1000
            
            return {
                'filename': file_path.name,
                'size': file_size,
                'word_count': word_count,
                'entities': entities,
                'processing_time_ms': processing_time,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'filename': file_path.name,
                'status': 'error',
                'error': str(e),
                'processing_time_ms': (time.perf_counter() - start_time) * 1000
            }
    
    def test_1_current_queue_approach(self) -> Dict[str, Any]:
        """Test current queue-based approach"""
        print("\n🔄 Test 1: Current Queue Approach")
        print("-" * 40)
        
        if SERVICE_PROCESSOR_AVAILABLE:
            # Use actual ServiceProcessor
            print("   Using real ServiceProcessor...")
            try:
                processor = ServiceProcessor(self.config, self.max_workers)
                
                start_time = time.perf_counter()
                
                # Process files using ServiceProcessor
                results = processor.process_files_service(self.test_files, Path("../output/test"))
                
                total_time = (time.perf_counter() - start_time) * 1000
                
                return {
                    'approach': 'ServiceProcessor',
                    'total_time_ms': total_time,
                    'files_processed': len(results) if results else 0,
                    'files_per_sec': (len(results) if results else 0) / (total_time / 1000) if total_time > 0 else 0,
                    'status': 'success'
                }
                
            except Exception as e:
                print(f"   ❌ ServiceProcessor failed: {e}")
                return {'approach': 'ServiceProcessor', 'status': 'failed', 'error': str(e)}
        
        else:
            # Simulate current queue approach
            print("   Using simulated queue approach...")
            
            work_queue = queue.Queue(maxsize=self.queue_size)
            result_queue = queue.Queue()
            stop_event = threading.Event()
            
            def producer():
                """Producer thread - puts files in queue"""
                for file_path in self.test_files:
                    try:
                        work_queue.put(file_path, timeout=2.0)
                    except queue.Full:
                        print(f"   ⚠️ Queue full, skipping {file_path.name}")
                        break
                
                # Send poison pills
                for _ in range(self.max_workers):
                    try:
                        work_queue.put(None, timeout=1.0)
                    except queue.Full:
                        break
            
            def consumer():
                """Consumer thread - processes files"""
                processed = 0
                while not stop_event.is_set():
                    try:
                        file_path = work_queue.get(timeout=3.0)
                        if file_path is None:  # Poison pill
                            break
                        
                        result = self._mock_process_document(file_path)
                        result_queue.put(result)
                        processed += 1
                        work_queue.task_done()
                        
                    except queue.Empty:
                        break
                    except Exception as e:
                        print(f"   ❌ Consumer error: {e}")
                        break
                
                return processed
            
            start_time = time.perf_counter()
            
            # Start threads
            prod_thread = threading.Thread(target=producer)
            cons_threads = [threading.Thread(target=consumer) for _ in range(self.max_workers)]
            
            prod_thread.start()
            for t in cons_threads:
                t.start()
            
            # Wait for completion with timeout
            prod_thread.join(timeout=10.0)
            if prod_thread.is_alive():
                print("   ⚠️ Producer timeout")
                stop_event.set()
            
            for t in cons_threads:
                t.join(timeout=5.0)
                if t.is_alive():
                    print("   ⚠️ Consumer timeout")
                    stop_event.set()
            
            total_time = (time.perf_counter() - start_time) * 1000
            results_count = result_queue.qsize()
            
            return {
                'approach': 'Queue-based',
                'total_time_ms': total_time,
                'files_processed': results_count,
                'files_per_sec': results_count / (total_time / 1000) if total_time > 0 else 0,
                'status': 'success'
            }
    
    def test_2_threadpool_executor(self) -> Dict[str, Any]:
        """Test ThreadPoolExecutor approach"""
        print("\n⚡ Test 2: ThreadPoolExecutor Approach")
        print("-" * 40)
        
        start_time = time.perf_counter()
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all work
                futures = [executor.submit(self._mock_process_document, file_path) 
                          for file_path in self.test_files]
                
                # Collect results as they complete
                results = []
                for future in futures:
                    try:
                        result = future.result(timeout=5.0)
                        results.append(result)
                    except Exception as e:
                        results.append({
                            'status': 'error',
                            'error': str(e)
                        })
            
            total_time = (time.perf_counter() - start_time) * 1000
            successful_results = [r for r in results if r.get('status') == 'success']
            
            return {
                'approach': 'ThreadPoolExecutor',
                'total_time_ms': total_time,
                'files_processed': len(successful_results),
                'files_per_sec': len(successful_results) / (total_time / 1000) if total_time > 0 else 0,
                'status': 'success',
                'success_rate': len(successful_results) / len(results) if results else 0
            }
            
        except Exception as e:
            return {
                'approach': 'ThreadPoolExecutor',
                'status': 'failed',
                'error': str(e)
            }
    
    def test_3_direct_processing(self) -> Dict[str, Any]:
        """Test direct processing (baseline)"""
        print("\n📄 Test 3: Direct Processing (Baseline)")
        print("-" * 40)
        
        start_time = time.perf_counter()
        
        results = []
        for file_path in self.test_files:
            result = self._mock_process_document(file_path)
            results.append(result)
        
        total_time = (time.perf_counter() - start_time) * 1000
        successful_results = [r for r in results if r.get('status') == 'success']
        
        return {
            'approach': 'Direct',
            'total_time_ms': total_time,
            'files_processed': len(successful_results),
            'files_per_sec': len(successful_results) / (total_time / 1000) if total_time > 0 else 0,
            'status': 'success',
            'success_rate': len(successful_results) / len(results) if results else 0
        }
    
    def generate_comparison_report(self, results: List[Dict[str, Any]]):
        """Generate performance comparison report"""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE COMPARISON REPORT")
        print("=" * 60)
        
        # Filter successful tests
        successful_tests = [r for r in results if r.get('status') == 'success']
        
        if not successful_tests:
            print("❌ No successful tests to compare")
            return
        
        print(f"\n📈 Results (processing {len(self.test_files)} files):")
        print("-" * 60)
        print(f"{'Approach':<20} {'Time (ms)':<12} {'Files/sec':<12} {'Status'}")
        print("-" * 60)
        
        for result in successful_tests:
            approach = result['approach']
            time_ms = result['total_time_ms']
            files_per_sec = result['files_per_sec']
            status = "✅ Success" if result.get('files_processed', 0) > 0 else "⚠️ No files"
            
            print(f"{approach:<20} {time_ms:>10.2f}  {files_per_sec:>10.1f}  {status}")
        
        # Find fastest approach
        fastest = min(successful_tests, key=lambda x: x['total_time_ms'])
        slowest = max(successful_tests, key=lambda x: x['total_time_ms'])
        
        print(f"\n🏆 WINNER: {fastest['approach']}")
        print(f"   Time: {fastest['total_time_ms']:.2f}ms")
        print(f"   Speed: {fastest['files_per_sec']:.1f} files/sec")
        
        if fastest != slowest:
            speedup = slowest['total_time_ms'] / fastest['total_time_ms']
            print(f"\n📈 Performance Improvement:")
            print(f"   {speedup:.2f}x faster than {slowest['approach']}")
            print(f"   Time saved: {slowest['total_time_ms'] - fastest['total_time_ms']:.2f}ms")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATION:")
        print("-" * 40)
        
        if fastest['approach'] == 'ThreadPoolExecutor':
            print("✅ Replace ServiceProcessor queues with ThreadPoolExecutor")
            print("   - Eliminates queue blocking issues")
            print("   - Better performance and reliability")
            print("   - Easier to maintain and debug")
            
        elif fastest['approach'] == 'Direct':
            print("✅ Consider direct processing for sequential workloads")
            print("   - No parallelization overhead")
            print("   - Simpler architecture")
            print("   - Good for I/O bound tasks")
            
        else:
            print("⚠️ Current approach is already optimal")
            print("   - No immediate changes needed")
            print("   - Monitor for blocking issues")
        
        # Next steps
        print(f"\n🔧 Next Steps:")
        print("-" * 40)
        if fastest['approach'] == 'ThreadPoolExecutor':
            print("1. Update ServiceProcessor to use ThreadPoolExecutor")
            print("2. Remove manual queue management code")
            print("3. Test with larger document batches")
            print("4. Deploy to production")
        
        print("=" * 60)
    
    def run_comparison_test(self):
        """Run all tests and compare results"""
        print(f"🚀 Starting Performance Comparison")
        print(f"Files to process: {len(self.test_files)}")
        print("=" * 60)
        
        results = []
        
        # Test 1: Current approach
        result1 = self.test_1_current_queue_approach()
        results.append(result1)
        if result1.get('status') == 'success':
            print(f"   ✅ {result1['files_processed']} files in {result1['total_time_ms']:.2f}ms")
        else:
            print(f"   ❌ Failed: {result1.get('error', 'Unknown error')}")
        
        # Test 2: ThreadPoolExecutor
        result2 = self.test_2_threadpool_executor()
        results.append(result2)
        if result2.get('status') == 'success':
            print(f"   ✅ {result2['files_processed']} files in {result2['total_time_ms']:.2f}ms")
        else:
            print(f"   ❌ Failed: {result2.get('error', 'Unknown error')}")
        
        # Test 3: Direct processing
        result3 = self.test_3_direct_processing()
        results.append(result3)
        if result3.get('status') == 'success':
            print(f"   ✅ {result3['files_processed']} files in {result3['total_time_ms']:.2f}ms")
        else:
            print(f"   ❌ Failed: {result3.get('error', 'Unknown error')}")
        
        # Generate report
        self.generate_comparison_report(results)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ThreadPoolExecutor vs Queue Performance Test")
    parser.add_argument('--config', default='config/full.yaml', help='Config file path')
    parser.add_argument('--files', type=int, default=20, help='Number of files to test')
    
    args = parser.parse_args()
    
    # Create and run test
    tester = ThreadPoolVsQueueTest(args.config)
    tester.run_comparison_test()


if __name__ == "__main__":
    main()