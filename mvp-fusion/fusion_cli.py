#!/usr/bin/env python3
"""
MVP-Fusion Command Line Interface
=================================

High-performance document processing with MVP-Hyper output compatibility.
Process individual files or entire directories at 10,000+ pages/sec.

Usage:
    python fusion_cli.py --file document.pdf
    python fusion_cli.py --directory ~/documents/ --batch-size 32
    python fusion_cli.py --config custom_config.yaml --performance-test
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import json

# Import our centralized logging configuration
from utils.logging_config import setup_logging, get_fusion_logger

# Import extraction architecture
from extraction import (
    BaseExtractor,
    HighSpeed_Markdown_General_Extractor,
    HighAccuracy_Markdown_General_Extractor,
    HighSpeed_JSON_PDF_Extractor,
    Specialized_Markdown_Legal_Extractor
)


def get_available_extractors():
    """Return mapping of extractor names to classes."""
    return {
        'highspeed_markdown_general': HighSpeed_Markdown_General_Extractor,
        'highaccuracy_markdown_general': HighAccuracy_Markdown_General_Extractor,
        'highspeed_json_pdf': HighSpeed_JSON_PDF_Extractor,
        'specialized_markdown_legal': Specialized_Markdown_Legal_Extractor
    }

def create_extractor(extractor_name: str, config: dict = None):
    """Factory function to create extractor by name."""
    extractors = get_available_extractors()
    
    if extractor_name not in extractors:
        available = list(extractors.keys())
        raise ValueError(f"Unknown extractor '{extractor_name}'. Available: {available}")
    
    extractor_class = extractors[extractor_name]
    
    # Pass config parameters if the extractor supports them
    if config and extractor_name == 'highspeed_markdown_general':
        page_limit = config.get('page_limit', 100)
        return extractor_class(page_limit=page_limit)
    else:
        return extractor_class()



def process_single_file(extractor: BaseExtractor, file_path: Path, output_dir: Path = None, quiet: bool = False) -> Dict[str, Any]:
    """Process a single file and return results."""
    logger = get_fusion_logger(__name__)
    if not quiet:
        logger.stage(f"Processing: {file_path.name}")
    
    result = extractor.extract_single(file_path, output_dir or Path.cwd())
    
    if not quiet and not result.success:
        logger.logger.error(f"❌ Error: {result.error}")
    
    return result


def process_directory(extractor: BaseExtractor, directory: Path, 
                     file_extensions: List[str] = None, output_dir: Path = None):
    """Process all files in a directory using high-speed batch processing."""
    logger = get_fusion_logger(__name__)
    if file_extensions is None:
        file_extensions = ['.txt', '.md', '.pdf', '.docx', '.doc']
    
    # Find all files
    files = []
    for ext in file_extensions:
        files.extend(directory.glob(f"**/*{ext}"))
    
    if not files:
        logger.logger.warning(f"No files found in {directory} with extensions {file_extensions}")
        return []
    
    logger.stage(f"📁 Found {len(files)} files in {directory.name}")
    
    # Show progress indicator for large batches
    if len(files) > 100:
        logger.stage(f"🚀 Processing {len(files)} files (progress shown every 100 files)...")
    else:
        logger.stage(f"🚀 Processing {len(files)} files...")
    
    start_time = time.time()
    
    # Use the extractor's optimized batch processing
    batch_result = extractor.extract_batch(files, output_dir or Path.cwd())
    
    # Handle different return signatures (some extractors return resource summary)
    if len(batch_result) == 3:
        results, total_time, resource_summary = batch_result
    else:
        results, total_time = batch_result
        resource_summary = None
    
    # Clean summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    rate = len(files) / total_time if total_time > 0 else 0
    
    logger.success(f"Completed: {successful} successful, {failed} failed ({rate:.0f} files/sec)")
    
    # Final statistics
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    
    logger.stage(f"\n📊 Processing Complete:")
    logger.stage(f"   Total files: {len(results)}")
    logger.stage(f"   Successful: {successful}")
    logger.stage(f"   Failed: {failed}")
    logger.stage(f"   Total time: {total_time:.2f}s")
    logger.stage(f"   Average rate: {len(results)/total_time:.1f} files/sec")
    
    return results


def run_performance_test(extractor: BaseExtractor, max_workers: int) -> Dict[str, Any]:
    """Run performance benchmark test using the configured extractor."""
    logger = get_fusion_logger(__name__)
    logger.stage("🚀 Running MVP-Fusion Performance Test...")
    
    # Create test content
    test_content = """
    OSHA regulation 29 CFR 1926.95 requires all construction workers to wear 
    appropriate personal protective equipment (PPE) including hard hats, 
    safety glasses, and high-visibility clothing when working in designated areas.
    
    For training information, contact safety-coordinator@company.com or call 
    (555) 123-4567 to schedule a session. Training costs $2,500 per group 
    and must be completed by March 15, 2024 at 2:30 PM.
    
    Environmental compliance is monitored by the EPA under regulation 
    40 CFR 261.1. All hazardous materials must be properly disposed of 
    to prevent soil and groundwater contamination.
    
    Temperature monitoring systems must maintain readings between 65-75°F 
    in all work areas. Version 2.1.3 of the monitoring software is required 
    for compliance reporting.
    
    Workers exposed to noise levels above 85 dB must wear hearing protection.
    The permissible exposure limit (PEL) for chemical substances varies by 
    material but must not exceed NIOSH recommended levels.
    
    Emergency procedures require immediate notification of supervisors and 
    evacuation following posted routes. All incidents must be reported 
    within 24 hours to comply with OSHA recordkeeping requirements.
    """
    
    # Test different scenarios
    test_scenarios = [
        ("Small document", test_content[:500], 100),
        ("Medium document", test_content, 50),  
        ("Large document", test_content * 3, 25),
        ("Complex document", test_content * 5, 10)
    ]
    
    results = {}
    
    for scenario_name, content, iterations in test_scenarios:
        logger.stage(f"\n📋 Testing {scenario_name} ({len(content)} chars, {iterations} iterations)...")
        
        start_time = time.time()
        scenario_results = []
        
        # Create temporary test file
        test_file = Path(f"temp_test_doc.txt")
        test_file.write_text(content)
        
        try:
            for i in range(iterations):
                result = extractor.extract_single(test_file, Path.cwd())
                scenario_results.append(result)
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
            
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                logger.entity(f"  Progress: {i+1}/{iterations} ({rate:.1f} docs/sec)")
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in scenario_results if r.success)
        
        if successful > 0:
            avg_processing_time = sum(
                r.extraction_time_ms 
                for r in scenario_results if r.success
            ) / successful
            
            total_pages = sum(
                r.page_count
                for r in scenario_results if r.success
            )
            
            docs_per_sec = iterations / total_time
            chars_per_sec = (len(content) * iterations) / total_time
            
            results[scenario_name] = {
                'iterations': iterations,
                'successful': successful,
                'total_time': total_time,
                'docs_per_sec': docs_per_sec,
                'chars_per_sec': chars_per_sec,
                'avg_processing_time_ms': avg_processing_time,
                'total_pages': total_pages,
                'chars_per_doc': len(content)
            }
            
            logger.success(f"{successful}/{iterations} successful")
            logger.entity(f"📊 Rate: {docs_per_sec:.1f} docs/sec")
            logger.entity(f"⚡ Speed: {chars_per_sec:,.0f} chars/sec")
            logger.entity(f"📚 Pages: {total_pages} total")
        else:
            results[scenario_name] = {'error': 'All tests failed'}
    
    return results


def print_performance_summary(extractor: BaseExtractor, max_workers: int):
    """Print comprehensive performance summary."""
    logger = get_fusion_logger(__name__)
    perf = extractor.get_performance_summary()
    
    logger.stage("\n" + "="*60)
    logger.stage("🎯 MVP-FUSION PERFORMANCE SUMMARY")
    logger.stage("="*60)
    logger.stage(f"🔧 Engine: {extractor.__class__.__name__}")
    logger.stage(f"⚡ Peak Performance: {perf.get('pages_per_second', 0):.0f} pages/sec")
    logger.stage(f"📊 Efficiency: {perf.get('success_rate', 0)*100:.1f}% success rate")
    logger.stage(f"🔧 Configuration: {max_workers} workers, {perf.get('total_files', 0)} files processed")
    return
    
    logger.stage(f"\n" + "="*60)
    logger.stage(f"🎯 MVP-FUSION PERFORMANCE SUMMARY")
    logger.stage(f"="*60)
    
    # Pipeline performance
    logger.stage(f"📄 Documents processed: {metrics['documents_processed']}")
    logger.stage(f"⏱️  Average time per doc: {metrics.get('avg_processing_time_per_doc', 0):.3f}s")
    logger.stage(f"🚀 Pages per second: {metrics.get('pages_per_second', 0):.1f}")
    logger.logger.error(f"❌ Error rate: {metrics.get('error_rate', 0):.1%}")
    
    # Engine performance
    fusion_metrics = metrics.get('fusion_engine_metrics', {})
    if fusion_metrics:
        logger.stage(f"\n🔧 Engine Performance:")
        logger.stage(f"   Pages/sec: {fusion_metrics.get('pages_per_second', 0):.1f}")
        logger.stage(f"   Entities/doc: {fusion_metrics.get('entities_per_document', 0):.1f}")
        logger.stage(f"   Engine usage: {fusion_metrics.get('engine_usage', {})}")
    
    # Batch processor performance
    batch_metrics = metrics.get('batch_processor_metrics', {})
    if batch_metrics:
        logger.stage(f"\n📦 Batch Processing:")
        logger.stage(f"   Docs/sec: {batch_metrics.get('documents_per_second', 0):.1f}")
        logger.stage(f"   Parallel efficiency: {batch_metrics.get('parallel_efficiency', 0):.1%}")
        logger.stage(f"   Avg docs/batch: {batch_metrics.get('avg_docs_per_batch', 0):.1f}")
    
    logger.stage(f"\n" + "="*60)


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description="MVP-Fusion: High-Performance Document Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Verbosity Levels:
  -q, --quiet     : Minimal output (errors and final results only)
  (default)       : Normal output (stage progress and key metrics)  
  -v, --verbose   : Detailed output (includes entity counts, memory usage)
  -vv             : Debug output (full diagnostic info with timestamps)

Examples:
  # Basic file processing
  python fusion_cli.py --file document.pdf                    # Normal output
  python fusion_cli.py --file document.pdf -q                 # Quiet mode
  python fusion_cli.py --file document.pdf -v                 # Verbose mode
  python fusion_cli.py --file document.pdf -vv                # Debug mode
  
  # Directory processing with options
  python fusion_cli.py --directory ~/documents/ --extensions .pdf .docx
  python fusion_cli.py --directory ~/documents/ -q            # Process quietly
  python fusion_cli.py --directory ~/documents/ -v --log-file process.log
  
  # Pipeline control
  python fusion_cli.py --config config/fusion_config.yaml --stages all
  python fusion_cli.py --config config/fusion_config.yaml --convert-only -v
  python fusion_cli.py --config config/fusion_config.yaml --stages convert classify
  
  # Performance testing
  python fusion_cli.py --performance-test                     # Normal output
  python fusion_cli.py --performance-test -vv                 # Full debug info
  
  # Additional output options
  python fusion_cli.py --file doc.pdf --no-color              # Disable colors
  python fusion_cli.py --file doc.pdf --json-logs             # JSON format
  python fusion_cli.py --file doc.pdf -v --log-file out.log   # Log to file
        """
    )
    
    # Input options (optional if config file has directories)
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--file', '-f', type=str, help='Process single file')
    input_group.add_argument('--directory', '-d', type=str, help='Process directory')
    input_group.add_argument('--config-directories', action='store_true',
                           help='Process all directories specified in config file')
    input_group.add_argument('--performance-test', '-t', action='store_true', 
                           help='Run performance benchmark')
    
    # Configuration options
    parser.add_argument('--config', '-c', type=str, default='config/config.yaml',
                       help='Configuration file path (default: config/config.yaml)')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--batch-size', '-b', type=int, default=32, 
                       help='Batch size for parallel processing')
    
    # File options
    parser.add_argument('--extensions', nargs='+', default=['.txt', '.md', '.pdf', '.docx'],
                       help='File extensions to process')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process directories recursively')
    
    # Performance options
    parser.add_argument('--workers', '-w', type=int, 
                       help='Workers (cores): 1=524 p/s, 4=2014 p/s, 8=3454 p/s (sweet spot), 16=4160 p/s')
    parser.add_argument('--memory-limit', type=int, help='Memory limit in GB')
    parser.add_argument('--extractor', '-e', type=str,
                       choices=['highspeed_markdown_general', 'highaccuracy_markdown_general', 
                               'highspeed_json_pdf', 'specialized_markdown_legal'],
                       help='Extraction engine (default: from config file)')
    
    # Pipeline stage options
    parser.add_argument('--stages', nargs='+', 
                       choices=['convert', 'classify', 'enrich', 'extract', 'all'],
                       default=['all'],
                       help='Pipeline stages to run (default: all)')
    parser.add_argument('--convert-only', action='store_true',
                       help='Run only conversion stage (PDF -> Markdown)')
    parser.add_argument('--classify-only', action='store_true', 
                       help='Run only classification stage')
    parser.add_argument('--enrich-only', action='store_true',
                       help='Run only enrichment stage')
    parser.add_argument('--extract-only', action='store_true',
                       help='Run only semantic extraction stage')
    
    # Output options
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('--quiet', '-q', action='store_true',
                                help='Quiet mode: minimal output showing only errors and final results (PAGES/SEC, SUCCESS RATE)')
    verbosity_group.add_argument('--verbose', '-v', action='count', default=0,
                                help='Increase verbosity (use -v for detailed progress with entity counts, -vv for full debug with timestamps)')
    parser.add_argument('--log-file', type=str, 
                       help='Save all output to specified file (useful with -v or -vv for debugging)')
    parser.add_argument('--no-color', action='store_true', 
                       help='Disable colored terminal output (useful for log files or CI/CD pipelines)')
    parser.add_argument('--json-logs', action='store_true', 
                       help='Output logs in JSON format for structured logging systems')
    parser.add_argument('--export-metrics', type=str, help='Export metrics to JSON file')
    
    args = parser.parse_args()
    
    # Load base configuration first to get logging defaults
    config = _load_and_override_config(args)
    
    # Setup logging with proper verbosity levels
    # Priority: CLI flags > config file > defaults
    if args.quiet:
        verbosity = 0  # QUIET mode
    elif args.verbose:
        verbosity = min(args.verbose + 1, 3)  # -v=2 (VERBOSE), -vv=3 (DEBUG)
    else:
        # Use config file setting or default to NORMAL (1)
        verbosity = config.get('logging', {}).get('verbosity', 1)
    
    # Get logging options from config or CLI
    log_file_config = config.get('logging', {}).get('file')
    log_file = Path(args.log_file) if args.log_file else (Path(log_file_config) if log_file_config else None)
    
    use_colors_config = config.get('logging', {}).get('use_colors', True)
    use_colors = not args.no_color and use_colors_config
    
    json_format_config = config.get('logging', {}).get('json_format', False)
    json_format = args.json_logs or json_format_config
    
    setup_logging(
        verbosity=verbosity,
        log_file=log_file,
        use_colors=use_colors,
        json_format=json_format
    )
    
    # Get logger for CLI module
    logger = get_fusion_logger(__name__)
    
    try:
        # Config was already loaded above for logging setup
        # No need to reload here
        
        # Initialize configured extractor
        extractor_name = args.extractor or config.get('extractor', {}).get('name', 'highspeed_markdown_general')
        extractor_config = {
            'page_limit': config.get('performance', {}).get('page_limit', 100)
        }
        extractor = create_extractor(extractor_name, extractor_config)
        max_workers = args.workers or config.get('performance', {}).get('max_workers', 2)
        
        logger.stage(f"🔧 MVP-Fusion Engine: {extractor.name}")
        logger.stage(f"⚡ Performance: {extractor.description}")
        logger.stage(f"🔧 Workers: {max_workers} | Formats: {len(extractor.get_supported_formats())}")
        
        # Determine output directory
        output_dir = None
        if args.output:
            output_dir = Path(args.output)
        elif config.get('output', {}).get('base_directory'):
            output_dir = Path(config['output']['base_directory']).expanduser()
        
        if output_dir:
            logger.stage(f"📁 Output directory: {output_dir}")
        
        # Execute command
        if args.file:
            # Process single file
            file_path = Path(args.file)
            if not file_path.exists():
                logger.logger.error(f"❌ File not found: {file_path}")
                sys.exit(1)
            
            result = process_single_file(extractor, file_path, output_dir)
            
        elif args.directory:
            # Process directory
            directory = Path(args.directory).expanduser()
            if not directory.exists():
                logger.logger.error(f"❌ Directory not found: {directory}")
                sys.exit(1)
            
            results = process_directory(extractor, directory, args.extensions, output_dir)
            
        elif args.config_directories:
            # Process all directories from config
            config_dirs = config.get('inputs', {}).get('directories', [])
            if not config_dirs:
                logger.logger.error(f"❌ No directories specified in config file")
                sys.exit(1)
            
            logger.stage(f"🗂️  Processing {len(config_dirs)} directories from config:")
            for config_dir in config_dirs:
                logger.stage(f"   - {config_dir}")
            
            all_results = []
            for config_dir in config_dirs:
                directory = Path(config_dir).expanduser()
                if not directory.exists():
                    logger.logger.warning(f"⚠️  Directory not found: {directory} (skipping)")
                    continue
                    
                logger.stage(f"\n📂 Processing directory: {directory}")
                extensions = config.get('files', {}).get('supported_extensions', args.extensions)
                results = process_directory(fusion, directory, extensions, output_dir)
                all_results.extend(results if isinstance(results, list) else [results])
            
            logger.success(f"\n✅ Processed {len(all_results)} total files across all directories")
            
        elif args.config and not args.file and not args.directory and not args.performance_test:
            # Auto-process directories from config file when only --config is provided
            config_dirs = config.get('inputs', {}).get('directories', [])
            if config_dirs:
                # Collect all files from all directories first
                logger.stage(f"🗂️  Scanning {len(config_dirs)} directories:")
                for config_dir in config_dirs:
                    logger.stage(f"   - {config_dir}")
                
                all_files = []
                extensions = config.get('files', {}).get('supported_extensions', args.extensions)
                
                for config_dir in config_dirs:
                    directory = Path(config_dir).expanduser()
                    if not directory.exists():
                        logger.logger.warning(f"⚠️  Directory not found: {directory} (skipping)")
                        continue
                    
                    # Collect files from this directory
                    files = []
                    for ext in extensions:
                        files.extend(directory.glob(f"**/*{ext}"))
                    all_files.extend(files)
                
                if not all_files:
                    logger.logger.error(f"❌ No files found in any directories")
                    sys.exit(1)
                
                # Show summary before processing
                file_types = {}
                for file_path in all_files:
                    ext = file_path.suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                
                logger.stage(f"\n📊 PROCESSING SUMMARY:")
                logger.stage(f"   Total files: {len(all_files)}")
                logger.stage(f"   File types: {dict(file_types)}")
                logger.stage(f"   Workers: {max_workers}")
                
                # Process everything in one batch
                logger.stage(f"\n🚀 Starting batch processing...")
                start_time = time.time()
                
                # Choose pipeline architecture based on configuration
                use_shared_memory = config.get('pipeline', {}).get('use_shared_memory', False)
                
                if use_shared_memory:
                    logger.stage(f"🏊 Using Shared Memory Pipeline (Edge Optimized)")
                    from pipeline.shared_memory_pipeline import SharedMemoryFusionPipeline
                    pipeline = SharedMemoryFusionPipeline(config)
                else:
                    logger.stage(f"🔄 Using Traditional In-Memory Pipeline")
                    from pipeline.fusion_pipeline import FusionPipeline
                    pipeline = FusionPipeline(config)
                
                batch_result = pipeline.process_files(extractor, all_files, output_dir or Path.cwd(), max_workers=max_workers)
                if len(batch_result) == 3:
                    results, extraction_time, resource_summary = batch_result
                else:
                    results, extraction_time = batch_result
                    resource_summary = None
                    
                total_time = time.time() - start_time
                
                # Calculate comprehensive metrics (InMemoryDocument objects)
                successful = sum(1 for doc in results if doc.success)
                failed = len(results) - successful
                total_pages = sum(doc.pages_processed for doc in results if doc.success)
                
                # Calculate input data sizes by scanning all attempted files directly
                total_input_bytes = 0
                skipped_large = 0
                
                # Scan all files that were attempted (not just results)
                for file_path in all_files:
                    try:
                        input_size = file_path.stat().st_size
                        total_input_bytes += input_size
                    except:
                        pass
                
                # Count skipped files from results
                for doc in results:
                    if not doc.success and doc.error_message and "pages (>100 limit)" in doc.error_message:
                        skipped_large += 1
                
                # Calculate output size from in-memory documents (exact calculation)
                total_output_bytes = 0
                output_file_count = 0
                total_memory_mb = 0
                
                for doc in results:
                    if doc.success:
                        # Get memory footprint (includes markdown + YAML + JSON)
                        doc_memory = doc.get_memory_footprint()
                        total_output_bytes += doc_memory
                        total_memory_mb += doc_memory / 1024 / 1024
                        output_file_count += 1
                
                logger.entity(f"   💾 In-memory processing: {total_memory_mb:.1f}MB total document memory")
                
                # Calculate metrics
                input_mb = total_input_bytes / 1024 / 1024
                output_mb = total_output_bytes / 1024 / 1024
                throughput_mb_sec = input_mb / total_time if total_time > 0 else 0
                compression_ratio = input_mb / output_mb if output_mb > 0 else 0
                pages_per_sec = total_pages / total_time if total_time > 0 else 0
                
                # True failures vs skips and warnings
                true_failures = failed - skipped_large
                warnings_count = sum(1 for doc in results if doc.success and doc.error_message)
                
                logger.stage(f"\n🚀 PROCESSING PERFORMANCE:")
                logger.stage(f"   🚀 PAGES/SEC: {pages_per_sec:.0f} (overall pipeline)")
                logger.stage(f"   ⚡ THROUGHPUT: {throughput_mb_sec:.1f} MB/sec raw document processing")
                
                # Add per-stage performance breakdown if available
                if resource_summary and 'stage_timings' in resource_summary:
                    logger.stage(f"\n📊 STAGE-BY-STAGE PERFORMANCE:")
                    stage_timings = resource_summary['stage_timings']
                    total_pages_for_stages = resource_summary.get('total_pages', total_pages)
                    
                    # Define stage display names
                    stage_names = {
                        'load': 'Conversion',
                        'classify': 'Classification',
                        'enrich': 'Enrichment',
                        'extract': 'Extraction',
                        'write': 'Writing'
                    }
                    
                    for stage_key, display_name in stage_names.items():
                        if stage_key in stage_timings:
                            timing = stage_timings[stage_key]
                            time_s = timing['time_ms'] / 1000
                            pages_sec = timing['pages_per_sec']
                            logger.stage(f"   • {display_name}: ~{pages_sec:,.0f} pages/sec ({time_s:.1f}s for {total_pages_for_stages:,} pages)")
                
                logger.success(f"\n✅ DATA TRANSFORMATION SUMMARY:")
                logger.stage(f"   📊 INPUT: {input_mb:.0f} MB across {len(results)} files ({total_pages:,} pages)")
                logger.stage(f"   📊 OUTPUT: {output_mb:.1f} MB in {output_file_count} markdown files")
                if output_mb > 0:
                    compression_percent = ((input_mb - output_mb) / input_mb) * 100
                    logger.stage(f"   🗜️  COMPRESSION: {compression_percent:.1f}% smaller (eliminated formatting, images, bloat)")
                else:
                    logger.stage(f"   🗜️  COMPRESSION: Unable to calculate (output scanning issue)")
                logger.stage(f"   📁 RESULTS: {successful} successful")
                if skipped_large > 0:
                    logger.stage(f"   ⏭️  SKIPPED: {skipped_large} files (>100 pages, too large for this mode)")
                if true_failures > 0:
                    logger.logger.error(f"   ❌ FAILED: {true_failures} files (corrupted or unsupported)")
                if warnings_count > 0:
                    logger.logger.warning(f"   ⚠️  WARNINGS: {warnings_count} files (minor PDF issues, but text extracted successfully)")
                logger.stage(f"   ⏱️  TOTAL TIME: {total_time:.2f}s")
                
                # Add system resource information if available
                if resource_summary:
                    logger.stage(f"\n💻 PROCESSING FOOTPRINT:")
                    if 'shared_memory_architecture' in resource_summary:
                        # Shared memory architecture stats
                        logger.stage(f"   🏊 SHARED MEMORY: {resource_summary['current_memory_mb']:.1f}MB")
                        logger.stage(f"   ⚡ MEMORY SAVINGS: {resource_summary['memory_efficiency_gain_percent']:.1f}%")
                        logger.stage(f"   📊 DOCUMENTS IN POOL: {resource_summary['documents_in_shared_pool']}")
                        logger.stage(f"   🌐 EDGE READY: {'✅ CloudFlare compatible' if resource_summary['edge_deployment_ready']['cloudflare_workers_compatible'] else '❌ Too large'}")
                    elif 'cpu_workers_used' in resource_summary:
                        # Traditional architecture stats
                        logger.stage(f"   🖥️  WORKERS: {resource_summary['cpu_workers_used']}/{resource_summary['cpu_cores_total']} cores (1 worker = 1 core)")
                        logger.entity(f"   🧠 MEMORY: {resource_summary['memory_peak_mb']:.1f} MB peak usage")
                        if resource_summary.get('memory_used_mb', 0) > 0:
                            logger.entity(f"   📈 PROCESSING MEMORY: {resource_summary['memory_used_mb']:.1f} MB during extraction")
                        logger.stage(f"   ⚡ EFFICIENCY: {resource_summary['efficiency_pages_per_worker']:.0f} pages/worker, {resource_summary['efficiency_mb_per_worker']:.1f} MB/worker")
                
                logger.success(f"   ✅ SUCCESS RATE: {(successful/len(results)*100):.1f}% ({successful}/{len(results)})")
            else:
                logger.logger.error(f"❌ No input specified and no directories in config file")
                sys.exit(1)
            
        elif args.performance_test:
            # Run performance test
            test_results = run_performance_test(extractor, max_workers)
            
            logger.stage(f"\n🏆 Performance Test Results:")
            for scenario, result in test_results.items():
                if 'error' not in result:
                    logger.stage(f"   {scenario}:")
                    logger.stage(f"     Rate: {result['docs_per_sec']:.1f} docs/sec")
                    logger.stage(f"     Speed: {result['chars_per_sec']:,.0f} chars/sec")
        
        # Processing complete - no additional summary needed
        
        # Export metrics if requested (UltraFastFusion doesn't have built-in metrics export)
        if args.export_metrics:
            metrics_data = {
                'extractor_workers': max_workers,
                'performance_metrics': extractor.get_performance_summary()
            }
            with open(args.export_metrics, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            logger.stage(f"📊 Basic metrics exported to {args.export_metrics}")
        
        
    except KeyboardInterrupt:
        logger.logger.warning(f"\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.logger.error(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _load_and_override_config(args) -> dict:
    """Load config file and apply CLI overrides (industry best practice)."""
    import yaml
    from pathlib import Path
    
    # Step 1: Load base configuration
    config = {}
    config_path = Path(args.config)
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        print(f"📋 Config: {config_path}")  # Keep this as print since logger isn't available yet
    else:
        if args.config == 'config/config.yaml':  # Default config missing
            print(f"❌ Default configuration file not found: {args.config}")
            print(f"💡 Please create config/config.yaml or specify a config file with --config")
            print(f"💡 Example: python fusion_cli.py --config /path/to/your/config.yaml")
        else:  # User-specified config missing
            print(f"❌ Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Step 2: Apply CLI overrides to config
    
    # Override pipeline stages based on CLI arguments
    if not config.get('pipeline'):
        config['pipeline'] = {}
    if not config['pipeline'].get('stages'):
        config['pipeline']['stages'] = {}
    
    # Determine which stages to run from CLI args
    if args.convert_only:
        stages_to_run = ['convert']
    elif args.classify_only:
        stages_to_run = ['classify']
    elif args.enrich_only:
        stages_to_run = ['enrich']
    elif args.extract_only:
        stages_to_run = ['extract']
    elif 'all' in args.stages:
        stages_to_run = ['convert', 'classify', 'enrich', 'extract']
    else:
        stages_to_run = args.stages
    
    # Set stage flags in config
    for stage in ['convert', 'classify', 'enrich', 'extract']:
        config['pipeline']['stages'][stage] = stage in stages_to_run
    
    # Store stages list for reference
    config['pipeline']['stages_to_run'] = stages_to_run
    
    # Override other settings
    if args.batch_size:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['batch_size'] = args.batch_size
    
    if args.workers:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['max_workers'] = args.workers
    
    if args.memory_limit:
        if not config.get('performance'):
            config['performance'] = {}
        config['performance']['max_memory_usage_gb'] = args.memory_limit
    
    return config


if __name__ == "__main__":
    main()