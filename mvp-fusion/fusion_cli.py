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
import logging
from pathlib import Path
from typing import List, Dict, Any
import json

# Import fusion components
from pipeline.fusion_pipeline import FusionPipeline
from performance.fusion_metrics import FusionMetrics


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('fusion_pipeline.log', mode='a')
        ]
    )


def process_single_file(pipeline: FusionPipeline, file_path: Path) -> Dict[str, Any]:
    """Process a single file and return results."""
    print(f"Processing: {file_path}")
    
    start_time = time.time()
    result = pipeline.process_document(file_path)
    processing_time = time.time() - start_time
    
    if result['status'] == 'success':
        metadata = result['processing_metadata']
        print(f"  ✅ Success - {processing_time:.3f}s")
        print(f"     Pages/sec: {metadata['pages_per_sec']:.1f}")
        print(f"     Entities: {metadata['entities_found']}")
        print(f"     Engine: {metadata['engine_used']}")
        print(f"     Outputs: {list(result['output_paths'].keys())}")
    else:
        print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
    
    return result


def process_directory(pipeline: FusionPipeline, directory: Path, 
                     file_extensions: List[str] = None) -> List[Dict[str, Any]]:
    """Process all files in a directory."""
    if file_extensions is None:
        file_extensions = ['.txt', '.md', '.pdf', '.docx', '.doc']
    
    # Find all files
    files = []
    for ext in file_extensions:
        files.extend(directory.glob(f"**/*{ext}"))
    
    if not files:
        print(f"No files found in {directory} with extensions {file_extensions}")
        return []
    
    print(f"Found {len(files)} files to process in {directory}")
    
    results = []
    start_time = time.time()
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] ", end="")
        result = process_single_file(pipeline, file_path)
        results.append(result)
        
        # Show progress
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            print(f"\nProgress: {i}/{len(files)} files ({rate:.1f} files/sec)")
    
    # Final statistics
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = len(results) - successful
    
    print(f"\n📊 Processing Complete:")
    print(f"   Total files: {len(results)}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average rate: {len(results)/total_time:.1f} files/sec")
    
    return results


def run_performance_test(pipeline: FusionPipeline) -> Dict[str, Any]:
    """Run performance benchmark test."""
    print("🚀 Running MVP-Fusion Performance Test...")
    
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
        print(f"\n📋 Testing {scenario_name} ({len(content)} chars, {iterations} iterations)...")
        
        start_time = time.time()
        scenario_results = []
        
        for i in range(iterations):
            result = pipeline.process_document(f"test_doc_{i}.txt", content)
            scenario_results.append(result)
            
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                print(f"  Progress: {i+1}/{iterations} ({rate:.1f} docs/sec)")
        
        # Calculate statistics
        total_time = time.time() - start_time
        successful = sum(1 for r in scenario_results if r['status'] == 'success')
        
        if successful > 0:
            avg_processing_time = sum(
                r['processing_metadata']['total_time_ms'] 
                for r in scenario_results if r['status'] == 'success'
            ) / successful
            
            total_entities = sum(
                r['processing_metadata']['entities_found']
                for r in scenario_results if r['status'] == 'success'
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
                'total_entities': total_entities,
                'chars_per_doc': len(content)
            }
            
            print(f"  ✅ {successful}/{iterations} successful")
            print(f"  📊 Rate: {docs_per_sec:.1f} docs/sec")
            print(f"  ⚡ Speed: {chars_per_sec:,.0f} chars/sec")
            print(f"  🎯 Entities: {total_entities} total")
        else:
            results[scenario_name] = {'error': 'All tests failed'}
    
    return results


def print_performance_summary(pipeline: FusionPipeline):
    """Print comprehensive performance summary."""
    metrics = pipeline.get_performance_metrics()
    
    print("\n" + "="*60)
    print("🎯 MVP-FUSION PERFORMANCE SUMMARY")
    print("="*60)
    
    # Pipeline performance
    print(f"📄 Documents processed: {metrics['documents_processed']}")
    print(f"⏱️  Average time per doc: {metrics.get('avg_processing_time_per_doc', 0):.3f}s")
    print(f"🚀 Pages per second: {metrics.get('pages_per_second', 0):.1f}")
    print(f"❌ Error rate: {metrics.get('error_rate', 0):.1%}")
    
    # Engine performance
    fusion_metrics = metrics.get('fusion_engine_metrics', {})
    if fusion_metrics:
        print(f"\n🔧 Engine Performance:")
        print(f"   Pages/sec: {fusion_metrics.get('pages_per_second', 0):.1f}")
        print(f"   Entities/doc: {fusion_metrics.get('entities_per_document', 0):.1f}")
        print(f"   Engine usage: {fusion_metrics.get('engine_usage', {})}")
    
    # Batch processor performance
    batch_metrics = metrics.get('batch_processor_metrics', {})
    if batch_metrics:
        print(f"\n📦 Batch Processing:")
        print(f"   Docs/sec: {batch_metrics.get('documents_per_second', 0):.1f}")
        print(f"   Parallel efficiency: {batch_metrics.get('parallel_efficiency', 0):.1%}")
        print(f"   Avg docs/batch: {batch_metrics.get('avg_docs_per_batch', 0):.1f}")
    
    print("\n" + "="*60)


def main():
    """Main command line interface."""
    parser = argparse.ArgumentParser(
        description="MVP-Fusion: High-Performance Document Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fusion_cli.py --file document.pdf
  python fusion_cli.py --directory ~/documents/ --extensions .pdf .docx
  python fusion_cli.py --config-directories --config config/fusion_config.yaml --stages all
  python fusion_cli.py --config-directories --config config/fusion_config.yaml --convert-only
  python fusion_cli.py --config-directories --config config/fusion_config.yaml --stages convert classify
  python fusion_cli.py --performance-test --verbose
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--file', '-f', type=str, help='Process single file')
    input_group.add_argument('--directory', '-d', type=str, help='Process directory')
    input_group.add_argument('--config-directories', action='store_true',
                           help='Process all directories specified in config file')
    input_group.add_argument('--performance-test', '-t', action='store_true', 
                           help='Run performance benchmark')
    
    # Configuration options
    parser.add_argument('--config', '-c', type=str, help='Configuration file path')
    parser.add_argument('--output', '-o', type=str, help='Output directory')
    parser.add_argument('--batch-size', '-b', type=int, default=32, 
                       help='Batch size for parallel processing')
    
    # File options
    parser.add_argument('--extensions', nargs='+', default=['.txt', '.md', '.pdf', '.docx'],
                       help='File extensions to process')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process directories recursively')
    
    # Performance options
    parser.add_argument('--workers', '-w', type=int, help='Number of parallel workers')
    parser.add_argument('--memory-limit', type=int, help='Memory limit in GB')
    
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
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Minimal output')
    parser.add_argument('--export-metrics', type=str, help='Export metrics to JSON file')
    
    args = parser.parse_args()
    
    # Setup logging
    if not args.quiet:
        setup_logging(args.verbose)
    
    try:
        # Initialize pipeline
        print("🔧 Initializing MVP-Fusion Pipeline...")
        pipeline = FusionPipeline(args.config)
        
        # Override config with command line args
        if args.output:
            pipeline.output_directory = Path(args.output)
            pipeline._setup_output_directories()
        
        if args.workers:
            pipeline.batch_processor.max_workers = args.workers
        
        # Configure pipeline stages
        stages_to_run = _configure_pipeline_stages(args, pipeline)
        
        print(f"✅ Pipeline initialized")
        print(f"   Output directory: {pipeline.output_directory}")
        print(f"   Strategy: {pipeline.strategy}")
        print(f"   Max workers: {pipeline.batch_processor.max_workers}")
        print(f"   Stages to run: {', '.join(stages_to_run)}")
        
        # Execute command
        if args.file:
            # Process single file
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"❌ File not found: {file_path}")
                sys.exit(1)
            
            result = process_single_file(pipeline, file_path)
            
        elif args.directory:
            # Process directory
            directory = Path(args.directory).expanduser()
            if not directory.exists():
                print(f"❌ Directory not found: {directory}")
                sys.exit(1)
            
            results = process_directory(pipeline, directory, args.extensions)
            
        elif args.config_directories:
            # Process all directories from config
            config_dirs = pipeline.config.get('inputs', {}).get('directories', [])
            if not config_dirs:
                print("❌ No directories specified in config file")
                sys.exit(1)
            
            print(f"🗂️  Processing {len(config_dirs)} directories from config:")
            for config_dir in config_dirs:
                print(f"   - {config_dir}")
            
            all_results = []
            for config_dir in config_dirs:
                directory = Path(config_dir).expanduser()
                if not directory.exists():
                    print(f"⚠️  Directory not found: {directory} (skipping)")
                    continue
                    
                print(f"\n📂 Processing directory: {directory}")
                extensions = pipeline.config.get('files', {}).get('supported_extensions', args.extensions)
                results = process_directory(pipeline, directory, extensions)
                all_results.extend(results if isinstance(results, list) else [results])
            
            print(f"\n✅ Processed {len(all_results)} total files across all directories")
            
        elif args.performance_test:
            # Run performance test
            test_results = run_performance_test(pipeline)
            
            print(f"\n🏆 Performance Test Results:")
            for scenario, result in test_results.items():
                if 'error' not in result:
                    print(f"   {scenario}:")
                    print(f"     Rate: {result['docs_per_sec']:.1f} docs/sec")
                    print(f"     Speed: {result['chars_per_sec']:,.0f} chars/sec")
        
        # Print performance summary
        if not args.quiet:
            print_performance_summary(pipeline)
        
        # Export metrics if requested
        if args.export_metrics:
            pipeline.metrics.export_metrics(args.export_metrics)
            print(f"📊 Metrics exported to {args.export_metrics}")
        
        print("\n🎉 MVP-Fusion processing complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _configure_pipeline_stages(args, pipeline) -> List[str]:
    """Configure which pipeline stages to run based on CLI arguments."""
    # Handle stage-specific flags
    if args.convert_only:
        return ['convert']
    elif args.classify_only:
        return ['classify']
    elif args.enrich_only:
        return ['enrich']
    elif args.extract_only:
        return ['extract']
    
    # Handle --stages argument
    if 'all' in args.stages:
        stages = ['convert', 'classify', 'enrich', 'extract']
    else:
        stages = args.stages
    
    # Configure pipeline stages
    if hasattr(pipeline, 'config'):
        if 'pipeline' not in pipeline.config:
            pipeline.config['pipeline'] = {}
        if 'stages' not in pipeline.config['pipeline']:
            pipeline.config['pipeline']['stages'] = {}
        
        # Set stage flags
        for stage in ['convert', 'classify', 'enrich', 'extract']:
            pipeline.config['pipeline']['stages'][stage] = stage in stages
    
    return stages


if __name__ == "__main__":
    main()