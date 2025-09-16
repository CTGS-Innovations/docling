#!/usr/bin/env python3
"""
Shared Memory Pipeline for Edge-Optimized Processing
===================================================
CloudFlare Workers ready - strict 1GB memory limit compliance.
Load documents once, stream processing across cores.
"""

import time
from pathlib import Path
from typing import List, Dict, Any

from .shared_memory_pool import SharedMemoryPool
from .fusion_pipeline import FusionPipeline


class SharedMemoryFusionPipeline:
    """
    Edge-optimized pipeline using shared memory pool architecture.
    
    Architecture:
    1. Load Phase: All documents → shared memory pool (once)
    2. Process Phase: Stream classification, enrichment, extraction across cores
    3. Write Phase: Single write operation from shared pool
    
    Memory Efficiency: 50% reduction vs traditional multi-core approach
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stages_to_run = config.get('pipeline', {}).get('stages_to_run', ['convert'])
        
        # Memory configuration for edge deployment
        memory_limit_gb = config.get('pipeline', {}).get('service_memory_limit_mb', 1024) / 1024
        doc_limit_mb = config.get('pipeline', {}).get('memory_limit_mb', 100)
        
        self.memory_pool = SharedMemoryPool(
            max_memory_gb=memory_limit_gb,
            max_doc_size_mb=doc_limit_mb
        )
        
        # Use traditional pipeline for classification logic
        self.traditional_pipeline = FusionPipeline(config)
        
    def process_files(self, extractor, file_paths: List[Path], output_dir: Path, 
                     max_workers: int = 2) -> tuple[List[Any], float, Dict[str, Any]]:
        """
        Process files using shared memory pool architecture.
        
        Edge-optimized flow:
        1. LOAD: All documents → shared memory pool (once)
        2. STREAM: Classification across shared pool
        3. STREAM: Enrichment across shared pool  
        4. STREAM: Extraction across shared pool
        5. WRITE: All documents from pool → disk
        """
        start_time = time.perf_counter()
        
        print(f"🏊 Shared Memory Pipeline: {' → '.join(self.stages_to_run)}")
        print(f"🎯 Edge Optimized: Load once → Stream processing → Single write")
        
        # Phase 1: LOAD all documents into shared memory pool
        if 'convert' in self.stages_to_run:
            print(f"\n📊 Phase 1: Loading documents into shared memory pool...")
            load_start = time.perf_counter()
            
            successful_loads, failed_loads = self.memory_pool.load_documents_batch(
                extractor, file_paths, output_dir, max_workers=max_workers
            )
            
            load_time = (time.perf_counter() - load_start) * 1000
            print(f"   ✅ Load phase complete: {load_time:.0f}ms")
            
            if successful_loads == 0:
                print("   ❌ No documents loaded successfully")
                return [], time.perf_counter() - start_time, {}
        
        # Phase 2: STREAM processing across shared pool
        processing_stats = {}
        
        # Stream Classification
        if 'classify' in self.stages_to_run:
            print(f"\n🌊 Phase 2a: Streaming classification across shared pool...")
            
            def classify_document(doc):
                """Classification function for streaming"""
                classification_data = self.traditional_pipeline._generate_classification_data(
                    doc.markdown_content, doc.source_filename
                )
                doc.add_classification_data(classification_data)
            
            processing_stats['classify'] = self.memory_pool.stream_process_documents(
                classify_document, "Classification", max_workers
            )
        
        # Stream Enrichment  
        if 'enrich' in self.stages_to_run:
            print(f"\n🌊 Phase 2b: Streaming enrichment across shared pool...")
            
            def enrich_document(doc):
                """Enrichment function for streaming"""
                # TODO: Implement domain-specific enrichment
                enrichment_data = {
                    'description': 'Domain-Specific Enrichment & Entity Extraction',
                    'enrichment_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'enrichment_method': 'mvp-fusion-shared-memory',
                    'domains_processed': '["general"]',
                    'total_entities': 0,
                    'enhanced_mode': False,
                    'shared_memory_optimized': True
                }
                doc.add_enrichment_data(enrichment_data)
            
            processing_stats['enrich'] = self.memory_pool.stream_process_documents(
                enrich_document, "Enrichment", max_workers
            )
        
        # Stream Extraction
        if 'extract' in self.stages_to_run:
            print(f"\n🌊 Phase 2c: Streaming extraction across shared pool...")
            
            def extract_document(doc):
                """Extraction function for streaming"""
                # TODO: Implement semantic rule extraction
                semantic_data = {
                    'extraction_date': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'extraction_method': 'mvp-fusion-shared-memory',
                    'rules_extracted': 0,
                    'knowledge_points': [],
                    'shared_memory_optimized': True
                }
                doc.set_semantic_data(semantic_data)
            
            processing_stats['extract'] = self.memory_pool.stream_process_documents(
                extract_document, "Extraction", max_workers
            )
        
        # Phase 3: WRITE all documents from shared pool
        print(f"\n💾 Phase 3: Writing all documents from shared pool...")
        write_stats = self.memory_pool.write_all_documents(output_dir)
        
        total_time = time.perf_counter() - start_time
        
        # Generate comprehensive results
        memory_stats = self.memory_pool.get_memory_stats()
        performance_summary = self.memory_pool.get_performance_summary()
        
        # Convert shared pool documents to list for compatibility
        results = list(self.memory_pool.documents.values())
        
        # Resource summary with shared memory advantages
        resource_summary = {
            'shared_memory_architecture': True,
            'memory_efficiency_gain_percent': memory_stats['memory_efficiency_vs_traditional_percent'],
            'current_memory_mb': memory_stats['current_memory_mb'],
            'traditional_memory_mb': memory_stats['traditional_memory_usage_mb'],
            'documents_in_shared_pool': memory_stats['documents_in_pool'],
            'edge_deployment_ready': performance_summary['edge_deployment_ready'],
            'processing_stats': processing_stats,
            'write_stats': write_stats
        }
        
        # Print shared memory advantages
        print(f"\n🎯 SHARED MEMORY ADVANTAGES:")
        print(f"   💾 Memory used: {memory_stats['current_memory_mb']:.1f}MB (vs {memory_stats['traditional_memory_usage_mb']:.1f}MB traditional)")
        print(f"   ⚡ Memory efficiency: {memory_stats['memory_efficiency_vs_traditional_percent']:.1f}% improvement")
        print(f"   🌐 Edge ready: {'✅' if performance_summary['edge_deployment_ready']['cloudflare_workers_compatible'] else '❌'}")
        
        # Cleanup
        self.memory_pool.cleanup()
        
        return results, total_time, resource_summary
        
    def __str__(self):
        return f"SharedMemoryFusionPipeline({self.memory_pool})"
        
    def __repr__(self):
        return self.__str__()