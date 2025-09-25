#!/usr/bin/env python3
"""
Docker-Optimized Queue-Based Document Processing Service
=======================================================
GOAL: Maximize 2-core, 1GB efficiency through queue-based architecture
REASON: Current batch processing underutilizes CPU (5%) and has unpredictable memory
PROBLEM: Need predictable resource usage for Docker deployment

Architecture:
- Bounded request queue (prevents OOM)
- 2 dedicated workers (matches Docker CPU allocation)  
- 10-file processing window (memory-controlled batches)
- Continuous service model (vs batch processing)
"""

import time
import threading
import queue
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import gc

@dataclass
class ProcessingRequest:
    """Individual processing request with metadata"""
    request_id: str
    files: List[Path] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    output_dir: Path = None
    priority: int = 0  # Higher = more urgent
    metadata: Dict[str, Any] = field(default_factory=dict)
    submitted_at: float = field(default_factory=time.time)
    status: str = "queued"  # queued, processing, completed, failed
    result: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServiceMetrics:
    """Docker-optimized service metrics"""
    requests_processed: int = 0
    files_processed: int = 0
    avg_processing_time_ms: float = 0
    memory_usage_mb: float = 0
    cpu_utilization_percent: float = 0
    queue_depth: int = 0
    worker_efficiency: float = 0  # % time workers are busy
    throughput_files_per_sec: float = 0

class DockerOptimizedQueueService:
    """
    Queue-based document processing service optimized for Docker deployment
    
    Constraints:
    - 2 CPU cores maximum
    - 1GB RAM maximum  
    - Predictable resource usage
    - Continuous operation model
    """
    
    def __init__(self, config_path: str = "config/full.yaml"):
        """Initialize Docker-optimized service"""
        # Docker resource constraints
        self.max_memory_mb = 800  # Leave 200MB for system overhead
        self.max_workers = 2      # Match Docker CPU allocation
        self.batch_size = 10      # Memory-safe processing window
        
        # Queue configuration (bounded to prevent OOM)
        self.max_queue_size = 50  # Limit memory pressure
        self.request_queue = queue.PriorityQueue(maxsize=self.max_queue_size)
        
        # Worker management
        self.workers = []
        self.worker_pool = None
        self.is_running = False
        self.shutdown_event = threading.Event()
        
        # Performance monitoring
        self.metrics = ServiceMetrics()
        self.metrics_lock = threading.Lock()
        
        # Processing components (initialized lazily)
        self.processor = None
        self.config = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Load configuration
        self._load_config(config_path)
        
    def _load_config(self, config_path: str):
        """Load processing configuration"""
        import yaml
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            self.logger.info(f"✅ Configuration loaded: {config_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to load config {config_path}: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self):
        """Default configuration for Docker deployment"""
        return {
            'performance': {
                'max_workers': 2,
                'batch_size': 10,
                'memory_limit_mb': 800
            },
            'output': {
                'base_directory': '../output/queue_service'
            }
        }
    
    def start_service(self):
        """Start the queue processing service"""
        if self.is_running:
            self.logger.warning("⚠️  Service already running")
            return
        
        self.logger.info("🚀 Starting Docker-optimized queue service")
        self.logger.info(f"   Max workers: {self.max_workers}")
        self.logger.info(f"   Batch size: {self.batch_size}")
        self.logger.info(f"   Memory limit: {self.max_memory_mb}MB")
        self.logger.info(f"   Queue capacity: {self.max_queue_size}")
        
        # Initialize processing components
        self._initialize_processor()
        
        # Start worker threads
        self.is_running = True
        self.worker_pool = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="QueueWorker")
        
        # Start worker processes
        for i in range(self.max_workers):
            worker_future = self.worker_pool.submit(self._worker_loop, i)
            self.workers.append(worker_future)
        
        # Start metrics collection
        metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
        metrics_thread.start()
        
        self.logger.info("✅ Queue service started")
    
    def stop_service(self):
        """Gracefully stop the service"""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Stopping queue service...")
        
        # Signal shutdown
        self.is_running = False
        self.shutdown_event.set()
        
        # Wait for workers to complete
        if self.worker_pool:
            self.worker_pool.shutdown(wait=True)
        
        self.logger.info("✅ Queue service stopped")
    
    def _initialize_processor(self):
        """Initialize the document processor (lazy initialization)"""
        if self.processor is not None:
            return
        
        self.logger.info("🏗️  Initializing document processor...")
        try:
            # Import and initialize the existing processor
            from pipeline.legacy.service_processor import ServiceProcessor
            
            self.processor = ServiceProcessor(
                config=self.config,
                max_workers=self.max_workers
            )
            
            self.logger.info("✅ Document processor initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize processor: {e}")
            raise
    
    def submit_request(self, 
                      files: List[Union[str, Path]] = None,
                      urls: List[str] = None,
                      output_dir: Union[str, Path] = None,
                      priority: int = 0,
                      metadata: Dict[str, Any] = None) -> str:
        """
        Submit a processing request to the queue
        
        Returns:
            request_id: Unique identifier for tracking
        """
        # Generate unique request ID
        request_id = f"req_{int(time.time() * 1000)}_{threading.get_ident()}"
        
        # Convert paths
        file_paths = [Path(f) for f in (files or [])]
        output_path = Path(output_dir) if output_dir else Path(self.config['output']['base_directory'])
        
        # Create request
        request = ProcessingRequest(
            request_id=request_id,
            files=file_paths,
            urls=urls or [],
            output_dir=output_path,
            priority=priority,
            metadata=metadata or {}
        )
        
        try:
            # Add to queue (blocks if queue is full - provides backpressure)
            self.request_queue.put((priority, time.time(), request), timeout=30)
            
            self.logger.info(f"📥 Request {request_id} queued ({len(file_paths)} files)")
            return request_id
            
        except queue.Full:
            self.logger.error(f"❌ Queue full - request {request_id} rejected")
            raise RuntimeError("Service queue is full - try again later")
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of a specific request"""
        # In a production system, this would query a status store
        # For now, return basic metrics
        with self.metrics_lock:
            return {
                'request_id': request_id,
                'service_metrics': {
                    'queue_depth': self.metrics.queue_depth,
                    'throughput': self.metrics.throughput_files_per_sec,
                    'memory_usage_mb': self.metrics.memory_usage_mb,
                    'cpu_utilization': self.metrics.cpu_utilization_percent
                }
            }
    
    def _worker_loop(self, worker_id: int):
        """Main worker loop - processes batches from queue"""
        worker_name = f"Worker-{worker_id}"
        self.logger.info(f"🔧 {worker_name} started")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Collect batch of requests (up to batch_size)
                batch = self._collect_batch(timeout=1.0)
                
                if not batch:
                    continue  # No requests available
                
                # Process batch
                self.logger.info(f"⚡ {worker_name} processing batch of {len(batch)} requests")
                self._process_batch(batch, worker_id)
                
                # Force garbage collection to manage memory
                gc.collect()
                
            except Exception as e:
                self.logger.error(f"❌ {worker_name} error: {e}")
                time.sleep(0.1)  # Brief pause on error
        
        self.logger.info(f"🔧 {worker_name} stopped")
    
    def _collect_batch(self, timeout: float = 1.0) -> List[ProcessingRequest]:
        """Collect up to batch_size requests from queue"""
        batch = []
        end_time = time.time() + timeout
        
        while len(batch) < self.batch_size and time.time() < end_time:
            try:
                # Get request from queue (blocking with timeout)
                remaining_time = max(0, end_time - time.time())
                _, _, request = self.request_queue.get(timeout=remaining_time)
                batch.append(request)
                self.request_queue.task_done()
                
            except queue.Empty:
                break  # No more requests available
        
        return batch
    
    def _process_batch(self, batch: List[ProcessingRequest], worker_id: int):
        """Process a batch of requests"""
        batch_start = time.time()
        
        # Check memory before processing
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        if memory_mb > self.max_memory_mb:
            self.logger.warning(f"⚠️  High memory usage: {memory_mb:.1f}MB")
            gc.collect()  # Force cleanup
        
        # Extract all files from batch requests
        all_files = []
        request_map = {}  # file -> request mapping
        
        for request in batch:
            request.status = "processing"
            for file_path in request.files:
                all_files.append(file_path)
                request_map[file_path] = request
        
        if not all_files:
            self.logger.warning("📭 Empty batch - no files to process")
            return
        
        try:
            # Process all files in batch using existing processor
            self.logger.info(f"🔄 Processing {len(all_files)} files")
            
            # Use existing service processor for actual document processing
            results = self._process_files_batch(all_files)
            
            # Map results back to requests
            for request in batch:
                request.status = "completed"
                request.result = {
                    'processed_files': len(request.files),
                    'completed_at': time.time()
                }
            
            # Update metrics
            processing_time = (time.time() - batch_start) * 1000
            with self.metrics_lock:
                self.metrics.requests_processed += len(batch)
                self.metrics.files_processed += len(all_files)
                self.metrics.avg_processing_time_ms = (
                    (self.metrics.avg_processing_time_ms + processing_time) / 2
                )
            
            self.logger.info(f"✅ Batch completed: {len(all_files)} files in {processing_time:.1f}ms")
            
        except Exception as e:
            self.logger.error(f"❌ Batch processing failed: {e}")
            for request in batch:
                request.status = "failed"
                request.result = {'error': str(e)}
    
    def _process_files_batch(self, files: List[Path]) -> Dict[str, Any]:
        """Process files using existing service processor"""
        try:
            # Use the existing service processor
            documents, processing_time = self.processor.process_files_service(files)
            return {
                'documents': documents,
                'processing_time': processing_time,
                'files_processed': len(files)
            }
            
        except Exception as e:
            self.logger.error(f"❌ File processing failed: {e}")
            raise
    
    def _metrics_loop(self):
        """Background metrics collection"""
        while self.is_running:
            try:
                # Collect system metrics
                process = psutil.Process()
                
                with self.metrics_lock:
                    self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                    self.metrics.cpu_utilization_percent = process.cpu_percent(interval=1)
                    self.metrics.queue_depth = self.request_queue.qsize()
                
                # Log metrics periodically
                if int(time.time()) % 10 == 0:  # Every 10 seconds
                    self._log_metrics()
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                self.logger.error(f"❌ Metrics collection error: {e}")
    
    def _log_metrics(self):
        """Log current service metrics"""
        with self.metrics_lock:
            m = self.metrics
            self.logger.info(
                f"📊 Metrics: "
                f"Queue: {m.queue_depth}, "
                f"Memory: {m.memory_usage_mb:.1f}MB, "
                f"CPU: {m.cpu_utilization_percent:.1f}%, "
                f"Processed: {m.files_processed} files, "
                f"Avg: {m.avg_processing_time_ms:.1f}ms"
            )
    
    def get_metrics(self) -> ServiceMetrics:
        """Get current service metrics"""
        with self.metrics_lock:
            return ServiceMetrics(
                requests_processed=self.metrics.requests_processed,
                files_processed=self.metrics.files_processed,
                avg_processing_time_ms=self.metrics.avg_processing_time_ms,
                memory_usage_mb=self.metrics.memory_usage_mb,
                cpu_utilization_percent=self.metrics.cpu_utilization_percent,
                queue_depth=self.metrics.queue_depth,
                throughput_files_per_sec=self.metrics.throughput_files_per_sec
            )

def main():
    """Test the queue service"""
    import sys
    import signal
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create service
    service = DockerOptimizedQueueService()
    
    # Graceful shutdown handler
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down service...")
        service.stop_service()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start service
    service.start_service()
    
    # Example: Submit test requests
    test_files = [
        "/home/corey/projects/docling/scout-docs/storage/fbef1082-aeec-48a9-b59b-4dbd2be804f7/DocTest.pdf",
        "/home/corey/projects/docling/scout-docs/storage/dc73e6e0-810a-47ce-abeb-da18f945e963/Complex2.pdf"
    ]
    
    # Submit requests
    for i, file_path in enumerate(test_files):
        try:
            request_id = service.submit_request(
                files=[file_path],
                priority=i,
                metadata={'test_run': True}
            )
            print(f"📥 Submitted request: {request_id}")
        except Exception as e:
            print(f"❌ Failed to submit: {e}")
    
    # Keep service running
    print("🚀 Queue service running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(10)
            metrics = service.get_metrics()
            print(f"📊 Status: {metrics.files_processed} files processed, "
                  f"{metrics.queue_depth} in queue, "
                  f"{metrics.memory_usage_mb:.1f}MB memory")
    except KeyboardInterrupt:
        pass
    
    service.stop_service()

if __name__ == "__main__":
    main()