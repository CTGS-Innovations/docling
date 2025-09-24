#!/usr/bin/env python3
"""
Pipeline Performance Isolation Test
====================================

GOAL: Isolate performance bottlenecks in the MVP-Fusion pipeline
REASON: Processing is slower than expected, need to identify which stage causes slowdown
PROBLEM: Could be I/O constraints, CPU blocking, queue overhead, or stage switching

This test:
1. Loads only OSHA documents (controlled dataset ~500 docs)
2. Runs each pipeline stage independently with timing
3. Measures I/O, CPU, memory usage per stage
4. Identifies bottlenecks and overhead sources
"""

import time
import psutil
import tracemalloc
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple
import sys
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import pipeline components - handle missing imports gracefully
try:
    from pipeline.legacy.service_processor import ServiceProcessor
except ImportError:
    ServiceProcessor = None
    print("⚠️ ServiceProcessor not available")

try:
    from pipeline.in_memory_document import InMemoryDocument
except ImportError:
    # Fallback to simple dict structure
    class InMemoryDocument:
        def __init__(self, source_path=None):
            self.source_path = source_path
            self.source_filename = ""
            self.markdown_content = ""
            self.page_count = 0
            self.metadata = {}

try:
    from utils.deployment_manager import DeploymentManager
except ImportError:
    # Fallback deployment manager
    class DeploymentManager:
        def __init__(self, config):
            self.config = config
        
        def get_max_workers(self):
            return self.config.get('performance', {}).get('max_workers', 2)
        
        def get_memory_limit_mb(self):
            profile = self.config.get('deployment', {}).get('profiles', {}).get('local', {})
            return profile.get('memory_mb', 8192)


@dataclass
class StageMetrics:
    """Metrics for a single processing stage"""
    name: str
    start_time: float
    end_time: float
    duration_ms: float
    cpu_percent: float
    memory_mb: float
    memory_delta_mb: float
    io_reads: int
    io_writes: int
    docs_processed: int
    pages_processed: int
    error_count: int = 0
    notes: str = ""


class PipelinePerformanceIsolator:
    """Isolates and measures performance of each pipeline stage"""
    
    def __init__(self, config_path: str = None):
        """Initialize with configuration"""
        self.config_path = config_path or "config/full.yaml"
        self.metrics: List[StageMetrics] = []
        self.documents: List[InMemoryDocument] = []
        self.process = psutil.Process()
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
            
        # Override config to use only OSHA documents for testing
        self.config['inputs']['directories'] = ["/home/corey/projects/docling/cli/data_osha"]
        self.config['inputs']['files'] = []
        self.config['inputs']['urls'] = []
        self.config['inputs']['url_files'] = []
        
        # Get deployment configuration
        self.deployment_manager = DeploymentManager(self.config)
        self.max_workers = self.deployment_manager.get_max_workers()
        
        print(f"🔬 Pipeline Performance Isolation Test")
        print(f"📁 Test dataset: OSHA documents only")
        print(f"⚙️  Max workers: {self.max_workers}")
        print(f"📊 Memory limit: {self.deployment_manager.get_memory_limit_mb()}MB")
        print("-" * 60)
    
    def _measure_stage(self, stage_name: str, stage_func, *args, **kwargs) -> Tuple[Any, StageMetrics]:
        """Execute a stage function and measure its performance"""
        print(f"\n🔄 Starting stage: {stage_name}")
        
        # Get initial metrics
        tracemalloc.start()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_io = self.process.io_counters()
        
        # Record start time and CPU
        start_time = time.perf_counter()
        cpu_start = self.process.cpu_percent(interval=None)
        
        # Execute the stage
        result = None
        error_count = 0
        try:
            result = stage_func(*args, **kwargs)
        except Exception as e:
            print(f"❌ Stage {stage_name} failed: {e}")
            error_count = 1
            
        # Record end time
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        
        # Get final metrics
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        memory_delta = final_memory - initial_memory
        cpu_percent = self.process.cpu_percent(interval=None) - cpu_start
        
        final_io = self.process.io_counters()
        io_reads = final_io.read_count - initial_io.read_count
        io_writes = final_io.write_count - initial_io.write_count
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Create metrics
        metrics = StageMetrics(
            name=stage_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            cpu_percent=cpu_percent,
            memory_mb=final_memory,
            memory_delta_mb=memory_delta,
            io_reads=io_reads,
            io_writes=io_writes,
            docs_processed=len(self.documents) if self.documents else 0,
            pages_processed=sum(d.page_count for d in self.documents) if self.documents else 0,
            error_count=error_count
        )
        
        self.metrics.append(metrics)
        
        # Print immediate feedback
        print(f"✅ Stage completed in {duration_ms:.2f}ms")
        print(f"   Memory: {final_memory:.1f}MB (Δ {memory_delta:+.1f}MB)")
        print(f"   I/O: {io_reads} reads, {io_writes} writes")
        print(f"   CPU: {cpu_percent:.1f}%")
        
        return result, metrics
    
    def stage_1_file_discovery(self) -> List[Path]:
        """Stage 1: File discovery and listing"""
        def discover_files():
            files = []
            for directory in self.config['inputs']['directories']:
                dir_path = Path(directory)
                if dir_path.exists():
                    # Get all supported files
                    for ext in self.config['files']['supported_extensions']:
                        files.extend(dir_path.glob(f"**/*{ext}"))
            return files
        
        files, metrics = self._measure_stage("1_file_discovery", discover_files)
        metrics.notes = f"Found {len(files)} files"
        print(f"   Files found: {len(files)}")
        return files
    
    def stage_2_file_loading(self, files: List[Path]) -> List[Dict]:
        """Stage 2: Load files into memory (I/O test)"""
        def load_files():
            loaded = []
            for file_path in files[:100]:  # Limit to 100 files for testing
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        loaded.append({
                            'path': file_path,
                            'size': len(content),
                            'content': content[:1000]  # Keep first 1KB for testing
                        })
                except Exception:
                    pass
            return loaded
        
        loaded, metrics = self._measure_stage("2_file_loading", load_files)
        total_size = sum(f['size'] for f in loaded) / 1024 / 1024  # MB
        metrics.notes = f"Loaded {len(loaded)} files, {total_size:.1f}MB total"
        print(f"   Total size: {total_size:.1f}MB")
        return loaded
    
    def stage_3_docling_conversion(self, files: List[Path]) -> List[InMemoryDocument]:
        """Stage 3: Convert documents to markdown using Docling"""
        def convert_docs():
            try:
                from extractors.core8_extractor import Core8Extractor
                extractor = Core8Extractor(self.config)
            except ImportError:
                # Fallback: just read text files directly
                print("   ⚠️  Core8Extractor not available, using fallback text reading")
                extractor = None
            
            documents = []
            
            # Process subset of files
            test_files = files[:20]  # Process 20 files for testing
            
            for file_path in test_files:
                try:
                    # Create InMemoryDocument
                    doc = InMemoryDocument(source_path=str(file_path))
                    doc.source_filename = file_path.name
                    
                    if extractor:
                        # Convert to markdown using extractor
                        markdown_content = extractor.extract_markdown(str(file_path))
                    else:
                        # Fallback: read as text if possible
                        if file_path.suffix in ['.txt', '.md']:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                markdown_content = f.read()
                        else:
                            markdown_content = f"[Binary file: {file_path.name}]"
                    
                    doc.markdown_content = markdown_content
                    doc.page_count = len(markdown_content) // 3000  # Estimate pages
                    
                    documents.append(doc)
                except Exception as e:
                    print(f"   ⚠️  Failed to convert {file_path.name}: {e}")
            
            return documents
        
        self.documents, metrics = self._measure_stage("3_docling_conversion", convert_docs)
        metrics.docs_processed = len(self.documents)
        print(f"   Documents converted: {len(self.documents)}")
        return self.documents
    
    def stage_4_classification(self, documents: List[InMemoryDocument]) -> List[InMemoryDocument]:
        """Stage 4: Document classification"""
        def classify_docs():
            try:
                from extractors.classification import classify_document_by_content
                classifier_available = True
            except ImportError:
                print("   ⚠️  Classification module not available, using mock classification")
                classifier_available = False
            
            for doc in documents:
                if doc.markdown_content:
                    # Classify document
                    if classifier_available:
                        classification = classify_document_by_content(doc.markdown_content[:5000])
                    else:
                        # Mock classification for testing
                        classification = {
                            'category': 'document',
                            'confidence': 0.85,
                            'subcategories': ['safety', 'compliance']
                        }
                    doc.metadata['classification'] = classification
            
            return documents
        
        classified, metrics = self._measure_stage("4_classification", classify_docs)
        print(f"   Documents classified: {len(classified)}")
        return classified
    
    def stage_5_entity_extraction(self, documents: List[InMemoryDocument]) -> List[InMemoryDocument]:
        """Stage 5: Entity extraction"""
        def extract_entities():
            try:
                from extractors.core8_extractor import Core8Extractor
                extractor = Core8Extractor(self.config)
            except ImportError:
                print("   ⚠️  Core8Extractor not available, using mock entity extraction")
                extractor = None
            
            for doc in documents:
                if doc.markdown_content:
                    if extractor:
                        # Extract entities using real extractor
                        entities = extractor.extract_entities(doc.markdown_content)
                    else:
                        # Mock entities for testing
                        entities = {
                            'person': ['John Doe', 'Jane Smith'],
                            'organization': ['OSHA', 'EPA'],
                            'location': ['Washington DC'],
                            'date': ['2024-01-01'],
                            'money': ['$100,000']
                        }
                    
                    doc.metadata['entities'] = entities
                    
                    # Count entities
                    entity_count = sum(len(v) for v in entities.values())
                    doc.metadata['entity_count'] = entity_count
            
            return documents
        
        with_entities, metrics = self._measure_stage("5_entity_extraction", extract_entities)
        total_entities = sum(doc.metadata.get('entity_count', 0) for doc in with_entities)
        metrics.notes = f"Extracted {total_entities} total entities"
        print(f"   Total entities extracted: {total_entities}")
        return with_entities
    
    def stage_6_normalization(self, documents: List[InMemoryDocument]) -> List[InMemoryDocument]:
        """Stage 6: Entity normalization"""
        def normalize_entities():
            try:
                from extractors.entity_normalizer import EntityNormalizer
                normalizer = EntityNormalizer(self.config)
            except ImportError:
                print("   ⚠️  EntityNormalizer not available, skipping normalization")
                normalizer = None
            
            for doc in documents:
                if 'entities' in doc.metadata:
                    if normalizer:
                        # Normalize entities
                        normalized = normalizer.normalize_entities(doc.metadata['entities'])
                    else:
                        # Pass through entities unchanged
                        normalized = doc.metadata['entities']
                    
                    doc.metadata['normalized_entities'] = normalized
            
            return documents
        
        normalized, metrics = self._measure_stage("6_normalization", normalize_entities)
        print(f"   Documents normalized: {len(normalized)}")
        return normalized
    
    def stage_7_semantic_extraction(self, documents: List[InMemoryDocument]) -> List[InMemoryDocument]:
        """Stage 7: Semantic fact extraction"""
        def extract_semantics():
            try:
                from extractors.semantic_fact_extractor import SemanticFactExtractor
                extractor = SemanticFactExtractor(self.config)
            except ImportError:
                print("   ⚠️  SemanticFactExtractor not available, using mock facts")
                extractor = None
            
            for doc in documents:
                if doc.markdown_content:
                    if extractor:
                        # Extract semantic facts
                        facts = extractor.extract_facts(doc.markdown_content)
                    else:
                        # Mock facts for testing
                        facts = {
                            'facts': [
                                {'fact': 'Safety requirement identified', 'confidence': 0.9},
                                {'fact': 'Compliance standard referenced', 'confidence': 0.85}
                            ],
                            'rules': [],
                            'relationships': []
                        }
                    
                    doc.metadata['semantic_facts'] = facts
                    doc.metadata['fact_count'] = len(facts.get('facts', []))
            
            return documents
        
        with_semantics, metrics = self._measure_stage("7_semantic_extraction", extract_semantics)
        total_facts = sum(doc.metadata.get('fact_count', 0) for doc in with_semantics)
        metrics.notes = f"Extracted {total_facts} semantic facts"
        print(f"   Total facts extracted: {total_facts}")
        return with_semantics
    
    def stage_8_json_generation(self, documents: List[InMemoryDocument]) -> int:
        """Stage 8: Generate JSON output"""
        def generate_json():
            output_dir = Path("../output/performance_test")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                from utils.high_performance_json import HighPerformanceJsonHandler
                json_handler = HighPerformanceJsonHandler()
            except ImportError:
                print("   ⚠️  HighPerformanceJsonHandler not available, using standard json")
                json_handler = None
            
            files_written = 0
            
            for doc in documents:
                # Prepare JSON data
                json_data = {
                    'filename': doc.source_filename,
                    'pages': doc.page_count,
                    'classification': doc.metadata.get('classification', {}),
                    'entities': doc.metadata.get('normalized_entities', {}),
                    'facts': doc.metadata.get('semantic_facts', {})
                }
                
                # Write JSON
                output_path = output_dir / f"{Path(doc.source_filename).stem}_semantic.json"
                
                if json_handler:
                    json_handler.write_json(json_data, output_path)
                else:
                    # Use standard json
                    with open(output_path, 'w') as f:
                        json.dump(json_data, f, indent=2)
                
                files_written += 1
            
            return files_written
        
        files_written, metrics = self._measure_stage("8_json_generation", generate_json)
        metrics.notes = f"Generated {files_written} JSON files"
        print(f"   JSON files written: {files_written}")
        return files_written
    
    def stage_9_parallel_processing(self, files: List[Path]) -> float:
        """Stage 9: Test parallel processing overhead"""
        def test_parallel():
            # Test with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Simple task: read file size
                def get_file_size(path):
                    return path.stat().st_size if path.exists() else 0
                
                # Submit all tasks
                futures = [executor.submit(get_file_size, f) for f in files[:100]]
                
                # Wait for completion
                results = [f.result() for f in futures]
                
            return sum(results)
        
        total_size, metrics = self._measure_stage("9_parallel_processing", test_parallel)
        metrics.notes = f"Processed {len(files[:100])} files in parallel"
        print(f"   Parallel overhead test completed")
        return total_size
    
    def stage_10_queue_overhead(self) -> float:
        """Stage 10: Test queue creation and management overhead"""
        def test_queues():
            import queue
            import threading
            
            # Create queues like in ServiceProcessor
            work_queue = queue.Queue(maxsize=self.config['deployment']['profiles']['local']['queue_size'])
            result_queue = queue.Queue()
            
            # Simulate queue operations
            test_items = list(range(1000))
            
            def producer():
                for item in test_items:
                    work_queue.put(item)
                    time.sleep(0.0001)  # Simulate work
            
            def consumer():
                while True:
                    try:
                        item = work_queue.get(timeout=0.1)
                        result_queue.put(item * 2)
                        work_queue.task_done()
                    except queue.Empty:
                        break
            
            # Start threads
            prod_thread = threading.Thread(target=producer)
            cons_threads = [threading.Thread(target=consumer) for _ in range(self.max_workers)]
            
            prod_thread.start()
            for t in cons_threads:
                t.start()
            
            prod_thread.join()
            for t in cons_threads:
                t.join()
            
            return result_queue.qsize()
        
        queue_size, metrics = self._measure_stage("10_queue_overhead", test_queues)
        metrics.notes = f"Processed {queue_size} items through queue"
        print(f"   Queue operations completed: {queue_size}")
        return queue_size
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 80)
        print("📊 PERFORMANCE ANALYSIS REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_time = sum(m.duration_ms for m in self.metrics)
        total_memory = max(m.memory_mb for m in self.metrics)
        total_io_reads = sum(m.io_reads for m in self.metrics)
        total_io_writes = sum(m.io_writes for m in self.metrics)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total execution time: {total_time:.2f}ms ({total_time/1000:.2f}s)")
        print(f"   Peak memory usage: {total_memory:.1f}MB")
        print(f"   Total I/O reads: {total_io_reads:,}")
        print(f"   Total I/O writes: {total_io_writes:,}")
        
        # Stage breakdown
        print(f"\n🔍 Stage-by-Stage Analysis:")
        print("-" * 80)
        print(f"{'Stage':<30} {'Time (ms)':<12} {'Memory Δ':<12} {'I/O R/W':<15} {'Notes'}")
        print("-" * 80)
        
        for m in self.metrics:
            io_str = f"{m.io_reads}/{m.io_writes}"
            print(f"{m.name:<30} {m.duration_ms:>10.2f}  {m.memory_delta_mb:>+10.1f}MB  {io_str:<15} {m.notes}")
        
        # Identify bottlenecks
        print(f"\n🚨 Bottleneck Analysis:")
        print("-" * 80)
        
        # Sort by duration
        sorted_metrics = sorted(self.metrics, key=lambda x: x.duration_ms, reverse=True)
        top_3 = sorted_metrics[:3]
        
        print(f"Top 3 slowest stages:")
        for i, m in enumerate(top_3, 1):
            percentage = (m.duration_ms / total_time) * 100
            print(f"   {i}. {m.name}: {m.duration_ms:.2f}ms ({percentage:.1f}% of total)")
        
        # Memory analysis
        memory_intensive = sorted(self.metrics, key=lambda x: x.memory_delta_mb, reverse=True)[:3]
        print(f"\nTop 3 memory-intensive stages:")
        for i, m in enumerate(memory_intensive, 1):
            print(f"   {i}. {m.name}: +{m.memory_delta_mb:.1f}MB")
        
        # I/O analysis
        io_intensive = sorted(self.metrics, key=lambda x: x.io_reads + x.io_writes, reverse=True)[:3]
        print(f"\nTop 3 I/O-intensive stages:")
        for i, m in enumerate(io_intensive, 1):
            total_io = m.io_reads + m.io_writes
            print(f"   {i}. {m.name}: {total_io:,} operations ({m.io_reads} reads, {m.io_writes} writes)")
        
        # Recommendations
        print(f"\n💡 Performance Recommendations:")
        print("-" * 80)
        
        # Check for specific bottlenecks
        if sorted_metrics[0].duration_ms > total_time * 0.5:
            print(f"⚠️  Stage '{sorted_metrics[0].name}' takes {sorted_metrics[0].duration_ms/total_time*100:.1f}% of total time")
            print(f"   Consider optimizing or parallelizing this stage")
        
        if any(m.memory_delta_mb > 500 for m in self.metrics):
            print(f"⚠️  High memory usage detected in some stages")
            print(f"   Consider streaming processing or batch size reduction")
        
        if total_io_reads > 10000:
            print(f"⚠️  High I/O read operations ({total_io_reads:,} total)")
            print(f"   Consider caching frequently accessed files or using memory-mapped files")
        
        # Queue overhead check
        queue_metric = next((m for m in self.metrics if 'queue' in m.name.lower()), None)
        if queue_metric and queue_metric.duration_ms > 100:
            print(f"⚠️  Queue overhead detected: {queue_metric.duration_ms:.2f}ms")
            print(f"   Consider reducing queue size or using faster IPC mechanisms")
        
        # Save report to file
        report_path = Path("../output/performance_test/performance_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config_path,
            'summary': {
                'total_time_ms': total_time,
                'peak_memory_mb': total_memory,
                'total_io_reads': total_io_reads,
                'total_io_writes': total_io_writes
            },
            'stages': [
                {
                    'name': m.name,
                    'duration_ms': m.duration_ms,
                    'memory_delta_mb': m.memory_delta_mb,
                    'io_reads': m.io_reads,
                    'io_writes': m.io_writes,
                    'notes': m.notes
                }
                for m in self.metrics
            ]
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Full report saved to: {report_path}")
        print("=" * 80)
    
    def run_full_test(self):
        """Run all stages and generate report"""
        print("\n🚀 Starting Full Pipeline Performance Test")
        print("=" * 80)
        
        try:
            # Stage 1: File discovery
            files = self.stage_1_file_discovery()
            
            # Stage 2: File loading (I/O test)
            loaded = self.stage_2_file_loading(files)
            
            # Stage 3: Document conversion
            documents = self.stage_3_docling_conversion(files)
            
            # Stage 4: Classification
            classified = self.stage_4_classification(documents)
            
            # Stage 5: Entity extraction
            with_entities = self.stage_5_entity_extraction(classified)
            
            # Stage 6: Normalization
            normalized = self.stage_6_normalization(with_entities)
            
            # Stage 7: Semantic extraction
            with_semantics = self.stage_7_semantic_extraction(normalized)
            
            # Stage 8: JSON generation
            self.stage_8_json_generation(with_semantics)
            
            # Stage 9: Parallel processing test
            self.stage_9_parallel_processing(files)
            
            # Stage 10: Queue overhead test
            self.stage_10_queue_overhead()
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Generate report
        self.generate_report()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Pipeline Performance Isolation Test")
    parser.add_argument('--config', default='config/full.yaml', help='Config file path')
    parser.add_argument('--stages', nargs='+', help='Run specific stages only')
    
    args = parser.parse_args()
    
    # Create and run test
    tester = PipelinePerformanceIsolator(args.config)
    
    if args.stages:
        # Run specific stages
        print(f"Running stages: {args.stages}")
        for stage_name in args.stages:
            method_name = f"stage_{stage_name}"
            if hasattr(tester, method_name):
                method = getattr(tester, method_name)
                method([])  # Pass empty list for testing
            else:
                print(f"⚠️  Unknown stage: {stage_name}")
    else:
        # Run full test
        tester.run_full_test()


if __name__ == "__main__":
    main()