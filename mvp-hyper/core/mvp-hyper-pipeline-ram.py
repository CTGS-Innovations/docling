#!/usr/bin/env python3
"""
MVP Hyper Pipeline - RAM Version
In-memory processing pipeline to eliminate disk I/O bottlenecks.

Instead of: Convert→Disk→Read→Classify→Disk→Read→Enrich→Disk→Read→Extract→Disk
We do: Convert→RAM→Classify→RAM→Enrich→RAM→Extract→Disk (once)

This should dramatically improve performance by eliminating intermediate disk I/O.
"""

import time
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
import threading
import multiprocessing as mp
from collections import defaultdict

# Import existing modules
from yaml_metadata_manager import YAMLMetadataManager
from enhanced_classification_with_entities import EnhancedClassifierWithEntities
from enhanced_enrichment_targeted import TargetedEnrichment


def process_document_worker(doc_data):
    """Standalone worker function for parallel processing."""
    try:
        doc_name, content, file_size_bytes, config = doc_data
        
        # Initialize processors in each worker process with config
        classifier = EnhancedClassifierWithEntities(config=config)
        enricher = TargetedEnrichment()
        
        start_time = time.time()
        
        # Step 1: Classification
        classify_start = time.time()
        result = classifier.classify_and_extract(content, doc_name)
        classify_time = time.time() - classify_start
        
        # Generate classification metadata
        classification_data = {
            "description": "Document Classification & Type Detection",
            "classification_date": datetime.now().isoformat(),
            "classification_method": "enhanced",
            "processing_time_ms": classify_time * 1000,
            "enhanced_mode": True
        }
        
        # Add classification results
        if result:
            for key, value in result.items():
                if key == 'universal_entities':
                    entity_count = sum(len(v) if isinstance(v, list) else 1 for v in value.values()) if value else 0
                    classification_data['universal_entities_found'] = entity_count
                    for entity_type, entities in value.items():
                        if entities:
                            classification_data[entity_type] = json.dumps(entities, separators=(',', ':'))
                else:
                    if isinstance(value, (list, dict)):
                        classification_data[key] = json.dumps(value, separators=(',', ':'))
                    else:
                        classification_data[key] = value
        
        # Step 2: Enrichment
        enrich_start = time.time()
        primary_domain = classification_data.get('primary_domain', 'general')
        classification_dummy = {"primary_domain": primary_domain, "document_types": ["general"]}
        enrichment_result = enricher.extract_entities_targeted(content, classification_dummy, [primary_domain])
        enrich_time = time.time() - enrich_start
        
        # Generate enrichment metadata
        enrichment_data = {
            "description": "Domain-Specific Enrichment & Entity Extraction",
            "enrichment_date": datetime.now().isoformat(),
            "enrichment_method": "enhanced",
            "processing_time_ms": enrich_time * 1000
        }
        
        if enrichment_result and 'metadata' in enrichment_result:
            metadata = enrichment_result['metadata']
            enrichment_data.update({
                "entities_extracted": metadata.get('total_entity_count', 0),
                "domains_processed": json.dumps(metadata.get('domains_scanned', []), separators=(',', ':'))
            })
            
            for domain, entities in enrichment_result.items():
                if domain != 'metadata' and entities:
                    enrichment_data[f"{domain}_entities"] = json.dumps(entities, separators=(',', ':'))
        
        # Step 3: Conversion metadata
        conversion_data = {
            "description": "Document Conversion & File Analysis",
            "source_type": "file",
            "filename": doc_name,
            "file_extension": ".md",
            "format": "MD",
            "size_bytes": file_size_bytes,
            "size_human": f"{file_size_bytes} bytes",
            "conversion_date": datetime.now().isoformat(),
            "character_count": len(content),
            "word_count": len(content.split()),
            "line_count": content.count('\n'),
            "conversion_method": "mvp-hyper-pipeline-ram"
        }
        
        total_time = time.time() - start_time
        
        return {
            'doc_name': doc_name,
            'content': content,
            'metadata': {
                'conversion': conversion_data,
                'classification': classification_data,
                'enrichment': enrichment_data
            },
            'processing_times': {
                'classification': classify_time,
                'enrichment': enrich_time,
                'total': total_time
            }
        }
        
    except Exception as e:
        return {'error': str(e), 'doc_name': doc_data[0] if doc_data else 'unknown'}


@dataclass
class DocumentInMemory:
    """Represents a document being processed entirely in memory."""
    filename: str
    source_path: Path
    original_content: str  # Raw content from conversion
    current_content: str   # Content with progressive enhancements
    metadata: Dict[str, Any]  # All metadata sections
    processing_times: Dict[str, float]  # Timing data
    file_size_bytes: int
    creation_time: float


class RAMPipelineProcessor:
    """In-memory document processing pipeline."""
    
    def __init__(self, config_path: str):
        """Initialize the RAM pipeline processor."""
        self.config = self._load_config(config_path)
        self.metadata_manager = YAMLMetadataManager()
        
        # Initialize processors
        self.classifier = None
        self.enricher = None
        self.enhanced_mode = True
        
        # In-memory document storage
        self.documents: Dict[str, DocumentInMemory] = {}
        self.processing_stats = defaultdict(list)
        
        # Performance settings
        self.max_workers = self.config.get('processing', {}).get('max_workers', 4)
        
        print("🚀 RAM Pipeline Processor initialized")
        print(f"   💾 No file size limits - processing full files in RAM")
        print(f"   🔄 Max workers: {self.max_workers}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def initialize_processors(self):
        """Initialize classification and enrichment processors."""
        print("🔧 Initializing processors...")
        
        if self.enhanced_mode:
            self.classifier = EnhancedClassifierWithEntities(config=self.config)
            self.enricher = TargetedEnrichment()
            print("✅ Enhanced processors loaded")
        else:
            print("⚠️  Basic mode - limited functionality")
    
    def load_documents_to_memory(self, source_dirs: List[str]) -> int:
        """Load all documents into memory for processing."""
        print("📖 Loading documents into memory...")
        start_time = time.time()
        
        total_loaded = 0
        total_size_mb = 0
        
        for source_dir in source_dirs:
            source_path = Path(source_dir).expanduser()
            if not source_path.exists():
                print(f"⚠️  Directory not found: {source_path}")
                continue
                
            # Find all markdown files (assuming they're already converted)
            for md_file in source_path.rglob("*.md"):
                try:
                    file_size_bytes = md_file.stat().st_size
                    file_size_mb = file_size_bytes / (1024 * 1024)
                    
                    # Load full content into memory
                    load_start = time.time()
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if file_size_mb > 10:  # Just log large files, don't limit them
                        print(f"📄 LARGE FILE: {md_file.name} ({file_size_mb:.1f}MB) - processing full content")
                    
                    load_time = time.time() - load_start
                    
                    # Parse existing metadata if any
                    metadata, body = self.metadata_manager.parse_existing_metadata(content)
                    
                    # Create in-memory document
                    doc = DocumentInMemory(
                        filename=md_file.name,
                        source_path=md_file,
                        original_content=content,
                        current_content=body,  # Content without metadata
                        metadata=metadata,
                        processing_times={'load': load_time},
                        file_size_bytes=file_size_bytes,
                        creation_time=time.time()
                    )
                    
                    self.documents[md_file.name] = doc
                    total_loaded += 1
                    total_size_mb += len(content) / (1024 * 1024)
                    
                    if total_loaded % 50 == 0:
                        print(f"   📄 Loaded {total_loaded} documents...")
                        
                except Exception as e:
                    print(f"❌ Error loading {md_file.name}: {e}")
        
        load_time = time.time() - start_time
        print(f"✅ Loaded {total_loaded} documents in {load_time:.2f}s")
        print(f"   💾 Total content in memory: {total_size_mb:.1f}MB")
        print(f"   ⚡ Loading speed: {total_loaded/load_time:.1f} files/sec")
        
        return total_loaded
    
    def process_document_in_memory(self, doc_name: str) -> bool:
        """Process a single document entirely in memory."""
        if doc_name not in self.documents:
            return False
            
        doc = self.documents[doc_name]
        
        try:
            # Step 1: Classification
            if self.classifier:
                classify_start = time.time()
                result = self.classifier.classify_and_extract(doc.current_content, doc.filename)
                classify_time = time.time() - classify_start
                
                # Generate structured classification metadata
                classification_data = self._generate_classification_metadata(result, classify_time)
                doc.metadata['classification'] = classification_data
                doc.processing_times['classification'] = classify_time
            
            # Step 2: Enrichment  
            if self.enricher:
                enrich_start = time.time()
                # Use classification results to guide enrichment
                classification_result = doc.metadata.get('classification', {})
                primary_domain = classification_result.get('primary_domain', 'general')
                
                # Create a dummy classification result for enrichment
                classification_dummy = {"primary_domain": primary_domain, "document_types": ["general"]}
                enrichment_result = self.enricher.extract_entities_targeted(doc.current_content, classification_dummy, [primary_domain])
                enrich_time = time.time() - enrich_start
                
                # Generate structured enrichment metadata
                enrichment_data = self._generate_enrichment_metadata(enrichment_result, enrich_time)
                doc.metadata['enrichment'] = enrichment_data
                doc.processing_times['enrichment'] = enrich_time
            
            # Step 3: Generate conversion metadata
            conversion_data = self._generate_conversion_metadata(doc)
            doc.metadata['conversion'] = conversion_data
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing {doc_name}: {e}")
            return False
    
    def process_all_documents_parallel(self) -> Dict[str, Any]:
        """Process all documents in parallel using ThreadPoolExecutor."""
        print(f"🔄 Processing {len(self.documents)} documents with {self.max_workers} parallel workers...")
        start_time = time.time()
        
        results = {
            'processed': 0,
            'failed': 0,
            'total_time': 0,
            'step_times': defaultdict(list)
        }
        
        # Prepare data for parallel processing
        doc_data_list = [
            (doc.filename, doc.current_content, doc.file_size_bytes, self.config)
            for doc in self.documents.values()
        ]
        
        # Process documents in parallel using processes (not threads) for CPU-bound work
        print(f"🚀 Launching {self.max_workers} CPU processes for parallel processing...")
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = [executor.submit(process_document_worker, doc_data) for doc_data in doc_data_list]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if 'error' in result:
                        print(f"❌ Error processing {result.get('doc_name', 'unknown')}: {result['error']}")
                        results['failed'] += 1
                    else:
                        # Update the document with processed results
                        doc_name = result['doc_name']
                        if doc_name in self.documents:
                            doc = self.documents[doc_name]
                            doc.metadata = result['metadata']
                            doc.processing_times.update(result['processing_times'])
                            
                            results['processed'] += 1
                            for step, timing in result['processing_times'].items():
                                results['step_times'][step].append(timing)
                        
                    # Progress reporting
                    total_done = results['processed'] + results['failed']
                    if total_done % 20 == 0:
                        print(f"   ⚡ Processed {total_done}/{len(self.documents)} documents...")
                        
                except Exception as e:
                    print(f"❌ Error in parallel processing: {e}")
                    results['failed'] += 1
        
        results['total_time'] = time.time() - start_time
        
        # Calculate performance metrics
        total_processed = results['processed']
        total_time = results['total_time']
        
        print(f"✅ Parallel processing complete!")
        print(f"   📊 Processed: {total_processed} documents")
        print(f"   ❌ Failed: {results['failed']} documents") 
        print(f"   ⏱️  Total time: {total_time:.2f}s")
        print(f"   ⚡ Overall speed: {total_processed/total_time:.1f} docs/sec")
        
        # Show step-by-step timing
        for step, times in results['step_times'].items():
            if times:
                avg_time = sum(times) / len(times)
                print(f"   🔍 {step.title()}: avg {avg_time*1000:.1f}ms per doc")
        
        return results
    
    def write_results_to_disk(self, output_dir: str) -> int:
        """Write all processed documents to disk in one batch."""
        print(f"💾 Writing {len(self.documents)} documents to disk...")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        written = 0
        start_time = time.time()
        
        for doc_name, doc in self.documents.items():
            try:
                # Combine metadata and content
                final_content = self._create_document_with_metadata(doc.current_content, doc.metadata)
                
                # Write to disk
                output_file = output_path / doc_name
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                
                written += 1
                
                if written % 100 == 0:
                    print(f"   💾 Written {written} files...")
                    
            except Exception as e:
                print(f"❌ Error writing {doc_name}: {e}")
        
        write_time = time.time() - start_time
        print(f"✅ Written {written} documents in {write_time:.2f}s")
        print(f"   ⚡ Write speed: {written/write_time:.1f} files/sec")
        
        return written
    
    def _generate_conversion_metadata(self, doc: DocumentInMemory) -> Dict[str, Any]:
        """Generate conversion metadata for a document."""
        return {
            "description": "Document Conversion & File Analysis",
            "source_type": "file", 
            "source_path": str(doc.source_path),
            "filename": doc.filename,
            "file_extension": doc.source_path.suffix,
            "format": doc.source_path.suffix.upper().lstrip('.'),
            "size_bytes": doc.file_size_bytes,
            "size_human": f"{doc.file_size_bytes} bytes",
            "conversion_date": datetime.now().isoformat(),
            "character_count": len(doc.current_content),
            "word_count": len(doc.current_content.split()),
            "line_count": doc.current_content.count('\n'),
            "conversion_method": "mvp-hyper-pipeline-ram"
        }
    
    def _generate_classification_metadata(self, result: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate structured classification metadata."""
        if not result:
            return {"description": "Document Classification & Type Detection", "error": "No classification result"}
            
        data = {
            "description": "Document Classification & Type Detection",
            "classification_date": datetime.now().isoformat(),
            "classification_method": "enhanced",
            "processing_time_ms": processing_time * 1000,
            "enhanced_mode": True
        }
        
        # Add classification results with compact JSON formatting
        for key, value in result.items():
            if key == 'universal_entities':
                # Count entities
                entity_count = sum(len(v) if isinstance(v, list) else 1 for v in value.values()) if value else 0
                data['universal_entities_found'] = entity_count
                
                # Add individual entity types as compact JSON
                for entity_type, entities in value.items():
                    if entities:
                        data[entity_type] = json.dumps(entities, separators=(',', ':'))
            else:
                if isinstance(value, (list, dict)):
                    data[key] = json.dumps(value, separators=(',', ':'))
                else:
                    data[key] = value
        
        return data
    
    def _generate_enrichment_metadata(self, result: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate structured enrichment metadata."""
        data = {
            "description": "Domain-Specific Enrichment & Entity Extraction", 
            "enrichment_date": datetime.now().isoformat(),
            "enrichment_method": "enhanced",
            "processing_time_ms": processing_time * 1000
        }
        
        if result and 'metadata' in result:
            metadata = result['metadata']
            data.update({
                "entities_extracted": metadata.get('total_entity_count', 0),
                "domains_processed": json.dumps(metadata.get('domains_scanned', []), separators=(',', ':'))
            })
            
            # Add domain-specific entities as compact JSON
            for domain, entities in result.items():
                if domain != 'metadata' and entities:
                    data[f"{domain}_entities"] = json.dumps(entities, separators=(',', ':'))
        
        return data
    
    def _create_document_with_metadata(self, content: str, metadata: Dict[str, Any]) -> str:
        """Create final document by combining metadata and content."""
        if not metadata:
            return content
            
        # Create YAML frontmatter
        yaml_content = "---\n"
        for section_name, section_data in metadata.items():
            yaml_content += f"{section_name}:\n"
            for key, value in section_data.items():
                yaml_content += f"  {key}: {repr(value)}\n"
        yaml_content += "---\n\n"
        
        return yaml_content + content
    
    def run_full_pipeline(self, source_dirs: List[str], output_dir: str) -> Dict[str, Any]:
        """Run the complete RAM-based pipeline."""
        pipeline_start = time.time()
        
        print("🚀 Starting RAM-based pipeline...")
        print("=" * 60)
        
        # Step 1: Initialize processors
        self.initialize_processors()
        
        # Step 2: Load all documents to memory
        loaded_count = self.load_documents_to_memory(source_dirs)
        if loaded_count == 0:
            print("❌ No documents loaded, exiting")
            return {}
        
        # Step 3: Process all documents in parallel
        processing_results = self.process_all_documents_parallel()
        
        # Step 4: Write results to disk
        written_count = self.write_results_to_disk(output_dir)
        
        # Final summary
        total_time = time.time() - pipeline_start
        
        print("\n" + "=" * 60)
        print("🎉 RAM PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"📄 Documents loaded: {loaded_count}")
        print(f"✅ Documents processed: {processing_results['processed']}")
        print(f"💾 Documents written: {written_count}")
        print(f"⏱️  Total pipeline time: {total_time:.2f}s")
        print(f"⚡ Overall performance: {processing_results['processed']/total_time:.1f} docs/sec")
        
        # Memory efficiency note
        total_memory_mb = sum(len(doc.current_content) for doc in self.documents.values()) / (1024 * 1024)
        print(f"💾 Peak memory usage: ~{total_memory_mb:.1f}MB")
        
        return {
            'loaded': loaded_count,
            'processed': processing_results['processed'],
            'written': written_count,
            'total_time': total_time,
            'docs_per_sec': processing_results['processed']/total_time,
            'memory_mb': total_memory_mb
        }


def main():
    """Main entry point for RAM pipeline."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python mvp-hyper-pipeline-ram.py <config_file>")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Initialize processor
    processor = RAMPipelineProcessor(config_file)
    
    # Get source directories and output from config
    config = processor.config
    source_dirs = config.get('inputs', {}).get('directories', [])
    output_dir = config.get('output', {}).get('directory', 'output')
    
    # Run the pipeline
    results = processor.run_full_pipeline(source_dirs, output_dir)
    
    # Save performance stats
    stats_file = Path(output_dir) / 'ram_pipeline_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📊 Performance stats saved to: {stats_file}")


if __name__ == "__main__":
    main()