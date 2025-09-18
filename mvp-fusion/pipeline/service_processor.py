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
from pipeline.in_memory_document import InMemoryDocument

# Import real extraction functions
try:
    import fitz  # PyMuPDF for PDF processing
except ImportError:
    fitz = None

# Import real entity extraction
try:
    from knowledge.extractors.semantic_fact_extractor import SemanticFactExtractor
    from knowledge.aho_corasick_engine import AhoCorasickEngine
except ImportError:
    SemanticFactExtractor = None
    AhoCorasickEngine = None


@dataclass
class WorkItem:
    """Work item passed from I/O worker to CPU workers"""
    document: 'InMemoryDocument'  # Pass the actual document object, not just markdown
    metadata: Dict[str, Any]
    ingestion_time: float


class ServiceProcessor:
    """
    Clean I/O + CPU service processor for edge deployment.
    
    Separates I/O-bound ingestion from CPU-bound processing with async queue.
    """
    
    def __init__(self, config: Dict[str, Any], max_workers: int = None):
        self.config = config
        self.logger = get_fusion_logger(__name__)
        
        # Worker configuration - use CLI override if provided, otherwise config
        if max_workers is not None:
            self.cpu_workers = max_workers  # Use CLI override
        else:
            # Fallback to config file
            from utils.deployment_manager import DeploymentManager
            deployment_manager = DeploymentManager(config)
            self.cpu_workers = deployment_manager.get_max_workers()
        self.queue_size = config.get('pipeline', {}).get('queue_size', 100)
        self.memory_limit_mb = config.get('pipeline', {}).get('memory_limit_mb', 100)
        
        # Work queue between I/O and CPU layers
        self.work_queue = Queue(maxsize=self.queue_size)
        
        # Processing state
        self.active = False
        self.io_worker = None
        self.cpu_executor = None
        
        # Initialize real extractors (shared across CPU workers)
        self.aho_corasick_engine = None
        self.semantic_extractor = None
        self._initialize_extractors()
        
        self.logger.staging(f"Service Processor initialized: 1 I/O + {self.cpu_workers} CPU workers")
        self.logger.logger.debug(f"📋 Queue size: {self.queue_size}, Memory limit: {self.memory_limit_mb}MB")
    
    def _initialize_extractors(self):
        """Initialize real entity extractors for CPU workers"""
        if AhoCorasickEngine and SemanticFactExtractor:
            try:
                # Initialize Aho-Corasick engine for pattern matching
                self.aho_corasick_engine = AhoCorasickEngine(self.config)
                
                # Initialize semantic fact extractor
                self.semantic_extractor = SemanticFactExtractor()
                
                self.logger.logger.debug("✅ Real extractors initialized")
            except Exception as e:
                self.logger.logger.warning(f"⚠️  Failed to initialize extractors: {e}")
                self.aho_corasick_engine = None
                self.semantic_extractor = None
        else:
            self.logger.logger.warning("⚠️  Real extractors not available - using mock processing")
    
    def start_service(self):
        """Start the I/O + CPU worker service"""
        if self.active:
            self.logger.logger.warning("⚠️  Service already running")
            return
        
        self.active = True
        self.logger.staging("Starting I/O + CPU service...")
        
        # Start CPU worker pool
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=self.cpu_workers, 
            thread_name_prefix="CPUWorker"
        )
        
        self.logger.staging(f"Service started: 1 I/O worker + {self.cpu_workers} CPU workers")
    
    def stop_service(self):
        """Stop the I/O + CPU worker service"""
        if not self.active:
            return
        
        self.logger.staging("Stopping I/O + CPU service...")
        self.active = False
        
        # Stop CPU workers
        if self.cpu_executor:
            self.cpu_executor.shutdown(wait=True)
            self.cpu_executor = None
        
        self.logger.staging("Service stopped")
    
    def _convert_pdf_to_markdown(self, pdf_path: Path) -> str:
        """Convert PDF to markdown using PyMuPDF (real conversion)"""
        if not fitz:
            return f"# {pdf_path.name}\n\nPyMuPDF not available - mock content"
        
        try:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            # Skip files that are too large
            if page_count > 100:
                doc.close()
                return f"# {pdf_path.name}\n\nSkipped: {page_count} pages (>100 limit)"
            
            # Extract text from all pages
            markdown_content = [f"# {pdf_path.stem}\n"]
            
            for page_num in range(page_count):
                page = doc[page_num]
                
                # Use blocks method for fastest extraction
                blocks = page.get_text("blocks")
                if blocks:
                    markdown_content.append(f"\n## Page {page_num + 1}\n")
                    for block in blocks:
                        if block[4]:  # Check if block contains text
                            text = block[4].strip()
                            if text:
                                markdown_content.append(text + "\n")
            
            doc.close()
            return '\n'.join(markdown_content)
            
        except Exception as e:
            return f"# {pdf_path.name}\n\nPDF conversion error: {str(e)}"
    
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
        
        self.logger.staging(f"I/O worker starting ingestion of {len(file_paths)} files")
        
        for i, file_path in enumerate(file_paths):
            if not self.active:
                break
            
            ingestion_start = time.perf_counter()
            
            try:
                self.logger.conversion(f"Reading file: {file_path.name}")
                
                # Real file processing (I/O bound)
                if file_path.suffix.lower() == '.pdf':
                    self.logger.conversion(f"Converting PDF to markdown: {file_path.name}")
                    markdown_content = self._convert_pdf_to_markdown(file_path)
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
        
        self.logger.staging(f"I/O worker completed ingestion of {len(file_paths)} files")
    
    def _cpu_worker_processing(self, worker_id: int) -> List[InMemoryDocument]:
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
                
                self.logger.semantics(f"Processing entities: {work_item.source_filename}")
                
                # Create InMemoryDocument object first
                result = InMemoryDocument(
                    source_file_path=str(work_item.file_path),
                    memory_limit_mb=self.memory_limit_mb
                )
                result.markdown_content = work_item.markdown_content
                
                # Real entity extraction and classification
                try:
                    if self.aho_corasick_engine and self.semantic_extractor:
                        # Real classification with Aho-Corasick
                        self.logger.classification(f"Classifying document: {work_item.source_filename}")
                        classification_result = self.aho_corasick_engine.classify_document(
                            work_item.markdown_content, 
                            work_item.source_filename
                        )
                        
                        if classification_result:
                            result.yaml_frontmatter['classification'] = classification_result
                            
                            # Real semantic extraction
                            self.logger.semantics(f"Extracting semantic facts: {work_item.source_filename}")
                            semantic_facts = self.semantic_extractor.extract_semantic_facts_from_classification(
                                classification_result, 
                                work_item.markdown_content
                            )
                            
                            if semantic_facts:
                                result.semantic_json = semantic_facts
                                
                                # Log entity counts (following Rule #11 format)
                                global_facts = semantic_facts.get('global_entities', {})
                                domain_facts = semantic_facts.get('domain_entities', {})
                                
                                if global_facts:
                                    global_counts = [f"{k}:{len(v)}" for k, v in global_facts.items() if v]
                                    if global_counts:
                                        self.logger.semantics(f"Global entities: {', '.join(global_counts)}")
                                
                                if domain_facts:
                                    domain_counts = [f"{k}:{len(v)}" for k, v in domain_facts.items() if v]
                                    if domain_counts:
                                        self.logger.semantics(f"Domain entities: {', '.join(domain_counts)}")
                        
                        result.success = True
                    else:
                        # Fallback to mock processing
                        result.success = True
                        self.logger.logger.debug(f"⚠️  Using mock processing for {work_item.source_filename}")
                        
                except Exception as e:
                    self.logger.logger.error(f"❌ Entity extraction failed for {work_item.source_filename}: {e}")
                    result.success = False
                    result.mark_failed(f"Entity extraction error: {e}")
                
                processing_time = time.perf_counter() - processing_start
                
                results.append(result)
                self.logger.logger.debug(f"✅ Completed processing: {work_item.source_filename}")
                
            except Empty:
                # Normal timeout, continue checking
                continue
            except Exception as e:
                self.logger.logger.error(f"❌ CPU worker {worker_id} error: {e}")
        
        self.logger.logger.debug(f"🏁 CPU worker {worker_id} finished: {len(results)} items processed")
        return results
    
    def process_files_service(self, file_paths: List[Path], output_dir: Path = None) -> tuple[List[InMemoryDocument], float]:
        """
        Process files using clean I/O + CPU service architecture.
        
        Returns:
            Tuple of (in_memory_documents_list, total_processing_time)
        """
        if not self.active:
            self.start_service()
        
        total_start = time.perf_counter()
        
        self.logger.staging(f"Processing {len(file_paths)} files with I/O + CPU service")
        
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
        self.logger.staging("I/O ingestion completed")
        
        # Collect CPU results
        all_results = []
        for i, future in enumerate(cpu_futures):
            worker_results = future.result()
            all_results.extend(worker_results)
            self.logger.logger.debug(f"📊 CPU worker {i+1} returned {len(worker_results)} results")
        
        total_time = time.perf_counter() - total_start
        
        self.logger.staging(f"Service processing complete: {len(all_results)} results in {total_time:.2f}s")
        
        # Write files to disk (WRITER-IO phase)
        if all_results:
            self._write_results_to_disk(all_results, output_dir or Path.cwd())
        
        return all_results, total_time
    
    def _write_results_to_disk(self, results: List[InMemoryDocument], output_dir: Path):
        """WRITER-IO phase: Write processed documents to disk"""
        # Set thread name for I/O worker attribution 
        original_name = threading.current_thread().name
        threading.current_thread().name = "IOWorker-1"
        
        try:
            successful_writes = 0
            
            for doc in results:
                if doc.success and doc.markdown_content:
                    try:
                        # Write markdown file
                        md_filename = f"{doc.source_stem}.md"
                        md_path = output_dir / md_filename
                        
                        self.logger.writer(f"Writing markdown: {md_filename}")
                        with open(md_path, 'w', encoding='utf-8') as f:
                            f.write(doc.markdown_content)
                        
                        # Write JSON knowledge file if we have semantic data
                        if doc.semantic_json:
                            json_filename = f"{doc.source_stem}.json"
                            json_path = output_dir / json_filename
                            
                            self.logger.writer(f"Writing JSON knowledge: {json_filename}")
                            import json
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(doc.semantic_json, f, indent=2)
                        
                        successful_writes += 1
                        
                    except Exception as e:
                        self.logger.logger.error(f"❌ Failed to write {doc.source_filename}: {e}")
            
            self.logger.writer(f"Saved {successful_writes} files to {output_dir}")
            
        finally:
            # Restore original thread name
            threading.current_thread().name = original_name


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