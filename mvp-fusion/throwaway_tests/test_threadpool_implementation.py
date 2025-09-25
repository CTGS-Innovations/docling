#!/usr/bin/env python3
"""
Test ThreadPool ServiceProcessor Implementation
==============================================

GOAL: Test the new ThreadPoolExecutor-based ServiceProcessor
REASON: Verify 142x performance improvement works in actual implementation
PROBLEM: Need to confirm new implementation works with real pipeline
"""

import time
import yaml
import sys
from pathlib import Path
from typing import List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import both versions for comparison
try:
    from pipeline.legacy.service_processor import ServiceProcessor as OriginalServiceProcessor
    ORIGINAL_AVAILABLE = True
except ImportError:
    ORIGINAL_AVAILABLE = False
    print("⚠️ Original ServiceProcessor not available")

try:
    from pipeline.legacy.service_processor_threadpool import ServiceProcessorThreadPool
    THREADPOOL_AVAILABLE = True
except ImportError:
    THREADPOOL_AVAILABLE = False
    print("⚠️ ThreadPool ServiceProcessor not available")


def find_test_files(limit: int = 10) -> List[Path]:
    """Find test files for processing"""
    files = []
    
    # Look for OSHA files first
    osha_dir = Path("/home/corey/projects/docling/cli/data_osha")
    if osha_dir.exists():
        files.extend(list(osha_dir.glob("**/*.pdf"))[:limit//2])
        files.extend(list(osha_dir.glob("**/*.txt"))[:limit//2])
    
    # If not enough files, look elsewhere
    if len(files) < limit:
        data_dirs = [
            "/home/corey/projects/docling/cli/data",
            "/home/corey/projects/docling/cli/data_complex"
        ]
        
        for data_dir in data_dirs:
            dir_path = Path(data_dir)
            if dir_path.exists():
                remaining = limit - len(files)
                files.extend(list(dir_path.glob("**/*.*"))[:remaining])
                if len(files) >= limit:
                    break
    
    return files[:limit]


def test_threadpool_implementation():
    """Test the new ThreadPool implementation"""
    print("🔬 Testing ThreadPool ServiceProcessor Implementation")
    print("=" * 60)
    
    # Load config
    config_path = Path("config/full.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Default config
        config = {
            'deployment': {'profiles': {'local': {'max_workers': 2}}},
            'corpus': {
                'first_names_path': 'knowledge/corpus/foundation_data/first_names_2025_09_18.txt',
                'last_names_path': 'knowledge/corpus/foundation_data/last_names_2025_09_18.txt',
                'organizations_path': 'knowledge/corpus/foundation_data/organizations_100k.txt'
            }
        }
    
    # Find test files
    test_files = find_test_files(10)
    print(f"📁 Found {len(test_files)} test files")
    
    if not test_files:
        print("❌ No test files found!")
        return
    
    # Test ThreadPool implementation
    if THREADPOOL_AVAILABLE:
        print(f"\n🚀 Testing ThreadPool Implementation")
        print("-" * 40)
        
        try:
            processor = ServiceProcessorThreadPool(config, max_workers=2)
            
            start_time = time.perf_counter()
            
            # Process files
            documents, processing_time = processor.process_files_service(
                test_files, 
                Path("../output/threadpool_test")
            )
            
            total_time = time.perf_counter() - start_time
            
            print(f"✅ ThreadPool Results:")
            print(f"   Files processed: {len(documents)}")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Processing time: {processing_time:.2f}s")
            print(f"   Speed: {len(documents)/total_time:.1f} files/sec")
            print(f"   Average: {(total_time/len(documents))*1000:.1f}ms per file")
            
            # Check document content
            if documents:
                sample_doc = documents[0]
                print(f"\n📄 Sample Document Analysis:")
                print(f"   Filename: {sample_doc.source_filename}")
                print(f"   Content length: {len(sample_doc.markdown_content)} chars")
                print(f"   Has YAML: {bool(sample_doc.yaml_frontmatter)}")
                print(f"   Has entities: {hasattr(sample_doc, 'global_entities')}")
                print(f"   Has semantic facts: {hasattr(sample_doc, 'semantic_facts')}")
                
                if hasattr(sample_doc, 'global_entities'):
                    entities = sample_doc.global_entities
                    entity_counts = {k: len(v) for k, v in entities.items() if v}
                    if entity_counts:
                        count_str = ", ".join([f"{k}:{v}" for k, v in entity_counts.items()])
                        print(f"   Entities: {count_str}")
            
            processor.stop_service()
            
        except Exception as e:
            print(f"❌ ThreadPool test failed: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("❌ ThreadPool ServiceProcessor not available")
    
    # Compare with original if available
    if ORIGINAL_AVAILABLE and THREADPOOL_AVAILABLE:
        print(f"\n⚖️  Comparison Test (smaller batch)")
        print("-" * 40)
        
        # Use fewer files for comparison to avoid hanging
        comparison_files = test_files[:5]
        print(f"Comparing with {len(comparison_files)} files...")
        
        try:
            print("Testing original implementation...")
            original_processor = OriginalServiceProcessor(config, max_workers=2)
            
            start_time = time.perf_counter()
            
            # Set timeout for original processor
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Original processor timeout")
            
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
            
            try:
                original_docs, original_time = original_processor.process_files_service(
                    comparison_files,
                    Path("../output/original_test")
                )
                signal.alarm(0)  # Cancel timeout
                
                original_total = time.perf_counter() - start_time
                
                print(f"✅ Original: {len(original_docs)} files in {original_total:.2f}s")
                print(f"   Speed: {len(original_docs)/original_total:.1f} files/sec")
                
            except TimeoutError:
                signal.alarm(0)
                print("❌ Original processor timed out (>30s)")
                original_total = 30.0
                original_docs = []
            
            # Test ThreadPool with same files
            print("Testing ThreadPool implementation...")
            threadpool_processor = ServiceProcessorThreadPool(config, max_workers=2)
            
            start_time = time.perf_counter()
            threadpool_docs, threadpool_time = threadpool_processor.process_files_service(
                comparison_files,
                Path("../output/threadpool_comparison")
            )
            threadpool_total = time.perf_counter() - start_time
            
            print(f"✅ ThreadPool: {len(threadpool_docs)} files in {threadpool_total:.2f}s")
            print(f"   Speed: {len(threadpool_docs)/threadpool_total:.1f} files/sec")
            
            # Calculate improvement
            if original_total > 0 and threadpool_total > 0:
                speedup = original_total / threadpool_total
                print(f"\n🏆 Performance Improvement: {speedup:.1f}x faster")
                
                if len(original_docs) > 0 and len(threadpool_docs) > 0:
                    original_per_file = original_total / len(original_docs)
                    threadpool_per_file = threadpool_total / len(threadpool_docs)
                    per_file_speedup = original_per_file / threadpool_per_file
                    print(f"   Per-file speedup: {per_file_speedup:.1f}x faster")
            
            threadpool_processor.stop_service()
            
        except Exception as e:
            print(f"❌ Comparison test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 Test Complete")
    print("=" * 60)


def main():
    """Main entry point"""
    test_threadpool_implementation()


if __name__ == "__main__":
    main()