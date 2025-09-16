#!/usr/bin/env python3
"""
Shared Memory Pool for Edge-Optimized Document Processing
========================================================
CloudFlare Workers / Edge deployment with strict 1GB RAM limit.
Load documents once into shared memory, stream processing across cores.
"""

import time
import threading
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import gc

from .in_memory_document import InMemoryDocument, MemoryOverflowError


class SharedMemoryPool:
    """
    Edge-optimized shared memory pool for document processing.
    
    Architecture:
    1. Load Phase: All documents → shared memory pool (once)
    2. Process Phase: Multiple cores stream from shared pool
    3. Memory Efficiency: 1 copy per document vs N copies per core
    
    Perfect for CloudFlare Workers with strict memory limits.
    """
    
    def __init__(self, max_memory_gb: float = 1.0, max_doc_size_mb: int = 100):
        self.max_memory_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
        self.max_doc_size_bytes = max_doc_size_mb * 1024 * 1024
        self.max_doc_size_mb = max_doc_size_mb  # Store as attribute for InMemoryDocument
        
        # Document storage
        self.documents: Dict[str, InMemoryDocument] = {}
        self.load_stats: Dict[str, Any] = {}
        
        # Memory management
        self.current_memory_usage = 0
        self.peak_memory_usage = 0
        self.memory_lock = threading.Lock()
        
        # Performance tracking
        self.load_start_time = None
        self.processing_stats = {
            'documents_loaded': 0,
            'documents_failed': 0,
            'total_pages': 0,
            'memory_efficiency': 0,
            'load_time_ms': 0
        }
        
    def estimate_document_memory(self, file_path: Path) -> int:
        """Estimate memory usage for a document before loading"""
        try:
            file_size = file_path.stat().st_size
            # Rough estimate: markdown is typically 1/20th of PDF size
            estimated_memory = file_size // 20
            return max(estimated_memory, 1024)  # Minimum 1KB
        except:
            return 1024  # Default estimate
            
    def can_load_document(self, file_path: Path) -> bool:
        """Check if document can fit in memory pool"""
        estimated_size = self.estimate_document_memory(file_path)
        return (self.current_memory_usage + estimated_size) < self.max_memory_bytes
        
    def load_documents_batch(self, extractor, file_paths: List[Path], 
                           output_dir: Path, max_workers: int = 2) -> Tuple[int, int]:
        """
        Load all documents into shared memory pool.
        Returns (successful_loads, failed_loads)
        """
        print(f"🏊 Loading {len(file_paths)} documents into shared memory pool...")
        print(f"💾 Pool limit: {self.max_memory_bytes/1024/1024:.0f}MB")
        
        self.load_start_time = time.perf_counter()
        
        # Filter documents that can fit in memory
        loadable_files = []
        skipped_too_large = 0
        
        for file_path in file_paths:
            if self.can_load_document(file_path):
                loadable_files.append(file_path)
            else:
                skipped_too_large += 1
                
        print(f"   📊 Loadable: {len(loadable_files)}, Too large: {skipped_too_large}")
        
        if not loadable_files:
            return 0, len(file_paths)
            
        # Use extractor to convert documents
        conversion_results, conversion_time, resource_summary = extractor.extract_batch(
            loadable_files, output_dir, max_workers=max_workers
        )
        
        # Load successful conversions into memory pool
        successful_loads = 0
        failed_loads = 0
        
        for result in conversion_results:
            if result.success and hasattr(result, 'output_path') and result.output_path:
                try:
                    # Check if output file exists
                    output_file = Path(result.output_path)
                    if not output_file.exists():
                        # File might not have been written, skip
                        failed_loads += 1
                        continue
                        
                    # Read the converted markdown
                    with open(output_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse YAML frontmatter
                    yaml_metadata = {}
                    markdown_content = content
                    if content.startswith('---'):
                        parts = content.split('---', 2)
                        if len(parts) >= 3:
                            import yaml
                            yaml_metadata = yaml.safe_load(parts[1]) or {}
                            markdown_content = parts[2]
                    
                    # Create in-memory document
                    doc = InMemoryDocument(result.file_path, self.max_doc_size_mb)
                    doc.set_conversion_data(markdown_content, yaml_metadata, result.pages)
                    
                    # Add to shared pool
                    with self.memory_lock:
                        doc_memory = doc.get_memory_footprint()
                        
                        if self.current_memory_usage + doc_memory < self.max_memory_bytes:
                            self.documents[result.file_path] = doc
                            self.current_memory_usage += doc_memory
                            self.peak_memory_usage = max(self.peak_memory_usage, self.current_memory_usage)
                            successful_loads += 1
                            self.processing_stats['total_pages'] += result.pages
                        else:
                            failed_loads += 1
                            print(f"   ⚠️  Memory limit reached, skipping: {Path(result.file_path).name}")
                    
                    # Delete temporary file (we have it in memory now)
                    Path(result.output_path).unlink()
                    
                except Exception as e:
                    failed_loads += 1
                    print(f"   ❌ Failed to load {Path(result.file_path).name}: {e}")
            else:
                failed_loads += 1
        
        # Update stats
        self.processing_stats['documents_loaded'] = successful_loads
        self.processing_stats['documents_failed'] = failed_loads + skipped_too_large
        self.processing_stats['load_time_ms'] = (time.perf_counter() - self.load_start_time) * 1000
        
        load_mb = self.current_memory_usage / 1024 / 1024
        print(f"   ✅ Loaded {successful_loads} documents into shared pool ({load_mb:.1f}MB)")
        
        return successful_loads, failed_loads
        
    def stream_process_documents(self, process_func, process_name: str, 
                               max_workers: int = 2) -> Dict[str, Any]:
        """
        Stream processing function across all documents in pool using multiple cores.
        Simulates edge computing with shared memory access.
        """
        if not self.documents:
            return {'processed': 0, 'failed': 0, 'time_ms': 0}
            
        print(f"🌊 {process_name}: Streaming across {len(self.documents)} documents with {max_workers} cores...")
        
        start_time = time.perf_counter()
        successful = 0
        failed = 0
        
        # Create thread pool to simulate multiple cores accessing shared memory
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            
            # Submit all documents for processing
            for file_path, doc in self.documents.items():
                if doc.success:
                    future = executor.submit(self._safe_process_document, doc, process_func, process_name)
                    futures.append(future)
            
            # Collect results
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        successful += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    print(f"   ❌ {process_name} failed: {e}")
        
        processing_time_ms = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ {process_name} complete: {processing_time_ms:.0f}ms ({successful}/{len(self.documents)} successful)")
        
        return {
            'processed': successful,
            'failed': failed,
            'time_ms': processing_time_ms,
            'throughput_docs_per_sec': successful / (processing_time_ms / 1000) if processing_time_ms > 0 else 0
        }
        
    def _safe_process_document(self, doc: InMemoryDocument, process_func, process_name: str) -> bool:
        """Safely process a document with error handling"""
        try:
            if doc.success:
                process_func(doc)
                return True
            return False
        except MemoryOverflowError as e:
            doc.mark_failed(f"{process_name} memory overflow: {e}")
            return False
        except Exception as e:
            doc.mark_failed(f"{process_name} failed: {e}")
            return False
            
    def write_all_documents(self, output_dir: Path) -> Dict[str, Any]:
        """Write all documents from shared pool to disk"""
        print(f"💾 Writing {len(self.documents)} documents from shared pool to disk...")
        
        start_time = time.perf_counter()
        successful_writes = 0
        failed_writes = 0
        
        for file_path, doc in self.documents.items():
            if doc.success:
                try:
                    # Generate final markdown
                    final_markdown = doc.generate_final_markdown()
                    output_file = output_dir / f"{doc.source_stem}.md"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(final_markdown)
                    
                    # Write semantic JSON if available
                    if doc.semantic_json:
                        json_file = output_dir / f"{doc.source_stem}.semantic.json"
                        import json
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(doc.semantic_json, f, indent=2)
                    
                    successful_writes += 1
                    
                except Exception as e:
                    doc.mark_failed(f"Write failed: {e}")
                    failed_writes += 1
        
        write_time_ms = (time.perf_counter() - start_time) * 1000
        print(f"   ✅ Write complete: {write_time_ms:.0f}ms ({successful_writes}/{len(self.documents)} successful)")
        
        return {
            'written': successful_writes,
            'failed': failed_writes,
            'time_ms': write_time_ms
        }
        
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        current_mb = self.current_memory_usage / 1024 / 1024
        peak_mb = self.peak_memory_usage / 1024 / 1024
        limit_mb = self.max_memory_bytes / 1024 / 1024
        
        # Calculate memory efficiency vs traditional approach
        traditional_memory = self.current_memory_usage * 2  # 2 cores = 2 copies
        efficiency_percent = (1 - (self.current_memory_usage / traditional_memory)) * 100 if traditional_memory > 0 else 0
        
        return {
            'current_memory_mb': current_mb,
            'peak_memory_mb': peak_mb,
            'memory_limit_mb': limit_mb,
            'memory_utilization_percent': (current_mb / limit_mb) * 100 if limit_mb > 0 else 0,
            'documents_in_pool': len(self.documents),
            'avg_document_size_kb': (self.current_memory_usage / len(self.documents) / 1024) if self.documents else 0,
            'memory_efficiency_vs_traditional_percent': efficiency_percent,
            'traditional_memory_usage_mb': traditional_memory / 1024 / 1024
        }
        
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        memory_stats = self.get_memory_stats()
        
        total_processing_time = self.processing_stats.get('load_time_ms', 0)
        pages_per_sec = (self.processing_stats['total_pages'] / (total_processing_time / 1000)) if total_processing_time > 0 else 0
        
        return {
            'load_performance': {
                'documents_loaded': self.processing_stats['documents_loaded'],
                'documents_failed': self.processing_stats['documents_failed'],
                'total_pages': self.processing_stats['total_pages'],
                'load_time_ms': self.processing_stats['load_time_ms'],
                'pages_per_sec': pages_per_sec
            },
            'memory_efficiency': memory_stats,
            'edge_deployment_ready': {
                'memory_under_1gb': memory_stats['current_memory_mb'] < 1024,
                'memory_efficiency_gain': memory_stats['memory_efficiency_vs_traditional_percent'],
                'cloudflare_workers_compatible': memory_stats['current_memory_mb'] < 512  # Conservative limit
            }
        }
        
    def cleanup(self):
        """Clean up memory pool"""
        with self.memory_lock:
            self.documents.clear()
            self.current_memory_usage = 0
            gc.collect()
        print(f"🧹 Shared memory pool cleaned up")
        
    def __str__(self):
        return f"SharedMemoryPool({len(self.documents)} docs, {self.current_memory_usage/1024/1024:.1f}MB)"
        
    def __repr__(self):
        return self.__str__()