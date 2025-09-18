#!/usr/bin/env python3
"""
MVP-Fusion Service Processor
============================
Clean I/O + CPU worker architecture for edge service deployment.

Architecture:
- 1 I/O Worker: Non-blocking ingestion (downloads, file reads, PDF conversion)
- N CPU Workers: Pure compute (entity extraction, classification, semantic analysis)
- Work Queue: Async queue between I/O and CPU layers with backpressure
"""

import time
import threading
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty, Full
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from dataclasses import dataclass

from utils.logging_config import get_fusion_logger


@dataclass
class WorkItem:
    """Work item passed from I/O worker to CPU workers"""
    file_path: Path
    markdown_content: str
    source_filename: str
    metadata: Dict[str, Any]
    ingestion_time: float


class ServiceProcessor:
    """
    Clean I/O + CPU service processor for edge deployment.
    
    Separates I/O-bound ingestion from CPU-bound processing with async queue.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_fusion_logger(__name__)
        
        # Worker configuration
        self.cpu_workers = mp.cpu_count()  # Match CPU cores exactly
        self.queue_size = config.get('pipeline', {}).get('queue_size', 100)
        self.memory_limit_mb = config.get('pipeline', {}).get('memory_limit_mb', 100)
        
        # Work queue between I/O and CPU layers
        self.work_queue = Queue(maxsize=self.queue_size)
        
        # Processing state
        self.active = False
        self.io_worker = None
        self.cpu_executor = None
        
        self.logger.stage(f"🏗️  Service Processor initialized: 1 I/O + {self.cpu_workers} CPU workers")
        self.logger.logger.debug(f"📋 Queue size: {self.queue_size}, Memory limit: {self.memory_limit_mb}MB")
    
    def start_service(self):
        """Start the I/O + CPU worker service"""
        if self.active:
            self.logger.logger.warning("⚠️  Service already running")
            return
        
        self.active = True
        self.logger.stage("🚀 Starting I/O + CPU service...")
        
        # Start CPU worker pool
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=self.cpu_workers, 
            thread_name_prefix="CPUWorker"
        )
        
        self.logger.stage(f"✅ Service started: 1 I/O worker + {self.cpu_workers} CPU workers")
    
    def stop_service(self):
        """Stop the I/O + CPU worker service"""
        if not self.active:
            return
        
        self.logger.stage("🛑 Stopping I/O + CPU service...")
        self.active = False
        
        # Stop CPU workers
        if self.cpu_executor:
            self.cpu_executor.shutdown(wait=True)
            self.cpu_executor = None
        
        self.logger.stage("✅ Service stopped")
    
    def _io_worker_ingestion(self, file_paths: List[Path]) -> None:
        """
        I/O Worker: Handle all I/O-bound operations.
        
        Responsibilities:
        - File reading and validation
        - PDF to markdown conversion  
        - URL downloading
        - Feed work items to CPU queue
        """
        # Set thread name for worker tagging
        threading.current_thread().name = "IOWorker-1"
        
        self.logger.stage(f"📥 I/O worker starting ingestion of {len(file_paths)} files")
        
        for i, file_path in enumerate(file_paths):
            if not self.active:
                break
            
            ingestion_start = time.perf_counter()
            
            try:
                self.logger.logger.debug(f"📂 Reading file: {file_path.name}")
                
                # Simulate file reading and PDF conversion (I/O bound)
                if file_path.suffix.lower() == '.pdf':
                    self.logger.logger.debug(f"🔄 Converting PDF to markdown: {file_path.name}")
                    # TODO: Actual PDF conversion logic here
                    markdown_content = f"# Converted content from {file_path.name}\n\nSample markdown content..."
                else:
                    # Read text files directly
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        markdown_content = f.read()
                
                # Create work item for CPU workers
                work_item = WorkItem(
                    file_path=file_path,
                    markdown_content=markdown_content,
                    source_filename=file_path.name,
                    metadata={'conversion_time': time.perf_counter() - ingestion_start},
                    ingestion_time=time.perf_counter()
                )
                
                # Add to queue with backpressure handling
                try:
                    self.work_queue.put(work_item, timeout=5.0)
                    self.logger.logger.debug(f"✅ Queued for CPU processing: {file_path.name}")
                except Full:
                    self.logger.logger.warning(f"⚠️  Queue full, dropping: {file_path.name}")
                    
            except Exception as e:
                self.logger.logger.error(f"❌ I/O error processing {file_path.name}: {e}")
        
        # Signal completion to CPU workers
        for _ in range(self.cpu_workers):
            self.work_queue.put(None)  # Sentinel value
        
        self.logger.stage(f"✅ I/O worker completed ingestion of {len(file_paths)} files")
    
    def _cpu_worker_processing(self, worker_id: int) -> List[Dict[str, Any]]:
        """
        CPU Worker: Handle all CPU-bound operations.
        
        Responsibilities:
        - Entity extraction
        - Document classification
        - Semantic analysis
        - JSON generation
        """
        # Set thread name for worker tagging
        threading.current_thread().name = f"CPUWorker-{worker_id}"
        
        results = []
        self.logger.logger.debug(f"🧠 CPU worker {worker_id} started")
        
        while self.active:
            try:
                # Get work from I/O queue
                work_item = self.work_queue.get(timeout=1.0)
                
                # Check for completion signal
                if work_item is None:
                    break
                
                # Process work item (CPU bound)
                processing_start = time.perf_counter()
                
                self.logger.logger.debug(f"⚙️  Processing entities: {work_item.source_filename}")
                
                # TODO: Actual entity extraction, classification, semantic analysis
                # This is where the real CPU-intensive work happens
                processed_result = {
                    'file_path': str(work_item.file_path),
                    'source_filename': work_item.source_filename,
                    'processing_time': time.perf_counter() - processing_start,
                    'ingestion_time': work_item.metadata.get('conversion_time', 0),
                    'queue_wait_time': processing_start - work_item.ingestion_time,
                    'worker_id': worker_id,
                    'success': True
                }
                
                results.append(processed_result)
                self.logger.logger.debug(f"✅ Completed processing: {work_item.source_filename}")
                
            except Empty:
                # Normal timeout, continue checking
                continue
            except Exception as e:
                self.logger.logger.error(f"❌ CPU worker {worker_id} error: {e}")
        
        self.logger.logger.debug(f"🏁 CPU worker {worker_id} finished: {len(results)} items processed")
        return results
    
    def process_files_service(self, file_paths: List[Path]) -> tuple[List[Dict[str, Any]], float]:
        """
        Process files using clean I/O + CPU service architecture.
        
        Returns:
            Tuple of (results_list, total_processing_time)
        """
        if not self.active:
            self.start_service()
        
        total_start = time.perf_counter()
        
        self.logger.stage(f"🚀 Processing {len(file_paths)} files with I/O + CPU service")
        
        # Start I/O worker thread
        io_thread = threading.Thread(
            target=self._io_worker_ingestion,
            args=(file_paths,),
            name="IOWorker-1"
        )
        io_thread.start()
        
        # Start CPU worker futures
        cpu_futures = []
        for worker_id in range(1, self.cpu_workers + 1):
            future = self.cpu_executor.submit(self._cpu_worker_processing, worker_id)
            cpu_futures.append(future)
        
        # Wait for I/O completion
        io_thread.join()
        self.logger.stage("✅ I/O ingestion completed")
        
        # Collect CPU results
        all_results = []
        for i, future in enumerate(cpu_futures):
            worker_results = future.result()
            all_results.extend(worker_results)
            self.logger.logger.debug(f"📊 CPU worker {i+1} returned {len(worker_results)} results")
        
        total_time = time.perf_counter() - total_start
        
        self.logger.stage(f"✅ Service processing complete: {len(all_results)} results in {total_time:.2f}s")
        
        return all_results, total_time


if __name__ == "__main__":
    # Test the service processor
    from utils.logging_config import setup_logging
    
    setup_logging(verbosity=3, log_file=None, use_colors=False)
    
    config = {'pipeline': {'queue_size': 10, 'memory_limit_mb': 100}}
    processor = ServiceProcessor(config)
    
    # Test with sample files
    test_files = [
        Path('/tmp/test1.txt'),
        Path('/tmp/test2.txt')
    ]
    
    # Create test files
    for f in test_files:
        f.write_text(f"Sample content for {f.name}")
    
    try:
        results, timing = processor.process_files_service(test_files)
        print(f"\n✅ Test completed: {len(results)} results in {timing:.2f}s")
        
        for result in results:
            print(f"  - {result['source_filename']}: worker {result['worker_id']}, "
                  f"processing {result['processing_time']:.3f}s")
    finally:
        processor.stop_service()
        # Clean up test files
        for f in test_files:
            f.unlink(missing_ok=True)