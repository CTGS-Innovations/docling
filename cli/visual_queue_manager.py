#!/usr/bin/env python3
"""
Visual Queue Management System
=============================

Manages queuing and processing of visual elements that require enhanced GPU processing.
Implements intelligent batching, priority scheduling, and result stitching.

Features:
- Priority-based queue management
- Batch optimization for GPU efficiency
- Progress tracking and status updates
- Result stitching back to original documents
- Concurrent processing support
"""

import time
import json
import threading
import queue
import tempfile
import subprocess
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import uuid
import hashlib


class JobStatus(Enum):
    """Status of visual processing jobs."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ElementType(Enum):
    """Types of visual elements."""
    IMAGE = "image"
    TABLE = "table" 
    FORMULA = "formula"
    CHART = "chart"
    DIAGRAM = "diagram"
    COMPLEX_LAYOUT = "complex_layout"


class Priority(Enum):
    """Processing priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class VisualJob:
    """A visual processing job."""
    job_id: str
    document_id: str
    document_path: Path
    element_type: ElementType
    page_number: int
    bbox: Optional[Tuple[float, float, float, float]]
    priority: Priority
    created_time: datetime
    estimated_processing_time: float
    docling_flags: List[str]  # Specific flags for this job
    placeholder_id: Optional[str] = None  # Original placeholder ID for integration
    
    # Status tracking
    status: JobStatus = JobStatus.QUEUED
    started_time: Optional[datetime] = None
    completed_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Results
    enhanced_content: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class BatchJob:
    """A batch of visual jobs for efficient processing."""
    batch_id: str
    jobs: List[VisualJob]
    batch_type: ElementType
    priority: Priority
    created_time: datetime
    estimated_total_time: float
    
    # Processing info
    docling_command: List[str]
    temp_directory: Optional[Path] = None
    status: JobStatus = JobStatus.QUEUED


@dataclass
class ProcessingStats:
    """Statistics for queue performance monitoring."""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    average_processing_time: float = 0.0
    queue_length: int = 0
    active_batches: int = 0
    throughput_per_minute: float = 0.0
    last_update: datetime = None


class VisualQueueManager:
    """Manages visual processing queue with intelligent batching."""
    
    def __init__(self, max_workers: int = 2, batch_timeout: float = 5.0):
        self.max_workers = max_workers
        self.batch_timeout = batch_timeout
        
        # Setup detailed logging
        self.log_file = Path("/home/corey/projects/docling/cli/vlm_processing.log")
        self.log_file.parent.mkdir(exist_ok=True)
        
        # Clear previous log
        with open(self.log_file, 'w') as f:
            f.write(f"=== VLM PROCESSING LOG - {datetime.now()} ===\n\n")
        
        # Queue management
        self.job_queue = queue.PriorityQueue()
        self.queued_jobs: Dict[str, VisualJob] = {}  # Track ALL queued jobs
        self.active_jobs: Dict[str, VisualJob] = {}
        self.completed_jobs: Dict[str, VisualJob] = {}
        self.failed_jobs: Dict[str, VisualJob] = {}
        
        # Batch management
        self.pending_batches: List[BatchJob] = []
        self.active_batches: Dict[str, BatchJob] = {}
        
        # Worker threads
        self.workers: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        
        # Stats and monitoring
        self.stats = ProcessingStats()
        self.callbacks: List[Callable] = []
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Start batch processor
        print(f"🚀 Starting VLM queue manager with {max_workers} workers")
        try:
            # Don't use daemon threads - we need them to stay alive
            self.batch_thread = threading.Thread(target=self._batch_processor, daemon=False)
            self.batch_thread.start()
            print("📦 Batch processor thread started")
            
            # Start worker threads
            for i in range(max_workers):
                worker = threading.Thread(target=self._worker, name=f"VisualWorker-{i}", daemon=False)
                worker.start()
                self.workers.append(worker)
                print(f"👷 Worker thread {i} started")
            
            print("✅ VLM queue manager initialization complete")
            
            # Give threads a moment to start
            time.sleep(0.1)
            print(f"🔍 Thread status check:")
            print(f"   Batch thread alive: {self.batch_thread.is_alive()}")
            for i, worker in enumerate(self.workers):
                print(f"   Worker {i} alive: {worker.is_alive()}")
                
        except Exception as e:
            print(f"❌ Error starting VLM queue manager: {e}")
            import traceback
            traceback.print_exc()
    
    def _log(self, message: str):
        """Thread-safe logging to file and console."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {message}\n"
        
        # Print to console
        print(message)
        
        # Write to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_line)
        except Exception:
            pass  # Don't let logging errors crash the system
    
    def add_job(self, document_path: Path, element_type: ElementType, 
                page_number: int, priority: Priority = Priority.NORMAL,
                bbox: Optional[Tuple[float, float, float, float]] = None,
                estimated_time: float = 5.0,
                docling_flags: Optional[List[str]] = None,
                placeholder_id: Optional[str] = None) -> str:
        """
        Add a visual processing job to the queue.
        
        Returns:
            job_id: Unique identifier for tracking the job
        """
        
        job_id = str(uuid.uuid4())
        document_id = self._get_document_id(document_path)
        
        if docling_flags is None:
            docling_flags = self._get_default_flags(element_type)
        
        job = VisualJob(
            job_id=job_id,
            document_id=document_id,
            document_path=document_path,
            element_type=element_type,
            page_number=page_number,
            bbox=bbox,
            priority=priority,
            created_time=datetime.now(),
            estimated_processing_time=estimated_time,
            docling_flags=docling_flags,
            placeholder_id=placeholder_id,
            metadata={}
        )
        
        with self.lock:
            # Add to priority queue (lower priority value = higher priority)
            self.job_queue.put((priority.value, time.time(), job))
            # Track in queued_jobs so we can find it
            self.queued_jobs[job_id] = job
            self.stats.total_jobs += 1
            self.stats.queue_length += 1
            self._update_stats()
        
        self._log(f"🎯 Queued job {job_id[:8]}: {element_type.value} on page {page_number} of {document_path.name}")
        self._log(f"📊 Queue stats: {self.job_queue.qsize()} jobs queued, {len(self.active_jobs)} active")
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[VisualJob]:
        """Get current status of a job."""
        with self.lock:
            if job_id in self.queued_jobs:
                return self.queued_jobs[job_id]
            elif job_id in self.active_jobs:
                return self.active_jobs[job_id]
            elif job_id in self.completed_jobs:
                return self.completed_jobs[job_id]
            elif job_id in self.failed_jobs:
                return self.failed_jobs[job_id]
        return None
    
    def get_document_jobs(self, document_path: Path) -> List[VisualJob]:
        """Get all jobs for a specific document."""
        document_id = self._get_document_id(document_path)
        jobs = []
        
        with self.lock:
            # Include queued jobs too!
            for job_dict in [self.queued_jobs, self.active_jobs, self.completed_jobs, self.failed_jobs]:
                for job in job_dict.values():
                    if job.document_id == document_id:
                        jobs.append(job)
        
        return sorted(jobs, key=lambda j: j.page_number)
    
    def get_queue_stats(self) -> ProcessingStats:
        """Get current queue statistics."""
        with self.lock:
            return self.stats
    
    def add_callback(self, callback: Callable[[VisualJob], None]):
        """Add callback for job completion notifications."""
        self.callbacks.append(callback)
    
    def wait_for_document(self, document_path: Path, timeout: float = 300.0) -> List[VisualJob]:
        """
        Wait for all jobs for a document to complete.
        
        Returns:
            List of completed jobs for the document
        """
        document_id = self._get_document_id(document_path)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            doc_jobs = self.get_document_jobs(document_path)
            
            if all(job.status in [JobStatus.COMPLETED, JobStatus.FAILED] for job in doc_jobs):
                return [job for job in doc_jobs if job.status == JobStatus.COMPLETED]
            
            time.sleep(0.5)
        
        # Timeout
        print(f"⚠️  Timeout waiting for {document_path.name} jobs to complete")
        return []
    
    def shutdown(self, timeout: float = 30.0):
        """Shutdown the queue manager gracefully."""
        print("🛑 Shutting down visual queue manager...")
        self._log("🛑 Shutdown initiated")
        
        # Process any remaining jobs in queue first
        remaining = self.job_queue.qsize()
        pending = len(self.pending_batches)
        active = len(self.active_batches)
        
        if remaining > 0 or pending > 0 or active > 0:
            print(f"⏳ Status: {remaining} queued jobs, {pending} pending batches, {active} active batches")
            self._log(f"⏳ Status at shutdown: {remaining} queued, {pending} pending, {active} active")
            # Give more time to process
            time.sleep(3.0)
        
        # Now signal shutdown
        self.shutdown_event.set()
        self._log("🚦 Shutdown event set")
        
        # Wait for workers to finish
        for i, worker in enumerate(self.workers):
            print(f"⏳ Waiting for worker {i}...")
            worker.join(timeout=timeout/len(self.workers))
        
        if self.batch_thread.is_alive():
            print("⏳ Waiting for batch processor...")
            self.batch_thread.join(timeout=timeout/2)
        
        self._log(f"✅ Shutdown complete: {len(self.completed_jobs)} completed, {len(self.failed_jobs)} failed")
        print(f"✅ Visual queue manager shutdown complete: {len(self.completed_jobs)} completed, {len(self.failed_jobs)} failed")
    
    def _batch_processor(self):
        """Background thread that creates batches from queued jobs."""
        self._log("🏭 Batch processor thread started")
        
        # Give a moment for initial jobs to be queued
        time.sleep(0.2)
        
        while not self.shutdown_event.is_set():
            try:
                jobs_before = self.job_queue.qsize()
                
                # Only log and process if there are jobs
                if jobs_before > 0:
                    self._log(f"🔄 Batch processor: Found {jobs_before} jobs to batch")
                    self._create_batches()
                    jobs_after = self.job_queue.qsize()
                    self._log(f"✅ After batching: {jobs_after} jobs remain in queue")
                
                # Short sleep to be more responsive
                time.sleep(0.1)  # Check even more frequently
                
            except Exception as e:
                self._log(f"❌ Batch processor error: {e}")
                import traceback
                self._log(f"Stack trace: {traceback.format_exc()}")
                time.sleep(2.0)
        self._log("🏭 Batch processor thread stopping")
    
    def _create_batches(self):
        """Create processing batches from queued jobs."""
        queue_size = self.job_queue.qsize()
        queue_empty = self.job_queue.empty()
        self._log(f"🔍 Batch creation check: queue size={queue_size}, empty={queue_empty}")
        
        if self.job_queue.empty():
            return
        
        # Collect jobs for batching
        jobs_to_batch = []
        collected_jobs = []
        
        # Collect jobs immediately - don't wait for batch timeout
        self._log(f"🔍 Creating batches from {self.job_queue.qsize()} queued jobs")
        
        while (not self.job_queue.empty() and 
               len(collected_jobs) < 10):  # Max batch size
            
            try:
                priority, queue_time, job = self.job_queue.get(timeout=0.1)
                collected_jobs.append(job)
                # Move from queued to active
                with self.lock:
                    if job.job_id in self.queued_jobs:
                        del self.queued_jobs[job.job_id]
                    self.active_jobs[job.job_id] = job
                    job.status = JobStatus.PROCESSING
                self._log(f"   Collected job {job.job_id[:8]} for batching")
            except queue.Empty:
                break
        
        self._log(f"📦 Collected {len(collected_jobs)} jobs for batching")
        
        if not collected_jobs:
            return
        
        # Group jobs by type and document for optimal batching
        batches = self._group_jobs_for_batching(collected_jobs)
        
        with self.lock:
            for batch in batches:
                self.pending_batches.append(batch)
                print(f"📦 Created batch {batch.batch_id[:8]}: {len(batch.jobs)} {batch.batch_type.value} jobs")
                print(f"📊 Queue status: {len(self.pending_batches)} pending batches, {len(self.active_batches)} active batches")
    
    def _group_jobs_for_batching(self, jobs: List[VisualJob]) -> List[BatchJob]:
        """Group jobs into optimal batches."""
        batches = []
        
        # Group by element type and document
        grouped = {}
        for job in jobs:
            key = (job.element_type, job.document_id)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(job)
        
        # Create batches
        for (element_type, document_id), job_group in grouped.items():
            batch_id = str(uuid.uuid4())
            
            # Calculate batch priority (highest individual priority)
            batch_priority = max((job.priority for job in job_group), key=lambda p: p.value)
            
            # Calculate estimated total time
            total_time = sum(job.estimated_processing_time for job in job_group)
            
            # Generate docling command for this batch
            docling_command = self._generate_batch_command(job_group)
            
            batch = BatchJob(
                batch_id=batch_id,
                jobs=job_group,
                batch_type=element_type,
                priority=batch_priority,
                created_time=datetime.now(),
                estimated_total_time=total_time,
                docling_command=docling_command
            )
            
            batches.append(batch)
        
        return batches
    
    def _generate_batch_command(self, jobs: List[VisualJob]) -> List[str]:
        """Generate optimal docling command for a batch of jobs."""
        
        # Get the document path (all jobs in batch should be same document)
        document_path = jobs[0].document_path
        element_type = jobs[0].element_type
        
        # Use local docling from virtual environment (CLI folder allows Python)
        # Base command runs docling locally
        cmd = [
            '/home/corey/projects/docling/cli/.venv/bin/docling',
            str(document_path),
            '--to', 'md'
        ]
        
        # Add flags based on element type - optimize for each content type
        if element_type == ElementType.TABLE:
            cmd.extend([
                '--table-mode', 'accurate'  # Extract tables as proper markdown tables
            ])
        elif element_type in [ElementType.IMAGE, ElementType.CHART, ElementType.DIAGRAM]:
            cmd.extend([
                '--pipeline', 'vlm',
                '--vlm-model', 'smoldocling',
                '--enrich-picture-description'
            ])
        elif element_type == ElementType.FORMULA:
            cmd.extend([
                '--pipeline', 'vlm',
                '--vlm-model', 'smoldocling'
            ])
        else:
            # Default: comprehensive processing for mixed content
            cmd.extend([
                '--table-mode', 'accurate',
                '--pipeline', 'vlm', 
                '--vlm-model', 'smoldocling'
            ])
        
        return cmd
    
    def _worker(self):
        """Worker thread that processes batches."""
        worker_name = threading.current_thread().name
        self._log(f"👷 Worker {worker_name} started")
        while not self.shutdown_event.is_set():
            try:
                batch = self._get_next_batch()
                if batch:
                    self._log(f"👷 Worker {worker_name} got batch {batch.batch_id[:8]} with {len(batch.jobs)} jobs")
                    self._process_batch(batch)
                else:
                    time.sleep(0.5)  # No work available
            except Exception as e:
                self._log(f"❌ Worker {worker_name} error: {e}")
                import traceback
                self._log(f"Stack trace: {traceback.format_exc()}")
                time.sleep(2.0)
        self._log(f"👷 Worker {worker_name} stopping")
    
    def _get_next_batch(self) -> Optional[BatchJob]:
        """Get the next batch to process (highest priority first)."""
        with self.lock:
            if not self.pending_batches:
                return None
            
            # Sort by priority (higher priority value = higher priority)
            self.pending_batches.sort(key=lambda b: b.priority.value, reverse=True)
            
            batch = self.pending_batches.pop(0)
            self.active_batches[batch.batch_id] = batch
            
            # Mark jobs as processing
            for job in batch.jobs:
                job.status = JobStatus.PROCESSING
                job.started_time = datetime.now()
                self.active_jobs[job.job_id] = job
            
            return batch
    
    def _process_batch(self, batch: BatchJob):
        """Process a batch of visual jobs."""
        print(f"🔄 Processing batch {batch.batch_id[:8]}: {len(batch.jobs)} jobs")
        
        start_time = time.time()
        
        try:
            # Create temporary output directory in CLI folder for staging
            cli_temp_dir = Path('/home/corey/projects/docling/cli/temp')
            cli_temp_dir.mkdir(exist_ok=True)
            
            with tempfile.TemporaryDirectory(dir=cli_temp_dir) as temp_dir:
                temp_path = Path(temp_dir)
                batch.temp_directory = temp_path
                
                # NEW APPROACH: Extract individual images and process them separately
                if batch.batch_type in [ElementType.IMAGE, ElementType.CHART, ElementType.DIAGRAM]:
                    self._process_individual_images(batch, temp_path)
                else:
                    # Fallback to original approach for other types
                    self._process_full_document(batch, temp_path)
                    
        except subprocess.TimeoutExpired:
            self._mark_batch_failed(batch, "Processing timeout")
        except Exception as e:
            self._mark_batch_failed(batch, str(e))
        
        finally:
            # Clean up
            with self.lock:
                if batch.batch_id in self.active_batches:
                    del self.active_batches[batch.batch_id]
                
                processing_time = time.time() - start_time
                print(f"⏱️  Batch {batch.batch_id[:8]} completed in {processing_time:.1f}s")
    
    def _process_batch_results(self, batch: BatchJob, output_dir: Path, stdout: str):
        """Process successful batch results."""
        
        # Find output files
        output_files = list(output_dir.glob('*.md'))
        
        if output_files:
            # Read the enhanced content
            output_file = output_files[0]  # Assume single file output
            with open(output_file, 'r', encoding='utf-8') as f:
                enhanced_content = f.read()
            
            # Log the VLM output for debugging
            print(f"📄 VLM Output File: {output_file}")
            print(f"📊 VLM Content Length: {len(enhanced_content)} characters")
            print(f"🔍 VLM Raw Content (first 500 chars):")
            print(f"   {repr(enhanced_content[:500])}")
            
            # Save full VLM output for verification
            verification_file = "/home/corey/projects/docling/cli/temp/full_vlm_output.md"
            with open(verification_file, 'w') as f:
                f.write("# Full VLM Output\n\n")
                f.write(f"**Source File**: {output_file}\n\n")
                f.write(f"**Content Length**: {len(enhanced_content)} characters\n\n")
                f.write("## Complete VLM Content:\n\n")
                f.write(enhanced_content)
            print(f"💾 Saved full VLM output to: {verification_file}")
            
            # Check for common patterns
            if 'table' in enhanced_content.lower():
                print(f"📊 TABLE content detected in VLM output")
            if 'chart' in enhanced_content.lower() or 'graph' in enhanced_content.lower():
                print(f"📈 CHART/GRAPH content detected in VLM output")
            if '|' in enhanced_content and enhanced_content.count('|') > 5:
                print(f"📋 MARKDOWN TABLE structure detected in VLM output")
            
            # Mark all jobs as completed
            with self.lock:
                for job in batch.jobs:
                    job.status = JobStatus.COMPLETED
                    job.completed_time = datetime.now()
                    job.enhanced_content = enhanced_content
                    print(f"✅ Job {job.job_id[:8]} completed: {job.element_type.value} on page {job.page_number}")
                    job.metadata = {
                        "batch_id": batch.batch_id,
                        "processing_method": "docling_" + batch.batch_type.value,
                        "output_file": str(output_file)
                    }
                    
                    # Move to completed jobs
                    if job.job_id in self.active_jobs:
                        del self.active_jobs[job.job_id]
                    self.completed_jobs[job.job_id] = job
                    
                    self.stats.completed_jobs += 1
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(job)
                        except Exception as e:
                            print(f"⚠️  Callback error: {e}")
                
                self._update_stats()
        
        else:
            self._mark_batch_failed(batch, "No output files generated")
    
    def _mark_batch_failed(self, batch: BatchJob, error_message: str):
        """Mark all jobs in a batch as failed."""
        print(f"❌ Batch {batch.batch_id[:8]} failed: {error_message}")
        
        with self.lock:
            for job in batch.jobs:
                job.status = JobStatus.FAILED
                job.completed_time = datetime.now()
                job.error_message = error_message
                
                # Move to failed jobs
                if job.job_id in self.active_jobs:
                    del self.active_jobs[job.job_id]
                self.failed_jobs[job.job_id] = job
                
                self.stats.failed_jobs += 1
            
            self._update_stats()
    
    def _get_document_id(self, document_path: Path) -> str:
        """Generate unique document ID."""
        return hashlib.md5(str(document_path).encode()).hexdigest()[:12]
    
    def _get_default_flags(self, element_type: ElementType) -> List[str]:
        """Get default docling flags for element type."""
        
        flags_map = {
            ElementType.IMAGE: ['--enrich-picture-description'],
            ElementType.TABLE: ['--table-mode', 'accurate'],
            ElementType.FORMULA: ['--enrich-formula'],
            ElementType.CHART: ['--enrich-picture-description'],
            ElementType.DIAGRAM: ['--enrich-picture-description'],
            ElementType.COMPLEX_LAYOUT: ['--pipeline', 'vlm']
        }
        
        return flags_map.get(element_type, [])
    
    def _update_stats(self):
        """Update processing statistics."""
        current_time = datetime.now()
        
        self.stats.queue_length = self.job_queue.qsize()
        self.stats.active_batches = len(self.active_batches)
        
        if self.stats.completed_jobs > 0:
            # Calculate throughput (jobs per minute)
            if self.stats.last_update:
                time_diff = (current_time - self.stats.last_update).total_seconds() / 60.0
                if time_diff > 0:
                    recent_completions = 1  # This update represents 1 completion
                    self.stats.throughput_per_minute = recent_completions / time_diff
        
        self.stats.last_update = current_time

    def _process_individual_images(self, batch: BatchJob, temp_path: Path):
        """Extract and process individual images from PDF."""
        print(f"🖼️  Processing individual images for batch {batch.batch_id[:8]}")
        
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("❌ PyMuPDF not available, falling back to full document processing")
            self._process_full_document(batch, temp_path)
            return
            
        document_path = batch.jobs[0].document_path
        
        try:
            # Open PDF document
            doc = fitz.open(str(document_path))
            
            # Process each job (each represents a specific visual element)
            for job in batch.jobs:
                page_num = job.page_number - 1  # PyMuPDF uses 0-based indexing
                
                if page_num < len(doc):
                    page = doc[page_num]
                    
                    # Extract all images from this page
                    images = page.get_images()
                    
                    if images:
                        # Select the appropriate image for this job
                        # If we have multiple images, use the job's figure number or position
                        img_index = 0  # Default to first image
                        
                        # Try to match figure number from placeholder description
                        if hasattr(job, 'description') and 'Figure' in job.description:
                            import re
                            fig_match = re.search(r'Figure\s+(\d+)', job.description)
                            if fig_match:
                                fig_num = int(fig_match.group(1))
                                # Use figure number as index (Figure 1 = index 0, Figure 2 = index 1)
                                img_index = min(fig_num - 1, len(images) - 1)
                                print(f"   📍 Selecting image {img_index} for {job.description}")
                        
                        # Ensure we don't go out of bounds
                        img_index = max(0, min(img_index, len(images) - 1))
                        
                        if img_index < len(images):
                            # Extract the image
                            xref = images[img_index][0]
                            base_image = doc.extract_image(xref)
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]
                            
                            # Save image to temp file
                            image_filename = f"extracted_image_{job.placeholder_id}.{image_ext}"
                            image_path = temp_path / image_filename
                            
                            with open(image_path, "wb") as img_file:
                                img_file.write(image_bytes)
                            
                            print(f"💾 Extracted image for {job.placeholder_id}: {image_path}")
                            
                            # Process this specific image with docling VLM
                            self._process_single_image(job, image_path, temp_path)
                        else:
                            print(f"⚠️  No image {img_index} found on page {page_num + 1}")
                            job.status = JobStatus.FAILED
                            job.error_message = f"Image not found on page {page_num + 1}"
                    else:
                        print(f"⚠️  No images found on page {page_num + 1}")
                        job.status = JobStatus.FAILED
                        job.error_message = f"No images on page {page_num + 1}"
                else:
                    print(f"⚠️  Page {page_num + 1} not found in document")
                    job.status = JobStatus.FAILED
                    job.error_message = f"Page {page_num + 1} not found"
            
            doc.close()
            
        except Exception as e:
            print(f"❌ Error extracting images: {e}")
            self._mark_batch_failed(batch, f"Image extraction failed: {e}")
    
    def _process_single_image(self, job: VisualJob, image_path: Path, temp_path: Path):
        """Process a single extracted image with docling VLM."""
        try:
            # Create docling command matching the successful manual test
            cmd = [
                '/home/corey/projects/docling/cli/.venv/bin/docling',
                str(image_path),
                '--to', 'md',
                '--pipeline', 'vlm',
                '--vlm-model', 'smoldocling',
                '--device', 'auto',
                '--output', str(temp_path),
                '-v'  # Verbose logging
            ]
            
            self._log(f"🔄 Processing {job.placeholder_id} with: {' '.join(cmd)}")
            
            # Execute docling command
            env = {
                'PATH': '/home/corey/projects/docling/cli/.venv/bin:' + os.environ.get('PATH', ''),
                'VIRTUAL_ENV': '/home/corey/projects/docling/cli/.venv'
            }
            env.update(os.environ)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd='/home/corey/projects/docling/cli',
                env=env
            )
            
            self._log(f"📋 Docling result: returncode={result.returncode}")
            self._log(f"📤 Stdout: {result.stdout if result.stdout else 'None'}")
            if result.stderr:
                self._log(f"❌ Stderr: {result.stderr}")
            
            if result.returncode == 0:
                # Success - find the output file (docling creates .md file with same name as image)
                image_name = image_path.stem  # Get filename without extension
                expected_output = temp_path / f"{image_name}.md"
                
                if expected_output.exists():
                    with open(expected_output, 'r', encoding='utf-8') as f:
                        enhanced_content = f.read()
                    
                    job.enhanced_content = enhanced_content
                    job.status = JobStatus.COMPLETED
                    job.completed_time = datetime.now()
                    
                    print(f"✅ {job.placeholder_id} processed successfully ({len(enhanced_content)} chars)")
                    print(f"🔍 Content preview: {repr(enhanced_content[:200])}")
                    
                    # Move job to completed jobs dict
                    with self.lock:
                        if job.job_id in self.active_jobs:
                            del self.active_jobs[job.job_id]
                        self.completed_jobs[job.job_id] = job
                        self.stats.completed_jobs += 1
                    
                else:
                    job.status = JobStatus.FAILED
                    job.error_message = f"No output file found at {expected_output}"
                    print(f"❌ No output file found for {job.placeholder_id} at {expected_output}")
                    
                    # Move to failed jobs dict
                    with self.lock:
                        if job.job_id in self.active_jobs:
                            del self.active_jobs[job.job_id]
                        self.failed_jobs[job.job_id] = job
                        self.stats.failed_jobs += 1
            else:
                job.status = JobStatus.FAILED
                job.error_message = f"Docling failed (exit {result.returncode}): {result.stderr}"
                print(f"❌ Docling failed for {job.placeholder_id}: {result.stderr}")
                
                # Move to failed jobs dict
                with self.lock:
                    if job.job_id in self.active_jobs:
                        del self.active_jobs[job.job_id]
                    self.failed_jobs[job.job_id] = job
                    self.stats.failed_jobs += 1
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = f"Processing error: {e}"
            print(f"❌ Error processing {job.placeholder_id}: {e}")
    
    def _process_full_document(self, batch: BatchJob, temp_path: Path):
        """Fallback: Process full document (original approach)."""
        print(f"📄 Processing full document for batch {batch.batch_id[:8]}")
        
        # Add output directory to command and prevent binary data embedding
        cmd = batch.docling_command + ['--image-export-mode', 'placeholder', '--output', str(temp_path)]
        
        print(f"🔄 Running: {' '.join(cmd)}")
        
        # Execute docling command with virtual environment
        env = {
            'PATH': '/home/corey/projects/docling/cli/.venv/bin:' + os.environ.get('PATH', ''),
            'VIRTUAL_ENV': '/home/corey/projects/docling/cli/.venv'
        }
        env.update(os.environ)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd='/home/corey/projects/docling/cli',
                env=env
            )
            
            if result.returncode == 0:
                # Success - process results
                print(f"✅ Docling command succeeded for batch {batch.batch_id[:8]}")
                self._process_batch_results(batch, temp_path, result.stdout)
            else:
                # Failure
                error_msg = f"Docling failed (exit {result.returncode}): {result.stderr}"
                print(f"❌ Docling command failed: {error_msg}")
                self._mark_batch_failed(batch, error_msg)
                
        except subprocess.TimeoutExpired:
            self._mark_batch_failed(batch, "Processing timeout")
        except Exception as e:
            self._mark_batch_failed(batch, str(e))


def main():
    """Test the visual queue manager."""
    print("🎬 VISUAL QUEUE MANAGER TEST")
    print("=" * 50)
    
    # Initialize queue manager
    queue_manager = VisualQueueManager(max_workers=1, batch_timeout=2.0)
    
    # Find test files
    data_dir = Path('/home/corey/projects/docling/cli/data')
    pdf_files = list(data_dir.glob('**/*.pdf'))[:3]  # Test with 3 PDFs
    
    if not pdf_files:
        print("No PDF files found for testing")
        return
    
    # Add some test jobs
    job_ids = []
    
    for pdf_file in pdf_files:
        # Add image processing job
        job_id = queue_manager.add_job(
            document_path=pdf_file,
            element_type=ElementType.IMAGE,
            page_number=1,
            priority=Priority.HIGH,
            estimated_time=3.0
        )
        job_ids.append(job_id)
        
        # Add table processing job
        job_id = queue_manager.add_job(
            document_path=pdf_file,
            element_type=ElementType.TABLE,
            page_number=1,
            priority=Priority.NORMAL,
            estimated_time=2.0
        )
        job_ids.append(job_id)
    
    print(f"\n🎯 Added {len(job_ids)} jobs to queue")
    
    # Monitor progress
    print("\n📊 Monitoring queue progress...")
    
    start_time = time.time()
    
    while time.time() - start_time < 60:  # Monitor for 1 minute max
        stats = queue_manager.get_queue_stats()
        
        print(f"\r   Queue: {stats.queue_length} | Active: {len(queue_manager.active_jobs)} | Completed: {stats.completed_jobs} | Failed: {stats.failed_jobs}", end="")
        
        # Check if all jobs are done
        if stats.completed_jobs + stats.failed_jobs >= len(job_ids):
            break
        
        time.sleep(1)
    
    print(f"\n\n📋 FINAL RESULTS:")
    
    # Show job results
    for job_id in job_ids:
        job = queue_manager.get_job_status(job_id)
        if job:
            status_icon = "✅" if job.status == JobStatus.COMPLETED else "❌" if job.status == JobStatus.FAILED else "🔄"
            print(f"   {status_icon} {job_id[:8]}: {job.element_type.value} - {job.status.value}")
            
            if job.status == JobStatus.FAILED and job.error_message:
                print(f"      Error: {job.error_message}")
    
    # Shutdown
    queue_manager.shutdown()
    
    print("\n✅ Test complete")


if __name__ == "__main__":
    main()