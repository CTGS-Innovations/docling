#!/usr/bin/env python3
"""
Continuous processor for duration-based benchmarking.
Processes files repeatedly for a specified duration with progress reporting.
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
import yaml
import importlib.util

# Import the main processor using importlib to handle hyphenated filename
spec = importlib.util.spec_from_file_location("mvp_hyper_core", "/app/mvp-hyper-core.py")
mvp_hyper_core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mvp_hyper_core)

from config_loader import load_config

UltraFastExtractor = mvp_hyper_core.UltraFastExtractor
process_batch_ultra = mvp_hyper_core.process_batch_ultra


def run_continuous_processing(duration_seconds: int = 30, progress_interval: int = 10):
    """Run continuous processing for specified duration with progress reporting."""
    
    # Load configuration
    config = load_config("/app/config.yaml" if Path("/app/config.yaml").exists() else "config.yaml")
    
    # Get all files to process
    all_files = config.get_input_files()
    if not all_files:
        print("❌ No files found to process")
        return
    
    # Initialize extractor
    extractor = UltraFastExtractor(cache_enabled=True)
    
    # Tracking variables
    start_time = time.time()
    end_time = start_time + duration_seconds
    last_report_time = start_time
    
    total_files_processed = 0
    total_pages_processed = 0
    cycles_completed = 0
    
    print(f"🚀 Starting continuous processing for {duration_seconds} seconds")
    print(f"📂 Processing {len(all_files)} files per cycle")
    print("=" * 60)
    
    # Process continuously until duration expires
    while time.time() < end_time:
        cycle_start = time.time()
        
        # Process all files once
        results = process_batch_ultra(all_files, extractor, config)
        
        # Update totals
        total_files_processed += results['total_files']
        total_pages_processed += results['total_pages']
        cycles_completed += 1
        
        # Progress reporting every 10 seconds
        current_time = time.time()
        elapsed = current_time - start_time
        
        if current_time - last_report_time >= progress_interval:
            pages_per_sec = total_pages_processed / elapsed if elapsed > 0 else 0
            files_per_sec = total_files_processed / elapsed if elapsed > 0 else 0
            
            print(f"[{int(elapsed):3d}s] Cycle {cycles_completed:3d} | "
                  f"Files: {total_files_processed:5d} ({files_per_sec:.1f}/s) | "
                  f"Pages: {total_pages_processed:6d} ({pages_per_sec:.1f}/s)")
            
            last_report_time = current_time
    
    # Final results
    total_time = time.time() - start_time
    final_pages_per_sec = total_pages_processed / total_time if total_time > 0 else 0
    final_files_per_sec = total_files_processed / total_time if total_time > 0 else 0
    
    print("=" * 60)
    print("✅ CONTINUOUS PROCESSING COMPLETE")
    print(f"⏱️  Duration: {total_time:.1f}s")
    print(f"🔄 Cycles completed: {cycles_completed}")
    print(f"📄 Total files processed: {total_files_processed:,}")
    print(f"📑 Total pages processed: {total_pages_processed:,}")
    print(f"⚡ Average throughput: {final_pages_per_sec:.1f} pages/sec")
    print(f"📊 Average throughput: {final_files_per_sec:.1f} files/sec")
    
    # Output results for the benchmark orchestrator to parse
    results_json = {
        'duration': total_time,
        'cycles': cycles_completed,
        'total_files': total_files_processed,
        'total_pages': total_pages_processed,
        'pages_per_second': final_pages_per_sec,
        'files_per_second': final_files_per_sec,
        'timestamp': datetime.now().isoformat()
    }
    
    print("\n📊 RESULTS_JSON_START")
    print(json.dumps(results_json))
    print("RESULTS_JSON_END")
    
    return results_json


if __name__ == "__main__":
    # Get duration from command line or use default
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    run_continuous_processing(duration)