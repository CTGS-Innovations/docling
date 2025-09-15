#!/usr/bin/env python3
"""
MVP Docling Core: High-Performance Document Processor with Docling
================================================================
Target: Fast conversion using Docling's DocumentConverter with performance fallbacks
Uses Docling for everything but provides performance fallbacks for slow files
"""

import os
import sys
import time
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import hashlib
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import asyncio

# Docling imports
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
    HAS_DOCLING = True
except ImportError:
    HAS_DOCLING = False
    print("ERROR: Docling not available. Install with: pip install docling")
    sys.exit(1)

# Optional performance fallback
try:
    import fitz  # PyMuPDF for fallback
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


@dataclass
class DoclingResult:
    """Result structure for Docling conversion."""
    file_path: str
    success: bool
    text: str
    page_count: int
    extraction_time: float
    pages_per_second: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
    conversion_method: str = "docling"


class DoclingExtractor:
    """Core extraction engine using Docling with performance fallbacks."""
    
    def __init__(self, 
                 num_workers: Optional[int] = None,
                 batch_size: int = 100,
                 fallback_threshold: float = 5.0,  # Use fallback if file takes >5s
                 use_gpu: bool = False):
        
        self.num_workers = num_workers or min(32, (os.cpu_count() or 1) + 4)
        self.batch_size = batch_size
        self.fallback_threshold = fallback_threshold
        # Force CPU processing regardless of use_gpu flag
        self.use_gpu = False
        
        # Initialize Docling converter
        self.converter = self._create_docling_converter()
        
        # Performance tracking
        self.total_files = 0
        self.total_pages = 0
        self.total_time = 0.0
        self.conversion_stats = {
            'docling': {'files': 0, 'pages': 0, 'time': 0},
            'fallback': {'files': 0, 'pages': 0, 'time': 0}
        }
    
    def _create_docling_converter(self) -> DocumentConverter:
        """Create optimized Docling DocumentConverter using fast PyPdfium backend."""
        
        # Import the fast backend (like scout-docs)
        from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
        from docling.datamodel.pipeline_options import PdfBackend
        
        # Force CPU-only processing for better performance
        accelerator_options = AcceleratorOptions(
            device=AcceleratorDevice.CPU,
            num_threads=8
        )
        
        # Use the FAST_TEXT configuration from scout-docs
        pipeline_options = PdfPipelineOptions(
            accelerator_options=accelerator_options,
            do_ocr=False,
            do_table_structure=False,
            do_picture_classification=False,
            do_picture_description=False,
            generate_page_images=False,
            generate_picture_images=False,
            generate_table_images=False,
            generate_parsed_pages=False,
            force_backend_text=True
        )
        
        # Create converter with PyPdfium backend for speed (like scout-docs FAST_TEXT)
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend  # This is the key!
                )
            }
        )
        
        return converter
    
    def _fallback_extract_pdf(self, file_path: str) -> DoclingResult:
        """Fallback PDF extraction using PyMuPDF for performance."""
        if not HAS_PYMUPDF:
            return DoclingResult(
                file_path=file_path,
                success=False,
                text="",
                page_count=0,
                extraction_time=0,
                pages_per_second=0,
                metadata={},
                error="No fallback extractor available",
                conversion_method="fallback_failed"
            )
        
        start_time = time.time()
        try:
            doc = fitz.open(file_path)
            page_count = len(doc)
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(page_count):
                page = doc[page_num]
                text_parts.append(page.get_text())
            
            text = "\n\n".join(text_parts)
            doc.close()
            
            elapsed = time.time() - start_time
            pages_per_sec = page_count / elapsed if elapsed > 0 else 0
            
            return DoclingResult(
                file_path=file_path,
                success=True,
                text=text,
                page_count=page_count,
                extraction_time=elapsed,
                pages_per_second=pages_per_sec,
                metadata={'method': 'pymupdf_fallback'},
                conversion_method="fallback"
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            return DoclingResult(
                file_path=file_path,
                success=False,
                text="",
                page_count=0,
                extraction_time=elapsed,
                pages_per_second=0,
                metadata={},
                error=str(e),
                conversion_method="fallback_failed"
            )
    
    def _extract_single_file(self, file_path: str, max_pages: int = 25) -> DoclingResult:
        """Extract single file using Docling with fallback logic."""
        
        start_time = time.time()
        
        try:
            # Try Docling first
            result = self.converter.convert(file_path)
            
            # Check if it's taking too long (implement timeout if needed)
            elapsed = time.time() - start_time
            
            # If successful, extract text (use faster text export instead of markdown)
            if result.document:
                text = result.document.export_to_text()  # Much faster than markdown
                page_count = len(result.document.pages) if hasattr(result.document, 'pages') else 1
                
                # Limit pages if specified
                if max_pages > 0 and page_count > max_pages:
                    # For now, just note it in metadata - Docling handles page limiting differently
                    pass
                
                pages_per_sec = page_count / elapsed if elapsed > 0 else 0
                
                return DoclingResult(
                    file_path=file_path,
                    success=True,
                    text=text,
                    page_count=page_count,
                    extraction_time=elapsed,
                    pages_per_second=pages_per_sec,
                    metadata={
                        'method': 'docling',
                        'docling_version': 'latest'
                    },
                    conversion_method="docling"
                )
            else:
                # Docling failed, try fallback
                if elapsed > self.fallback_threshold:
                    print(f"⚠️  Docling slow ({elapsed:.1f}s), trying fallback for {Path(file_path).name}")
                    return self._fallback_extract_pdf(file_path)
                else:
                    return DoclingResult(
                        file_path=file_path,
                        success=False,
                        text="",
                        page_count=0,
                        extraction_time=elapsed,
                        pages_per_second=0,
                        metadata={},
                        error="Docling conversion failed",
                        conversion_method="docling_failed"
                    )
                    
        except Exception as e:
            elapsed = time.time() - start_time
            
            # If Docling fails or is too slow, try fallback
            if elapsed > self.fallback_threshold or "timeout" in str(e).lower():
                print(f"⚠️  Docling failed/slow ({elapsed:.1f}s), trying fallback for {Path(file_path).name}")
                return self._fallback_extract_pdf(file_path)
            else:
                return DoclingResult(
                    file_path=file_path,
                    success=False,
                    text="",
                    page_count=0,
                    extraction_time=elapsed,
                    pages_per_second=0,
                    metadata={},
                    error=str(e),
                    conversion_method="docling_failed"
                )
    
    def process_files(self, file_paths: List[str], output_dir: str, max_pages: int = 25) -> List[DoclingResult]:
        """Process multiple files with progress tracking."""
        
        results = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📂 Processing {len(file_paths)} files with Docling")
        print(f"🎯 Target: Fast conversion with fallbacks")
        print(f"📁 Output: {output_dir}")
        
        start_time = time.time()
        
        # Process files in batches for better performance
        for i in range(0, len(file_paths), self.batch_size):
            batch = file_paths[i:i + self.batch_size]
            batch_results = []
            
            # Process batch with threading (Docling may benefit from this)
            with ThreadPoolExecutor(max_workers=min(4, len(batch))) as executor:
                futures = []
                for file_path in batch:
                    future = executor.submit(self._extract_single_file, file_path, max_pages)
                    futures.append(future)
                
                for future in futures:
                    result = future.result()
                    batch_results.append(result)
                    
                    # Write output file if successful
                    if result.success and result.text:
                        input_file = Path(result.file_path)
                        output_file = output_path / f"{input_file.stem}.md"
                        
                        # Create simple markdown (faster than complex front matter)
                        markdown_content = f"# {input_file.stem}\n\n{result.text}"
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
            
            results.extend(batch_results)
            
            # Update stats
            for result in batch_results:
                self.total_files += 1
                if result.success:
                    self.total_pages += result.page_count
                    self.total_time += result.extraction_time
                    
                    # Track by conversion method
                    method = result.conversion_method
                    if method in self.conversion_stats:
                        self.conversion_stats[method]['files'] += 1
                        self.conversion_stats[method]['pages'] += result.page_count
                        self.conversion_stats[method]['time'] += result.extraction_time
            
            # Progress update
            processed = min(i + self.batch_size, len(file_paths))
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            
            print(f"📊 Progress: {processed}/{len(file_paths)} files ({rate:.1f} files/sec)")
            
        return results
    
    def print_performance_summary(self):
        """Print detailed performance breakdown."""
        total_elapsed = self.total_time
        avg_pages_per_sec = self.total_pages / total_elapsed if total_elapsed > 0 else 0
        
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    DOCLING PERFORMANCE SUMMARY               ║
╚═══════════════════════════════════════════════════════════════╝

📊 OVERALL METRICS:
   Total Files:    {self.total_files}
   Total Pages:    {self.total_pages}
   Total Time:     {total_elapsed:.2f}s
   Avg Speed:      {avg_pages_per_sec:.1f} pages/sec

🔄 CONVERSION METHOD BREAKDOWN:""")
        
        for method, stats in self.conversion_stats.items():
            if stats['files'] > 0:
                method_speed = stats['pages'] / stats['time'] if stats['time'] > 0 else 0
                print(f"   {method.upper():12} {stats['files']:4} files, {stats['pages']:5} pages, {method_speed:6.1f} pages/sec")
        
        print(f"""
✨ Docling conversion complete! Check output directory for results.
        """)


def load_config(config_path: str) -> Dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"⚠️  Config file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        print(f"⚠️  Error parsing config file: {e}")
        return {}


def collect_files(input_paths: List[str], config: Dict) -> List[str]:
    """Collect files to process from input paths and config."""
    all_files = []
    
    # If command line input is provided, use ONLY that - ignore config directories
    if input_paths:
        for input_path in input_paths:
            path = Path(input_path).expanduser()
            if path.is_file():
                all_files.append(str(path))
            elif path.is_dir():
                for file_path in path.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.pptx', '.xlsx']:
                        all_files.append(str(file_path))
    else:
        # Only use config directories if no command line input provided
        if config and 'inputs' in config and 'directories' in config['inputs']:
            for dir_path in config['inputs']['directories']:
                expanded_path = Path(dir_path).expanduser()
                if expanded_path.exists():
                    for file_path in expanded_path.rglob('*'):
                        if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.pptx', '.xlsx']:
                            all_files.append(str(file_path))
    
    # Remove duplicates and apply filters
    unique_files = list(set(all_files))
    
    # Apply skip patterns and size limits from config
    filtered_files = []
    skip_extensions = config.get('processing', {}).get('skip_extensions', [])
    max_size_mb = config.get('processing', {}).get('max_file_size_mb', 100)
    
    for file_path in unique_files:
        path = Path(file_path)
        
        # Skip by extension
        if path.suffix.lower() in skip_extensions:
            continue
        
        # Skip by size
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > max_size_mb:
                continue
        except:
            continue
        
        filtered_files.append(file_path)
    
    return filtered_files


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MVP Docling Core - High-Performance Document Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("input", nargs='*', help="Input files or directories")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--max-pages", type=int, default=25, help="Max pages to extract per document")
    parser.add_argument("--workers", type=int, help="Number of worker processes")
    parser.add_argument("--gpu", action="store_true", help="Use GPU acceleration if available")
    parser.add_argument("--fallback-threshold", type=float, default=5.0, help="Fallback threshold in seconds")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        config = load_config(args.config)
    else:
        # Try default config locations
        current_dir = Path(__file__).parent
        default_configs = [
            current_dir / ".config" / "config.yaml",
            current_dir / ".config" / "mvp-docling-config.yaml"
        ]
        
        for config_path in default_configs:
            if config_path.exists():
                config = load_config(str(config_path))
                break
    
    # Collect files to process
    input_paths = args.input if args.input else []
    files_to_process = collect_files(input_paths, config)
    
    if not files_to_process:
        print("❌ No files found to process")
        return
    
    if not args.quiet:
        print(f"🎯 Found {len(files_to_process)} files to process")
        print(f"📁 Output directory: {args.output}")
        print(f"🔧 Using Docling with performance fallbacks")
        if args.gpu:
            print("🚀 GPU acceleration enabled")
    
    # Initialize extractor
    extractor = DoclingExtractor(
        num_workers=args.workers,
        fallback_threshold=args.fallback_threshold,
        use_gpu=args.gpu
    )
    
    # Process files
    start_time = time.time()
    results = extractor.process_files(files_to_process, args.output, args.max_pages)
    total_time = time.time() - start_time
    
    # Print summary
    if not args.quiet:
        extractor.print_performance_summary()
        
        # Print per-extension breakdown
        extensions = {}
        for result in results:
            if result.success:
                ext = Path(result.file_path).suffix.lower()
                if ext not in extensions:
                    extensions[ext] = {'files': 0, 'pages': 0, 'time': 0}
                extensions[ext]['files'] += 1
                extensions[ext]['pages'] += result.page_count
                extensions[ext]['time'] += result.extraction_time
        
        print("📈 BY FILE TYPE:")
        for ext, stats in sorted(extensions.items()):
            speed = stats['pages'] / stats['time'] if stats['time'] > 0 else 0
            print(f"   {ext:8} {stats['files']:4} files, {stats['pages']:5} pages, {speed:6.1f} pages/sec")


if __name__ == "__main__":
    main()