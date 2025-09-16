#!/usr/bin/env python3
"""
Diagnostic script to identify the real performance bottleneck.
DELETE THIS FILE AFTER TESTING.
"""

import time
import os
from pathlib import Path
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Import modules
from enhanced_classification_with_entities import EnhancedClassifierWithEntities
from enhanced_enrichment_targeted import TargetedEnrichment

def simple_classification_test(content, iterations=10):
    """Test raw classification performance."""
    classifier = EnhancedClassifierWithEntities()
    
    start_time = time.time()
    for i in range(iterations):
        result = classifier.classify_and_extract(content, f"test_{i}.md")
    total_time = time.time() - start_time
    
    return total_time / iterations

def test_memory_bottleneck():
    """Test if memory allocation is the bottleneck."""
    print("🔍 Testing memory allocation bottleneck...")
    
    # Create progressively larger content
    base_content = "This is a test document with some content. " * 100
    
    for size_factor in [1, 10, 100, 1000]:
        content = base_content * size_factor
        content_mb = len(content) / (1024 * 1024)
        
        avg_time = simple_classification_test(content, 3)
        
        print(f"   Content size: {content_mb:.2f}MB, Avg time: {avg_time*1000:.1f}ms")

def test_io_bottleneck():
    """Test if I/O operations are the bottleneck."""
    print("\n🔍 Testing I/O bottleneck...")
    
    # Test file loading speed
    test_files = list(Path("../cli/data").rglob("*.md"))[:20] if Path("../cli/data").exists() else []
    
    if not test_files:
        print("   No test files found")
        return
    
    start_time = time.time()
    total_chars = 0
    
    for file_path in test_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                total_chars += len(content)
        except:
            continue
    
    load_time = time.time() - start_time
    print(f"   Loaded {len(test_files)} files ({total_chars/1024/1024:.1f}MB) in {load_time*1000:.1f}ms")
    print(f"   I/O speed: {len(test_files)/load_time:.1f} files/sec")

def test_initialization_overhead():
    """Test if classifier initialization is the bottleneck."""
    print("\n🔍 Testing initialization overhead...")
    
    # Test single initialization
    start_time = time.time()
    classifier = EnhancedClassifierWithEntities()
    init_time = time.time() - start_time
    print(f"   Single classifier init: {init_time*1000:.1f}ms")
    
    # Test multiple initializations (like in multiprocessing)
    start_time = time.time()
    for i in range(8):  # 8 processes
        classifier = EnhancedClassifierWithEntities()
    multi_init_time = time.time() - start_time
    print(f"   8 classifier inits: {multi_init_time*1000:.1f}ms")

def worker_with_timing(content):
    """Worker function that measures its own performance."""
    start_time = time.time()
    
    # Initialization
    init_start = time.time()
    classifier = EnhancedClassifierWithEntities()
    enricher = TargetedEnrichment()
    init_time = time.time() - init_start
    
    # Classification
    classify_start = time.time()
    result = classifier.classify_and_extract(content, "test.md")
    classify_time = time.time() - classify_start
    
    # Enrichment
    enrich_start = time.time()
    dummy_classification = {"primary_domain": "general", "document_types": ["general"]}
    enrichment_result = enricher.extract_entities_targeted(content, dummy_classification, ["general"])
    enrich_time = time.time() - enrich_start
    
    total_time = time.time() - start_time
    
    return {
        'init_time': init_time,
        'classify_time': classify_time,
        'enrich_time': enrich_time,
        'total_time': total_time,
        'process_id': os.getpid()
    }

def test_thread_vs_process_overhead():
    """Compare thread vs process overhead with detailed timing."""
    print("\n🔍 Testing thread vs process overhead...")
    
    # Use a medium-sized content sample
    content = "This is a test document with various content. " * 1000
    
    # Test with threads
    print("   Testing ThreadPoolExecutor...")
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_with_timing, content) for _ in range(8)]
        thread_results = [f.result() for f in futures]
    thread_total_time = time.time() - start_time
    
    # Test with processes
    print("   Testing ProcessPoolExecutor...")
    start_time = time.time()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_with_timing, content) for _ in range(8)]
        process_results = [f.result() for f in futures]
    process_total_time = time.time() - start_time
    
    # Analyze results
    print(f"\n   📊 THREAD RESULTS (8 tasks, 4 workers):")
    print(f"      Total time: {thread_total_time*1000:.1f}ms")
    print(f"      Avg init: {sum(r['init_time'] for r in thread_results)/len(thread_results)*1000:.1f}ms")
    print(f"      Avg classify: {sum(r['classify_time'] for r in thread_results)/len(thread_results)*1000:.1f}ms")
    print(f"      Throughput: {len(thread_results)/thread_total_time:.1f} docs/sec")
    
    print(f"\n   📊 PROCESS RESULTS (8 tasks, 4 workers):")
    print(f"      Total time: {process_total_time*1000:.1f}ms")
    print(f"      Avg init: {sum(r['init_time'] for r in process_results)/len(process_results)*1000:.1f}ms")
    print(f"      Avg classify: {sum(r['classify_time'] for r in process_results)/len(process_results)*1000:.1f}ms")
    print(f"      Throughput: {len(process_results)/process_total_time:.1f} docs/sec")
    
    # Check if we're seeing different process IDs
    thread_pids = set(r['process_id'] for r in thread_results)
    process_pids = set(r['process_id'] for r in process_results)
    
    print(f"\n   🔍 Process diversity:")
    print(f"      Threads used {len(thread_pids)} process(es): {thread_pids}")
    print(f"      Processes used {len(process_pids)} process(es): {process_pids}")

def main():
    """Run all diagnostic tests."""
    print("🔬 PERFORMANCE BOTTLENECK DIAGNOSTIC")
    print("=" * 50)
    
    # System info
    print(f"💻 System: {mp.cpu_count()} CPU cores")
    
    test_memory_bottleneck()
    test_io_bottleneck()
    test_initialization_overhead()
    test_thread_vs_process_overhead()
    
    print("\n" + "=" * 50)
    print("🎯 BOTTLENECK ANALYSIS COMPLETE")
    print("Look for the largest time consumers above to identify the real bottleneck!")

if __name__ == "__main__":
    main()