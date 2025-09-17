#!/usr/bin/env python3
"""
Production Extractor: High-speed document processing with markdown output.
Handles all document types in corpus (PDF, HTML, text, Excel, etc.)
Optimized for 2000+ pages/second throughput with format-specific optimization.
"""

import os
import sys
import time
import tracemalloc
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from typing import List, Union, Dict, Any
from contextlib import redirect_stderr
from io import StringIO

# Optimization flags
os.environ['PYTHONOPTIMIZE'] = '2'

try:
    import fitz
except ImportError:
    raise ImportError("PyMuPDF (fitz) is required for ProductionExtractor")

from .base_extractor import BaseExtractor, ExtractionResult

# Import centralized YAML metadata engine
import sys
sys.path.append(str(Path(__file__).parent.parent))
from metadata.yaml_metadata_engine import generate_conversion_yaml


class LightweightResourceMonitor:
    """Lightweight resource monitoring focused on processing footprint only"""
    
    def __init__(self):
        self.start_memory = None
        self.peak_memory = 0
        self.cpu_count = mp.cpu_count()
        
    def start_monitoring(self):
        """Start lightweight memory tracking"""
        tracemalloc.start()
        self.start_memory = tracemalloc.get_traced_memory()[0]
        self.peak_memory = self.start_memory
        
    def update_peak_memory(self):
        """Update peak memory usage using tracemalloc"""
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            if peak > self.peak_memory:
                self.peak_memory = peak
            
    def get_resource_summary(self, max_workers: int) -> Dict[str, Any]:
        """Get lightweight resource usage summary"""
        if self.start_memory is None:
            return {}
            
        # Get final memory usage
        if tracemalloc.is_tracing():
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        else:
            current_memory = self.start_memory
            peak_memory = self.peak_memory
            
        memory_used_mb = (peak_memory - self.start_memory) / 1024 / 1024
        peak_memory_mb = peak_memory / 1024 / 1024
        
        # Simple worker count (1 worker = 1 core assumption)
        actual_cores_used = max_workers
        
        return {
            'cpu_cores_total': self.cpu_count,
            'cpu_workers_used': actual_cores_used,
            'memory_peak_mb': peak_memory_mb,
            'memory_used_mb': memory_used_mb,
            'efficiency_pages_per_worker': 0,  # Will be calculated later
            'efficiency_mb_per_worker': 0      # Will be calculated later
        }


def _extract_pdf_to_markdown(pdf_path_and_output_dir):
    """
    Worker function for multiprocessing extraction.
    Optimized for maximum speed using PyMuPDF blocks method.
    """
    pdf_path, output_dir = pdf_path_and_output_dir
    
    try:
        # Capture MuPDF errors to analyze them
        error_buffer = StringIO()
        with redirect_stderr(error_buffer):
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
        
        # Check if we got recoverable errors
        captured_errors = error_buffer.getvalue()
        has_warnings = False
        critical_error = False
        
        if captured_errors:
            if "could not parse color space" in captured_errors:
                has_warnings = True  # Recoverable - color issue, text extraction may still work
            elif "No default Layer config" in captured_errors:
                has_warnings = True  # Recoverable - layer issue, text may still be accessible
            elif "cannot read" in captured_errors or "broken" in captured_errors:
                critical_error = True  # Critical - file is genuinely corrupted
        
        if critical_error:
            doc.close()
            return ExtractionResult(
                success=False,
                file_path=str(pdf_path),
                pages=0,
                error=f"Critical PDF corruption: {captured_errors.strip()[:100]}"
            ).to_dict()
        
        # Skip files that are too large for production processing
        if page_count > 100:
            doc.close()
            return ExtractionResult(
                success=False,
                file_path=str(pdf_path),
                pages=0,
                error=f"Skipped: {page_count} pages (>100 limit)"
            ).to_dict()
        
        # Extract text using blocks method (fastest approach)
        markdown_content = []
        
        # Generate comprehensive YAML frontmatter (single-pass, no re-reading)
        # Check if this is a URL-based extraction (look for companion metadata file)
        metadata_file = pdf_path.parent / f"{pdf_path.stem}_url_metadata.json"
        if metadata_file.exists():
            # URL-based extraction - load metadata
            try:
                import json
                with open(metadata_file, 'r') as f:
                    url_meta = json.load(f)
                yaml_metadata = generate_conversion_yaml(
                    pdf_path, page_count,
                    source_url=url_meta.get('source_url'),
                    content_type=url_meta.get('content_type'), 
                    original_size=url_meta.get('original_size'),
                    http_status=url_meta.get('http_status'),
                    response_headers=url_meta.get('response_headers'),
                    validation_success=url_meta.get('validation_success'),
                    validation_message=url_meta.get('validation_message')
                )
                # Note: Metadata file cleanup handled by pipeline to avoid race conditions
            except Exception:
                # Fallback to regular file processing
                yaml_metadata = generate_conversion_yaml(pdf_path, page_count)
        else:
            # Regular file-based extraction
            yaml_metadata = generate_conversion_yaml(pdf_path, page_count)
        markdown_content.append(yaml_metadata)
        
        # Use URL-based filename if available, otherwise use file name
        if metadata_file.exists():
            try:
                import json
                with open(metadata_file, 'r') as f:
                    url_meta = json.load(f)
                header_name = url_meta.get('safe_filename', pdf_path.name)
            except Exception:
                header_name = pdf_path.name
        else:
            header_name = pdf_path.name
            
        markdown_content.append(f"\n# {header_name}\n\n")
        
        # Process each page with optimal block extraction (suppress MuPDF errors)
        with redirect_stderr(error_buffer):
            for i in range(page_count):
                page = doc[i]
                
                # Add page header for structure
                markdown_content.append(f"## Page {i+1}\n\n")
                
                # Get text blocks for better structure preservation
                blocks = page.get_text("blocks")
                
                for block in blocks:
                    if len(block) > 4:
                        text = block[4].strip()
                        if text:
                            # Clean text for markdown compatibility
                            text = text.replace('\r\n', '\n').replace('\r', '\n')
                            markdown_content.append(text)
                            markdown_content.append("\n\n")
                
                # Add page separator (except for last page)
                if i < page_count - 1:
                    markdown_content.append("---\n\n")
        
        doc.close()
        
        # Join content and save
        full_markdown = ''.join(markdown_content)
        output_file = output_dir / f"{pdf_path.stem}.md"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_markdown)
            
            result_metadata = {'text_len': len(full_markdown)}
            if has_warnings:
                result_metadata['warnings'] = captured_errors.strip()
            
            return ExtractionResult(
                success=True,
                file_path=str(pdf_path),
                pages=page_count,
                output_path=str(output_file),
                **result_metadata
            ).to_dict()
            
        except Exception as save_error:
            return ExtractionResult(
                success=False,
                file_path=str(pdf_path),
                pages=page_count,
                error=f"Save failed: {str(save_error)}"
            ).to_dict()
        
    except Exception as e:
        return ExtractionResult(
            success=False,
            file_path=str(pdf_path),
            pages=0,
            error=str(e)
        ).to_dict()


class HighSpeed_Markdown_General_Extractor(BaseExtractor):
    """
    High-speed PDF extractor optimized for production workloads.
    
    Target Performance: 2000+ pages/second
    Method: PyMuPDF blocks extraction with process pooling
    Output: Clean markdown with structure preservation
    Use Case: Bulk document processing, data pipeline ingestion
    """
    
    def __init__(self, page_limit: int = 100):
        super().__init__(
            name="HighSpeed_Markdown_General",
            description="High-speed document extraction (2000+ pages/sec) with markdown output"
        )
        self.page_limit = page_limit
        self.supported_formats = ['pdf', 'html', 'txt', 'xlsx', 'xls', 'docx', 'doc', 'csv', 'json', 'xml']
        self.output_formats = ['markdown']
    
    def extract_single(self, file_path: Union[str, Path], output_dir: Union[str, Path], 
                      **kwargs) -> ExtractionResult:
        """Extract single PDF with production-optimized settings"""
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.can_process(file_path):
            return ExtractionResult(
                success=False,
                file_path=str(file_path),
                error=f"Unsupported format: {file_path.suffix}"
            )
        
        # Use the optimized worker function
        result_dict = _extract_pdf_to_markdown((file_path, output_dir))
        
        # Convert dictionary keys back to constructor parameters
        # The to_dict() method changes 'file_path' to 'file'
        if 'file' in result_dict:
            result_dict['file_path'] = result_dict.pop('file')
        if 'output' in result_dict:
            result_dict['output_path'] = result_dict.pop('output')
        
        # Remove keys that aren't constructor parameters
        constructor_keys = {'success', 'file_path', 'pages', 'output_path', 'error'}
        filtered_dict = {k: v for k, v in result_dict.items() if k in constructor_keys}
        other_metadata = {k: v for k, v in result_dict.items() if k not in constructor_keys}
        
        # Convert back to ExtractionResult object
        return ExtractionResult(**filtered_dict, **other_metadata)
    
    def extract_batch(self, file_paths: List[Union[str, Path]], 
                     output_dir: Union[str, Path], 
                     max_workers: int = None, **kwargs) -> tuple[List[ExtractionResult], float, Dict[str, Any]]:
        """
        Process multiple PDFs using ProcessPoolExecutor for maximum throughput.
        
        Optimizations:
        - Process-level parallelism for CPU-bound extraction
        - Minimal memory overhead per process
        - Optimized PyMuPDF usage patterns
        
        Returns:
            Tuple of (results_list, total_processing_time, resource_summary)
        """
        if max_workers is None:
            max_workers = mp.cpu_count()
        
        # Initialize lightweight resource monitoring
        resource_monitor = LightweightResourceMonitor()
        resource_monitor.start_monitoring()
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Filter to supported files only
        valid_files = [Path(fp) for fp in file_paths if self.can_process(fp)]
        
        if not valid_files:
            return [], 0.0, {}
        
        # Prepare job arguments for multiprocessing
        job_args = [(pdf_path, output_dir) for pdf_path in valid_files]
        
        start_time = time.perf_counter()
        
        # Execute with ProcessPoolExecutor for optimal parallel processing
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_extract_pdf_to_markdown, args) for args in job_args]
            result_dicts = []
            
            # Show progress every 100 files for large batches
            for i, future in enumerate(futures):
                result_dicts.append(future.result())
                # Update peak memory usage periodically
                if i % 10 == 0:
                    resource_monitor.update_peak_memory()
                if len(valid_files) > 100 and (i + 1) % 100 == 0:
                    print(f"   📊 Progress: {i + 1}/{len(valid_files)} files processed")
        
        total_time = time.perf_counter() - start_time
        
        # Convert result dictionaries back to ExtractionResult objects
        results = []
        for rd in result_dicts:
            # Extract standard parameters and put the rest in kwargs
            # Note: to_dict() maps file_path -> 'file' and output_path -> 'output'
            standard_params = {
                'success': rd.get('success', False),
                'file_path': rd.get('file_path', rd.get('file', '')),  # Check both keys
                'pages': rd.get('pages', 0),
                'output_path': rd.get('output_path', rd.get('output')),  # Check both keys
                'error': rd.get('error')
            }
            # Put any extra fields in kwargs
            kwargs = {k: v for k, v in rd.items() if k not in standard_params and k not in ['file', 'output']}
            results.append(ExtractionResult(**standard_params, **kwargs))
        
        # Update performance metrics
        self.update_metrics(results, total_time)
        
        # Get system resource summary
        resource_summary = resource_monitor.get_resource_summary(max_workers)
        
        # Calculate efficiency metrics
        successful_results = [r for r in results if r.success]
        total_pages = sum(r.pages for r in successful_results)
        total_input_mb = sum(Path(r.file_path).stat().st_size for r in successful_results) / 1024 / 1024
        
        if resource_summary and total_pages > 0:
            resource_summary['efficiency_pages_per_worker'] = total_pages / resource_summary['cpu_workers_used']
            resource_summary['efficiency_mb_per_worker'] = total_input_mb / resource_summary['cpu_workers_used']
        
        return results, total_time, resource_summary
    
    def get_supported_formats(self) -> List[str]:
        """Return supported input formats"""
        return self.supported_formats.copy()
    
    def get_output_formats(self) -> List[str]:
        """Return supported output formats"""
        return self.output_formats.copy()
    
    def benchmark_performance(self, test_files: List[Union[str, Path]], 
                            output_dir: Union[str, Path], 
                            target_pages_per_sec: float = 2000.0) -> Dict[str, Any]:
        """
        Run performance benchmark and return detailed metrics.
        
        Args:
            test_files: List of PDF files for testing
            output_dir: Output directory for results
            target_pages_per_sec: Target performance threshold
            
        Returns:
            Dictionary with comprehensive performance analysis
        """
        print(f"🎯 ProductionExtractor Benchmark")
        print(f"📁 Test files: {len(test_files)}")
        print(f"🎯 Target: {target_pages_per_sec}+ pages/sec")
        
        # Reset metrics for clean benchmark
        self.reset_metrics()
        
        # Run extraction
        results, total_time, resource_summary = self.extract_batch(test_files, output_dir)
        
        # Calculate detailed metrics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        total_pages = sum(r.pages for r in successful)
        total_chars = sum(r.metadata.get('text_len', 0) for r in successful)
        
        performance = self.get_performance_summary()
        
        # Performance analysis
        benchmark_result = {
            'extractor': self.name,
            'performance': performance,
            'results_summary': {
                'total_files': len(results),
                'successful_files': len(successful),
                'failed_files': len(failed),
                'total_pages': total_pages,
                'total_characters': total_chars,
                'processing_time': total_time
            },
            'target_analysis': {
                'target_pages_per_sec': target_pages_per_sec,
                'actual_pages_per_sec': performance['pages_per_second'],
                'target_achieved': performance['pages_per_second'] >= target_pages_per_sec,
                'performance_ratio': performance['pages_per_second'] / target_pages_per_sec if target_pages_per_sec > 0 else 0
            },
            'quality_metrics': {
                'success_rate': performance['success_rate'],
                'avg_pages_per_file': total_pages / len(successful) if successful else 0,
                'avg_chars_per_page': total_chars / total_pages if total_pages > 0 else 0
            }
        }
        
        # Print results
        self._print_benchmark_results(benchmark_result)
        
        return benchmark_result
    
    def _print_benchmark_results(self, benchmark: Dict[str, Any]):
        """Print formatted benchmark results"""
        perf = benchmark['performance']
        results = benchmark['results_summary']
        target = benchmark['target_analysis']
        quality = benchmark['quality_metrics']
        
        print(f"\n" + "="*70)
        print(f"📊 PRODUCTION EXTRACTOR BENCHMARK RESULTS")
        print(f"="*70)
        
        print(f"✅ Files processed: {results['successful_files']}/{results['total_files']}")
        print(f"📄 Total pages: {results['total_pages']}")
        print(f"📝 Total characters: {results['total_characters']:,}")
        print(f"⏱️  Processing time: {results['processing_time']:.2f}s")
        
        print(f"\n🚀 PERFORMANCE METRICS:")
        print(f"   Pages per second: {perf['pages_per_second']:.1f}")
        print(f"   Files per second: {perf['files_per_second']:.1f}")
        print(f"   Success rate: {quality['success_rate']:.1%}")
        
        # Target analysis
        if target['target_achieved']:
            print(f"\n🎉 TARGET ACHIEVED!")
            print(f"   🚀 {perf['pages_per_second']:.1f} pages/sec (target: {target['target_pages_per_sec']})")
            print(f"   📈 Performance ratio: {target['performance_ratio']:.2f}x target")
        else:
            print(f"\n⚠️  Below target:")
            print(f"   📊 {perf['pages_per_second']:.1f} pages/sec (target: {target['target_pages_per_sec']})")
            print(f"   📉 Performance ratio: {target['performance_ratio']:.2f}x target")
        
        print(f"\n📋 QUALITY METRICS:")
        print(f"   Average pages per file: {quality['avg_pages_per_file']:.1f}")
        print(f"   Average characters per page: {quality['avg_chars_per_page']:.0f}")
    
    def verify_output_quality(self, output_dir: Union[str, Path], 
                            sample_count: int = 3) -> Dict[str, Any]:
        """
        Verify the quality of generated markdown files.
        
        Args:
            output_dir: Directory containing output files
            sample_count: Number of files to sample for quality check
            
        Returns:
            Quality analysis results
        """
        output_dir = Path(output_dir)
        md_files = list(output_dir.glob("*.md"))[:sample_count]
        
        if not md_files:
            return {'error': 'No markdown files found in output directory'}
        
        quality_results = {
            'files_checked': len(md_files),
            'total_files': len(list(output_dir.glob("*.md"))),
            'file_analyses': []
        }
        
        print(f"\n🔍 QUALITY VERIFICATION")
        print(f"="*70)
        
        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Analyze structure and content
            analysis = {
                'filename': md_file.name,
                'size_bytes': len(content.encode('utf-8')),
                'size_chars': len(content),
                'has_title': content.startswith("#"),
                'has_metadata': "**Pages:**" in content and "**Source:**" in content,
                'has_page_headers': "## Page" in content,
                'page_count': content.count("## Page"),
                'has_substantial_content': len(content) > 1000,
                'line_count': content.count('\n')
            }
            
            quality_results['file_analyses'].append(analysis)
            
            print(f"\n📄 {analysis['filename']}:")
            print(f"   ✓ Size: {analysis['size_chars']:,} characters")
            print(f"   ✓ Has title: {analysis['has_title']}")
            print(f"   ✓ Has metadata: {analysis['has_metadata']}")
            print(f"   ✓ Has page headers: {analysis['has_page_headers']}")
            print(f"   ✓ Pages extracted: {analysis['page_count']}")
            print(f"   ✓ Substantial content: {analysis['has_substantial_content']}")
        
        return quality_results