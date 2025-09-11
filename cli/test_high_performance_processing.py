#!/usr/bin/env python3
"""
High-Performance Processing Benchmark
====================================

Comprehensive benchmark comparing traditional docling processing
with the new high-performance dual-path architecture.

Tests:
1. Fast text extraction performance (target: 100+ pages/sec)
2. Document classification and tagging accuracy
3. Overall throughput comparison
4. Memory usage and resource efficiency
5. Visual processing queue performance
"""

import time
import subprocess
import tempfile
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime
import statistics

# Import our high-performance system
from high_performance_pdf_processor import HighPerformancePDFProcessor, ProcessingResult
from pdf_complexity_analyzer import PDFComplexityAnalyzer, ProcessingStrategy
from fast_text_extractor import FastTextExtractor
from universal_document_tagger import UniversalDocumentTagger


@dataclass
class BenchmarkResult:
    """Results from a benchmark test."""
    test_name: str
    file_count: int
    total_time: float
    throughput_files_per_minute: float
    pages_processed: int
    pages_per_second: float
    success_rate: float
    memory_peak_mb: float
    cpu_usage_percent: float
    
    # Detailed metrics
    individual_times: List[float]
    average_time_per_file: float
    median_time_per_file: float
    min_time: float
    max_time: float
    
    # Strategy breakdown
    fast_text_count: int = 0
    vlm_count: int = 0
    hybrid_count: int = 0
    
    # Quality metrics
    documents_tagged: int = 0
    visual_elements_detected: int = 0
    
    errors: List[str] = None


class PerformanceBenchmark:
    """Comprehensive performance benchmark suite."""
    
    def __init__(self):
        self.results: Dict[str, BenchmarkResult] = {}
        self.test_data_dir = Path('/home/corey/projects/docling/cli/data')
        
    def run_comprehensive_benchmark(self) -> Dict[str, BenchmarkResult]:
        """Run complete benchmark suite."""
        
        print("🏁 HIGH-PERFORMANCE PROCESSING BENCHMARK")
        print("=" * 60)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Test data: {self.test_data_dir}")
        
        # Find test files
        test_files = self._gather_test_files()
        
        if not test_files:
            print("❌ No test files found")
            return {}
        
        print(f"📁 Found {len(test_files)} test files")
        self._print_file_breakdown(test_files)
        
        # Run benchmarks
        self.results["high_performance"] = self._benchmark_high_performance_system(test_files)
        self.results["traditional_docling"] = self._benchmark_traditional_docling(test_files[:5])  # Limit for speed
        self.results["fast_text_only"] = self._benchmark_fast_text_extraction(test_files)
        self.results["tagging_performance"] = self._benchmark_document_tagging(test_files[:10])
        
        # Generate comparison report
        self._generate_comparison_report()
        
        return self.results
    
    def _gather_test_files(self) -> List[Path]:
        """Gather test files of various types."""
        
        test_files = []
        
        # Priority order: PDFs first, then others
        file_patterns = [
            ('*.pdf', 10),      # Up to 10 PDFs
            ('*.docx', 5),      # Up to 5 DOCX
            ('*.html', 3),      # Up to 3 HTML
            ('*.pptx', 3),      # Up to 3 PPTX
            ('*.xlsx', 2),      # Up to 2 XLSX
            ('*.csv', 2),       # Up to 2 CSV
            ('*.md', 2)         # Up to 2 MD
        ]
        
        for pattern, limit in file_patterns:
            files = list(self.test_data_dir.glob(f'**/{pattern}'))[:limit]
            test_files.extend(files)
        
        return test_files
    
    def _print_file_breakdown(self, test_files: List[Path]):
        """Print breakdown of test files by type."""
        
        file_types = {}
        for file_path in test_files:
            ext = file_path.suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print("📋 File breakdown:")
        for ext, count in sorted(file_types.items()):
            print(f"   {ext}: {count} files")
    
    def _benchmark_high_performance_system(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark the new high-performance system."""
        
        print("\n🚀 BENCHMARKING HIGH-PERFORMANCE SYSTEM")
        print("-" * 40)
        
        # Setup
        processor = HighPerformancePDFProcessor(max_visual_workers=1)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            # Monitor system resources
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            start_time = time.time()
            individual_times = []
            results = []
            
            try:
                # Process files
                for i, file_path in enumerate(test_files, 1):
                    print(f"   [{i:2d}/{len(test_files)}] {file_path.name}")
                    
                    file_start = time.time()
                    result = processor.process_document(file_path, output_dir)
                    file_time = time.time() - file_start
                    
                    individual_times.append(file_time)
                    results.append(result)
                
                total_time = time.time() - start_time
                
                # Calculate metrics
                successful_results = [r for r in results if r.success]
                success_rate = len(successful_results) / len(results) if results else 0
                
                total_pages = sum(r.extraction_result.page_count for r in successful_results 
                                 if r.extraction_result)
                
                # Strategy breakdown
                fast_text_count = sum(1 for r in successful_results 
                                    if r.processing_strategy == ProcessingStrategy.FAST_TEXT)
                vlm_count = sum(1 for r in successful_results 
                               if r.processing_strategy == ProcessingStrategy.FULL_VLM)
                hybrid_count = sum(1 for r in successful_results 
                                  if r.processing_strategy == ProcessingStrategy.HYBRID)
                
                # Quality metrics
                documents_tagged = sum(1 for r in successful_results if r.document_tags)
                visual_elements = sum(r.visual_jobs_queued for r in successful_results)
                
                # Resource usage
                peak_memory = process.memory_info().rss / 1024 / 1024
                memory_usage = peak_memory - initial_memory
                
                return BenchmarkResult(
                    test_name="High-Performance System",
                    file_count=len(test_files),
                    total_time=total_time,
                    throughput_files_per_minute=len(test_files) / (total_time / 60),
                    pages_processed=total_pages,
                    pages_per_second=total_pages / total_time if total_time > 0 else 0,
                    success_rate=success_rate,
                    memory_peak_mb=memory_usage,
                    cpu_usage_percent=psutil.cpu_percent(),
                    individual_times=individual_times,
                    average_time_per_file=statistics.mean(individual_times) if individual_times else 0,
                    median_time_per_file=statistics.median(individual_times) if individual_times else 0,
                    min_time=min(individual_times) if individual_times else 0,
                    max_time=max(individual_times) if individual_times else 0,
                    fast_text_count=fast_text_count,
                    vlm_count=vlm_count,
                    hybrid_count=hybrid_count,
                    documents_tagged=documents_tagged,
                    visual_elements_detected=visual_elements,
                    errors=[r.error_message for r in results if r.error_message]
                )
                
            finally:
                processor.shutdown()
    
    def _benchmark_traditional_docling(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark traditional docling CLI."""
        
        print("\n📜 BENCHMARKING TRADITIONAL DOCLING")
        print("-" * 40)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            
            start_time = time.time()
            individual_times = []
            successful_files = 0
            errors = []
            
            for i, file_path in enumerate(test_files, 1):
                print(f"   [{i:2d}/{len(test_files)}] {file_path.name}")
                
                file_start = time.time()
                
                try:
                    # Run traditional docling
                    cmd = [
                        'docling',
                        str(file_path),
                        '--to', 'md',
                        '--output', str(output_dir),
                        '--device', 'cuda'
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    file_time = time.time() - file_start
                    individual_times.append(file_time)
                    
                    if result.returncode == 0:
                        successful_files += 1
                    else:
                        errors.append(f"{file_path.name}: {result.stderr[:100]}")
                        
                except subprocess.TimeoutExpired:
                    file_time = 60.0
                    individual_times.append(file_time)
                    errors.append(f"{file_path.name}: Timeout")
                except Exception as e:
                    file_time = 0.0
                    individual_times.append(file_time)
                    errors.append(f"{file_path.name}: {str(e)}")
            
            total_time = time.time() - start_time
            success_rate = successful_files / len(test_files) if test_files else 0
            
            return BenchmarkResult(
                test_name="Traditional Docling",
                file_count=len(test_files),
                total_time=total_time,
                throughput_files_per_minute=len(test_files) / (total_time / 60),
                pages_processed=0,  # Can't easily determine
                pages_per_second=0,
                success_rate=success_rate,
                memory_peak_mb=0,  # Not measured
                cpu_usage_percent=0,
                individual_times=individual_times,
                average_time_per_file=statistics.mean(individual_times) if individual_times else 0,
                median_time_per_file=statistics.median(individual_times) if individual_times else 0,
                min_time=min(individual_times) if individual_times else 0,
                max_time=max(individual_times) if individual_times else 0,
                errors=errors
            )
    
    def _benchmark_fast_text_extraction(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark pure text extraction performance."""
        
        print("\n⚡ BENCHMARKING FAST TEXT EXTRACTION")
        print("-" * 40)
        
        extractor = FastTextExtractor()
        
        start_time = time.time()
        individual_times = []
        successful_extractions = 0
        total_pages = 0
        total_words = 0
        errors = []
        
        for i, file_path in enumerate(test_files, 1):
            print(f"   [{i:2d}/{len(test_files)}] {file_path.name}")
            
            file_start = time.time()
            result = extractor.extract(file_path)
            file_time = time.time() - file_start
            
            individual_times.append(file_time)
            
            if result.success:
                successful_extractions += 1
                total_pages += result.page_count
                total_words += result.word_count
            else:
                errors.append(f"{file_path.name}: {result.error_message}")
        
        total_time = time.time() - start_time
        success_rate = successful_extractions / len(test_files) if test_files else 0
        
        return BenchmarkResult(
            test_name="Fast Text Extraction",
            file_count=len(test_files),
            total_time=total_time,
            throughput_files_per_minute=len(test_files) / (total_time / 60),
            pages_processed=total_pages,
            pages_per_second=total_pages / total_time if total_time > 0 else 0,
            success_rate=success_rate,
            memory_peak_mb=0,
            cpu_usage_percent=0,
            individual_times=individual_times,
            average_time_per_file=statistics.mean(individual_times) if individual_times else 0,
            median_time_per_file=statistics.median(individual_times) if individual_times else 0,
            min_time=min(individual_times) if individual_times else 0,
            max_time=max(individual_times) if individual_times else 0,
            errors=errors
        )
    
    def _benchmark_document_tagging(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark document tagging performance."""
        
        print("\n🏷️  BENCHMARKING DOCUMENT TAGGING")
        print("-" * 40)
        
        extractor = FastTextExtractor()
        tagger = UniversalDocumentTagger()
        
        start_time = time.time()
        individual_times = []
        successful_tags = 0
        total_keywords = 0
        total_entities = 0
        errors = []
        
        for i, file_path in enumerate(test_files, 1):
            print(f"   [{i:2d}/{len(test_files)}] {file_path.name}")
            
            file_start = time.time()
            
            try:
                # Extract text first
                extraction_result = extractor.extract(file_path)
                if not extraction_result.success:
                    raise Exception(f"Text extraction failed: {extraction_result.error_message}")
                
                # Tag document
                tags = tagger.tag_document(
                    extraction_result.text_content,
                    file_path,
                    extraction_result.metadata
                )
                
                file_time = time.time() - file_start
                individual_times.append(file_time)
                
                successful_tags += 1
                total_keywords += len(tags.keywords)
                total_entities += len(tags.entities)
                
            except Exception as e:
                file_time = time.time() - file_start
                individual_times.append(file_time)
                errors.append(f"{file_path.name}: {str(e)}")
        
        total_time = time.time() - start_time
        success_rate = successful_tags / len(test_files) if test_files else 0
        
        return BenchmarkResult(
            test_name="Document Tagging",
            file_count=len(test_files),
            total_time=total_time,
            throughput_files_per_minute=len(test_files) / (total_time / 60),
            pages_processed=0,
            pages_per_second=0,
            success_rate=success_rate,
            memory_peak_mb=0,
            cpu_usage_percent=0,
            individual_times=individual_times,
            average_time_per_file=statistics.mean(individual_times) if individual_times else 0,
            median_time_per_file=statistics.median(individual_times) if individual_times else 0,
            min_time=min(individual_times) if individual_times else 0,
            max_time=max(individual_times) if individual_times else 0,
            documents_tagged=successful_tags,
            errors=errors
        )
    
    def _generate_comparison_report(self):
        """Generate comprehensive comparison report."""
        
        print("\n📊 BENCHMARK COMPARISON REPORT")
        print("=" * 60)
        
        # Performance comparison table
        print(f"{'Method':<25} {'Files/min':<12} {'Pages/sec':<12} {'Success':<10} {'Avg Time':<10}")
        print("-" * 70)
        
        for name, result in self.results.items():
            print(f"{result.test_name:<25} "
                  f"{result.throughput_files_per_minute:<12.1f} "
                  f"{result.pages_per_second:<12.1f} "
                  f"{result.success_rate*100:<10.1f}% "
                  f"{result.average_time_per_file:<10.3f}s")
        
        # Speed comparison
        if "high_performance" in self.results and "traditional_docling" in self.results:
            hp_speed = self.results["high_performance"].throughput_files_per_minute
            trad_speed = self.results["traditional_docling"].throughput_files_per_minute
            
            if trad_speed > 0:
                speedup = hp_speed / trad_speed
                print(f"\n🚀 SPEEDUP: {speedup:.1f}x faster than traditional docling")
        
        # Text extraction performance
        if "fast_text_only" in self.results:
            text_result = self.results["fast_text_only"]
            print(f"\n⚡ TEXT EXTRACTION PERFORMANCE:")
            print(f"   Speed: {text_result.pages_per_second:.1f} pages/second")
            print(f"   Throughput: {text_result.throughput_files_per_minute:.1f} files/minute")
            
            # Check if we hit our target
            if text_result.pages_per_second >= 100:
                print("   ✅ TARGET ACHIEVED: 100+ pages/second")
            else:
                print("   ⚠️  Target not achieved (100+ pages/second)")
        
        # Document intelligence features
        if "high_performance" in self.results:
            hp_result = self.results["high_performance"]
            print(f"\n🧠 DOCUMENT INTELLIGENCE:")
            print(f"   Documents tagged: {hp_result.documents_tagged}/{hp_result.file_count}")
            print(f"   Visual elements detected: {hp_result.visual_elements_detected}")
            print(f"   Strategy breakdown:")
            print(f"     Fast text: {hp_result.fast_text_count}")
            print(f"     VLM: {hp_result.vlm_count}")
            print(f"     Hybrid: {hp_result.hybrid_count}")
        
        # Save detailed report
        self._save_detailed_report()
    
    def _save_detailed_report(self):
        """Save detailed benchmark report to file."""
        
        report_data = {
            "benchmark_info": {
                "timestamp": datetime.now().isoformat(),
                "test_data_directory": str(self.test_data_dir),
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "memory_gb": psutil.virtual_memory().total / (1024**3),
                    "python_version": "3.x"
                }
            },
            "results": {}
        }
        
        for name, result in self.results.items():
            report_data["results"][name] = asdict(result)
        
        # Save to output directory
        output_dir = Path('/home/corey/projects/docling/cli/output/latest')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f"high_performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed report saved: {report_file}")


def main():
    """Run the high-performance processing benchmark."""
    
    benchmark = PerformanceBenchmark()
    
    try:
        results = benchmark.run_comprehensive_benchmark()
        
        print(f"\n✅ BENCHMARK COMPLETE")
        print(f"📋 {len(results)} test suites completed")
        
        # Quick summary
        if "high_performance" in results:
            hp = results["high_performance"]
            print(f"🎯 High-Performance System: {hp.throughput_files_per_minute:.1f} files/min, {hp.pages_per_second:.1f} pages/sec")
        
        if "fast_text_only" in results:
            ft = results["fast_text_only"]
            target_met = "✅" if ft.pages_per_second >= 100 else "⚠️"
            print(f"{target_met} Text Extraction: {ft.pages_per_second:.1f} pages/sec (target: 100+)")
            
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        raise


if __name__ == "__main__":
    main()